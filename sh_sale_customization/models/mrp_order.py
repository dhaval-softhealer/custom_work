# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.


from odoo import models, fields, _, api

class shPurchaseOrder(models.Model):
    _inherit = 'mrp.production'

    sh_purchase_order_count = fields.Integer(string='Purchase Order Count',compute='_count_purchase_order', readonly=True,)
    sh_attechment_count = fields.Integer(string='Attachments Count',compute='_count_attachment', readonly=True,)

    def _count_attachment(self):
        for order in self:
            attachments = self.env['ir.attachment'].search([('res_id','=',order.id)])
            print("\n\n\n\n\n\n\n\nattachments  ", attachments)
            if attachments:
                order.sh_attechment_count = len(attachments.ids)
            else:
                order.sh_attechment_count = 0

    def _count_purchase_order(self):
        for order in self:
            purchase_orders_list = []
            sale_order_ids = order.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
            for each_id in sale_order_ids:
                sale_order = self.env["sale.order"].browse(each_id)
                purchase_orders = self.env['purchase.order'].search([('id', '=', sale_order.sh_purchase_order_id.id)])
                purchase_orders_list.extend(purchase_orders.ids)
            
            if purchase_orders_list:
                order.sh_purchase_order_count = len(purchase_orders_list)
            else:
                order.sh_purchase_order_count = 0


    def action_view_po(self):
        sale_order_ids = self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
        purchase_order_ids = []

        for each_id in sale_order_ids:
            sale_order = self.env["sale.order"].browse(each_id)
            purchase_order_ids.append(sale_order.sh_purchase_order_id.id)

        result = {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', purchase_order_ids)],
        }

        if len(purchase_order_ids) == 1:
            result.update({
                'view_mode': 'form',
                'res_id': purchase_order_ids[0],
            })
        else:
            result.update({
                'view_mode': 'tree,form',
            })

        return result

        
    def action_view_attachments(self):
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree',
            'views': [(self.env.ref('sh_sale_customization.sh_view_attachment_tree').id, 'tree')],
            'domain' : [('res_id','=',self.id),('res_name','=',self.name),('res_model',"=",'mrp.production')],
        }

