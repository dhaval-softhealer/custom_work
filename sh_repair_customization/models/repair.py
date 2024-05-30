# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.


from odoo import models


class ResConfigInherit(models.Model):
    _inherit = 'repair.order'


    def action_validate(self):
        res =  super().action_validate()
        for each_line in self.operations:
            if each_line.product_id:
                for each_product in each_line.product_id:
                    for each_vendor in each_product.product_tmpl_id.variant_seller_ids:
                            self.env['purchase.order'].create({
                                "partner_id": each_vendor.partner_id.id,
                                "order_line": [(0, 0, {
                                    'product_id': each_product.id,
                                    'name': each_product.name,
                                    'product_qty': each_line.product_uom_qty,
                                    'price_unit': each_vendor.price,
                                })],
                            })
        return res