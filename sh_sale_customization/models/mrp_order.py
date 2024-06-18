# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.


from odoo import models, fields, _, api

class shPurchaseOrder(models.Model):
    _inherit = 'mrp.production'

    def action_view_po(self):
        sale_order_ids = self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
        for each_id in sale_order_ids:
            sale_order = self.env["sale.order"].browse(each_id)
            return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain' : [('id','=',sale_order.sh_purchase_order_id.id)],
            }
        
    def action_view_attachments(self):
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree',
            'views': [(self.env.ref('sh_sale_customization.sh_view_attachment_tree').id, 'tree')],
            'domain' : [('res_id','=',self.id)],
        }

