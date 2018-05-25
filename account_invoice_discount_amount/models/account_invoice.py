# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    price_discount = fields.Monetary(
        compute='_compute_price_discount',
        string='Price discount',
        readonly=True, store=True, )

    @api.depends('quantity', 'price_subtotal', 'price_unit')
    def _compute_price_discount(self):
        """
        Compute the amounts of the price discount.
        """
        for line in self:
            discount = (line.quantity * line.price_unit) - line.price_subtotal
            line.price_discount = discount


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    price_discount = fields.Monetary(
        compute='_compute_price_discount',
        string='Price discount',
        readonly=True, store=True, )

    @api.depends('invoice_line_ids.price_discount')
    def _compute_price_discount(self):
        for record in self:
            record.price_discount = sum(record.invoice_line_ids.mapped('price_discount'))
