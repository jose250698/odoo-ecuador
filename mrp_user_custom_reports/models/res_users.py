# -*- coding: utf-8 -*-
from openerp import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    mrp_format_id = fields.Many2one('report.custom.format', string="MRP Report Format", )
