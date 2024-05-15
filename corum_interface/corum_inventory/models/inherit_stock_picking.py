from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ref = fields.Char('Supplier Reference')
    # invoice_date = fields.Date('Invoice Date')
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')
    invoice_count = fields.Integer('Invoice Count', compute='_compute_invoice_count')
    bill_count = fields.Integer('Bill Count', compute='_compute_bill_count')

    # Make ref field mandatory for receipts
    # @api.constrains('ref', 'picking_type_code')
    # def _check_ref_required(self):
    #     for record in self:
    #         if record.picking_type_code != 'outgoing' and not record.ref:
    #             raise ValidationError(_("Supplier Reference is required."))
            
    # Make invoice_date field mandatory for receipts
    # @api.constrains('invoice_date', 'picking_type_code')
    # def _check_invoice_date_required(self):
    #     for record in self:
    #         if record.picking_type_code != 'outgoing' and not record.ref:
    #             raise ValidationError(_("Bill Date is required."))

    # Count related sale orders
    @api.depends('move_lines.sale_line_id.order_id')
    def _compute_sale_order_count(self):
        for record in self:
            sale_orders = record.move_lines.mapped('sale_line_id.order_id')
            record.sale_order_count = len(sale_orders)
    
    # Open related sale orders
    def action_view_sale_orders(self):
        self.ensure_one()
        sale_orders = self.move_lines.mapped('sale_line_id.order_id')
        action = self.env.ref('sale.action_orders').read()[0]
        if len(sale_orders) > 1:
            action['domain'] = [('id', 'in', sale_orders.ids)]
        elif sale_orders:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = sale_orders.id
        return action

    # Count related purchase orders
    @api.depends('move_lines.purchase_line_id.order_id')
    def _compute_purchase_order_count(self):
        for record in self:
            purchase_orders = record.move_lines.mapped('purchase_line_id.order_id')
            record.purchase_order_count = len(purchase_orders)

    # Open related purchase orders
    def action_view_purchase_orders(self):
        self.ensure_one()
        purchase_orders = self.move_lines.mapped('purchase_line_id.order_id')
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        if len(purchase_orders) > 1:
            action['domain'] = [('id', 'in', purchase_orders.ids)]
        elif purchase_orders:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = purchase_orders.id
        return action

    # Count related invoices
    @api.depends('sale_id.invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.sale_id.invoice_ids)
    
    # Open related invoices
    def action_invoices(self, documents=False):
        if not documents:
            documents = self.sale_id.invoice_ids

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        if len(documents) > 1:
            result['domain'] = [('id', 'in', documents.ids)]
        elif len(documents) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = documents.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    # Count related bills
    @api.depends('purchase_id.invoice_ids')
    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = len(rec.purchase_id.invoice_ids)

    # Open related bills
    def action_bills(self, documents=False):
        if not documents:
            documents = self.purchase_id.invoice_ids

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        if len(documents) > 1:
            result['domain'] = [('id', 'in', documents.ids)]
        elif len(documents) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = documents.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    
    
    # Method to create an invoice from the related sale order
    # def create_invoice_from_sales_order(self):
    #     for rec in self:
    #         if rec.sale_id:
    #             sale_order = rec.sale_id
    #             # Check there are no invoices already associated with the sale order
    #             if not sale_order.invoice_ids:
    #                 # Create the invoice using action_create_invoice method
    #                 sale_order._create_invoices()
    #                 invoice = sale_order.invoice_ids
    #                 # Confirm the invoice.
    #                 invoice.action_post()
    
    # Method to create a bill from the related purchase order
    # def create_bill_from_purchase_order(self):
    #     for rec in self:
    #         if rec.purchase_id:
    #             purchase_order = rec.purchase_id
    #             # Check there are no invoices already associated with the purchase order
    #             if not purchase_order.invoice_ids:
    #                 # Create the invoice using action_create_invoice method
    #                 purchase_order.action_create_invoice()
    #                 # Update the invoice with additional values
    #                 invoice = purchase_order.invoice_ids
    #                 invoice.write({
    #                     'ref': rec.ref,
    #                     'invoice_date': rec.invoice_date,
    #                 })
    #                 # Confirm the invoice
    #                 invoice.action_post()

    # Override the stock picking validation function to create a Bill if needed
    # def button_validate(self):
    #     res = super(StockPicking, self).button_validate()

    #     # Check if the stock picking has been successfully processed
    #     if self.state == 'done':
    #         self.create_invoice_from_sales_order()
    #         self.create_bill_from_purchase_order()
    #     return res