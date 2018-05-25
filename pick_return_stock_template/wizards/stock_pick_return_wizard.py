# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _


class StockPickReturnWizard(models.TransientModel):
    _name = "stock.pick.return.wizard"
    _inherit = 'pick.return.wizard'
    _description = "Create picking for the MO"

    template_id = fields.Many2one(
        'stock.picking.template', 'Picking Template', )
    pick_return_line_ids = fields.One2many(
        'pick.return.wizard.line',
        'stock_wizard_id',
        string='Moves to execute',
        ondelete='cascade',
    )

    @api.onchange('type', 'route_id')
    def _onchange_route_id(self):
        if self.route_id:
            loc_dest = self.location_dest_id
            dest, src, trans, out_type, in_type = self._prepare_locations(loc_dest=loc_dest)

            vals = {
                'location_dest_id': dest.id,
                'location_src_id': src.id,
                'location_trans_id': trans.id,
                'out_picking_type_id': out_type.id,
                'in_picking_type_id': in_type.id,
            }
            self.update(vals)

    @api.multi
    def create_move_lines_from_template(self):
        template = self.template_id

        if not template:
            raise exceptions.UserError(_('You need a template to '))

        lines = []
        for line in template.template_line_ids:
            lines.append({
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.product_uom_qty,
                'stock_wizard_id': self.id,
            })
        self.create_pick_return_lines(lines=lines)

    @api.multi
    def stock_create_picking(self):
        in_picking, out_picking = self.create_picking()
        pickings = in_picking + out_picking

        context = {'tree_view_ref': 'stock.vpicktree', 'form_view_ref': 'stock.view_picking_form'}
        return {
            'name': _('PICKINGS'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in pickings])],
            'context': context,
        }


class PickReturnWizardLine(models.TransientModel):
    _inherit = "pick.return.wizard.line"

    stock_wizard_id = fields.Many2one('stock.pick.return.wizard', string='Pick return wizard', )
