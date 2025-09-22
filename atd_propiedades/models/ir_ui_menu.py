from odoo import models, api

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _visible_menu_ids(self, debug=False):
        """ Add real estate menu visibility check based on company setting """
        visible_ids = super()._visible_menu_ids(debug=debug)
        
        if not self.env.company.enable_real_estate:
            real_estate_menus = [
                self.env.ref('atd_propiedades.menu_real_estate_reports').id,
                self.env.ref('atd_propiedades.menu_pago_enganche').id,
            ]
            visible_ids = visible_ids - set(real_estate_menus)
            
        return visible_ids 