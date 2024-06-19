# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.


from odoo import models, fields, _, api

class shSaleOrder(models.Model):
    _inherit = 'sale.order'
    
    sh_purchase_order_id = fields.Many2one('purchase.order', string="Sale order")
    sh_purchase_order_count = fields.Integer(string='Purchase Order Count',compute='_count_purchase_order', readonly=True,)
    sh_BOM_count = fields.Integer(string='BOM Count',compute='_count_bom', readonly=True,)
    sh_attechment_count = fields.Integer(string='Attachments Count',compute='_count_attachment', readonly=True,)


    def _count_purchase_order(self):
        for order in self:
            purchase_orders = self.env['purchase.order'].search( [('sh_sale_order_id','=',order.id)])
            if purchase_orders:
                order.sh_purchase_order_count = len(purchase_orders.ids)
            else:
                order.sh_purchase_order_count = 0
                
    def _count_bom(self):
        for order in self:
            bom_orders_list = []
            for orderline in order.order_line:
                bom_orders = self.env['mrp.bom'].search([['id', 'in', orderline.product_id.bom_ids.ids]])
                bom_orders_list.extend(bom_orders)
            
            if bom_orders_list:
                order.sh_BOM_count = len(bom_orders_list)
            else:
                order.sh_BOM_count = 0

    def _count_attachment(self):
        for order in self:
            attachments = self.env['ir.attachment'].search([('res_id','=',order.id)])
            print("\n\n\n\n\n\n\n\nattachments  ", attachments)
            if attachments:
                order.sh_attechment_count = len(attachments.ids)
            else:
                order.sh_attechment_count = 0


    def action_view_po(self):
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain' : [('sh_sale_order_id','=',self.id)],
        }

    def create_po(self):
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
             'context': {
                "sh_sale_order_id" :  self.id
            },
        }
    
    def action_view_mrp_bom(self):
        for orderline in self.order_line:
            result = {
                "type": "ir.actions.act_window",
                "res_model": "mrp.bom",
                "domain": [['id', 'in', orderline.product_id.bom_ids.ids]],
                "name": _("Bills of Materials"),
                'view_mode': 'tree,form',
            }
           
        return result
        
    def action_view_attachments(self):
         return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree',
            'views': [(self.env.ref('sh_sale_customization.sh_view_attachment_tree').id, 'tree')],
            'domain' : [('res_id','=',self.id)],
        }

