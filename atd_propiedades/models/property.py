from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Property(models.Model):
    _name = 'real.estate.property'
    _description = 'Propiedad'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _attachment = True

    name = fields.Char(string='Nombre de la Propiedad', required=True, tracking=True)
    description = fields.Text(
        string='Descripción',
        compute='_compute_description',
        store=False
    )
    square_meters = fields.Float(
        string='Metros Cuadrados Totales', 
        compute='_compute_square_meters',
        store=True,
        tracking=True
    )
    bathrooms = fields.Float(
        string='Número de Baños', 
        tracking=True,
        digits=(2,1)  # This allows numbers like 1.5 bathrooms
    )
    bedrooms = fields.Integer(string='Número de Habitaciones', tracking=True)
    
    price = fields.Float(string='Precio', tracking=True)
    state = fields.Selection([
        ('available', 'Disponible'),
        ('reserved', 'Reservado'),
        ('sold', 'Vendido'),
    ], string='Estado', default='available', tracking=True)
    property_type_id = fields.Many2one(
        'real.estate.property.type', 
        string='Tipo de Propiedad',
        required=True,
        tracking=True
    )

    partner_id = fields.Many2one('res.partner', string='Propietario')
    sale_line_ids = fields.One2many(
        'sale.order.line',
        'property_id',
        string='Líneas de Venta Relacionadas'
    )
    
    address = fields.Text(string='Dirección')

    active = fields.Boolean(default=True)

    parent_property_id = fields.Many2one(
        'real.estate.property',
        string='Propiedad Principal',
        tracking=True,
    )
    
    child_property_ids = fields.One2many(
        'real.estate.property',
        'parent_property_id',
        string='Propiedades Relacionadas',
        tracking=True,
    )

    property_model_id = fields.Many2one(
        'real.estate.property.model',
        string='Modelo',
        tracking=True
    )

    # New string fields
    areas = fields.Char(string='Áreas', tracking=True)
    gabinetes = fields.Char(string='Gabinetes', tracking=True)
    puertas = fields.Char(string='Puertas', tracking=True)
    piso = fields.Char(string='Piso', tracking=True)
    lavanderia = fields.Char(string='Lavandería', tracking=True)
    agua = fields.Char(string='Agua', tracking=True)
    closet = fields.Char(string='Closet', tracking=True)

    parqueos = fields.Integer(
        string='Parqueos',
        compute='_compute_parqueos',
        store=True,
        help='Número de parqueos asociados a esta propiedad'
    )

    total_price = fields.Float(
        string='Precio Total',
        compute='_compute_total_price',
        store=True,
        tracking=True
    )

    # Add company field
    company_id = fields.Many2one(
        'res.company', 
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    # Add SQL constraint for uniqueness per company
    _sql_constraints = [
        ('unique_property_per_company',
         'UNIQUE(name, company_id)',
         'This property already exists in this company!')
    ]

    # Add record rule for multi-company
    @api.model
    def _init_data(self):
        self.env['ir.rule'].create({
            'name': 'Property: Multi-company rule',
            'model_id': self.env['ir.model']._get('real.estate.property').id,
            'domain_force': "[('company_id', 'in', company_ids)]",
            'global': True,
        })

    @api.depends('price', 'child_property_ids', 'child_property_ids.price')
    def _compute_total_price(self):
        for record in self:
            child_total = sum(record.child_property_ids.mapped('price'))
            record.total_price = record.price + child_total

    @api.depends('child_property_ids', 'child_property_ids.property_type_id', 'child_property_ids.property_type_id.name')
    def _compute_parqueos(self):
        for record in self:
            record.parqueos = len(record.child_property_ids.filtered(
                lambda p: p.property_type_id and p.property_type_id.name and 
                         'parqueo' in p.property_type_id.name.lower()
            ))

    proyecto_id = fields.Many2one(
        'real.estate.proyecto',
        string='Proyecto',
        required=True,
        tracking=True,
        help='Proyecto al que pertenece esta propiedad'
    )

    # Add nivel field
    nivel = fields.Integer(string='Nivel', tracking=True)

    @api.onchange('parent_property_id')
    def _onchange_parent_property_id(self):
        for record in self:
            if record.state != 'sold':
                if record.parent_property_id:
                    record.state = 'reserved'
                else:
                    record.state = 'available'

    @api.depends('property_model_id', 'nivel', 'bedrooms', 'bedrooms_description', 'bathrooms', 'bathrooms_description', 'square_meters', 'child_property_ids', 'child_property_ids.name', 'number', 'vista', 'parqueos', 'parqueos_description')
    def _compute_description(self):
        for record in self:
            description_parts = []
            
            # Add model name if exists
            if record.property_model_id and record.property_model_id.name:
                description_parts.append(f"Modelo: {record.property_model_id.name}")
            
            # Add number if exists
            if record.number:
                description_parts.append(f"Número: {record.number}")
            
            # Add nivel if exists
            if record.nivel:
                description_parts.append(f"Nivel: {record.nivel}")
            
            # Add vista if exists
            if record.vista:
                description_parts.append(f"Vista: {record.vista}")
            
            # Add bedrooms using description if available, otherwise use number
            if record.bedrooms_description:
                description_parts.append(f"Habitaciones: {record.bedrooms_description}")
            elif record.bedrooms:
                description_parts.append(f"Habitaciones: {record.bedrooms}")
            
            # Add bathrooms using description if available, otherwise use number
            if record.bathrooms_description:
                description_parts.append(f"Baños: {record.bathrooms_description}")
            elif record.bathrooms:
                description_parts.append(f"Baños: {record.bathrooms}")
            
            # Add parqueos using description if available, otherwise use number
            if record.parqueos_description:
                description_parts.append(f"Parqueos: {record.parqueos_description}")
            elif record.parqueos:
                description_parts.append(f"Parqueos: {record.parqueos}")
            
            # Add areas if they exist
            if record.area_apartamento:
                description_parts.append(f"Área apartamento: {record.area_apartamento}m²")
            if record.area_balcon:
                description_parts.append(f"Área balcón: {record.area_balcon}m²")
            if record.area_jardin:
                description_parts.append(f"Área jardín: {record.area_jardin}m²")
            
            # Add total square meters if exists
            if record.square_meters:
                description_parts.append(f"Área total: {record.square_meters}m²")
            
            # Add child properties if exist
            if record.child_property_ids:
                child_names = record.child_property_ids.mapped('name')
                if child_names:
                    description_parts.append("Incluido: " + ", ".join(child_names))
            
            # Join all parts with commas
            record.description = ", ".join(description_parts) if description_parts else False
    
    number = fields.Char(string='Número', tracking=True)
    bedrooms_description = fields.Char(string='Descripción de Habitaciones', tracking=True)
    bathrooms_description = fields.Char(string='Descripción de Baños', tracking=True)
    
    area_apartamento = fields.Float(string='Área de Apartamento', tracking=True)
    area_balcon = fields.Float(string='Área de Balcón', tracking=True)
    area_jardin = fields.Float(string='Área de Jardín', tracking=True)
    
    @api.depends('area_apartamento', 'area_balcon', 'area_jardin')
    def _compute_square_meters(self):
        for record in self:
            record.square_meters = (record.area_apartamento or 0) + \
                                 (record.area_balcon or 0) + \
                                 (record.area_jardin or 0)
    
    vista = fields.Char(string='Vista', tracking=True)
    parqueos_description = fields.Char(string='Descripción de Parqueos', tracking=True)
    
    # Property registration fields
    finca = fields.Char(string='Finca', tracking=True, help='Número de finca registral')
    folio = fields.Char(string='Folio', tracking=True, help='Número de folio registral')
    libro = fields.Char(string='Libro', tracking=True, help='Número de libro registral')
    