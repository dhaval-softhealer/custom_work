# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.


from odoo import models, fields, _


class shRepairOrder(models.Model):
    _inherit = 'repair.order'

    sh_purchase_order_ids = fields.Many2many("purchase.order", string="purchase")
    

    def action_validate(self):
        PurchaseOrder = self.env['purchase.order']
        all_po = []
        for order in self:
            products_by_vendor = {}  # Dictionary to store products grouped by vendor
            for line in order.fees_lines:
                product = line.product_id
                if product.product_tmpl_id.variant_seller_ids:
                    lowest_vendor = min(product.product_tmpl_id.variant_seller_ids, key=lambda vendor: vendor.min_qty)
                    vendor = lowest_vendor.partner_id
                    if vendor not in products_by_vendor:
                                products_by_vendor[vendor] = []
                    products_by_vendor[vendor].append({
                                'product': product,
                                'quantity': line.product_uom_qty,
                                'price':lowest_vendor.price,
                            })
                
            # Create purchase orders
            for vendor, products in products_by_vendor.items():
                po_vals = {
                    'partner_id': vendor.id,
                    'order_line': [],
                    'sh_repair_order_id' : self.id,
                }
                for product in products:
                    po_vals['order_line'].append((0, 0, {
                        'product_id': product['product'].id,
                        'product_qty': product['quantity'],
                        'product_uom': product['product'].uom_id.id,
                        'price_unit': product['price'],  # Adjust price as needed
                    }))
                po = PurchaseOrder.create(po_vals)
                all_po.append(po.id)
                order["sh_purchase_order_ids"] = [(6, 0, all_po)]

        return super().action_validate()

    def action_view_po(self):
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain' : [('sh_repair_order_id','=',self.id)],
        }

class shPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    
    sh_repair_order_id = fields.Many2one('repair.order', string="Repair order")
    
    def action_view_ro(self):
        return {
            'name': _('Repair Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'repair.order',
            'view_mode': 'tree,form',
            'domain' : [('sh_purchase_order_ids','=',self.id)],
        }
