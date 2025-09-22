from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PagoEnganchePaymentType(models.Model):
    _name = 'pago.enganche.payment.type'
    _description = 'Tipos de Pago de Enganche'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True
    )
    active = fields.Boolean(
        default=True
    )
    description = fields.Text(
        string='Descripción'
    )
    has_retention = fields.Boolean(
        string='Sujeto a Retención',
        default=False,
        help='Indica si este tipo de pago está sujeto a retención'
    )
    retention_percentage = fields.Float(
        string='Porcentaje de Retención',
        default=0.0,
        help='Porcentaje de retención aplicable a este tipo de pago',
        digits=(5, 2)  # Allows up to 100.00%
    )
    retention_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Retención',
        help='Cuenta contable donde se registrará la retención'
    )

    @api.constrains('has_retention', 'retention_account_id')
    def _check_retention_account(self):
        for record in self:
            if record.has_retention and not record.retention_account_id:
                raise ValidationError('La cuenta de retención es obligatoria cuando el pago está sujeto a retención.') 