# -*- coding: utf-8 -*-
###############################################################################
#
#   @author: Daniel Alejandro Mendieta <damendieta@fslibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
#
###############################################################################
from openerp import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    date_deposit = fields.Date(string="Deposit date", )
