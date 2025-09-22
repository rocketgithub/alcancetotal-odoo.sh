from odoo import models, fields, api

class PropertyModel(models.Model):
    _name = 'real.estate.property.model'
    _description = 'Modelo de Propiedad'
    _order = 'name'

    name = fields.Char(
        string='Nombre del Modelo',
        required=True
    )
    description = fields.Text(
        string='Descripción'
    )
    property_ids = fields.One2many(
        'real.estate.property',
        'property_model_id',
        string='Propiedades'
    )
    active = fields.Boolean(default=True) 