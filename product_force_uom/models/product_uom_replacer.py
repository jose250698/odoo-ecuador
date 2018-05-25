# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api

class ProductUomReplacer(models.TransientModel):
    _name = "product_force_uom.wizard"
    _description = "Replace UOM on product templates"

    product_ids = fields.Many2many('product.product', string='Products', )
    uom_id = fields.Many2one('product.uom', 'Unit of measure', )

    @api.multi
    def button_force_uom(self):
        for r in self:
            uom = r.uom_id
            for product in r.product_ids:
                product.sudo().write({'uom_id': uom.id, 'uom_po_id': uom.id})

                template = product.product_tmpl_id
                template.sudo().write({'uom_id': uom.id, 'uom_po_id': uom.id})

                variantes = product.product_variant_ids
                variantes.sudo().write({'uom_id': uom.id, 'uom_po_id': uom.id})

                aal = self.env['account.analytic.line'].search([('product_id', '=', product.id)])
                aal.sudo().write({'product_uom_id': uom.id})

                ail = self.env['account.invoice.line'].search([('product_id', '=', product.id)])
                ail.sudo().write({'uom_id': uom.id})

                aml = self.env['account.move.line'].search([('product_id', '=', product.id)])
                aml.sudo().write({'product_uom_id': uom.id})

                he = self.env['hr.expense'].search([('product_id', '=', product.id)])
                he.sudo().write({'product_uom_id': uom.id})

                mp = self.env['make.procurement'].search([('product_id', '=', product.id)])
                mp.sudo().write({'uom_id': uom.id})

                mrp_bom = self.env['mrp.bom'].search([('product_id', '=', product.id)])
                mrp_bom.sudo().write({'product_uom': uom.id})

                bom_line = self.env['mrp.bom.line'].search([('product_id', '=', product.id)])
                bom_line.sudo().write({'product_uom': uom.id})

                mrp_production = self.env['mrp.production'].search([('product_id', '=', product.id)])
                mrp_production.sudo().write({'product_uom': uom.id})

                mppl = self.env['mrp.production.product.line'].search([('product_id', '=', product.id)])
                mppl.sudo().write({'product_uom': uom.id})

                msp = self.env['mrp.subproduct'].search([('product_id', '=', product.id)])
                msp.sudo().write({'product_uom': uom.id})

                po = self.env['procurement.order'].search([('product_id', '=', product.id)])
                po.sudo().write({'product_uom': uom.id})

                psi = self.env['product.supplierinfo'].search([('product_id', '=', product.id)])
                psi.sudo().write({'product_uom': uom.id})

                sol = self.env['sale.order.line'].search([('product_id', '=', product.id)])
                sol.sudo().write({'product_uom': uom.id})

                pol = self.env['purchase.order.line'].search([('product_id', '=', product.id)])
                pol.sudo().write({'product_uom': uom.id})

                sil = self.env['stock.inventory.line'].search([('product_id', '=', product.id)])
                sil.sudo().write({'product_uom_id': uom.id})

                spo = self.env['stock.pack.operation'].search([('product_id', '=', product.id)])
                spo.sudo().write({'product_uom_id': uom.id})

                sms = self.env['stock.move.scrap'].search([('product_id', '=', product.id)])
                sms.sudo().write({'product_uom': uom.id})

                swo = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product.id)])
                swo.sudo().write({'product_uom': uom.id})

                smc = self.env['stock.move.consume'].search([('product_id', '=', product.id)])
                smc.sudo().write({'product_uom': uom.id})

                stock_move = self.env['stock.move'].search([('product_id', '=', product.id)])
                stock_move.sudo().write({'product_uom': uom.id})

                quant_line = self.env['stock.quant'].search([('product_id', '=', product.id)])
                quant_line.sudo().write({'product_uom_id': uom.id})


    @api.multi
    def button_update_uom_bom(self):
        mrp_bom = self.env['mrp.bom'].search([])
        for bom in mrp_bom:
            uom = bom.product_tmpl_id.uom_id
            bom.product_uom = uom


