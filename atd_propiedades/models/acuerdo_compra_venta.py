from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError, UserError

class AcuerdoCompraVenta(models.Model):
    _name = 'acuerdo.compra.venta'
    _description = 'Acuerdo de Compra Venta'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'order_id'

    order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        required=True,
        tracking=True,
        ondelete='cascade'
    )



    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=False,
        default=lambda self: self.env.company,
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)

    # Tracking dates
    create_date = fields.Datetime(
        string='Fecha de Creación',
        readonly=True,
        tracking=True
    )

    write_date = fields.Datetime(
        string='Última Modificación',
        readonly=True,
        tracking=True
    )

    # Add the reverse relation in sale.order
    @api.model
    def _add_missing_default_values(self, values):
        values = super()._add_missing_default_values(values)
        return values

    # Deudor Information
    deudor_nombres = fields.Char(
        string='Nombres',
        required=False,
        tracking=True
    )

    deudor_apellidos = fields.Char(
        string='Apellidos',
        required=False,
        tracking=True
    )

    deudor_estado_civil = fields.Selection([
        ('soltero', 'Soltero(a)'),
        ('casado', 'Casado(a)'),
        ('divorciado', 'Divorciado(a)'),
        ('viudo', 'Viudo(a)')
    ], string='Estado Civil', required=False, tracking=True)

    deudor_profesion = fields.Char(
        string='Profesión',
        required=False,
        tracking=True
    )

    deudor_direccion = fields.Text(
        string='Dirección',
        required=False,
        tracking=True
    )

    deudor_nit = fields.Char(
        string='NIT',
        tracking=True
    )

    deudor_fecha_nacimiento = fields.Date(
        string='Fecha de Nacimiento',
        required=False,
        tracking=True
    )

    deudor_dpi = fields.Char(
        string='DPI',
        required=False,
        tracking=True
    )

    deudor_telefono = fields.Char(
        string='Teléfono',
        required=False,
        tracking=True
    )

    deudor_email = fields.Char(
        string='Correo Electrónico',
        tracking=True
    )

    deudor_edad = fields.Integer(
        string='Edad',
        compute='_compute_edad',
        store=True,
        tracking=True
    )

    @api.depends('deudor_fecha_nacimiento')
    def _compute_edad(self):
        today = date.today()
        for record in self:
            if record.deudor_fecha_nacimiento:
                edad = today.year - record.deudor_fecha_nacimiento.year
                if today.month < record.deudor_fecha_nacimiento.month or \
                   (today.month == record.deudor_fecha_nacimiento.month and \
                    today.day < record.deudor_fecha_nacimiento.day):
                    edad -= 1
                record.deudor_edad = edad
            else:
                record.deudor_edad = 0

    # Deudor Work Information
    deudor_laborales_empresa = fields.Char(
        string='Empresa',
        required=False,
        tracking=True
    )

    deudor_laborales_puesto = fields.Char(
        string='Puesto',
        required=False,
        tracking=True
    )

    # Currency field for monetary amounts
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Moneda',
        readonly=True
    )

    # Update monetary fields to use currency_id
    deudor_laborales_ingresos_mensuales = fields.Monetary(
        string='Ingresos Mensuales',
        currency_field='currency_id',
        required=False,
        tracking=True
    )

    deudor_laborales_fecha_ingreso = fields.Date(
        string='Fecha de Ingreso',
        required=False,
        tracking=True
    )

    deudor_laborales_telefono = fields.Char(
        string='Teléfono Trabajo',
        tracking=True
    )

    deudor_laborales_actividad_economica = fields.Char(
        string='Actividad Económica',
        required=False,
        tracking=True
    )

    deudor_laborales_tiempo_trabajo = fields.Float(
        string='Tiempo de Trabajo (Años)',
        compute='_compute_tiempo_trabajo',
        store=True,
        tracking=True,
        digits=(16, 2)
    )

    deudor_laborales_direccion = fields.Text(
        string='Dirección Trabajo',
        required=False,
        tracking=True
    )

    @api.depends('deudor_laborales_fecha_ingreso')
    def _compute_tiempo_trabajo(self):
        today = fields.Date.today()
        for record in self:
            if record.deudor_laborales_fecha_ingreso:
                delta = today - record.deudor_laborales_fecha_ingreso
                record.deudor_laborales_tiempo_trabajo = delta.days / 365.0
            else:
                record.deudor_laborales_tiempo_trabajo = 0.0

    # Deudor Secundario - Personal Information
    deudor_secundario_nombres = fields.Char(
        string='Nombres',
        tracking=True
    )

    deudor_secundario_apellidos = fields.Char(
        string='Apellidos',
        tracking=True
    )

    deudor_secundario_estado_civil = fields.Selection([
        ('soltero', 'Soltero(a)'),
        ('casado', 'Casado(a)'),
        ('divorciado', 'Divorciado(a)'),
        ('viudo', 'Viudo(a)')
    ], string='Estado Civil', tracking=True)

    deudor_secundario_profesion = fields.Char(
        string='Profesión',
        tracking=True
    )

    deudor_secundario_direccion = fields.Text(
        string='Dirección',
        tracking=True
    )

    deudor_secundario_nit = fields.Char(
        string='NIT',
        tracking=True
    )

    deudor_secundario_fecha_nacimiento = fields.Date(
        string='Fecha de Nacimiento',
        tracking=True
    )

    deudor_secundario_dpi = fields.Char(
        string='DPI',
        tracking=True
    )

    deudor_secundario_telefono = fields.Char(
        string='Teléfono',
        tracking=True
    )

    deudor_secundario_email = fields.Char(
        string='Correo Electrónico',
        tracking=True
    )

    deudor_secundario_edad = fields.Integer(
        string='Edad',
        compute='_compute_edad_secundario',
        store=True,
        tracking=True
    )

    # Deudor Secundario - Work Information
    deudor_secundario_laborales_empresa = fields.Char(
        string='Empresa',
        tracking=True
    )

    deudor_secundario_laborales_puesto = fields.Char(
        string='Puesto',
        tracking=True
    )

    # Update monetary fields to use currency_id
    deudor_secundario_laborales_ingresos_mensuales = fields.Monetary(
        string='Ingresos Mensuales',
        currency_field='currency_id',
        tracking=True
    )

    deudor_secundario_laborales_fecha_ingreso = fields.Date(
        string='Fecha de Ingreso',
        tracking=True
    )

    deudor_secundario_laborales_telefono = fields.Char(
        string='Teléfono Trabajo',
        tracking=True
    )

    deudor_secundario_laborales_actividad_economica = fields.Char(
        string='Actividad Económica',
        tracking=True
    )

    deudor_secundario_laborales_tiempo_trabajo = fields.Float(
        string='Tiempo de Trabajo (Años)',
        compute='_compute_tiempo_trabajo_secundario',
        store=True,
        tracking=True,
        digits=(16, 2)
    )

    deudor_secundario_laborales_direccion = fields.Text(
        string='Dirección Trabajo',
        tracking=True
    )

    @api.depends('deudor_secundario_fecha_nacimiento')
    def _compute_edad_secundario(self):
        today = fields.Date.today()
        for record in self:
            if record.deudor_secundario_fecha_nacimiento:
                edad = today.year - record.deudor_secundario_fecha_nacimiento.year
                if today.month < record.deudor_secundario_fecha_nacimiento.month or \
                   (today.month == record.deudor_secundario_fecha_nacimiento.month and \
                    today.day < record.deudor_secundario_fecha_nacimiento.day):
                    edad -= 1
                record.deudor_secundario_edad = edad
            else:
                record.deudor_secundario_edad = 0

    @api.depends('deudor_secundario_laborales_fecha_ingreso')
    def _compute_tiempo_trabajo_secundario(self):
        today = fields.Date.today()
        for record in self:
            if record.deudor_secundario_laborales_fecha_ingreso:
                delta = today - record.deudor_secundario_laborales_fecha_ingreso
                record.deudor_secundario_laborales_tiempo_trabajo = delta.days / 365.0
            else:
                record.deudor_secundario_laborales_tiempo_trabajo = 0.0

    asesor = fields.Char(
        string='Asesor',
        tracking=True,
        help='Nombre del asesor asignado'
    )

    acuerdos_especiales = fields.Text(
        string='Acuerdos Especiales',
        tracking=True,
        help='Campo opcional para especificar acuerdos especiales del contrato'
    )

    observaciones = fields.Text(
        string='Observaciones',
        tracking=True,
    )

    # First Co-signer
    cosigner_1_nombre = fields.Char(
        string='Nombre Completo',
        tracking=True
    )

    cosigner_1_dpi = fields.Char(
        string='DPI',
        tracking=True
    )

    cosigner_1_parentesco = fields.Char(
        string='Parentesco',
        tracking=True
    )

    # Second Co-signer
    cosigner_2_nombre = fields.Char(
        string='Nombre',
        tracking=True
    )

    cosigner_2_dpi = fields.Char(
        string='DPI',
        tracking=True
    )

    cosigner_2_parentesco = fields.Char(
        string='Parentesco',
        tracking=True
    )

    # Beneficiary Information
    beneficiario_nombre = fields.Char(
        string='Nombre Completo Beneficiario',
        tracking=True
    )

    beneficiario_dpi = fields.Char(
        string='DPI Beneficiario',
        tracking=True
    )

    name = fields.Char(
        string='Número de Acuerdo',
        readonly=True,
        copy=False
    )
    
    proyecto_id = fields.Many2one(
        'real.estate.proyecto',
        related='order_id.proyecto_id',
        store=True,
        string='Proyecto'
    )

    propiedad = fields.Many2one(
        'real.estate.property',
        store=False,
        readonly=True,
        related='order_id.property_id',
        string='Propiedad'
    )

    is_complete = fields.Boolean(
        string='Datos Completos',
        compute='_compute_is_complete',
        store=True,
        tracking=True
    )

    incomplete_reason = fields.Text(
        string='Razón Incompleta',
        compute='_compute_incomplete_reason',
        store=False
    )

    # New attachment fields
    dpi_attachment = fields.Binary(
        string='Adjunto DPI',
        attachment=True,
        tracking=True
    )
    
    acuerdo_firmado = fields.Binary(
        string='Acuerdo Firmado',
        attachment=True,
        tracking=True
    )

    # Update nacionalidad field for deudor principal to Char type
    deudor_nacionalidad = fields.Char(
        string='Nacionalidad',
        tracking=True
    )

    # Update nacionalidad field for deudor secundario to Char type
    deudor_secundario_nacionalidad = fields.Char(
        string='Nacionalidad',
        tracking=True
    )

    # Update nacionalidad field for deudor terciario to Char type
    deudor_terciario_nacionalidad = fields.Char(
        string='Nacionalidad',
        tracking=True
    )

    condiciones_formatted = fields.Html(
        string='Condiciones Formateadas',
        compute='_compute_condiciones_formatted',
        store=False,
        help='Condiciones de venta con valores reemplazados'
    )

    @api.depends(
        'order_id.proyecto_id.condiciones', 'order_id', 
        # Deudor principal
        'deudor_nombres', 'deudor_apellidos', 'deudor_dpi',
        # Deudor secundario
        'deudor_secundario_nombres', 'deudor_secundario_apellidos', 'deudor_secundario_dpi',
        # Deudor terciario
        'deudor_terciario_nombres', 'deudor_terciario_apellidos', 'deudor_terciario_dpi',
        # Other fields
        'acuerdos_especiales',
        'order_id.first_payment_amount'
    )
    def _compute_condiciones_formatted(self):
        for record in self:
            if not record.order_id or not record.order_id.proyecto_id or not record.order_id.proyecto_id.condiciones:
                record.condiciones_formatted = False
                return
                
            condiciones = record.order_id.proyecto_id.condiciones
            
            def numero_a_letras(numero):
                UNIDADES = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
                DECENAS = ['', 'DIEZ', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
                DIEZ_A_VEINTE = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE']
                CENTENAS = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']

                def convertir_grupo(n):
                    if n == 0:
                        return ''
                    elif n < 10:
                        return UNIDADES[n]
                    elif n < 20:
                        return DIEZ_A_VEINTE[n-10]
                    elif n < 100:
                        decena = DECENAS[n//10]
                        unidad = UNIDADES[n%10]
                        if unidad:
                            return f"{decena} Y {unidad}"
                        return decena
                    elif n == 100:
                        return "CIEN"
                    else:
                        centena = CENTENAS[n//100]
                        resto = n % 100
                        if resto:
                            return f"{centena} {convertir_grupo(resto)}"
                        return centena

                if numero == 0:
                    return "CERO"

                entero = int(numero)
                decimal = int(round((numero - entero) * 100))
                
                if entero == 1:
                    resultado = "UN"
                else:
                    resultado = ""
                    
                    millares = entero // 1000
                    resto = entero % 1000
                    
                    if millares:
                        if millares == 1:
                            resultado = "UN MIL"
                        else:
                            resultado = f"{convertir_grupo(millares)} MIL"
                    
                    if resto:
                        if resultado:
                            resultado += " "
                        resultado += convertir_grupo(resto)
                
                if decimal:
                    resultado = f"{resultado} QUETZALES CON {convertir_grupo(decimal)}/100"
                else:
                    resultado += " QUETZALES EXACTOS"
                
                return resultado

            # Define replacements dictionary
            replacements = {
                # Deudor principal
                '{{deudor_nombres}}': f"{record.deudor_nombres or ''}".strip(),
                '{{deudor_apellidos}}': f"{record.deudor_apellidos or ''}".strip(),
                '{{deudor_dpi}}': f"{record.deudor_dpi or ''}".strip(),

                # Deudor secundario
                '{{deudor_secundario_nombres}}': f"{record.deudor_secundario_nombres or ''}".strip(),
                '{{deudor_secundario_apellidos}}': f"{record.deudor_secundario_apellidos or ''}".strip(),
                '{{deudor_secundario_dpi}}': f"{record.deudor_secundario_dpi or ''}".strip(),

                # Deudor terciario
                '{{deudor_terciario_nombres}}': f"{record.deudor_terciario_nombres or ''}".strip(),
                '{{deudor_terciario_apellidos}}': f"{record.deudor_terciario_apellidos or ''}".strip(),
                '{{deudor_terciario_dpi}}': f"{record.deudor_terciario_dpi or ''}".strip(),
                '{{acuerdos_especiales}}': f"{record.acuerdos_especiales or ''}".strip(),
                '{{dia}}': str(fields.Date.today().day),
                '{{mes}}': {
                    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
                    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
                }[fields.Date.today().month],
                '{{año}}': str(fields.Date.today().year),
                # Updated monto_reserva replacement to include words
                '{{monto_reserva}}': f"{numero_a_letras(record.order_id.first_payment_amount)} (Q{record.order_id.first_payment_amount:,.2f})".strip(),
            }
            
            # Perform replacements
            formatted_text = condiciones
            for placeholder, value in replacements.items():
                formatted_text = formatted_text.replace(placeholder, str(value))
                
            record.condiciones_formatted = formatted_text

    @api.depends(
        'dpi_attachment', 'acuerdo_firmado',  # Add new dependencies
        'deudor_nacionalidad',
        'deudor_secundario_nacionalidad',
        'deudor_terciario_nacionalidad',
        # Deudor principal fields
        'deudor_nombres', 'deudor_apellidos', 'deudor_estado_civil',
        'deudor_profesion', 'deudor_direccion', 'deudor_nit',
        'deudor_fecha_nacimiento', 'deudor_dpi', 'deudor_telefono',
        'deudor_email', 'deudor_laborales_empresa', 'deudor_laborales_puesto',
        'deudor_laborales_ingresos_mensuales', 'deudor_laborales_fecha_ingreso',
        'deudor_laborales_telefono', 'deudor_laborales_actividad_economica',
        'deudor_laborales_direccion',
        # Deudor secundario fields
        'deudor_secundario_nombres', 'deudor_secundario_apellidos',
        'deudor_secundario_estado_civil', 'deudor_secundario_profesion',
        'deudor_secundario_direccion', 'deudor_secundario_nit',
        'deudor_secundario_fecha_nacimiento', 'deudor_secundario_dpi',
        'deudor_secundario_telefono', 'deudor_secundario_email',
        'deudor_secundario_laborales_empresa', 'deudor_secundario_laborales_puesto',
        'deudor_secundario_laborales_ingresos_mensuales',
        'deudor_secundario_laborales_fecha_ingreso',
        'deudor_secundario_laborales_telefono',
        'deudor_secundario_laborales_actividad_economica',
        'deudor_secundario_laborales_direccion',
        # Deudor terciario fields
        'deudor_terciario_nombres', 'deudor_terciario_apellidos',
        'deudor_terciario_estado_civil', 'deudor_terciario_profesion',
        'deudor_terciario_direccion', 'deudor_terciario_nit',
        'deudor_terciario_fecha_nacimiento', 'deudor_terciario_dpi',
        'deudor_terciario_telefono', 'deudor_terciario_email',
        'deudor_terciario_laborales_empresa', 'deudor_terciario_laborales_puesto',
        'deudor_terciario_laborales_ingresos_mensuales',
        'deudor_terciario_laborales_fecha_ingreso',
        'deudor_terciario_laborales_telefono',
        'deudor_terciario_laborales_actividad_economica',
        'deudor_terciario_laborales_direccion'
    )
    def _compute_is_complete(self):
        for record in self:

            # Check if all fields are filled when any field in the group has data
            deudor_complete = all([
                record.deudor_nombres, record.deudor_apellidos,
                record.deudor_estado_civil, record.deudor_profesion,
                record.deudor_direccion, record.deudor_nit,
                record.deudor_fecha_nacimiento, record.deudor_dpi,
                record.deudor_telefono, record.deudor_email,
                record.deudor_nacionalidad,
                record.deudor_laborales_empresa, record.deudor_laborales_puesto,
                record.deudor_laborales_ingresos_mensuales,
                record.deudor_laborales_fecha_ingreso,
                record.deudor_laborales_telefono,
                record.deudor_laborales_actividad_economica,
                record.deudor_laborales_direccion
            ])

            # Update final condition to include attachments
            record.is_complete = deudor_complete and self.secundario_complete() and self.terciario_complete()

    def secundario_complete(self):
        secundario_has_data = any([
            self.deudor_secundario_nombres, self.deudor_secundario_apellidos,
            self.deudor_secundario_estado_civil, self.deudor_secundario_profesion,
            self.deudor_secundario_direccion, self.deudor_secundario_nit,
            self.deudor_secundario_fecha_nacimiento, self.deudor_secundario_dpi,
            self.deudor_secundario_telefono, self.deudor_secundario_email,
            self.deudor_secundario_laborales_empresa,
            self.deudor_secundario_laborales_puesto,
            self.deudor_secundario_laborales_ingresos_mensuales,
            self.deudor_secundario_laborales_fecha_ingreso,
            self.deudor_secundario_laborales_telefono,
            self.deudor_secundario_laborales_actividad_economica,
            self.deudor_secundario_laborales_direccion
            ])

        return not secundario_has_data or all([
            self.deudor_secundario_nombres, self.deudor_secundario_apellidos,
            self.deudor_secundario_estado_civil, self.deudor_secundario_profesion,
            self.deudor_secundario_direccion, self.deudor_secundario_nit,
            self.deudor_secundario_fecha_nacimiento, self.deudor_secundario_dpi,
            self.deudor_secundario_telefono, self.deudor_secundario_email,
            self.deudor_secundario_nacionalidad,
            self.deudor_secundario_laborales_empresa,
            self.deudor_secundario_laborales_puesto,
            self.deudor_secundario_laborales_ingresos_mensuales,
            self.deudor_secundario_laborales_fecha_ingreso,
            self.deudor_secundario_laborales_telefono,
            self.deudor_secundario_laborales_actividad_economica,
            self.deudor_secundario_laborales_direccion
            ])
    
    def terciario_complete(self):

        terciario_has_data = any([
            self.deudor_terciario_nombres, self.deudor_terciario_apellidos,
            self.deudor_terciario_estado_civil, self.deudor_terciario_profesion,
            self.deudor_terciario_direccion, self.deudor_terciario_nit,
            self.deudor_terciario_fecha_nacimiento, self.deudor_terciario_dpi,
            self.deudor_terciario_telefono, self.deudor_terciario_email,
            self.deudor_terciario_laborales_empresa,
            self.deudor_terciario_laborales_puesto,
            self.deudor_terciario_laborales_ingresos_mensuales,
            self.deudor_terciario_laborales_fecha_ingreso,
            self.deudor_terciario_laborales_telefono,
            self.deudor_terciario_laborales_actividad_economica,
            self.deudor_terciario_laborales_direccion
            ])
        
        return not terciario_has_data or all([
            self.deudor_terciario_nombres, self.deudor_terciario_apellidos,
            self.deudor_terciario_estado_civil, self.deudor_terciario_profesion,
            self.deudor_terciario_direccion, self.deudor_terciario_nit,
            self.deudor_terciario_fecha_nacimiento, self.deudor_terciario_dpi,
            self.deudor_terciario_telefono, self.deudor_terciario_email,
            self.deudor_terciario_laborales_empresa,
            self.deudor_terciario_laborales_puesto,
            self.deudor_terciario_laborales_ingresos_mensuales,
            self.deudor_terciario_laborales_fecha_ingreso,
            self.deudor_terciario_laborales_telefono,
            self.deudor_terciario_laborales_actividad_economica,
            self.deudor_terciario_laborales_direccion
        ])

    # Add all deudor_terciario fields
    deudor_terciario_nombres = fields.Char(string='Nombres', tracking=True)
    deudor_terciario_apellidos = fields.Char(string='Apellidos', tracking=True)
    deudor_terciario_estado_civil = fields.Selection([
        ('soltero', 'Soltero(a)'),
        ('casado', 'Casado(a)'),
        ('divorciado', 'Divorciado(a)'),
        ('viudo', 'Viudo(a)')
    ], string='Estado Civil', tracking=True)
    deudor_terciario_profesion = fields.Char(string='Profesión', tracking=True)
    deudor_terciario_direccion = fields.Char(string='Dirección', tracking=True)
    deudor_terciario_nit = fields.Char(string='NIT', tracking=True)
    deudor_terciario_fecha_nacimiento = fields.Date(string='Fecha de Nacimiento', tracking=True)
    deudor_terciario_dpi = fields.Char(string='DPI', tracking=True)
    deudor_terciario_telefono = fields.Char(string='Teléfono', tracking=True)
    deudor_terciario_email = fields.Char(string='Email', tracking=True)
    deudor_terciario_edad = fields.Integer(
        string='Edad',
        compute='_compute_deudor_terciario_edad',
        store=True,
        tracking=True
    )

    # Información Laboral Terciario
    deudor_terciario_laborales_empresa = fields.Char(string='Empresa', tracking=True)
    deudor_terciario_laborales_puesto = fields.Char(string='Puesto', tracking=True)
    deudor_terciario_laborales_ingresos_mensuales = fields.Float(string='Ingresos Mensuales', tracking=True)
    deudor_terciario_laborales_fecha_ingreso = fields.Date(string='Fecha de Ingreso', tracking=True)
    deudor_terciario_laborales_telefono = fields.Char(string='Teléfono Laboral', tracking=True)
    deudor_terciario_laborales_actividad_economica = fields.Char(string='Actividad Económica', tracking=True)
    deudor_terciario_laborales_tiempo_trabajo = fields.Float(
        string='Tiempo de Trabajo (Años)',
        compute='_compute_deudor_terciario_tiempo_trabajo',
        store=True,
        tracking=True,
        digits=(16, 2)
    )
    deudor_terciario_laborales_direccion = fields.Char(string='Dirección Laboral', tracking=True)

    @api.depends('deudor_terciario_fecha_nacimiento')
    def _compute_deudor_terciario_edad(self):
        for record in self:
            if record.deudor_terciario_fecha_nacimiento:
                today = fields.Date.today()
                record.deudor_terciario_edad = today.year - record.deudor_terciario_fecha_nacimiento.year - (
                    (today.month, today.day) < (record.deudor_terciario_fecha_nacimiento.month, record.deudor_terciario_fecha_nacimiento.day)
                )
            else:
                record.deudor_terciario_edad = 0

    @api.depends('deudor_terciario_laborales_fecha_ingreso')
    def _compute_deudor_terciario_tiempo_trabajo(self):
        today = fields.Date.today()
        for record in self:
            if record.deudor_terciario_laborales_fecha_ingreso:
                delta = today - record.deudor_terciario_laborales_fecha_ingreso
                record.deudor_terciario_laborales_tiempo_trabajo = delta.days / 365.0
            else:
                record.deudor_terciario_laborales_tiempo_trabajo = 0.0

    @api.constrains('deudor_fecha_nacimiento', 'deudor_secundario_fecha_nacimiento', 'deudor_terciario_fecha_nacimiento')
    def _check_edad_minima(self):
        """Validate that all debtors are at least 18 years old"""
        for record in self:
            today = fields.Date.today()
            
            # Check primary debtor
            if record.deudor_fecha_nacimiento:
                edad = record.deudor_edad
                if edad < 18:
                    raise ValidationError(_('El deudor principal debe ser mayor de edad (18 años o más)'))
            
            # Check secondary debtor if data exists
            if record.deudor_secundario_fecha_nacimiento:
                edad = record.deudor_secundario_edad
                if edad < 18:
                    raise ValidationError(_('El deudor secundario debe ser mayor de edad (18 años o más)'))
            
            # Check tertiary debtor if data exists
            if record.deudor_terciario_fecha_nacimiento:
                edad = record.deudor_terciario_edad
                if edad < 18:
                    raise ValidationError(_('El deudor terciario debe ser mayor de edad (18 años o más)'))

    @api.model
    def create(self, vals):

        if 'order_id' in vals:
            order = self.env['sale.order'].browse(vals.get('order_id'))
            
            # Check if proyecto_id exists
            if not order.proyecto_id:
                raise ValidationError(_('No se puede crear el acuerdo: La orden de venta debe tener un proyecto asignado. Seleccione al menos una propiedad en las lineas de venta'))
            
            # Check if sequence fields are set in the project
            if not order.proyecto_id.sequence_number:
                raise ValidationError(_('No se puede crear el acuerdo: El proyecto no tiene configurado el número de secuencia.'))
            
            if not order.proyecto_id.sequence_prefix:
                raise ValidationError(_('No se puede crear el acuerdo: El proyecto no tiene configurado el prefijo de secuencia.'))
            
            if not order.proyecto_id.sequence_padding:
                raise ValidationError(_('No se puede crear el acuerdo: El proyecto no tiene configurado el padding de secuencia.'))

            if not vals.get('name'):
                proyecto = order.proyecto_id
                sequence_number = proyecto.sequence_number
                # Create the sequence number
                vals['name'] = f"{proyecto.sequence_prefix}{str(sequence_number).zfill(proyecto.sequence_padding)}"
                # Increment the sequence
                proyecto.sequence_number += 1
        else:
            raise ValidationError(_('No se puede crear el acuerdo: Se requiere una orden de venta.'))
        
        record = super().create(vals)
        record._sync_partner_data()
        return record


    @api.depends('is_complete')
    def _compute_incomplete_reason(self):
        for record in self:
            if record.is_complete:
                record.incomplete_reason = False
            else:
                reasons = []
                
                if not all([
                    record.deudor_nombres, record.deudor_apellidos,
                    record.deudor_estado_civil, record.deudor_profesion,
                    record.deudor_direccion, record.deudor_nit,
                    record.deudor_fecha_nacimiento, record.deudor_dpi,
                    record.deudor_telefono, record.deudor_email,
                    record.deudor_laborales_empresa, record.deudor_laborales_puesto,
                    record.deudor_laborales_ingresos_mensuales,
                    record.deudor_laborales_fecha_ingreso,
                    record.deudor_laborales_telefono,
                    record.deudor_laborales_actividad_economica,
                    record.deudor_laborales_direccion
                ]):
                    reasons.append("Deudor principal incompleto, todos los datos son requeridos")

                # Check if deudor secundario has any data and is incomplete
                secundario_has_data = any([
                    record.deudor_secundario_nombres, record.deudor_secundario_apellidos,
                    record.deudor_secundario_estado_civil, record.deudor_secundario_profesion,
                    record.deudor_secundario_direccion, record.deudor_secundario_nit,
                    record.deudor_secundario_fecha_nacimiento, record.deudor_secundario_dpi,
                    record.deudor_secundario_telefono, record.deudor_secundario_email,
                    record.deudor_secundario_laborales_empresa,
                    record.deudor_secundario_laborales_puesto,
                    record.deudor_secundario_laborales_ingresos_mensuales,
                    record.deudor_secundario_laborales_fecha_ingreso,
                    record.deudor_secundario_laborales_telefono,
                    record.deudor_secundario_laborales_actividad_economica,
                    record.deudor_secundario_laborales_direccion
                ])
                if secundario_has_data and not all([
                    record.deudor_secundario_nombres, record.deudor_secundario_apellidos,
                    record.deudor_secundario_estado_civil, record.deudor_secundario_profesion,
                    record.deudor_secundario_direccion, record.deudor_secundario_nit,
                    record.deudor_secundario_fecha_nacimiento, record.deudor_secundario_dpi,
                    record.deudor_secundario_telefono, record.deudor_secundario_email,
                    record.deudor_secundario_laborales_empresa,
                    record.deudor_secundario_laborales_puesto,
                    record.deudor_secundario_laborales_ingresos_mensuales,
                    record.deudor_secundario_laborales_fecha_ingreso,
                    record.deudor_secundario_laborales_telefono,
                    record.deudor_secundario_laborales_actividad_economica,
                    record.deudor_secundario_laborales_direccion
                ]):
                    reasons.append("Deudor secundario incompleto, todos los datos son requeridos, si no se requiere deudor secundario, dejar todo en blanco")

                # Check if deudor terciario has any data and is incomplete
                terciario_has_data = any([
                    record.deudor_terciario_nombres, record.deudor_terciario_apellidos,
                    record.deudor_terciario_estado_civil, record.deudor_terciario_profesion,
                    record.deudor_terciario_direccion, record.deudor_terciario_nit,
                    record.deudor_terciario_fecha_nacimiento, record.deudor_terciario_dpi,
                    record.deudor_terciario_telefono, record.deudor_terciario_email,
                    record.deudor_terciario_laborales_empresa,
                    record.deudor_terciario_laborales_puesto,
                    record.deudor_terciario_laborales_ingresos_mensuales,
                    record.deudor_terciario_laborales_fecha_ingreso,
                    record.deudor_terciario_laborales_telefono,
                    record.deudor_terciario_laborales_actividad_economica,
                    record.deudor_terciario_laborales_direccion
                ])
                if terciario_has_data and not all([
                    record.deudor_terciario_nombres, record.deudor_terciario_apellidos,
                    record.deudor_terciario_estado_civil, record.deudor_terciario_profesion,
                    record.deudor_terciario_direccion, record.deudor_terciario_nit,
                    record.deudor_terciario_fecha_nacimiento, record.deudor_terciario_dpi,
                    record.deudor_terciario_telefono, record.deudor_terciario_email,
                    record.deudor_terciario_laborales_empresa,
                    record.deudor_terciario_laborales_puesto,
                    record.deudor_terciario_laborales_ingresos_mensuales,
                    record.deudor_terciario_laborales_fecha_ingreso,
                    record.deudor_terciario_laborales_telefono,
                    record.deudor_terciario_laborales_actividad_economica,
                    record.deudor_terciario_laborales_direccion
                ]):
                    reasons.append("Deudor terciario incompleto, todos los datos son requeridos, si no se requiere deudor terciario, dejar todo en blanco")

                record.incomplete_reason = "\n".join(reasons) if reasons else "Información incompleta"

    def action_print_if_complete(self):
        self.ensure_one()
        if not self.is_complete:
            raise UserError('No se puede imprimir el acuerdo porque está incompleto.\n\nRazón:\n' + (self.incomplete_reason or 'Información faltante'))
            
        return self.env.ref('atd_propiedades.action_report_acuerdo_compra_venta').report_action(self)

    def write(self, vals):
        result = super().write(vals)
        self._sync_partner_data()
        return result

    
    def _sync_partner_data(self):
        """Sync deudor data with partner if fields are empty"""
        for record in self:
            if not record.order_id or not record.order_id.partner_id:
                continue

            partner = record.order_id.partner_id
            partner_vals = {}

            # Map deudor fields to partner fields
            field_mappings = {
                'deudor_email': 'email',
                'deudor_telefono': 'phone',
                'deudor_direccion': 'street',
                'deudor_nit': 'vat',
                'deudor_dpi': 'cui'
            }

            # Check each field and update partner if empty
            for deudor_field, partner_field in field_mappings.items():
                if hasattr(partner, partner_field):  # Check if partner has the field
                    deudor_value = getattr(record, deudor_field)
                    partner_value = getattr(partner, partner_field)
                    
                    if deudor_value and not partner_value:
                        partner_vals[partner_field] = deudor_value

            # Update partner if we have any values to sync
            if partner_vals:
                partner.write(partner_vals)