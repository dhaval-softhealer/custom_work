# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sh_vendor_pro_code = fields.Char(string="Product Code")

    def get_supplier_info(self, order_line):
        supplier_info = order_line.product_id.seller_ids.filtered(
            lambda h: (
                h.product_id == order_line.product_id
                and h.name == order_line.partner_id
            )
        )
        if supplier_info:
            return supplier_info[0]
        else:
            supplier_info = order_line.product_id.seller_ids.filtered(
                    lambda h: (
                        h.name == order_line.partner_id
                )
            )

            if supplier_info:
                return  supplier_info[0]
        
        return False

    @api.onchange('partner_id', 'product_id')
    def _onchange_product_vendor_code(self):
        for line in self:
            supplier_info = self.get_supplier_info(line)
            if supplier_info:
                line.sh_vendor_pro_code = supplier_info.product_code
            else:
                line.sh_vendor_pro_code = ''

    def write(self, vals):
        res = super(PurchaseOrderLine, self).write(vals)

        for rec in self:
            if rec.product_id != False and rec.sh_vendor_pro_code == False:
                supplier_info = self.get_supplier_info(rec)
                if supplier_info:
                    rec.write({'sh_vendor_pro_code': supplier_info.product_code or '' })

        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id')
    def _onchange_partner_product_code(self):
        for rec in self:
            order_lines = rec.order_line
            for line in order_lines:
                supplier_info = line.product_id.seller_ids.filtered(
                    lambda h: (
                        h.product_id == line.product_id
                        and h.name == line.partner_id
                    )
                )
                if supplier_info:
                    code = supplier_info[0].product_code or ''
                    line.sh_vendor_pro_code = code
                else:
                    supplier_info = line.product_id.seller_ids.filtered(
                        lambda h: (h.name == line.partner_id))
                    if supplier_info:
                        code = supplier_info[0].product_code or ''
                        line.sh_vendor_pro_code = code
                    else:
                        line.sh_vendor_pro_code = ''
