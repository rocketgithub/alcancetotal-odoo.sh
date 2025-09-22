from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PagoEngancheEditWizard(models.TransientModel):
    _name = 'pago.enganche.edit.wizard'
    _description = 'Wizard para Edición de Pago de Enganche'

    pago_enganche_id = fields.Many2one(
        'pago.enganche',
        string='Pago de Enganche',
        required=True
    )
    received_date = fields.Date(
        string='Fecha de Recepción',
        required=True
    )
    expected_date = fields.Date(
        string='Fecha Esperada',
        required=True
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
    amount_received = fields.Float(
        string='Monto Recibido', 
        required=True
    )
    banco_emisor_id = fields.Many2one(
        'res.bank',
        string='Banco Emisor'
    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_id'):
            pago = self.env['pago.enganche'].browse(self._context.get('active_id'))
            res.update({
                'pago_enganche_id': pago.id,
                'received_date': pago.received_date,
                'expected_date': pago.expected_date,
                'journal_id': pago.journal_id.id,
                'boleta': pago.boleta,
                'payment_type_id': pago.payment_type_id.id,
                'amount_received': pago.amount_received,
                'banco_emisor_id': pago.banco_emisor_id.id,
            })
        return res

    def action_confirm(self):
        self.ensure_one()
        pago = self.pago_enganche_id
        
        # If amount or journal changed, create new move
        if (pago.amount_received != self.amount_received or 
            pago.journal_id != self.journal_id):
            
            if pago.move_id:
                old_move = pago.move_id
                # Cancel old move
                old_move.button_draft()
                old_move.button_cancel()
                
                # Calculate retention if applicable
                retention_amount = 0.0
                if self.payment_type_id.has_retention:
                    if not self.payment_type_id.retention_account_id:
                        raise ValidationError('Por favor configure la cuenta de retención en el tipo de pago.')
                    iva = (self.amount_received / 1.12) * 0.12 
                    retention_amount = iva * (self.payment_type_id.retention_percentage / 100)

                sale_order_ref = pago.order_id.name or ''
                payment_ref = pago.name or ''
                line_name = f'Recepción de enganche {payment_ref} (Pedido: {sale_order_ref})'
                retention_line_name = f'Retención de enganche {payment_ref} (Pedido: {sale_order_ref})'

                # Create new move lines
                move_lines = []
                
                # Credit line
                move_lines.append((0, 0, {
                    'account_id': pago.order_id.proyecto_id.enganche_account_id.id,
                    'debit': 0.0,
                    'credit': self.amount_received,
                    'name': line_name,
                }))

                if retention_amount > 0:
                    move_lines.extend([
                        (0, 0, {
                            'account_id': self.journal_id.inbound_payment_method_line_ids[0].payment_account_id.id,
                            'debit': self.amount_received - retention_amount,
                            'credit': 0.0,
                            'name': line_name,
                        }),
                        (0, 0, {
                            'account_id': self.payment_type_id.retention_account_id.id,
                            'debit': retention_amount,
                            'credit': 0.0,
                            'name': retention_line_name,
                        })
                    ])
                else:
                    move_lines.append((0, 0, {
                        'account_id': self.journal_id.inbound_payment_method_line_ids[0].payment_account_id.id,
                        'debit': self.amount_received,
                        'credit': 0.0,
                        'name': line_name,
                    }))

                # Create new move
                new_move = self.env['account.move'].create({
                    'journal_id': self.journal_id.id,
                    'date': self.received_date,
                    'ref': f'Modificación de enganche {pago.name}',
                    'line_ids': move_lines,
                })
                
                # Post the new move
                new_move.action_post()
                
                # Post message about the change
                body = f"""
                    <p>Se modificó el pago:</p>
                    <ul>
                        <li>Asiento contable anterior: <a href="#" data-oe-model="account.move" data-oe-id="{old_move.id}">{old_move.name}</a> (Cancelado)</li>
                        <li>Nuevo asiento contable: <a href="#" data-oe-model="account.move" data-oe-id="{new_move.id}">{new_move.name}</a></li>
                    </ul>
                """
                pago.message_post(body=body)
                
                # Update current move reference
                pago.move_id = new_move.id

        # Update pago enganche
        pago.write({
            'received_date': self.received_date,
            'expected_date': self.expected_date,
            'journal_id': self.journal_id.id,
            'payment_type_id': self.payment_type_id.id,
            'amount_received': self.amount_received,
            'boleta': self.boleta,
            'banco_emisor_id': self.banco_emisor_id.id,
        })
        
        return {'type': 'ir.actions.act_window_close'}