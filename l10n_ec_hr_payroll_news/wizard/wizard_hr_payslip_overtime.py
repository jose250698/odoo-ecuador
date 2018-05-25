#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import StringIO
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


from openerp import _, api, fields, models
from openerp.exceptions import UserError


class WizardHrPayslipOvertime(models.TransientModel):
    """
    Import Overrtime data from xlsx file
    """
    _name = 'wizard.hr.payslip.overtime'

    name = fields.Char(_('Template Name'))
    file_template = fields.Binary(_('Template'))
    file_upload = fields.Binary(_('Template'))
    state = fields.Selection([('draft', _('Draft')),
                              ('generated', _('Generated'))], default='draft')

    @api.multi
    def generate_template(self):
        for row in self:
            file_data = StringIO.StringIO()
            xbook = xlsxwriter.Workbook(file_data, {'in_memory': True})
            xsheet = xbook.add_worksheet('Overtime')
            header = [_('Identification'), _('Passport'), _('Name'), _(
                'Hours Night Shift (25%)'), _('Overtime (50%)'), _('Extra Hours (100%)')]
            xsheet.write_row(0, 0, header)
            period = time.strftime('%Y/%m/%d')
            xbook.close()
            out = base64.encodestring(file_data.getvalue())
            row.write({'name': _('Overtime_Template_%s.xlsx') % period,
                       'file_template': out, 'state': 'generated'})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.hr.payslip.overtime',
            'view_id': False,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def import_template(self):
        employee_obj = self.env['hr.employee']
        line_obj = self.env['hr.payslip.overtime.line']
        overtime_id = self._context.get('active_id')
        for row in self:
            if not row.file_upload:
                raise UserError(_('Please, select file to Import'))
            xdata = base64.b64decode(row.file_upload)
            xbook = xlrd.open_workbook(file_contents=xdata)
            df = pd.read_excel(xbook, "Overtime", engine="xlrd")
            for index, y in df.iterrows():
                identification = None if pd.isnull(y[0]) else str(y[0]).split('.')[0]
                passport = None if pd.isnull(y[1]) else str(y[1]).split('.')[1]
                employee_id = employee_obj.search([
                    '|', ('identification_id', '=', identification), ('passport_id', '=', passport)])
                vals = {
                    'overtime_id': overtime_id,
                    'employee_id': employee_id.id,
                    'overtime_025': float(0 if pd.isnull(y[3]) else y[3]),
                    'overtime_050': float(0 if pd.isnull(y[4]) else y[4]),
                    'overtime_100': float(0 if pd.isnull(y[5]) else y[5]),
                }
                line_id = line_obj.create(vals)
                line_id.onchange_employee_id()
        return True
