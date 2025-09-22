from . import models
from . import wizards

def post_init_hook(cr, registry):
    """Post-install hook to populate stored computed fields"""
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Populate property_id field in sale.order for existing records
    sale_orders = env['sale.order'].search([])
    for order in sale_orders:
        # Trigger the compute method to populate the field
        order._compute_propiedad()
    
    # Populate proyecto_id field in sale.order for existing records
    for order in sale_orders:
        # Trigger the compute method to populate the field
        order._compute_proyecto_id()
    
    # Populate stored fields in pago.enganche for existing records
    pago_enganche_records = env['pago.enganche'].search([])
    for payment in pago_enganche_records:
        # Trigger the compute methods to populate stored fields
        payment._compute_balances()
        payment._compute_cliente_propiedad()