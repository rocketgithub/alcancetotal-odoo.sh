from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_real_estate = fields.Boolean(
        related='company_id.enable_real_estate',
        readonly=False,
        string='Enable Real Estate Management',
        help='Enable real estate property management features'
    )