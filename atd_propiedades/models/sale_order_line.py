from odoo import models, fields, api
import logging

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    property_id = fields.Many2one(
        'real.estate.property',
        string='Propiedad',
        tracking=True
    )
    property_state = fields.Selection(related='property_id.state', store=True)

    enable_real_estate = fields.Boolean(
        related='order_id.enable_real_estate',
        string='Bienes Raíces Habilitado',
        readonly=True
    )

    @api.onchange('property_id')
    def _onchange_property_id(self):
        # Create a duplicate line with same product and price
        
        _logger = logging.getLogger(__name__)
        _logger.info('========= ONCHANGE START =========')
        
        if not self.property_id or not self.order_id:
            return

        # First set the name and quantity
        self.name = self.property_id.description
        self.product_uom_qty = 1
        self.price_unit = self.property_id.total_price
        

        # Only proceed if we have child properties
        if not self.property_id.child_property_ids:
            return

        
        _logger.info('========= ONCHANGE END =========')

    def unlink(self):
        """Override unlink to handle child property lines"""
        for line in self:
            if line.property_id and line.property_id.child_property_ids:
                # Find and delete child property lines
                child_lines = self.search([
                    ('order_id', '=', line.order_id.id),
                    ('property_id', 'in', line.property_id.child_property_ids.ids)
                ])
                if child_lines:
                    child_lines.unlink()
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        _logger = logging.getLogger(__name__)
        lines = super().create(vals_list)
        for line in lines:
            if line.property_id:
                try:
                    line.order_id.message_post(
                        body=f"Se agregó la propiedad {line.property_id.name} y sus propiedades relacionadas al pedido."
                    )
                except Exception as e:
                    _logger.warning("Could not post property message: %s", e)
        return lines

    # Add this method to override the default price computation
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        # Skip standard price computation if we're setting property price
        if self.env.context.get('skip_price_computation'):
            return
        
        # For non-property lines, use standard computation
        lines_to_compute = self.filtered(lambda l: not l.property_id)
        if lines_to_compute:
            super(SaleOrderLine, lines_to_compute)._compute_price_unit()