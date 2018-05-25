# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class StockPickingTemplateLine(models.Model):
    _name = 'stock.picking.template.line'

    @api.multi
    @api.onchange('product_id')
    def _onchange_uom_domain(self):
        for r in self:
            uom_category = r.product_id.uom_id.category_id.id
            r.product_uom = r.product_id.uom_id
            return {'domain':{'product_uom': [('category_id', '=', uom_category)]}}

    product_id = fields.Many2one(
        'product.product', ondelete='set null', string="Product",
        required=True, )
    product_uom = fields.Many2one(
        'product.uom', ondelete='set null', string="Product UOM", ) # required=True,
    product_uom_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), )
    template_id = fields.Many2one('stock.picking.template', string='Template', ondelete='cascade', )


class StockPickingTemplate(models.Model):
    _name = 'stock.picking.template'

    name = fields.Char('Name', )
    template_line_ids = fields.One2many(
        'stock.picking.template.line', 'template_id', string='Template lines', )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picking_template_id = fields.Many2one(
        'stock.picking.template', ondelete='set null', string="Picking template", )

    @api.multi
    def prepare_move_lines_from_template(self, t=None, expected_date=None):
        vals = {
            'name': self.name + ' %s' % t.product_id.name,
            'picking_id': self.id,
            'date': expected_date,
            'date_expected': expected_date,
            'product_id': t.product_id.id,
            'product_uom_qty': t.product_uom_qty,
            'product_uom': t.product_uom.id,
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'procure_method': 'make_to_stock',
        }
        return vals

    @api.multi
    def clean_cero_qty_move_lines(self):
        for r in self:
            no_qty = self.env['stock.move']
            for m in r.move_lines:
                if m.product_uom_qty == 0:
                    no_qty += m
            no_qty.unlink()

    @api.multi
    def create_move_lines_from_template(self, **kwargs):
        # TODO evitar warning cuando los valores por defecto son mayores que el pedido real.
        expected_date = self.min_date

        if not expected_date:
            raise exceptions.UserError(_('Select an expected date and save your picking first.'))

        move_lines = {}

        for t in self.picking_template_id.template_line_ids:
            key = t.product_id.id

            vals = self.prepare_move_lines_from_template(t, expected_date)

            line = self.move_lines.filtered(lambda l: l.product_id.id == key)
            if len(line) > 0:
                line[0].product_uom_qty += vals['product_uom_qty']

            elif key in move_lines:
                move_lines[key]['product_uom_qty'] += vals['product_uom_qty']

            else:
                move_lines[key] = vals

        for ml in move_lines.values():
            self.env['stock.move'].create(ml)
