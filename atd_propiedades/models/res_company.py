from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_real_estate = fields.Boolean(
        string='Habilitar Bienes Raíces',
        default=False,
        help='Habilita las funciones de bienes raíces como enganche y pagos'
    )