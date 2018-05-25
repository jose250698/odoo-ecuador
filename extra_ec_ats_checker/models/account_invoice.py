# -*- coding: utf-8 -*-
from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = ['account.invoice']

    invoice_ats_errors = fields.Char('Validaciones ATS', store=True, )
    invoice_ats_exception = fields.Boolean('Ignorar advertencias', )

    @api.multi
    def button_sri_ats_checker(self):
        for inv in self:
            if not inv.invoice_ats_exception:
                inv.get_ats_errors()

    @api.multi
    def get_ats_errors(self):
        retenciones = ('RetIr', 'RetIva', 'RetBien10',
                       'RetBienes', 'RetServ50', 'RetServ100',
                       'RetServ20', 'RetServicios')
        impuestos = ('ImpExe', 'ImpGrav', 'Imponible',
                     'Reembolso', 'NoGraIva',)

        for inv in self:
            errors = ''
            if inv.state != 'cancelled':

                # DOCUMENTOS DUPLICADOS.
                # Buscamos sencuenciales duplicadas.
                duplicados = self.search([
                    ('type', '=', inv.type),
                    ('secuencial', '=', inv.secuencial),
                ])

                # Si el secuencial está duplicado aplicamos los demás filtros.
                duplicados = duplicados.search([
                    ('autorizacion', '=', inv.autorizacion),
                    ('establecimiento', '=', inv.establecimiento),
                    ('puntoemision', '=', inv.puntoemision),
                    ('company_id', '=', inv.company_id.id),
                    ('id', '!=', inv.id)])

                # Si es documento de tercero, comprobamos el partner.
                if inv.type in ('in_invoice', 'in_refund'):
                    duplicados = duplicados.search([('partner_id', inv.partner_id.id)])

                if duplicados:
                    errors += 'La factura parece ser duplicada de %s. ' % duplicados

                # VALIDACIONES DEL TIPO DE COMPROBANTE
                if not inv.comprobante_id.code:
                    if inv.tax_line_ids:
                        errors += 'El documento registra impuestos pero no tiene un comprobante válido. '
                    else:
                        errors += 'Este documento no se considerará en sus declaraciones. '

                # VALIDACIONES DE LA RETENCIÓN
                if any(tax.tax_id.tax_group_id.name in retenciones for tax in inv.tax_line_ids):
                    if not inv.estabretencion1 or len(inv.estabretencion1) != 3:
                        errors += 'El establecimiento del comprobante de retención dete tener 3 dígitos. '
                    if not inv.ptoemiretencion1 or len(inv.ptoemiretencion1) != 3:
                        errors += 'El punto de emisión del comprobante de retención debe tener 3 dígitos. '
                    if not inv.autretencion1 or len(inv.autretencion1) not in (10, 37):
                        errors += 'La autorización del comprobante de retención debe tener 10 o 37 dígitos. '
                    if not inv.fechaemiret1 or inv.date_invoice > inv.fechaemiret1:
                        errors += 'La fecha del comprobante de retención debe ser mayor a la fecha del comprobante. '
                    if not inv.secretencion1 or len(inv.secretencion1) > 9 or int(inv.secretencion1) == 0:
                        errors += 'El secuencial debe tener menos de 10 caracteres y ser distinto de cero. '
                    # Si tiene retenciones debe haber un registro con la base
                    for line in inv.invoice_line_ids:
                        if not any(tax.tax_group_id.name in impuestos for tax in line.invoice_line_tax_ids):
                            errors += 'Si registra una retención debe registrar el código de la base imponible. '

            # VALIDACIÓN DE REEMBOLSOS

            # Si tiene sustento tributario de reembolso.
            r = ['08', '06']
            if any(x in inv.codsustento for x in r) and not inv.reembolso_ids:
                errors += 'El documento registra sustentos tributarios de reembolso (06 o 08) pero no registra documentos reembolsados. '

            # Si tiene una base imponible de reembolso.
            if inv.basereembolso:
                if inv.comprobante_id.code != '41':
                    errors += 'Los comprobantes de venta emitidos por reembolso deben tener código 41. '
                if not inv.documento_reembolsado_ids:
                    errors += 'El documento contiene valores por reembolso pero no se registra el comprobante que fué reembolsado. '

            # Valida datos del partner
            if not inv.partner_id.vat:
                errors += 'El tercero no tiene registrado ruc o cédula. '
            if not inv.partner_id.property_account_position_id:
                errors += 'El tercero no tiene registrado el tipo de contribuyente. '

            if len(inv.establecimiento) != 3:
                errors += 'Existe un error en la autorización el establecimiento es incorrecto. '
            if len(inv.puntoemision) != 3:
                errors += 'Existe un error en la autorización el punto de impresión es incorrecto. '
            if int(inv.secuencial) == 0:
                errors += 'El secuencial de la factura es 0. '

            inv.invoice_ats_errors = errors
