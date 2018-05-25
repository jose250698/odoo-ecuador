# -*- coding: utf-8 -*-
from openerp import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mo_id = fields.Many2one(
        'mrp.production', ondelete='restrict', string="Production", )
