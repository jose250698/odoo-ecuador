# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Luis M. Ontalba
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    source_move_line_id = fields.Many2one('account.move.line', string="Source move line", )
