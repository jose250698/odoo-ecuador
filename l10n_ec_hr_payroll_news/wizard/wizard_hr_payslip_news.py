#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import io
import time

import logging
_logger = logging.getLogger(__name__)

try:
    import pandas as pd
except:
    _logger.error("The module pandas can't be loaded, try: pip install pandas")

try:
    import xlrd
except:
    _logger.error("The module xlrd can't be loaded, try: pip install xlrd")

try:
    import xlsxwriter
except:
    _logger.error("The module xlsxwriter can't be loaded, try: pip install xlsxwriter")


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizardHrPayslipNews(models.TransientModel):
    """
    Generate and Imports news from Template
    """
    _name = 'wizard.hr.payslip.news'
    _description = __doc__

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_wiz_news',
                                    'wiz_id', 'employee_id', _('Employees'))
    name = fields.Char(_('Name'))
    file_template = fields.Binary(_('Template'))
    file_upload = fields.Binary(_('Template'))
    approve_news = fields.Boolean(_('Approve news'))

    line_ids = fields.One2many('wizard.hr.payslip.news.line', 'wiz_id', string=_("Salary Rules"))
    option = fields.Selection([('export', _('Export Template')),
                               ('import', _('Import Template'))], string=_('Option'), default='export')
    state = fields.Selection([('draft', _('Draft')),
                              ('exported', _('Exported'))], string='State', default='draft')

    @api.multi
    def generate_template(self):
        for row in self:
            rules = []
            if not row.line_ids:
                raise UserError(
                    _('Please select at least one salary rule to generate the template!!'))
            for rule in row.line_ids:
                rules.append('%s|%s' % (rule.name, rule.rule_id.code))
            employee_data = []
            file_data = io.StringIO()
            xbook = xlsxwriter.Workbook(file_data, {'in_memory': True})
            xsheet = xbook.add_worksheet('News')
            header = [_('Identification'), _('Passport'), _('Name'), _('Period')] + rules
            period = time.strftime('%Y/%m/%d')
            if not row.employee_ids:
                raise UserError(_('Please select at least one employee to generate the template!!'))
            for hr in row.employee_ids:
                data = []
                data.insert(0, hr.identification_id or '')
                data.insert(1, hr.passport_id or '')
                data.insert(2, hr.name)
                data.insert(3, period)
                employee_data.append(data + [0.0 for x in rules])
                xsheet.write_row(0, 0, header)
            for line in range(0, len(employee_data)):
                xsheet.write_row(line + 1, 0, employee_data[line])
            xbook.close()
            out = base64.encodestring(file_data.getvalue())
            row.write({'name': _('News_Template_%s.xlsx') % period,
                       'file_template': out, 'state': 'exported'})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.hr.payslip.news',
            'view_id': False,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def import_template(self):
        employee_obj = self.env['hr.employee']
        news_obj = self.env['hr.payslip.news']
        rule_obj = self.env['hr.salary.rule']
        news_data = []
        for row in self:
            if not row.file_upload:
                raise UserError(_('Please Select file to import'))
            xdata = base64.b64decode(row.file_upload)
            xbook = xlrd.open_workbook(file_contents=xdata)
            df = pd.read_excel(xbook, "News", engine="xlrd")
            state = 'approved' if row.approve_news else 'draft'
            for index, y in df.iterrows():
                employee_id = employee_obj.search([
                    '|', ('identification_id', '=', y[0]), ('passport_id', '=', y[1])])
                data = y.to_dict()
                for key in data:
                    if key not in ['passport', 'identification', 'name', 'period']:
                        if data[key] > 0:
                            news_name, news_code = key.split('|')[0], key.split('|')[1]
                            rule_id = rule_obj.search([('code', '=', news_code)])
                            news_data.append({
                                'name': news_name,
                                'date': y[3],
                                'rule_id': rule_id.id,
                                'employee_id': employee_id.id,
                                'amount': data[key],
                                'state': state
                            })
        for new in news_data:
            news_obj.create(new)
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'tree,from',
            'res_model': 'hr.payslip.news',
            'view_id': False,
            'res_id': False,
            'type': 'ir.actions.act_window'
        }


class WizardHrPayslipNewsLine(models.TransientModel):
    """
    Salary Rule detail
    """
    _name = 'wizard.hr.payslip.news.line'
    _description = __doc__

    wiz_id = fields.Many2one('wizard.hr.payslip.news', string=_('Wizard'))
    name = fields.Char(_('Reason'), required=True)
    rule_id = fields.Many2one('hr.salary.rule', string=_("Salary Rule"), required=True)
