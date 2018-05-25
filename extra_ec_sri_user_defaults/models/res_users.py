# -*- coding: utf-8 -*-
from openerp import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    default_comprobante_id = fields.Many2one(
        'l10n_ec_sri.comprobante',
        'Default sale Document',
    )

    default_c_autorizacion_id = fields.Many2one(
        'l10n_ec_sri.autorizacion',
        'Default sale authorization',
    )
