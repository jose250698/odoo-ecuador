# -*- coding: utf-8 -*-

from openerp import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    puntoemision = fields.Integer('Punto de emisión', )
    establecimiento = fields.Integer('Establecimiento', )
    secuencial = fields.Integer('Secuencial')
    autorizacion = fields.Integer('Autorización')

    # BORRAR
    autorizacion_id = fields.Many2one('l10n_ec_sri.autorizacion', string='Autorizacion', )


class PosOrder(models.Model):
    _inherit = 'pos.order'

    puntoemision = fields.Integer('Punto de emisión', )
    establecimiento = fields.Integer('Establecimiento', )
    secuencial = fields.Integer('Secuencial')
    autorizacion = fields.Integer('Autorización')

    @api.multi
    def action_invoice(self):
        res = super(PosOrder, self).action_invoice()
        res_id = res['res_id']
        res_model = res['res_model']
        inv = self.env[res_model].browse(res_id)
        inv.compute_sri_invoice_amounts()
        return res

