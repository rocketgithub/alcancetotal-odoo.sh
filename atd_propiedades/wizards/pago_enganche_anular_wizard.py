from odoo import models, fields, _

class PagoEngancheAnularWizard(models.TransientModel):
    _name = 'pago.enganche.anular.wizard'
    _description = 'Wizard para anular pago de enganche'

    pago_enganche_id = fields.Many2one(
        'pago.enganche',
        string='Pago de Enganche',
        required=True
    )

    def action_confirm(self):
        self.ensure_one()
        self.pago_enganche_id.action_anular()
        
        # Return action to close wizard and refresh view
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        } 