from odoo import models, fields, api

class Proyecto(models.Model):
    _name = 'real.estate.proyecto'
    _description = 'Proyecto Inmobiliario'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre del Proyecto',
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Descripción',
        tracking=True
    )
    icon = fields.Binary(
        string='Icono',
        attachment=True,
        help='Icono representativo del proyecto'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    active = fields.Boolean(default=True)

    sequence_prefix = fields.Char(
        string='Prefijo de Secuencia',
        help='Prefijo para la numeración de acuerdos',
        default='ACU',
        tracking=True
    )
    sequence_number = fields.Integer(
        string='Próximo Número',
        default=1,
        tracking=True
    )
    sequence_padding = fields.Integer(
        string='Dígitos de Secuencia',
        default=4,
        help='Cantidad de dígitos para el número de secuencia',
        tracking=True
    )

    condiciones = fields.Html(
        string='Condiciones de la venta',
        tracking=True,
        help='Condiciones de la venta'
    )

    enganche_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de pasivos de enganche',
        required=True,
        help='Cuenta contable donde se registrarán los enganches recibidos'
    )

    recibo_sequence_prefix = fields.Char(
        string='Prefijo Secuencia Recibo',
        default='REC',
        tracking=True,
        help='Prefijo para la numeración de recibos de pago'
    )
    recibo_sequence_number = fields.Integer(
        string='Próximo Número de Recibo',
        default=1,
        tracking=True
    )
    recibo_sequence_padding = fields.Integer(
        string='Dígitos Secuencia Recibo',
        default=4,
        help='Cantidad de dígitos para el número de secuencia de recibos',
        tracking=True
    )

    payment_deadline = fields.Date(
        string='Fecha límite de pagos',
        tracking=True,
        help='Última fecha permitida para realizar pagos en este proyecto'
    )

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name, company_id)',
         'El nombre del proyecto debe ser único por compañía!')
    ] 

    def get_next_recibo_sequence(self):
        self.ensure_one()
        sequence = f"{self.recibo_sequence_prefix}{str(self.recibo_sequence_number).zfill(self.recibo_sequence_padding)}"
        self.recibo_sequence_number += 1
        return sequence