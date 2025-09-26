from odoo import models, fields, api, _, Command
import logging
import base64
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class PagoEnganche(models.Model):
    _name = 'pago.enganche'
    _description = 'Pagos de Enganche'
    _order = 'payment_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('scheduled', 'Programado'),
        ('due', 'Vencido'),
        ('received', 'Recibido'),
        ('confirmed', 'Confirmado'),
        ('anulado', 'Anulado')
    ], string='Estado', default='draft', tracking=True)

    expected_date = fields.Date(
        string='Fecha Esperada',
        required=True,
        tracking=True
    )

    order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        required=True,
        tracking=True
    )

    amount = fields.Float(
        string='Monto',
        required=True,
        tracking=True
    )

    amount_received = fields.Float(
        string='Monto recibido',
        tracking=True
    )

    payment_number = fields.Integer(
        string='Número de Pago',
        required=True
    )

    total_payments = fields.Integer(
        string='Total de Pagos',
        required=True
    )

    payment_sequence = fields.Char(
        string='Secuencia de Pago',
        compute='_compute_payment_sequence',
        store=True
    )

    deposit_number = fields.Char(
        string='Número de Depósito',
        tracking=True,
        copy=False
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        domain="[('type', 'in', ['bank', 'cash'])]",
        tracking=True
    )

    boleta = fields.Char(
        string='Número de Boleta',
        tracking=True,
        copy=False
    )

    # Mark the old field as deprecated (keep it temporarily for data migration if needed)
    payment_type_old = fields.Selection([
        ('cash', 'Efectivo'),
        ('transfer', 'Transferencia'),
        ('check', 'Cheque'),
        ('other', 'Otro')
    ], string='Tipo de Pago (Obsoleto)', tracking=True)

    # Define the new field
    payment_type_id = fields.Many2one(
        'pago.enganche.payment.type',
        string='Tipo de Pago',
        tracking=True,
        ondelete='restrict'
    )

    description = fields.Text(
        string='Descripción',
        tracking=True
    )

    received_date = fields.Date(
        string='Fecha de Recepción',
        tracking=True,
        copy=False,
        help='Fecha en que se recibió efectivamente el pago'
    )

    move_id = fields.Many2one(
        'account.move',
        string='Asiento Contable',
        readonly=True
    )

    recibo_number = fields.Char(
        string='Número de Recibo',
        readonly=True,
        copy=False,
        tracking=True
    )

    previous_balance = fields.Monetary(
        string='Saldo Anterior',
        compute='_compute_balances',
        currency_field='currency_id',
        store=False,
    )

    new_balance = fields.Monetary(
        string='Nuevo Saldo',
        compute='_compute_balances',
        currency_field='currency_id',
        store=False,
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='order_id.currency_id',
        store=True,
    )

    # Overpayment tracking fields
    is_overpayment = fields.Boolean(
        string='Es Sobrepago',
        compute='_compute_balances',
        store=False,
        help='Indica si este pago resulta en un sobrepago del enganche'
    )

    overpayment_amount = fields.Monetary(
        string='Monto de Sobrepago',
        compute='_compute_balances',
        currency_field='currency_id',
        store=False,
        help='Monto pagado en exceso del enganche acordado'
    )

    total_paid_to_date = fields.Monetary(
        string='Total Pagado a la Fecha',
        compute='_compute_balances',
        currency_field='currency_id',
        store=False,
        help='Total pagado incluyendo este pago'
    )

    banco_emisor_id = fields.Many2one(
        'res.bank',
        string='Banco Emisor',
        tracking=True
    )

    amount_received_text = fields.Char(
        string='Monto Recibido en Letras',
        compute='_compute_amount_received_text',
        store=False,
    )

    computed_amount = fields.Float(
        string='Monto real',
        compute='_compute_computed_amount',
        readonly=True,
        store=False
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        compute='_compute_company_id',
        store=True,
        readonly=True
    )

    # New fields for pivot table analysis
    cliente = fields.Char(
        string='Cliente',
        related='order_id.partner_id.name',
        store=True,
        readonly=True,
        help='Nombre del cliente de la orden de venta'
    )

    propiedad = fields.Char(
        string='Propiedad',
        related='order_id.property_id.name',
        store=True,
        readonly=True,
        help='Nombre de la propiedad de la orden de venta'
    )

    cliente_propiedad = fields.Char(
        string='Cliente - Propiedad',
        compute='_compute_cliente_propiedad',
        store=True,
        help='Concatenación de cliente y propiedad para análisis'
    )

    @api.depends('amount_received', 'currency_id')
    def _compute_amount_received_text(self):
        for record in self:
            if record.amount_received:
                try:
                    from num2words import num2words
                    amount_int = int(record.amount_received)
                    amount_decimal = round((record.amount_received - amount_int) * 100) 
                    
                    text = num2words(amount_int, lang='es').capitalize() + " quetzales"
                    text += f' con {amount_decimal}/100'
                    
                    #currency_name = record.currency_id.name or 'PESOS'
                    record.amount_received_text = f'{text}'
                except ImportError:
                    record.amount_received_text = 'Error: num2words library not installed'
            else:
                record.amount_received_text = False

    @api.depends('payment_number', 'total_payments')
    def _compute_payment_sequence(self):
        for record in self:
            record.payment_sequence = f'Pago {record.payment_number} de {record.total_payments}'

    @api.model
    def create(self, vals):
        # If total_payments is not provided, calculate it from existing payments
        if 'total_payments' not in vals and vals.get('order_id'):
            existing_payments = self.search([('order_id', '=', vals['order_id'])])
            if existing_payments:
                vals['total_payments'] = max(payment.total_payments for payment in existing_payments)
            else:
                vals['total_payments'] = 1  # If this is the first payment
        
        # Generate sequence number if needed
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pago.enganche') or _('New')
        
        # Check order status and set state accordingly
        if vals.get('order_id'):
            order = self.env['sale.order'].browse(vals['order_id'])
            if order.state not in ['draft', 'sent', 'cancel']:
                vals['state'] = 'scheduled'
        
        return super().create(vals)

    def action_schedule(self):
        self.state = 'scheduled'

    def action_mark_due(self):
        self.state = 'due'

    def action_receive(self):
        for record in self:
            # Get proyecto from order
            proyecto = record.order_id.proyecto_id
            if not proyecto:
                raise UserError(_('No se puede generar el recibo: La orden no tiene un proyecto asignado.'))

            # Generate and assign recibo number if not already assigned
            if not record.recibo_number:
                record.recibo_number = proyecto.get_next_recibo_sequence()

            return self.env.ref('atd_propiedades.action_report_pago_enganche').report_action(record)

    def action_confirm(self):
        self.state = 'confirmed'

    def action_open_receive_wizard(self):
        self.ensure_one()
        return {
            'name': 'Recibir Pago',
            'type': 'ir.actions.act_window',
            'res_model': 'pago.enganche.receive.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_pago_enganche_id': self.id,
            }
        }

    def _cron_check_due_payments(self):
        """Check and update status of payments that are due"""
        due_payments = self.search([
            ('state', '=', 'scheduled'),
            ('expected_date', '<', fields.Date.today())
        ])
        due_payments.action_mark_due()

    def write(self, vals):
        """Override write to handle state changes"""
        _logger.info('Write method called with vals: %s', vals)
        if vals.get('state') == 'received':
            _logger.info('Processing received state change')
            # If changing to received state via direct write, call action_receive
            records_to_receive = self.filtered(lambda r: r.state != 'received')
            _logger.info('Records to receive: %s', records_to_receive)
            result = super().write(vals)
            for record in records_to_receive:
                # Generate recibo number if needed
                proyecto = record.order_id.proyecto_id
                if not record.recibo_number and proyecto:
                    record.recibo_number = proyecto.get_next_recibo_sequence()
                # Return the report action for the last record
                if record == records_to_receive[-1]:
                    _logger.info('Returning report action for record: %s', record)
                    return self.env.ref('atd_propiedades.action_report_pago_enganche').report_action(record)
            return result
        return super().write(vals)

    @api.depends('order_id', 'order_id.enganche_amount', 'amount_received', 'state', 'recibo_number', 'order_id.pago_enganche_ids.state', 'order_id.pago_enganche_ids.amount_received', 'order_id.pago_enganche_ids.recibo_number')
    def _compute_balances(self):
        for record in self:
            if not record.order_id:
                record.previous_balance = 0
                record.new_balance = 0
                record.is_overpayment = False
                record.overpayment_amount = 0
                record.total_paid_to_date = 0
                continue
                
            # Get all valid payments for this order (received or confirmed, not anulado)
            valid_payments = record.order_id.pago_enganche_ids.filtered(
                lambda p: p.state in ['received', 'confirmed'] and p.id != record.id
            )
            
            # Sort payments by recibo_number to get chronological order
            # If no recibo_number, use payment_number as fallback
            sorted_payments = valid_payments.sorted(
                lambda p: (p.recibo_number or '999999', p.payment_number)
            )
            
            # Get payments that came BEFORE the current payment
            if record.recibo_number:
                # Use recibo_number for chronological order
                previous_payments = sorted_payments.filtered(
                    lambda p: p.recibo_number and p.recibo_number < record.recibo_number
                )
            else:
                # If current payment has no recibo_number, use payment_number
                previous_payments = sorted_payments.filtered(
                    lambda p: p.payment_number < record.payment_number
                )
            
            # Calculate total paid from previous payments only
            total_paid = sum(previous_payments.mapped('amount_received'))
            
            # Get total enganche amount from sale order
            total_to_pay = record.order_id.enganche_amount
            
            # Calculate previous balance (minimum 0 to avoid negative balances)
            record.previous_balance = max(0, total_to_pay - total_paid)
            
            # Calculate values including current payment
            if record.state in ['received', 'confirmed']:
                current_payment = record.amount_received
            else:
                current_payment = 0
                
            # Total paid including current payment
            record.total_paid_to_date = total_paid + current_payment
            
            # Check for overpayment
            if record.total_paid_to_date > total_to_pay:
                record.is_overpayment = True
                record.overpayment_amount = record.total_paid_to_date - total_to_pay
                record.new_balance = 0  # Balance is 0 when overpaid
            else:
                record.is_overpayment = False
                record.overpayment_amount = 0
                record.new_balance = max(0, total_to_pay - record.total_paid_to_date)

    def action_send_receipt_email(self):
        self.ensure_one()
        
        # Generate PDF report
        report = self.env['ir.actions.report']._get_report_from_name('atd_propiedades.action_report_pago_enganche')
        pdf_content, _ = report._render(report_ref='atd_propiedades.action_report_pago_enganche', res_ids=[self.id])
        

        # Prepare email template
        mail_template = self.env.ref('atd_propiedades.email_template_pago_enganche', raise_if_not_found=False)
        if not mail_template:
            raise ValidationError('Email template not found!')

        # Add PDF as attachment to the email
        attachment_name = f'Recibo_de_caja_{self.name}.pdf'
        #attachment_name = fields.Char(string='Nombre del archivo', tracking=True)
        attachment_vals = {
            'name': attachment_name,
            'datas': base64.b64encode(pdf_content),
            'res_model': 'pago.enganche',
            'res_id': self.id,
            'type': 'binary',
        }
        attachment = self.env['ir.attachment'].create(attachment_vals)

        # Send email with attachment
        mail_template.with_context(
            attachment_ids=[attachment.id]
        ).send_mail(
            self.id,
            force_send=True
        )

        # Show success message to user
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Recibo enviado por correo exitosamente',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_download_report(self):
        return self.env.ref('atd_propiedades.action_report_pago_enganche').report_action(self)

    def action_anular(self):
        """Anular el pago de enganche y crear uno nuevo"""
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(_('Solo los administradores pueden anular pagos.'))
        
        # Cancel associated account move if it exists
        if self.move_id:
            self.move_id.button_cancel()
        
        # Create duplicate payment
        new_payment = self.copy({
            'state': 'due' if self.expected_date < fields.Date.today() else 'scheduled',
            'amount_received': 0,
            'received_date': False,
            'deposit_number': False,
            'boleta': False,
            'recibo_number': False,
            'move_id': False,
        })
        
        # Mark original as anulado and set amount to zero
        self.write({
            'state': 'anulado',
            'amount': 0
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Pago anulado y nuevo pago creado'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_open_anular_wizard(self):
        """Open the anular wizard"""
        self.ensure_one()
        return {
            'name': _('Confirmar Anulación'),
            'type': 'ir.actions.act_window',
            'res_model': 'pago.enganche.anular.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_pago_enganche_id': self.id,
            }
        }

    @api.depends('state', 'amount', 'amount_received')
    def _compute_computed_amount(self):
        for record in self:
            if record.state == 'anulado':
                record.computed_amount = 0
            elif record.state == 'received':
                record.computed_amount = record.amount_received
            elif record.state in (  'scheduled', 'draft' ):
                record.computed_amount = record.amount
            else:
                record.computed_amount = 0

    @api.depends('order_id')
    def _compute_company_id(self):
        for record in self:
            record.company_id = record.order_id.company_id

    @api.depends('cliente', 'propiedad')
    def _compute_cliente_propiedad(self):
        for record in self:
            cliente = record.cliente or ''
            propiedad = record.propiedad or ''
            if cliente and propiedad:
                record.cliente_propiedad = f"{cliente} - {propiedad}"
            elif cliente:
                record.cliente_propiedad = cliente
            elif propiedad:
                record.cliente_propiedad = propiedad
            else:
                record.cliente_propiedad = ''

    def action_open_edit_wizard(self):
        self.ensure_one()
        return {
            'name': 'Editar Pago',
            'type': 'ir.actions.act_window',
            'res_model': 'pago.enganche.edit.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }

    def action_recalculate_balances(self):
        """Recalculate balances for all payments in the order"""
        self.ensure_one()
        # Trigger recalculation by touching the computed fields
        payments = self.order_id.pago_enganche_ids
        for payment in payments:
            payment._compute_balances()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Balances recalculados correctamente'),
                'type': 'success',
                'sticky': False,
            }
        }