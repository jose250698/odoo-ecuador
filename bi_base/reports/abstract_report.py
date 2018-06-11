# -*- coding: utf-8 -*-
import base64
import logging
from cStringIO import StringIO

from openerp import _, api, fields, models
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)


try:
    import openpyxl
except ImportError:
    _logger.error("The module openpyxl can't be loaded, try: pip install openpyxl")


class BiAbstractReport(models.AbstractModel):
    _name = 'bi.abstract.report'

    xlsx_file = fields.Binary('Production', attachment=False, readonly=True, )
    xlsx_filename = fields.Char(string="Production filename", )
    date_from = fields.Datetime(
        string='Date from', )
    date_to = fields.Datetime(
        string='Date to',
        required=True,
        default=fields.Datetime.now(), )

    @api.multi
    def get_report_data(self):
        """
        return: diccionario con:
        data = {
            'wizard': 'nombre.del.wizard',
            'filename': 'archivo.xlsx',
            'sheets':[
                {
                'name': 'nombre',
                'rows': [[A,B,C],[1,2,3],[4,5,6]]
                }
                {
                'name': 'nombre',
                'rows': [[A,B,C],[1,2,3],[4,5,6]]
                }
        """
        return False

    @api.multi
    def button_get_xlsx_report(self):
        data = self.get_report_data()
        wb = openpyxl.Workbook()

        sheets = data.get('sheets', [])
        if not sheets:
            raise UserError(_(u"No existen datos para el reporte."))
        for s in sheets:
            name = s.get('name', 'sheet %s' % sheets.index(s))
            ws = wb.create_sheet(name)
            rows = s.get('rows', [])
            for row in rows:
                ws.append(row)

        # Elimina la hoja por defecto
        wb.active = 1
        del wb['Sheet']

        output = StringIO()
        wb.save(output)
        xlsx_data = output.getvalue()
        self.write({'xlsx_filename': data.get('filename', 'report.xlsx'),
                    'xlsx_file': base64.encodestring(xlsx_data)})

        return {
            'type': 'ir.actions.act_window',
            'res_model': data.get('wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self._context,
        }
