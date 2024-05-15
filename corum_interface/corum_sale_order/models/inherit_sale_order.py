from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Prevent unit cost from changing when a pricelist is chosen
    def update_prices(self):
        self.ensure_one()
        for line in self._get_update_prices_lines():
            line.with_context(pricelist_change=True).product_uom_change()
            line.discount = 0
            line._onchange_discount()
        self.show_update_pricelist = False
        self.message_post(body=_("Product prices have been recomputed according to pricelist <b>%s<b> ", self.pricelist_id.display_name))

    # Validate stock picking and create invoice (deliver and invoice)
    def action_deliver_and_invoice(self):
        self.ensure_one()
        pickings = self.picking_ids.filtered(lambda p: p.state not in ['done', 'cancel'])
        for picking in pickings:
            picking.action_confirm()
            picking.action_assign()
            # picking.action_set_quantities_to_reservation()
            for move in picking.move_lines:
                move.quantity_done = move.product_uom_qty
            picking.button_validate()
            
        for order in self:
            if order.invoice_status == 'to invoice':
                order._create_invoices()
                invoice = order.invoice_ids
                invoice.action_post()
        return True

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Use cost price as the default for unit price
    @api.onchange('product_id', 'product_uom', 'product_uom_qty')
    def product_id_change(self):
        super_result = super(SaleOrderLine, self).product_id_change()
        if not self.env.context.get('pricelist_change'):
            if self.product_id:
                if self.product_id.taxes_id:
                    # Product has sales tax associated
                    taxes = self.product_id.taxes_id.filtered(lambda tax: tax.type_tax_use == 'sale')
                    if taxes:
                        # Calculate price inclusive of tax
                        self.price_unit = self.product_id.standard_price * (1 + taxes[0].amount / 100)
                    else:
                        # No sales tax found, set price to cost price
                        self.price_unit = self.product_id.standard_price
                else:
                    # No sales tax associated, set price to cost price
                    self.price_unit = self.product_id.standard_price
        return super_result

    # Use cost price as the default for unit price
    @api.onchange('product_uom')
    def product_uom_change(self):
        super_result = super(SaleOrderLine, self).product_uom_change()
        if not self.env.context.get('pricelist_change'):
            if self.product_id:
                if self.product_id.taxes_id:
                    # Product has sales tax associated
                    taxes = self.product_id.taxes_id.filtered(lambda tax: tax.type_tax_use == 'sale')
                    if taxes:
                        # Calculate price inclusive of tax
                        self.price_unit = self.product_id.standard_price * (1 + taxes[0].amount / 100)
                    else:
                        # No sales tax found, set price to cost price
                        self.price_unit = self.product_id.standard_price
                else:
                    # No sales tax associated, set price to cost price
                    self.price_unit = self.product_id.standard_price
        return super_result
