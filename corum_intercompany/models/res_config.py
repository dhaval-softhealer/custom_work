from odoo import fields, models, api


class InterCompanyRulesConfig(models.TransientModel):

    _inherit = "res.config.settings"

    # Product sharing
    company_share_product = fields.Boolean(
        "Share product to all companies",
        help="Share your product to all companies defined in your instance.\n"
        " * Checked : Product are visible for every company, "
        "even if a company is defined on the partner.\n"
        " * Unchecked : Each company can see only its product "
        "(product where company is defined). Product not related to a "
        "company are visible for all companies.",
    )

    # Sale Order > Purchase Order
    po_from_so = fields.Boolean(
        related="company_id.po_from_so",
        string="Create Purchase Orders when selling to this company",
        help="Generate a Purchase Order when a Sale Order with this company "
        "as customer is created.\n The intercompany user must at least be "
        "Purchase User.",
        readonly=False,
    )
    purchase_auto_validation = fields.Boolean(
        related="company_id.purchase_auto_validation",
        string="Purchase Order Auto Confirm",
        help="When a Purchase Order is created by a multi company rule for "
        "this company, it will automatically validate.",
        readonly=False,
    )
    intercompany_purchase_user_id = fields.Many2one(
        comodel_name="res.users",
        related="company_id.intercompany_purchase_user_id",
        string="Purchase User",
        help="User used to create the purchase order arising from a sale "
        "order from another company.",
        readonly=False,
    )

    # Purchase Order > Sale Order
    so_from_po = fields.Boolean(
        related="company_id.so_from_po",
        string="Create Sale Orders when buying from this company",
        help="Generate a Sale Order when a Purchase Order with this company "
        "as supplier is created.\n The intercompany user must at least be "
        "Sale User.",
        readonly=False,
    )
    sale_auto_validation = fields.Boolean(
        related="company_id.sale_auto_validation",
        string="Sale Order Auto Confirm",
        help="When a Sale Order is created by a multi company rule for "
        "this company, it will automatically validate.",
        readonly=False,
    )
    intercompany_sale_user_id = fields.Many2one(
        comodel_name="res.users",
        related="company_id.intercompany_sale_user_id",
        string="Sale User",
        help="User used to create the sales order arising from a purchase "
        "order from another company.",
        readonly=False,
    )

    invoice_auto_validation = fields.Boolean(
        related="company_id.invoice_auto_validation",
        string="Invoices Auto Validation",
        readonly=False,
        help="When an invoice is created by a multi company rule for "
        "this company, it will automatically validate it.",
    )
    intercompany_invoice_user_id = fields.Many2one(
        related="company_id.intercompany_invoice_user_id",
        readonly=False,
        help="Responsible user for creation of invoices triggered by "
        "intercompany rules. If not set the user initiating the"
        "transaction will be used",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        product_rule = self.env.ref("product.product_comp_rule")
        res.update(
            company_share_product=not bool(product_rule.active),
        )
        return res

    def set_values(self):
        res = super().set_values()
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.write({"active": not bool(self.company_share_product)})
        return res