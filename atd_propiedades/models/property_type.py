from odoo import models, fields

class PropertyType(models.Model):
    _name = 'real.estate.property.type'
    _description = 'Real Estate Property Type'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True)
    property_ids = fields.One2many('real.estate.property', 'property_type_id', string='Properties')
    property_count = fields.Integer(compute='_compute_property_count', string='Property Count')

    def _compute_property_count(self):
        for record in self:
            record.property_count = len(record.property_ids)