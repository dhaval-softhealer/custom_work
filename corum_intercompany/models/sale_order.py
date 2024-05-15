from odoo import fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Source Purchase Order",
        readonly=True,
        copy=False,
    )

    # Create intercompany purchase order based on conditions
    def _action_confirm(self):
        res = super()._action_confirm()
        for sale_order in self.sudo():

            # Skip if sale_order_id is populated
            if not sale_order.purchase_order_id:

                # Find the company from partner then trigger intercompany actions
                dest_company = (
                    sale_order.partner_id.commercial_partner_id.ref_company_ids
                )
                if dest_company and dest_company.po_from_so:
                    sale_order.with_company(
                        dest_company.id
                    )._inter_company_create_purchase_order(dest_company)
            return res

    def _check_intercompany_product(self, dest_company):
        dest_user = dest_company.intercompany_purchase_user_id
        if dest_user:
            for sale_line in self.order_line:
                if (
                    sale_line.product_id.company_id
                    and sale_line.product_id.company_id not in dest_user.company_ids
                ):
                    raise UserError(
                        _("You cannot create a purchase order because the product %s(%s) is not intercompany")
                        % (sale_line.product_id.name, sale_line.product_id.id)
                    )
                
    # Create a purchase order from the current sale order
    def _inter_company_create_purchase_order(self, dest_company):
        self.ensure_one()

        # Check intercompany user
        intercompany_user = dest_company.intercompany_purchase_user_id
        if not intercompany_user:
            intercompany_user = self.env.user

        # Check intercompany product
        self._check_intercompany_product(dest_company)

        # Accessing purchasing partner with purchasing user, so data like property_account_position can be retrieved
        company_partner = self.company_id.partner_id
        
        # Create the purchase order and generate lines from the sale order lines
        purchase_order_data = self._prepare_purchase_order_data(
            self.name, company_partner, dest_company
        )
        purchase_order = (
            self.env["purchase.order"]
            .with_user(intercompany_user.id)
            .sudo()
            .create(purchase_order_data)
        )

        # Update reference field on sale order
        if not self.client_order_ref:
            self.client_order_ref = purchase_order.name

        # Update purchase_order_id field on the sale order
        if not self.purchase_order_id:
            self.purchase_order_id = purchase_order.id

        # Update purchase_line_id field on the sale order line
        for sale_line in self.order_line:
            purchase_line_data = self._prepare_purchase_order_line_data(
                sale_line, purchase_order
            )
            purchase_line = self.env["purchase.order.line"].with_user(intercompany_user.id).sudo().create(
                purchase_line_data
            )
            sale_line.write({
                'purchase_line_id': purchase_line.id,
                'purchase_order_id': purchase_order.id
            })
        sale_line.purchase_order_id = purchase_line.order_id
        sale_line.purchase_line_id = purchase_line.id

        # Validate purchase order
        if dest_company.purchase_auto_validation:
            purchase_order.with_user(intercompany_user.id).sudo().button_confirm()

    # Generate purchase order values from sales order values
    def _prepare_purchase_order_data(self, name, partner, dest_company):
        self.ensure_one()
        new_order = self.env["purchase.order"].new(
            {
                "company_id": dest_company.id,
                "origin": name,
                "partner_ref": name,
                "partner_id": partner.id,
                "date_order": self.date_order,
                "sale_order_id": self.id,
            }
        )
        for onchange_method in new_order._onchange_methods["partner_id"]:
            onchange_method(new_order)
        new_order.user_id = False
        if self.note:
            new_order.notes = self.note
        new_order.date_planned = self.commitment_date
        return new_order._convert_to_write(new_order._cache)

    # Generate purchase order line values from sale order line values
    def _prepare_purchase_order_line_data(self, sale_line, purchase_order):
        new_line = self.env["purchase.order.line"].new(
            {
                "order_id": purchase_order.id,
                "sale_order_id": self.id,
                "sale_line_id": sale_line.id,
                "product_id": sale_line.product_id.id,
                "display_type": sale_line.display_type,
            }
        )

        for onchange_method in new_line._onchange_methods["product_id"]:
            onchange_method(new_line)
            
        new_line.update({
            "product_uom": sale_line.product_uom.id,
            "product_uom_qty": sale_line.product_uom_qty,
            "product_qty": sale_line.product_uom_qty,
            "price_unit": sale_line.price_unit,
            "price_unit_incl": sale_line.price_unit,
            "price_subtotal": sale_line.price_subtotal,
            "price_tax": sale_line.price_tax,
            "price_total": sale_line.price_total,
        })

        if new_line.display_type in ["line_section", "line_note"]:
            new_line.update({"name": sale_line.name})
        return new_line._convert_to_write(new_line._cache)
    
    # Cancel purchase order when the sale order is cancelled
    # def action_cancel(self):
    #     purchase_orders = (
    #         self.env["purchase.order"]
    #         .sudo()
    #         .search([("sale_order_id", "in", self.ids)])
    #     )
    #     for po in purchase_orders:
    #         if po.state not in ["draft", "sent", "cancel", "to approve"]:
    #             raise UserError(_("You cannot cancel an order in %s status.") % po.state)
    #     purchase_orders.button_cancel()
    #     self.write({"partner_ref": False})
    #     return super().action_cancel()
    
    # Update unit price for purchase order lines with sales order lines
    # def action_confirm(self):
    #     for order in self.filtered("purchase_order_id"):
    #         for line in order.order_line.sudo():
    #             if line.purchase_line_id:
    #                 line.purchase_line_id.price_unit = line.price_subtotal
    #                 line.purchase_line_id.price_unit_incl = line.price_subtotal
    #     return super().action_confirm()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Source Purchase Order",
        readonly=True,
        copy=False,
    )

    purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Source Purchase Order Line",
        readonly=True,
        copy=False,
    )
