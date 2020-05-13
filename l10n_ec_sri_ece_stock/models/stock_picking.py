# -*- coding: utf-8 -*-
from collections import OrderedDict
from datetime import datetime

import pytz
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    comprobante_id = fields.Many2one(
        'l10n_ec_sri.comprobante',
        string='Comprobante', copy=False, )
    autorizacion_id = fields.Many2one(
        'l10n_ec_sri.autorizacion',
        string=u'Autorización', copy=False, )
    establecimiento = fields.Char(
        'Establecimiento', copy=False, size=3, )
    puntoemision = fields.Char(
        'Punto de emisión', copy=False, size=3, )
    autorizacion = fields.Char(
        'Autorización', copy=False, )
    secuencial = fields.Char(
        string='Secuencial', copy=False, index=True, size=9,
        help="En caso de no tener secuencia, debe ingresar nueves, ejemplo: 999999.", )

    # PARA FACTURACIÓN ELECTRÓNICA
    # necesario en la base para declarar cuando es física.
    tipoem = fields.Selection(
        [
            ('F', 'Facturación física'),
            ('E', 'Facturación electrónica'),
        ],
        string='Tipo de emisión',
        defaut='F', )  # Default F es importante para que las facturas actuales sean todas físicas.

    guia_remision_electronica_id = fields.Many2one(
        'l10n_ec_sri.documento.electronico', ondelete='restrict',
        string="Guía de remisión electronica", )
    driver_id = fields.Many2one('res.partner', 'Driver')
    route = fields.Char('Route')
    fechainitransporte = fields.Date('Fecha Inicio Transporte')
    fechafintransporte = fields.Date('Fecha Fin Transporte')

    @api.multi
    def get_sri_secuencial_completo_guia(self):
        self.ensure_one()
        nro_guia = ''
        # No presentamos guias no legalizadas.
        if self.secuencial and self.puntoemision and self.establecimiento:
            nro_guia = '-'.join([
                self.establecimiento or '0',
                self.puntoemision or '0',
                (self.secuencial or '0').zfill(9)
            ])

        return nro_guia

    @api.multi
    def _get_custom_attachments(self):
        """
        return: recordset
        """
        attachments = []
        attachment_id = self.guia_remision_electronica_id

        if attachment_id:
            attachments.append(
                (attachment_id.xml_filename, attachment_id.xml_file)
            )
        return attachments

    @api.multi
    def get_motivotraslado(self):
        if self.picking_type_id.code == 'incoming':
            motivo = 'Compra de productos'
        elif self.picking_type_id.code == 'outgoing':
            motivo = 'Venta de productos'
        elif self.picking_type_id.code == 'internal':
            motivo = 'Movimiento interno de productos'
        return motivo

    @api.multi
    def get_destinatario_dict(self, d, docsustento, inv_obj):
        dirdestinatario = inv_obj.normalize(' '.join([d.street, d.street]))
        motivotraslado = self.get_motivotraslado()
        detalles = OrderedDict([
            ('detalle', []),
        ])
        for pack in self.pack_operation_product_ids:
            p = pack.product_id
            detalles['detalle'].append(
                self.get_detalle_dict(p, pack, inv_obj)
            )

        numDocSustento = '{}-{}-{:0>9}'.format(
            docsustento.autorizacion_id.establecimiento,
            docsustento.autorizacion_id.puntoemision,
            docsustento.secuencial
        )
        res = OrderedDict([
            ('identificacionDestinatario', d.vat),
            ('razonSocialDestinatario', d.name),
            ('dirDestinatario', dirdestinatario),
            ('motivoTraslado', motivotraslado),
            # ('docAduaneroUnico', ''),TODO
            # ('codEstabDestino', ''),TODO
            # ('ruta', ''),TODO
            ('codDocSustento', docsustento.comprobante_id.code),
            ('numDocSustento', numDocSustento),
            ('numAutDocSustento', docsustento.autorizacion),
            ('fechaEmisionDocSustento', inv_obj.normalize_date(docsustento.date_invoice)),
            ('detalles', detalles)
        ])
        return res

    @api.multi
    def get_detalle_dict(self, p, pack, inv_obj):
        res = OrderedDict([
            ('codigoInterno', p.default_code),
            ('codigoAdicional', p.barcode),
            ('descripcion', inv_obj.normalize(p.name)),
            ('cantidad', '{:.2f}'.format(pack.qty_done)),
        ])
        return res

    @api.multi
    def get_transportista(self):
        """
        Modificar con super
        :param self:
        :return: recordset de res.partner(id)
        """
        transportista = self.driver_id
        return transportista

    @api.multi
    def get_placa(self):
        """
        Modificar con super
        :param self:
        :return: str de placa
        """
        placa = self.carrier_tracking_ref
        return placa

    @api.multi
    def get_infoguiaremision_dict(self, autorizacion_id, dirpartida, inv_obj):
        transportista = self.get_transportista()
        placa = self.get_placa()
        today = inv_obj.normalize_date(fields.Date.today())
        tr_fiscal = transportista.property_account_position_id
        if not self.picking_type_id.warehouse_id.partner_id:
            raise UserError(_('Plase check address for Warehouse:'.format(
                self.picking_type_id.warehouse_id.name)))
        address = u'{} {}'.format(self.picking_type_id.warehouse_id.partner_id.street,
                                  self.picking_type_id.warehouse_id.partner_id.street2)
        res = OrderedDict([
            ('dirEstablecimiento', inv_obj.normalize(address)),
            ('dirPartida', dirpartida),
            ('razonSocialTransportista', inv_obj.normalize(transportista.name)),
            ('tipoIdentificacionTransportista', tr_fiscal.identificacion_id.tpidcliente),
            ('rucTransportista', transportista.vat),
            # ('rise', ''),TODO
            ('obligadoContabilidad', tr_fiscal.obligada_contabilidad and 'SI' or 'NO'),
            ('contribuyenteEspecial', self.company_id.contribuyenteespecial or '000'),
            ('fechaIniTransporte', inv_obj.normalize_date(self.fechainitransporte)),
            ('fechaFinTransporte', inv_obj.normalize_date(self.fechafintransporte)),
            ('placa', placa)])
        return res

    @api.multi
    def get_guia_remision_dict(self, dest=None):
        de_obj = self.env['l10n_ec_sri.documento.electronico']
        inv_obj = self.env['account.invoice']

        dest = dest or self.partner_id
        ambiente_id = self.env.user.company_id.ambiente_id
        company = self.env.user.company_id
        # company_fiscal = company.partner_id.property_account_position_id
        ruc = company.vat

        # La Guia de Remision siempre se envia con fecha actual.
        fechaemision = fields.Date.context_today(self)

        loc_src = self.location_id
        wh_src = loc_src.get_warehouse(loc_src)
        if not wh_src:
            partner_src = company.partner_id
        else:
            partner_src = self.env['stock.warehouse'].browse(wh_src).partner_id
            if not partner_src:
                partner_src = company.partner_id

        dirpartida = inv_obj.normalize(
            ' '.join([partner_src.street or u'', partner_src.street2 or u'']))

        if not self.invoice_ids and self.partner_id:
            raise UserError(_('You need at least one invoice to proceed'))
        docsustento = self.invoice_ids.filtered(lambda x: x.state in ['open', 'paid'])

        autorizacion_id = self.autorizacion_id
        comprobante_id = self.comprobante_id
        comprobante = comprobante_id.code
        establecimiento = self.establecimiento
        puntoemision = self.puntoemision
        tipoemision = '1'  # offline siempre es normal.
        secuencial = self.secuencial.zfill(9)
        # partner = self.partner_id
        # fiscal = partner.property_account_position_id
        claveacceso = de_obj.get_claveacceso(
            fechaemision, comprobante, ruc, ambiente_id,
            establecimiento, puntoemision, secuencial)

        infoTributaria = inv_obj.get_infotributaria_dict(
            ambiente_id, tipoemision, company, ruc,
            claveacceso, comprobante, establecimiento,
            puntoemision, secuencial)

        infoGuiaRemision = self.get_infoguiaremision_dict(
            autorizacion_id, dirpartida, inv_obj
        )

        detalles = OrderedDict([
            ('detalle', []),
        ])
        for pack in self.pack_operation_product_ids:
            p = pack.product_id
            detalles['detalle'].append(
                self.get_detalle_dict(p, pack, inv_obj)
            )

        destinatarios = OrderedDict([
            ('destinatario', []),
        ])
        for d in dest:
            destinatarios['destinatario'].append(
                self.get_destinatario_dict(d, docsustento, inv_obj)
            )

        guiaremision_dict = OrderedDict([
            ('guiaRemision', OrderedDict([
                ('@id', 'comprobante'),
                ('@version', '1.0.0'),
                ('infoTributaria', infoTributaria),
                ('infoGuiaRemision', infoGuiaRemision),
                ('destinatarios', destinatarios),
            ]),
            )
        ])

        return ambiente_id, comprobante_id, guiaremision_dict, claveacceso, tipoemision

    @api.one
    def get_autorizacion(self):
        """
        Si el usuario tiene una autorización la usamos.
        Caso contrario usamos la de la compañía.
        """
        u = self.env.user
        c = self.company_id
        aut = u.autorizacion_guias_remision_id or c.autorizacion_guias_remision_id

        secuencial = aut.secuencia_actual + 1

        self.update({
            'comprobante_id': aut.comprobante_id.id,
            'autorizacion_id': aut.id,
            'puntoemision': aut.puntoemision,
            'establecimiento': aut.establecimiento,
            'secuencial': secuencial,
        })
        aut.update({'secuencia_actual': secuencial})
        return True

    @api.multi
    def button_send_guia_remision_electronica(self):
        self.get_autorizacion()
        ambiente_id, comprobante_id, guiaremision_dict, claveacceso, tipoemision = self.get_guia_remision_dict()
        de_obj = self.env['l10n_ec_sri.documento.electronico']
        reference = 'stock.picking,%s' % self.id
        vals = de_obj.get_documento_electronico_dict(
            ambiente_id, comprobante_id, guiaremision_dict, claveacceso, tipoemision, reference
        )
        # La autorizacion de la guia de remision es igual a la clave de acceso.
        self.autorizacion = claveacceso

        if self.guia_remision_electronica_id:
            self.guia_remision_electronica_id.write(vals)
        else:
            de = de_obj.create(vals)
            self.guia_remision_electronica_id = de

        # Envía el correo electrónico a los destinatarios.
        # self.send_email_de()

        return True

    @api.multi
    def get_email_template(self):
        return self.env.ref('l10n_ec_sri_ece_stock.email_template_guia_remision_electronica', False)

    @api.multi
    def send_email_de(self):
        self.ensure_one()
        if self.guia_remision_electronica_id:
            template_id = self.get_email_template()
        elif not self.guia_remision_electronica_id:
            raise UserError(_(u"Debe generar una guía electrónica."))

        template_id.send_mail(self.ids[0], force_send=True)
        return True
