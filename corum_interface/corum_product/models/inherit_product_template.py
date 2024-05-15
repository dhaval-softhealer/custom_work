from datetime import datetime, timedelta
from odoo import models, api, fields, tools

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    on_order_count = fields.Float(string='On Order', compute='_compute_on_order_count')
    pos_order_count = fields.Float(string='Sold', compute='_compute_pos_order_count')

    @api.model
    def default_get(self, fields):
        result = super(ProductTemplate, self).default_get(fields)
        if 'available_in_pos' in result:
            result['available_in_pos'] = True
        return result

    detailed_type = fields.Selection(selection_add=[
        ('product', 'Storable Product')
    ], tracking=True, ondelete={'product': 'set consu'},default='product')

    markup_price = fields.Float(
        string='Markup',
        compute='_compute_markup_price',
        store=False
    )

    @api.depends('list_price', 'standard_price', 'taxes_id', 'taxes_id.amount')
    def _compute_markup_price(self):
        for template in self:
            tax_amount = sum(template.list_price / 110 * tax.amount for tax in template.taxes_id)
            template.markup_price = template.list_price - template.standard_price - tax_amount

    
    margin_percentage = fields.Float(
        string='Margin',
        compute='_compute_margin_percentage',
        store=False
    )

    @api.depends('markup_price', 'list_price')
    def _compute_margin_percentage(self):
        for template in self:
            if  template.list_price != 0:
                template.margin_percentage = (template.markup_price / template.list_price)
            else:
                template.margin_percentage = 0.0

    # Add Sold smart button
    def _compute_pos_order_count(self):
        for record in self:
            date_start = fields.Date.today() - timedelta(days=365)
            pos_order_lines = self.env['pos.order.line'].search([
                ('product_id.product_tmpl_id', '=', record.id),
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
            'domain': [('product_id.product_tmpl_id', 'in', self.ids),
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

    # Add Purchased smart button
    def action_view_po(self):
        date_one_year_ago = fields.Date.today() - timedelta(days=365)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Purchased',
            'view_mode': 'list,pivot,graph',
            'res_model': 'purchase.order.line',
            'domain': [('state', 'in', ['purchase', 'done']),
                       ('product_id.product_tmpl_id', 'in', self.ids),
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

    # Add On Order smart button
    def _compute_on_order_count(self):
        for record in self:
            purchase_order_lines = self.env['purchase.order.line'].search([
                ('product_id.product_tmpl_id', '=', record.id),
                ('order_id.invoice_status', '=', 'no'),
                ('order_id.state', '!=', 'cancel'),
            ])
            record.on_order_count = sum(line.product_qty for line in purchase_order_lines)

    def action_view_on_order(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [
            ('order_line.product_id.product_tmpl_id', '=', self.id),
            ('invoice_status', '=', 'no'),
            ('state', '!=', 'cancel'),
        ]
        return action

    # Replicate product data across all companies when creating products
    @api.model
    def create(self, vals):
        record = super(ProductTemplate, self).create(vals)
        record.sync_product_data_across_companies()
        return record

    def sync_product_data_across_companies(self):
        all_companies = self.env['res.company'].search([])
        property_obj = self.env['ir.property'].sudo()

        # Dynamically get the fields_id for 'standard_price' on 'product.product'
        field_id = self.env['ir.model.fields'].sudo().search([
            ('model', '=', 'product.product'),
            ('name', '=', 'standard_price')
        ], limit=1).id

        for company in all_companies:
            all_taxes_in_company = self.env['account.tax'].sudo().with_company(company).search([])

            # Filtering out the taxes by name and type
            customer_taxes_for_company = all_taxes_in_company.filtered(lambda tax: tax.name in self.taxes_id.mapped('name') and tax.type_tax_use == 'sale')
            supplier_taxes_for_company = all_taxes_in_company.filtered(lambda tax: tax.name in self.supplier_taxes_id.mapped('name') and tax.type_tax_use == 'purchase')

            # Synchronize taxes
            self.sudo().with_company(company).with_context(syncing_taxes=True).write({
                'taxes_id': [(4, tax.id) for tax in customer_taxes_for_company],
                'supplier_taxes_id': [(4, tax.id) for tax in supplier_taxes_for_company]
            })
