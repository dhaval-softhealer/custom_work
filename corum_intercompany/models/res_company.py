from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    # Product sharing
    company_share_product = fields.Boolean(
        "Share product to all companies",
        compute="_compute_share_product",
        compute_sudo=True,
    )

    # Sale Order > Purchase Order
    po_from_so = fields.Boolean(
        string="Create Purchase Orders when selling to this company",
        help="Generate a Purchase Order when a Sale Order with this company "
        "as customer is created.\n The intercompany user must at least be "
        "Purchase User.",
    )
    purchase_auto_validation = fields.Boolean(
        string="Purchase Orders Auto Validation",
        default=False,
        help="When a Purchase Order is created by a multi company rule for "
        "this company, it will automatically validate it.",
    )
    intercompany_purchase_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Intercompany Purchase User",
    )

    # Purchase Order > Sale Order
    so_from_po = fields.Boolean(
        string="Create Sale Orders when buying to this company",
        help="Generate a Sale Order when a Purchase Order with this company "
        "as supplier is created.\n The intercompany user must at least be "
        "Sale User.",
    )
    sale_auto_validation = fields.Boolean(
        string="Sale Orders Auto Validation",
        default=False,
        help="When a Sale Order is created by a multi company rule for "
        "this company, it will automatically validate it.",
    )
    intercompany_sale_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Intercompany Sale User",
    )

    # Invoice Validation
    invoice_auto_validation = fields.Boolean(
        help="When an invoice is created by a multi company rule "
        "for this company, it will automatically validate it",
        default=False,
    )
    intercompany_invoice_user_id = fields.Many2one(
        "res.users",
        string="Inter Company Invoice User",
        help="Responsible user for creation of invoices triggered by "
        "intercompany rules.",
    )

    def _compute_share_product(self):
        product_rule = self.env.ref("product.product_comp_rule")
        for company in self:
            company.company_share_product = not bool(product_rule.active)