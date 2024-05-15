from odoo import fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Source Sale Order",
        readonly=True,
        copy=False,
    )

    # Create intercompany sales order based on conditions
    def button_confirm(self):
        res = super().button_confirm()
        for purchase_order in self.sudo():

            # Skip if sale_order_id is populated
            if not purchase_order.sale_order_id:

                # Find the company from partner then trigger intercompany actions
                dest_company = (
                    purchase_order.partner_id.commercial_partner_id.ref_company_ids
                )
                if dest_company and dest_company.so_from_po:
                    purchase_order.with_company(
                        dest_company.id
                    )._inter_company_create_sale_order(dest_company)
            return res

    def _check_intercompany_product(self, dest_company):
        dest_user = dest_company.intercompany_sale_user_id
        if dest_user:
            for purchase_line in self.order_line:
                if (
                    purchase_line.product_id.company_id
                    and purchase_line.product_id.company_id not in dest_user.company_ids
                ):
                    raise UserError(
                        _("You cannot create a sale order because the product %s(%s) is not intercompany")
                        % (purchase_line.product_id.name, purchase_line.product_id.id)
                    )

    # Create a sale order from the current purchase order
    def _inter_company_create_sale_order(self, dest_company):
        self.ensure_one()

        # Check intercompany user
        intercompany_user = dest_company.intercompany_sale_user_id
        if not intercompany_user:
            intercompany_user = self.env.user

        # Check intercompany product
        self._check_intercompany_product(dest_company)

        # Accessing selling partner with selling user, so data like property_account_position can be retrieved
        company_partner = self.company_id.partner_id
        
        # Create the sale order and generate lines from the purchase order lines
        sale_order_data = self._prepare_sale_order_data(
            self.name, company_partner, dest_company
        )
        sale_order = (
            self.env["sale.order"]
            .with_user(intercompany_user.id)
            .sudo()
            .create(sale_order_data)
        )
        for purchase_line in self.order_line:
            sale_line_data = self._prepare_sale_order_line_data(
                purchase_line, dest_company, sale_order
            )
            self.env["sale.order.line"].with_user(intercompany_user.id).sudo().create(
                sale_line_data
            )

        # Update reference field on purchase order
        if not self.partner_ref:
            self.partner_ref = sale_order.name

        # Validate sale order
        if dest_company.sale_auto_validation:
            sale_order.with_user(intercompany_user.id).sudo().action_confirm()

    # Generate sale order values from purchase order values
    def _prepare_sale_order_data(self, name, partner, dest_company):
        self.ensure_one()
        new_order = self.env["sale.order"].new(
            {
                "company_id": dest_company.id,
                "origin": name,
                "client_order_ref": name,
                "partner_id": partner.id,
                "date_order": self.date_order,
                "purchase_order_id": self.id,
            }
        )
        for onchange_method in new_order._onchange_methods["partner_id"]:
            onchange_method(new_order)
        new_order.user_id = False
        if self.notes:
            new_order.note = self.notes
        new_order.commitment_date = self.date_planned
        return new_order._convert_to_write(new_order._cache)
    
    # Generate sale order line values from purchase order line values
    def _prepare_sale_order_line_data(self, purchase_line, dest_company, sale_order):
        new_line = self.env["sale.order.line"].new(
            {
                "order_id": sale_order.id,
                "purchase_order_id": self.id,
                "product_id": purchase_line.product_id.id,
                "product_uom": purchase_line.product_uom.id,
                "product_uom_qty": purchase_line.product_qty,
                "discount": purchase_line.discount,
                "purchase_line_id": purchase_line.id,
                "display_type": purchase_line.display_type,
            }
        )
        for onchange_method in new_line._onchange_methods["product_id"]:
            onchange_method(new_line)
        new_line.update({"product_uom": purchase_line.product_uom.id})

        # Fetch standard_price for sale order lines
        standard_price = purchase_line.product_id.standard_price

        # Fetch customer_tax for sale order lines
        customer_taxes = purchase_line.product_id.taxes_id.filtered(
        lambda tax: tax.company_id == dest_company)

        if len(customer_taxes) == 1:
            customer_tax = customer_taxes[0]
            tax_amount = customer_tax.amount / 100
            # Calculate standard_price including customer_tax
            price_unit = standard_price + (standard_price * tax_amount)
        else:
            # No tax or multiple tax records found, use standard_price directly
            tax_amount = 0
            price_unit = standard_price

        # Calculate standard_price including customer_tax
        price_unit = standard_price + (standard_price * tax_amount)

        # Update price_unit for sale order lines
        new_line.update({"price_unit": price_unit})

        if new_line.display_type in ["line_section", "line_note"]:
            new_line.update({"name": purchase_line.name})
        return new_line._convert_to_write(new_line._cache)
    
    # Cancel sale order when the purchase order is cancelled
    # def button_cancel(self):
    #     sale_orders = (
    #         self.env["sale.order"]
    #         .sudo()
    #         .search([("purchase_order_id", "in", self.ids)])
    #     )
    #     for so in sale_orders:
    #         if so.state not in ["draft", "sent", "cancel"]:
    #             raise UserError(_("You cannot cancel an order in %s status.") % so.state)
    #     sale_orders.action_cancel()
    #     self.write({"partner_ref": False})
    #     return super().button_cancel()
    