#!/usr/bin/env python
# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class HrPayslipInput(models.Model):
    """
    Add news links to hr.payslip.input
    """
    _inherit = ['hr.payslip.input']
    _description = __doc__

    new_id = fields.Many2one(
        'hr.payslip.news',
        string=_('New'),
        ondelete='cascade')
    overtime_id = fields.Many2one(
        'hr.payslip.overtime.line',
        string=_('New'),
        ondelete='cascade')
    quantity = fields.Char(_('Quantity'))


class HrPayslip(models.Model):
    _inherit = ['hr.payslip']

    @api.multi
    def hr_verify_sheet(self):
        for row in self:
            for line in row.input_line_ids:
                if line.new_id:
                    line.new_id.write({'state': 'done'})
                if line.overtime_id:
                    line.overtime_id.write({'state': 'done'})
                    line.overtime_id.overtime_id.write({'state': 'done'})
        return self.write({'state': 'verify'})

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        contract_obj = self.env['hr.contract']
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        news_obj = self.env['hr.payslip.news']
        overtime_obj = self.env['hr.payslip.overtime.line']
        for contract in contract_obj.browse(contract_ids):
            news_ids = news_obj.search([('date', '>=', date_from),
                                        ('date', '<=', date_to),
                                        ('employee_id', '=', contract.employee_id.id),
                                        ('state', '=', 'approved')])
            for new in news_ids:
                inputs = {
                    'name': str(new.name or new.rule_id.name).upper(),
                    'code': new.rule_id.category_id.code,
                    'contract_id': contract.id,
                    'new_id': new.id,
                    'amount': new.amount,
                }
                res += [inputs]
            overtime_ids = overtime_obj.search([('date', '>=', date_from),
                                                ('date', '<=', date_to),
                                                ('employee_id', '=', contract.employee_id.id),
                                                ('state', '=', 'approved')])
            for over in overtime_ids:
                if over.overtime_025:
                    inputs = {
                        'name': _('HOURS NIGHT SHIFT (25%)'),
                        'code': 'INGGRAV',
                        'contract_id': contract.id,
                        'overtime_id': over.id,
                        'quantity': over.overtime_025,
                        'amount': over.hour_cost * over.overtime_025 * 1.25
                    }
                    res += [inputs]
                if over.overtime_050:
                    inputs = {
                        'name': _('OVERTIME (50%)'),
                        'code': 'INGGRAV',
                        'contract_id': contract.id,
                        'overtime_id': over.id,
                        'quantity': over.overtime_050,
                        'amount': over.hour_cost * over.overtime_050 * 1.50
                    }
                    res += [inputs]
                if over.overtime_100:
                    inputs = {
                        'name': _('EXTRA HOURS (100%)'),
                        'code': 'INGGRAV',
                        'contract_id': contract.id,
                        'overtime_id': over.id,
                        'quantity': over.overtime_100,
                        'amount': over.hour_cost * over.overtime_100 * 2.00
                    }
                    res += [inputs]
        return res
