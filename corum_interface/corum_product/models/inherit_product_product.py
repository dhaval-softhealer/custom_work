from datetime import datetime, timedelta
from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    on_order_count = fields.Float(string='On Order', compute='_compute_on_order_count')
    pos_order_count = fields.Float(string='Sold', compute='_compute_pos_order_count')

    # Add Purchased smart button
    def action_view_po(self):
        date_one_year_ago = fields.Date.today() - timedelta(days=365)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Purchased',
            'view_mode': 'list,pivot,graph',
            'res_model': 'purchase.order.line',
            'domain': [('state', 'in', ['purchase', 'done']),
                       ('product_id', 'in', self.ids),
                       ('date_planned', '>=', date_one_year_ago)],
            'context': dict(self.env.context, search_default_later_than_a_year_ago=True),
        }

        search_view = self.env.ref('corum_interface.corum_purchase_order_line_search_view', False)
        if search_view:
            action['search_view_id'] = search_view.id

        views = []

        list_view = self.env.ref('corum_interface.corum_purchase_order_line_tree_view', False)
        if list_view:
            views.append((list_view.id, 'list'))

        pivot_view = self.env.ref('corum_interface.corum_purchase_order_line_tree_view', False)
        if pivot_view:
            views.append((pivot_view.id, 'pivot'))

        graph_view = self.env.ref('corum_interface.corum_purchase_order_line_tree_view', False)
        if graph_view:
            views.append((graph_view.id, 'graph'))

        if views:
            action['views'] = views

        return action


    @api.depends('purchase_order_line_ids')
    def _compute_on_order_count(self):
        for record in self:
            purchase_order_lines = self.env['purchase.order.line'].search([
                ('product_id', '=', record.id),
                ('order_id.invoice_status', '=', 'no'),
                ('order_id.state', '!=', 'cancel'),
            ])
            record.on_order_count = sum(line.product_qty for line in purchase_order_lines)

    def action_view_on_order(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [
            ('order_line.product_id', '=', self.id),
            ('invoice_status', '=', 'no'),
            ('state', '!=', 'cancel'),
        ]
        return action
    
    # Add Sold smart button
    def _compute_pos_order_count(self):
        for record in self:
            date_start = fields.Date.today() - timedelta(days=365)
            pos_order_lines = self.env['pos.order.line'].search([
                ('product_id', '=', record.id),
                ('order_id.date_order', '>=', date_start)
            ])
            record.pos_order_count = sum(line.qty for line in pos_order_lines)

    def action_view_pos_order(self):
        date_start = fields.Date.today() - timedelta(days=365)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Sold',
            'view_mode': 'list,pivot,graph',
            'res_model': 'pos.order.line',
            'domain': [('product_id', 'in', self.ids),
                       ('order_id.date_order', '>=', date_start)],
            'context': dict(self.env.context, search_default_later_than_a_year_ago=True),
        }

        search_view = self.env.ref('corum_interface.corum_pos_order_line_search_view', False)
        if search_view:
            action['search_view_id'] = search_view.id

        views = []

        list_view = self.env.ref('corum_interface.corum_pos_order_line_tree_view', False)
        if list_view:
            views.append((list_view.id, 'list'))

        pivot_view = self.env.ref('corum_interface.corum_pos_order_line_tree_view', False)
        if pivot_view:
            views.append((pivot_view.id, 'pivot'))

        graph_view = self.env.ref('corum_interface.corum_pos_order_line_tree_view', False)
        if graph_view:
            views.append((graph_view.id, 'graph'))

        if views:
            action['views'] = views

        return action