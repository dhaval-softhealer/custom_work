# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.


from odoo import models, fields, _, api

class shSaleOrder(models.Model):
    _inherit = 'sale.order'
    
    sh_purchase_order_id = fields.Many2one('purchase.order', string="Sale order")

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

