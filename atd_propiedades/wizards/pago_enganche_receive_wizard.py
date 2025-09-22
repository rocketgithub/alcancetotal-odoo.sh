from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PagoEngancheReceiveWizard(models.TransientModel):
    _name = 'pago.enganche.receive.wizard'
    _description = 'Wizard para Recepción de Pago de Enganche'

    pago_enganche_id = fields.Many2one(
        'pago.enganche',
        string='Pago de Enganche',
        required=True
    )
    received_date = fields.Date(
        string='Fecha de Recepción',
        required=True,
        default=fields.Date.context_today
    )
    attachment = fields.Binary(
        string='Comprobante',
        attachment=True
    )
    attachment_name = fields.Char(
        string='Nombre del Archivo'
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        domain="[('type', 'in', ['bank', 'cash'])]",
        required=True
    )
    boleta = fields.Char(
        string='Número de Boleta'
    )
    payment_type_id = fields.Many2one(
        'pago.enganche.payment.type',
        string='Tipo de Pago',
        required=True
    )
    amount = fields.Float(related='pago_enganche_id.amount')
    amount_received = fields.Float(string='Monto Recibido', required=True)
    banco_emisor_id = fields.Many2one(
        'res.bank',
        string='Banco Emisor'
    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Get the active_id from context (this will be the pago.enganche id)
        if self._context.get('active_id'):
            pago = self.env['pago.enganche'].browse(self._context.get('active_id'))
            res.update({
                'pago_enganche_id': pago.id,
                'amount': pago.amount,
                'amount_received': pago.amount
            })
        return res

    def action_confirm(self):
        self.ensure_one()
        if self.attachment:
            # Create attachment
            self.env['ir.attachment'].create({
                'name': self.attachment_name or 'Comprobante de pago',
                'type': 'binary',
                'datas': self.attachment,
                'res_model': 'pago.enganche',
                'res_id': self.pago_enganche_id.id,
            })
        
        # Create account move
        proyecto = self.pago_enganche_id.order_id.proyecto_id
        if not proyecto.enganche_account_id:
            raise ValidationError('Por favor configure la cuenta contable para enganches en el proyecto.')
        
        # Calculate retention if applicable
        retention_amount = 0.0
        if self.payment_type_id.has_retention:
            if not self.payment_type_id.retention_account_id:
                raise ValidationError('Por favor configure la cuenta de retención en el tipo de pago.')
            iva = (self.amount_received / 1.12) * 0.12 
            retention_amount = iva* (self.payment_type_id.retention_percentage / 100)

        # Get the sale order reference
        sale_order_ref = self.pago_enganche_id.order_id.name or ''
        payment_ref = self.pago_enganche_id.name or ''
        line_name = f'Recepción de enganche {payment_ref} (Pedido: {sale_order_ref})'
        retention_line_name = f'Retención de enganche {payment_ref} (Pedido: {sale_order_ref})'

        # Prepare move lines
        move_lines = []
        
        # Credit line - always 100% to enganche account
        move_lines.append((0, 0, {
            'account_id': proyecto.enganche_account_id.id,
            'debit': 0.0,
            'credit': self.amount_received,
            'name': line_name,
        }))

        if retention_amount > 0:
            # Debit line split between journal and retention
            move_lines.extend([
                # Main payment to journal
                (0, 0, {
                    'account_id': self.journal_id.inbound_payment_method_line_ids[0].payment_account_id.id,
                    'debit': self.amount_received - retention_amount,
                    'credit': 0.0,
                    'name': line_name,
                }),
                # Retention amount
                (0, 0, {
                    'account_id': self.payment_type_id.retention_account_id.id,
                    'debit': retention_amount,
                    'credit': 0.0,
                    'name': retention_line_name,
                })
            ])
        else:
            # Full debit to journal
            move_lines.append((0, 0, {
                'account_id': self.journal_id.inbound_payment_method_line_ids[0].payment_account_id.id,
                'debit': self.amount_received,
                'credit': 0.0,
                'name': line_name,
            }))

        move_vals = {
            'journal_id': self.journal_id.id,
            'date': self.received_date,
            'ref': f'Recepción de enganche {self.pago_enganche_id.name}',
            'line_ids': move_lines,
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        
        # Update pago enganche with additional fields
        self.pago_enganche_id.write({
            'state': 'received',
            'received_date': self.received_date,
            'move_id': move.id,
            'journal_id': self.journal_id.id,
            'payment_type_id': self.payment_type_id.id,
            'amount_received': self.amount_received,
            'boleta': self.boleta,
            'banco_emisor_id': self.banco_emisor_id.id,
        })
        
        return {'type': 'ir.actions.act_window_close'}