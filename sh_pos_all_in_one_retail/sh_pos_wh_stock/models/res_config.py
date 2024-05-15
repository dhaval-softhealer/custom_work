# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def sh_get_product_info_pos(self,pos_config_id):
        config = self.env['pos.config'].browse(pos_config_id)
        res = {}
        if config and config.sh_display_stock_from_other_companies and config.sh_warehouse_company_ids:
            warehouse_company_ids = []
            warehouse_detail = {}
            for each_warehouse_company in config.sh_warehouse_company_ids:
                warehouse_company_ids.append(each_warehouse_company.id)
            w = self.env['stock.warehouse'].sudo().search([])
            if w :
                for each_warehouse in w:
                    if each_warehouse.company_id and each_warehouse.company_id.id in warehouse_company_ids:
                        if warehouse_detail.get(each_warehouse.company_id.name):
                            warehouse_detail[each_warehouse.company_id.name].append({'name': each_warehouse.name,
                            'available_quantity': self.sudo().with_context({'warehouse': each_warehouse.id}).qty_available,
                            'forecasted_quantity': self.sudo().with_context({'warehouse': each_warehouse.id}).virtual_available,
                            'uom': self.uom_name,
                            'location_name': each_warehouse.code + '/' + each_warehouse.lot_stock_id.name,
                            'location_available_quantity': self.sudo().with_context({'location': each_warehouse.lot_stock_id.id}).qty_available,
                            'location_forecasted_quantity': self.sudo().with_context({'location': each_warehouse.lot_stock_id.id}).virtual_available,
                            })
                        else:
                            warehouse_detail[each_warehouse.company_id.name] = []
                            warehouse_detail[each_warehouse.company_id.name].append({'name': each_warehouse.name,
                            'available_quantity': self.sudo().with_context({'warehouse': each_warehouse.id}).qty_available,
                            'forecasted_quantity': self.sudo().with_context({'warehouse': each_warehouse.id}).virtual_available,
                            'uom': self.uom_name,
                            'location_name': each_warehouse.code + '/' + each_warehouse.lot_stock_id.name,
                            'location_available_quantity': self.sudo().with_context({'location': each_warehouse.lot_stock_id.id}).qty_available,
                            'location_forecasted_quantity': self.sudo().with_context({'location': each_warehouse.lot_stock_id.id}).virtual_available,
                            })
            res['warehouse_company_wise'] = warehouse_detail
        return res

    def get_product_info_pos(self, price, quantity, pos_config_id):
        res = super(ProductProduct, self).get_product_info_pos(price, quantity, pos_config_id)
        config = self.env['pos.config'].browse(pos_config_id)

        if config and config.sh_display_stock_from_other_companies and config.sh_warehouse_company_ids:
            warehouse_company_ids = []
            warehouse_detail = {}
            for each_warehouse_company in config.sh_warehouse_company_ids:
                warehouse_company_ids.append(each_warehouse_company.id)
            w = self.env['stock.warehouse'].sudo().search([])
            if w :
                for each_warehouse in w:
                    if each_warehouse.company_id and each_warehouse.company_id.id in warehouse_company_ids:
                        if warehouse_detail.get(each_warehouse.company_id.name):
                            warehouse_detail[each_warehouse.company_id.name].append({'name': each_warehouse.name,
                            'available_quantity': self.sudo().with_context({'warehouse': each_warehouse.id}).qty_available,
                            'forecasted_quantity': self.sudo().with_context({'warehouse': each_warehouse.id}).virtual_available,
                            'uom': self.uom_name,
                            'location_name': each_warehouse.code + '/' + each_warehouse.lot_stock_id.name,
                            'location_available_quantity': self.sudo().with_context({'location': each_warehouse.lot_stock_id.id}).qty_available,
                            'location_forecasted_quantity': self.sudo().with_context({'location': each_warehouse.lot_stock_id.id}).virtual_available,
                            })
                        else:
                            warehouse_detail[each_warehouse.company_id.name] = []
                            warehouse_detail[each_warehouse.company_id.name].append({'name': each_warehouse.name,
                            'available_quantity': self.sudo().with_context({'warehouse': each_warehouse.id}).qty_available,
                            'forecasted_quantity': self.sudo().with_context({'warehouse': each_warehouse.id}).virtual_available,
                            'uom': self.uom_name,
                            'location_name': each_warehouse.code + '/' + each_warehouse.lot_stock_id.name,
                            'location_available_quantity': self.sudo().with_context({'location': each_warehouse.lot_stock_id.id}).qty_available,
                            'location_forecasted_quantity': self.sudo().with_context({'location': each_warehouse.lot_stock_id.id}).virtual_available,
                            })
            res['warehouse_company_wise'] = warehouse_detail
        return res

class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_display_stock = fields.Boolean("Display Warehouse Stock")
    sh_display_by = fields.Selection([('location', 'Location'), (
        'warehouse', 'Warehouse')], string="Display Qty By", default="warehouse")
    sh_min_qty = fields.Integer("Min Quantity")
    sh_show_qty_location = fields.Boolean("Only show quantity in POS location")
    sh_pos_location = fields.Many2one('stock.location', "POS Location")
    sh_display_stock_from_other_companies = fields.Boolean(string="Display Stock From Other Companies")
    sh_warehouse_company_ids = fields.Many2many('res.company', string="Companies")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        """We'll create some picking based on order_lines"""

        pickings = self.env['stock.picking']
        stockable_lines = lines.filtered(lambda l: l.product_id.type in [
                                         'product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding))
        if not stockable_lines:
            return pickings
        positive_lines = stockable_lines.filtered(lambda l: l.qty > 0)
        negative_lines = stockable_lines - positive_lines
        if positive_lines:
            if lines[0] and lines[0].order_id and lines[0].order_id.config_id and lines[0].order_id.config_id.sh_pos_location and lines[0].order_id.config_id.sh_pos_location.id:
                location_id = lines[0].order_id.config_id.sh_pos_location.id
            else:
                location_id = picking_type.default_location_src_id.id
            positive_picking = self.env['stock.picking'].create(
                self._prepare_picking_vals(
                    partner, picking_type, location_id, location_dest_id)
            )

            positive_picking._create_move_from_pos_order_lines(positive_lines)
            try:
                with self.env.cr.savepoint():
                    positive_picking._action_done()
            except (UserError, ValidationError):
                pass

            pickings |= positive_picking
        if negative_lines:
            if picking_type.return_picking_type_id:
                return_picking_type = picking_type.return_picking_type_id
                return_location_id = return_picking_type.default_location_dest_id.id
            else:
                return_picking_type = picking_type
                return_location_id = picking_type.default_location_src_id.id

            negative_picking = self.env['stock.picking'].create(
                self._prepare_picking_vals(
                    partner, return_picking_type, location_dest_id, return_location_id)
            )
            negative_picking._create_move_from_pos_order_lines(negative_lines)
            try:
                with self.env.cr.savepoint():
                    negative_picking._action_done()
            except (UserError, ValidationError):
                pass
            pickings |= negative_picking
        return pickings
