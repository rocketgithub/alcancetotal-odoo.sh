from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    property_id = fields.Many2one(
        'real.estate.property',
        string='Propiedad principal',
        compute='_compute_propiedad',
        store=True,
        readonly=True
    )

    @api.depends('order_line')
    def _compute_propiedad(self):
        for record in self:
            property_id = False
            if record.order_line:
                # Get the first line with a property_id
                for line in record.order_line:
                    if line.property_id and line.property_id.parent_property_id != None:
                        property_id = line.property_id
                        break
            record.property_id = property_id

    @api.depends('order_line', 'order_line.property_id', 'order_line.property_id.proyecto_id')
    def _compute_proyecto_id(self):
        for record in self:
            proyecto_id = False
            if record.order_line:
                # Get the first line with a property_id that has a proyecto_id
                for line in record.order_line:
                    if line.property_id and line.property_id.proyecto_id:
                        proyecto_id = line.property_id.proyecto_id
                        break
            record.proyecto_id = proyecto_id
    

    @api.depends('company_id.enable_real_estate')
    def _compute_show_property(self):
        for record in self:
            record.show_property = record.company_id.enable_real_estate

    show_property = fields.Boolean(
        compute='_compute_show_property',
        store=False
    )

    enable_real_estate = fields.Boolean(
        related='company_id.enable_real_estate',
        store=False
    )

    enganche_percentage = fields.Float(
        string='Porcentaje de Enganche',
        default=0.20,
        help='Porcentaje del total que será pagado como enganche',
        digits=(3, 2)
    )

    @api.constrains('enganche_percentage')
    def _check_enganche_percentage(self):
        for record in self:
            if record.enganche_percentage < 0 or record.enganche_percentage > 1:
                raise ValidationError(_('El porcentaje de enganche debe estar entre 0 y 1 (ejemplo: 0.30 para 30%)'))

    enganche_amount = fields.Monetary(
        string='Monto Enganche',
        compute='_compute_enganche_amount',
        store=True
    )
    enganche_payments = fields.Integer(
        string='Número de Cuotas',
        default=1,
        help='Número de cuotas en que se dividirá el enganche'
    )
    first_payment_date = fields.Date(
        string='Fecha Primer Pago',
        default=fields.Date.today
    )
    @api.depends('enganche_amount')
    def _compute_first_payment_default(self):
        for record in self:
            record.first_payment_amount = 10000

    first_payment_amount = fields.Monetary(
        string='Reserva',
        compute='_compute_first_payment_default',
        store=True,
        readonly=False,
        help='Monto del primer pago del enganche (mínimo Q10,000)',
        default=10000
    )
    remaining_payment_amount = fields.Monetary(
        string='Monto Cuotas Restantes',
        help='Monto de cada cuota restante del enganche',
        readonly=True
    )

    @api.depends('amount_total', 'enganche_percentage')
    def _compute_enganche_amount(self):
        for order in self:
            old_enganche = order.enganche_amount
            order.enganche_amount = order.amount_total * order.enganche_percentage
            
            # If enganche amount changed and there are payments, trigger balance recalculation
            if old_enganche != order.enganche_amount and order.pago_enganche_ids:
                # Trigger recalculation of balances for all payments
                for payment in order.pago_enganche_ids:
                    payment._compute_balances()

    pago_enganche_ids = fields.One2many(
        'pago.enganche',
        'order_id',
        string='Pagos de Enganche'
    )

    enable_real_estate = fields.Boolean(
        related='company_id.enable_real_estate',
        string='Bienes Raíces Habilitado',
        readonly=True
    )

    acuerdo_ids = fields.One2many(
        'acuerdo.compra.venta',
        'order_id',
        string='Acuerdos de Compra Venta'
    )

    acuerdo_id = fields.One2many(
        'acuerdo.compra.venta',
        'order_id',
        string='Acuerdo de Compra Venta'
    )

    acuerdo_count = fields.Integer(
        string='Acuerdos',
        compute='_compute_acuerdo_count'
    )

    def _compute_acuerdo_count(self):
        for order in self:
            order.acuerdo_count = self.env['acuerdo.compra.venta'].search_count([
                ('order_id', '=', order.id)
            ])

    @api.depends('enganche_amount', 'first_payment_amount', 'enganche_payments', 'pago_enganche_ids.state', 'pago_enganche_ids.amount')
    def _compute_remaining_payments(self):
        for order in self:
            order.remaining_payment_amount = order._calculate_remaining_payment_amount()[0]

    def _calculate_remaining_payment_amount(self):
        """Helper method to calculate remaining payment amount and related values.
        Returns: tuple(remaining_payment_amount, remaining_amount, new_payments_count)
        """
        self.ensure_one()
        
        # Get existing confirmed and anulado payments
        existing_payments = self.pago_enganche_ids.filtered(
            lambda p: p.state not in ['draft', 'scheduled', 'due']
        )
        # Only count non-anulado payments for existing amount
        confirmed_payments = existing_payments.filtered(lambda p: p.state != 'anulado')
        existing_amount = sum(confirmed_payments.mapped('amount_received'))
        
        # Calculate remaining amount to be distributed
        remaining_amount = self.enganche_amount - existing_amount
        
        # Determine number of new payments needed
        new_payments_count = self.enganche_payments - len(confirmed_payments)
        
        # If no confirmed payments exist and we need more than one payment,
        # subtract first payment from remaining amount
        if not confirmed_payments and new_payments_count > 1:
            remaining_amount -= self.first_payment_amount
            new_payments_count -= 1
        
        # Calculate payment amount
        payment_amount = 0.0
        if remaining_amount > 0 and new_payments_count > 0:
            payment_amount = round(remaining_amount / new_payments_count, 2)
            
        return payment_amount, remaining_amount, new_payments_count

    def action_compute_enganche(self):
        self.ensure_one()
        
        if self.state not in ('draft', 'sent'):
            raise UserError('No se pueden calcular los pagos de enganche en una orden que no sea presupuesto.')
        
        # Calculate payment amount and get related values
        payment_amount, remaining_amount, new_payments_count = self._calculate_remaining_payment_amount()
        
        if new_payments_count <= 0:
            raise UserError(
                'El número de pagos seleccionado debe ser mayor al número de pagos ya confirmados'
            )
        
        # Delete existing draft/scheduled payments
        self.pago_enganche_ids.filtered(
            lambda p: p.state in ['draft', 'scheduled', 'due']
        ).unlink()
        
        # Get existing confirmed payments and sort them by date
        confirmed_payments = self.pago_enganche_ids.filtered(
            lambda p: p.state not in ['draft', 'scheduled', 'due', 'anulado']
        ).sorted('expected_date')
        
        # Find the first received payment
        first_received = confirmed_payments.filtered(lambda p: p.state == 'received')
        
        # Resequence confirmed payments starting from the first received payment
        next_payment_number = 1
        if first_received:
            # Get index of first received payment
            first_received_index = confirmed_payments.ids.index(first_received[0].id)
            # Update payment numbers for all payments from first received onwards
            for payment in confirmed_payments[first_received_index:]:
                payment.write({'payment_number': next_payment_number})
                next_payment_number += 1
        else:
            # If no received payments, start with payment number 1
            next_payment_number = 1
        
        # Create first payment if no confirmed payments exist
        if not confirmed_payments:
            self.env['pago.enganche'].create({
                'order_id': self.id,
                'amount': self.first_payment_amount,
                'payment_number': 1,
                'total_payments': self.enganche_payments,
                'expected_date': self.first_payment_date,
                'state': 'draft'
            })
            next_payment_number = 2
        
        # Create remaining payments if needed
        if remaining_amount > 0 and new_payments_count > 0:
            # Calculate total of regular payments
            total_regular_payments = payment_amount * (new_payments_count - 1)
            # Last payment adjusts for rounding differences
            last_payment_amount = round(remaining_amount - total_regular_payments, 2)
            
            # Determine the base date for new payments
            # Use the last confirmed payment's date only if there is more than 1 confirmed payment,
            # otherwise use first_payment_date
            if len(confirmed_payments) > 1:
                base_date = confirmed_payments[-1].expected_date
            else:
                base_date = self.first_payment_date
            
            for i in range(new_payments_count):
                amount = last_payment_amount if i == new_payments_count - 1 else payment_amount
                # Add months from the base date (last confirmed payment or first payment date)
                # i+1 because we want the first new payment to be 1 month after the base date
                expected_date = base_date + relativedelta(months=i+1)
                self.env['pago.enganche'].create({
                    'order_id': self.id,
                    'amount': amount,
                    'payment_number': next_payment_number + i,
                    'total_payments': self.enganche_payments,
                    'expected_date': expected_date,
                    'state': 'draft'
                })
        
        # Update total_payments for all payments
        self.pago_enganche_ids.write({'total_payments': self.enganche_payments})
        
        # Update the remaining_payment_amount field
        self.write({
            'remaining_payment_amount': payment_amount
        })

    def write(self, vals):
        """Override write to handle property-related lines"""
        # If order lines are being modified
        if 'order_line' in vals:
            lines_to_remove = []
            for operation in vals['order_line']:
                # Check for line removal operations (2 is the removal operation code)
                if operation[0] == 2:
                    line_id = operation[1]
                    line = self.env['sale.order.line'].browse(line_id)
                    if line.property_id and line.property_id.child_property_ids:
                        # Find child property lines
                        child_lines = self.order_line.filtered(
                            lambda l: l.property_id in line.property_id.child_property_ids
                        )
                        lines_to_remove.extend([(2, child.id, 0) for child in child_lines])
            
            if lines_to_remove:
                vals['order_line'].extend(lines_to_remove)
                
        return super().write(vals)

    def action_view_acuerdo(self):
        self.ensure_one()
        acuerdo = self.acuerdo_id
        if not acuerdo:
            # Create acuerdo if it doesn't exist
            acuerdo = self.env['acuerdo.compra.venta'].create({
                'order_id': self.id,
            })
        
        return {
            'name': _('Acuerdo de Compra Venta'),
            'type': 'ir.actions.act_window',
            'res_model': 'acuerdo.compra.venta',
            'view_mode': 'form',
            'res_id': acuerdo.id,
            'context': {'default_order_id': self.id}
        }

    def _validate_sale_confirmation(self):
        self.ensure_one()
        errors = []

        if not self.acuerdo_id:
            errors.append(_('No se puede confirmar la venta sin un Acuerdo de Compra Venta.'))
        
        if not self.banco_credito_id:
            errors.append(_('Debe seleccionar un banco de crédito.'))
        
        if not self.tipo_credito:
            errors.append(_('Debe seleccionar un tipo de crédito.'))
        
        # Validate enganche information
        if self.enganche_percentage <= 0:
            errors.append(_('El porcentaje de enganche debe ser mayor a 0.'))
        
        if self.enganche_payments <= 0:
            errors.append(_('El número de cuotas de enganche debe ser mayor a 0.'))
        
        if not self.enganche_payments:
            errors.append(_('Debe ingresar el número de cuotas de enganche antes de confirmar la venta.'))

        # Add new enganche validations
        if not self.first_payment_date:
            errors.append(_('Debe especificar la fecha del primer pago.'))
        
        if self.first_payment_amount < 10000:
            errors.append(_('El monto de reserva no puede ser menor a Q10,000.'))
        
        if not self.pago_enganche_ids:
            errors.append(_('Debe calcular las cuotas de enganche usando el botón "Calcular Cuotas de Enganche".'))
        
        # Validate total enganche amount matches calculated payments
        if self.pago_enganche_ids:
            total_pagos = sum(self.pago_enganche_ids.mapped('amount'))
            if abs(total_pagos - self.enganche_amount) > 0.01:  # Small difference tolerance
                errors.append(_('El total de las cuotas de enganche (%.2f) no coincide con el monto de enganche calculado (%.2f). Por favor, recalcule los pagos.') % (total_pagos, self.enganche_amount))

        if errors:
            raise ValidationError('\n'.join(errors))

    pending_enganche_amount = fields.Monetary(
        string='Enganche Pendiente',
        compute='_compute_pending_enganche_amount',
        store=False,
        help='Monto pendiente del enganche (Enganche total - Pagos confirmados o recibidos)'
    )

    remaining_balance = fields.Monetary(
        string='Saldo Pendiente',
        compute='_compute_remaining_balance',
        store=False,
        help='Monto total de la venta menos el enganche total'
    )

    @api.depends('amount_total', 'enganche_amount')
    def _compute_remaining_balance(self):
        for order in self:
            order.remaining_balance = order.amount_total - order.enganche_amount

    @api.depends('enganche_amount', 'pago_enganche_ids.state', 'pago_enganche_ids.amount')
    def _compute_pending_enganche_amount(self):
        _logger.info("Starting _compute_pending_enganche_amount for %d sale orders", len(self))
        
        for order in self:
            _logger.debug("Computing pending enganche amount for sale order %s (ID: %d)", order.name, order.id)
            
            # Log initial enganche amount
            _logger.debug("Initial enganche amount: %s", order.enganche_amount)
            
            # Get payments in valid states
            valid_payments = order.pago_enganche_ids.filtered(
                lambda p: p.state in ['confirmed', 'received']
            )
            
            _logger.debug("Found %d valid payments for order %s", len(valid_payments), order.name)
            
            # Calculate paid amount with detailed logging
            paid_amount = 0
            for payment in valid_payments:
                payment_amount = payment.amount_received or 0
                paid_amount += payment_amount
                _logger.debug("Payment %s (ID: %d) - State: %s, Amount received: %s", 
                             payment.name, payment.id, payment.state, payment_amount)
            
            _logger.debug("Total paid amount for order %s: %s", order.name, paid_amount)
            
            # Calculate pending amount
            pending_amount = order.enganche_amount - paid_amount

            _logger.info("Verificando pending amount: %s", pending_amount)
            

            if pending_amount < 0:
                pending_amount = 0

            order.pending_enganche_amount = pending_amount
            
            _logger.info("Order %s - Enganche: %s, Paid: %s, Pending: %s", 
                        order.name, order.enganche_amount, paid_amount, pending_amount)
            
            # Log warning if overpayment detected
            if pending_amount < 0:
                _logger.warning("Overpayment detected for order %s! Excess amount: %s", 
                              order.name, abs(pending_amount))
        
        _logger.info("Completed _compute_pending_enganche_amount computation")

    proyecto_id = fields.Many2one(
        'real.estate.proyecto',
        string='Proyecto',
        compute='_compute_proyecto_id',
        store=True,
        readonly=True,
        help='Proyecto relacionado con la propiedad seleccionada'
    )

    banco_credito_id = fields.Many2one(
        'res.bank',  # Asegúrate de que 'res.bank' es el modelo correcto para los bancos
        string='Banco de Crédito',
        help='Seleccione el banco de crédito para la orden de venta.'
    )
    tipo_credito = fields.Selection(
        selection=[('fha', 'FHA'), 
                   ('credito_directo', 'Crédito directo'), 
                   ('contado', 'Contado')],
        string='Tipo de Crédito',
        help='Seleccione el tipo de crédito.'
    )

    @api.onchange('first_payment_amount')
    def _onchange_first_payment_amount(self):
        if self.first_payment_amount < 10000:
            self.first_payment_amount = 10000
            return {
                'warning': {
                    'title': _('Valor Inválido'),
                    'message': _('El monto de reserva no puede ser menor a Q10,000.')
                }
            }
    
    def action_send_balance_report(self):
        self.ensure_one()
        
        # Get the report action
        report = self.env['ir.actions.report']._get_report_from_name('atd_propiedades.report_sale_balance')
        pdf_content, _ = report._render(report_ref='atd_propiedades.report_sale_balance', res_ids=[self.id])
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Estado de cuenta - {self.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'sale.order',
            'res_id': self.id,
        })
        
        # Prepare email template
        template = self.env['mail.template'].create({
            'name': 'Estado de cuenta',
            'subject': f'Estado de cuenta - {self.name}',
            'body_html': f"""
                <p>Estimado {self.partner_id.name},</p>
                <p>Adjunto podrá encontrar el estado de cuenta de su plan de pagos de enganche.</p>
                <p>Cordialmente,</p>
            """,
            'email_from': self.company_id.email,
            'email_to': self.partner_id.email,
            'model_id': self.env['ir.model']._get('sale.order').id,
            'attachment_ids': [(6, 0, [attachment.id])],
        })
        
        # Send email
        template.send_mail(self.id, force_send=True)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': 'El estado de cuenta ha sido enviado al cliente',
                'type': 'success',
                'sticky': False,
            }
        }
    
    state = fields.Selection(
        selection=[
            ('draft', _("Quotation")),
            ('sent', _("Quotation Sent")),
            ('reserved', _('Reservado')),
            ('sale', _("Pedido de venta")),
            ('done', _("Locked")),
            ('cancel', _("Cancelled")),
        ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default='draft'
    )

    def action_confirm(self):
        for order in self:
            # If real estate is not enabled, use standard confirmation
            if not order.enable_real_estate:
                return super(SaleOrder, self).action_confirm()

            # Basic validations for reservation
            if not order.order_line:
                raise ValidationError(_('No se puede confirmar una orden sin líneas de venta.'))

            # Check property availability
            property_lines = order.order_line.filtered(lambda l: l.property_id)
            for line in property_lines:
                if line.property_id.state != 'available':
                    raise ValidationError(_(
                        'La propiedad "%s" ya no está disponible. '
                        'Por favor, revise el estado de la propiedad antes de confirmar la orden.'
                    ) % line.property_id.name)

            # Move to reserved state
            order.write({'state': 'reserved'})
            
            # Update properties to reserved state
            for line in order.order_line:
                if line.property_id:
                    line.property_id.write({'state': 'reserved'})
            
            # Update pago_enganche status
            order.pago_enganche_ids.filtered(lambda p: p.state == 'draft').write({
                'state': 'scheduled'
            })
            
            return True

    def action_admin_confirm(self):
        """Final confirmation from reserved to confirmed state"""
        self.ensure_one()
        
        if not self.enable_real_estate:
            return super().action_confirm()
        
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise ValidationError(_('Solo los administradores de ventas pueden confirmar órdenes reservadas.'))
        
        if self.state != 'reserved':
            raise ValidationError(_('Solo se pueden confirmar órdenes que estén en estado reservado.'))

        # Run all pre-confirmation validations
        self._validate_sale_confirmation()

        if not self.acuerdo_id.is_complete:
            raise ValidationError(_('No se puede confirmar la orden. El acuerdo no está completo.'))
        
        # Call super's action_confirm for final confirmation
        result = super().action_confirm()
        
        # Properties remain in reserved state after final confirmation
        return result
    
    def action_draft(self):
        """Override to handle property states when resetting to draft"""
        for order in self:
            if order.enable_real_estate and order.state == 'reserved':
                # Check if user has sale admin rights
                if not self.env.user.has_group('sales_team.group_sale_manager'):
                    raise ValidationError(_('Solo los administradores de ventas pueden revertir órdenes reservadas.'))
                
                # Update properties back to available
                for line in order.order_line:
                    if line.property_id:
                        line.property_id.write({'state': 'available'})
                        
                # Set order back to draft state
                order.write({'state': 'draft'})
        
        return super().action_draft()
    
    def action_cancel(self):
        """Override to handle property states when canceling"""
        for order in self:
            if order.enable_real_estate:
                # Check if user has sale admin rights
                if not self.env.user.has_group('sales_team.group_sale_manager'):
                    raise ValidationError(_('Solo los administradores de ventas pueden cancelar órdenes reservadas.'))
                
                # Update properties back to available
                for line in order.order_line:
                    if line.property_id:
                        line.property_id.write({'state': 'available'})
                        
        return super().action_cancel()
    
    @api.constrains('enganche_payments', 'proyecto_id', 'first_payment_date')
    def _check_enganche_payments_deadline(self):
        for record in self:
            if record.enable_real_estate and record.proyecto_id and record.proyecto_id.payment_deadline:
                if not record.first_payment_date:
                    raise ValidationError(_('Debe especificar la fecha del primer pago antes de configurar el número de cuotas.'))
                
                # Calculate months between first payment and deadline
                months_until_deadline = (record.proyecto_id.payment_deadline.year - record.first_payment_date.year) * 12 + \
                                      (record.proyecto_id.payment_deadline.month - record.first_payment_date.month)
                
                if record.enganche_payments > months_until_deadline + 1:  # +1 to include the current month
                    raise ValidationError(_(
                        'El número de cuotas (%d) no puede ser mayor al número de meses hasta la fecha límite de pagos (%d). '
                        'La fecha límite del proyecto es %s.'
                    ) % (
                        record.enganche_payments, 
                        months_until_deadline + 1,
                        record.proyecto_id.payment_deadline.strftime('%d/%m/%Y')
                    ))
                
                if record.first_payment_date > record.proyecto_id.payment_deadline:
                    raise ValidationError(_(
                        'La fecha del primer pago (%s) no puede ser posterior a la fecha límite de pagos del proyecto (%s).'
                    ) % (
                        record.first_payment_date.strftime('%d/%m/%Y'),
                        record.proyecto_id.payment_deadline.strftime('%d/%m/%Y')
                    ))
    