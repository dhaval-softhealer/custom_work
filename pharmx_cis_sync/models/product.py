from odoo import models, fields

class ProductInherit(models.Model):
    _inherit = 'product.template'
    
    # Merged fields
    is_merged = fields.Boolean("Merged")
    merged_product_id = fields.Many2one('product.template', string="Merged Product Id", index=True)
    
    # Hidden CIS Fields
    cis_upi = fields.Char(string='CIS Universal Product Identifier', required=False)
    cis_department = fields.Char("CIS Department")
    cis_subdepartment = fields.Char("CIS Department")
    cis_description = fields.Char("CIS Description")
    cis_shelflabel = fields.Char("CIS Shelf Label")
    cis_gststatus = fields.Selection([('Yes','Yes'),('No','No'),('Free','Free')], string='CIS Suppliers GST Status')
    
    # # Seller Fields
    # seller_id = fields.Many2one('res.partner', string="Seller Id", index=True)
    # is_seller_product = fields.Boolean("Is Seller Product")
    # seller_product_ids = fields.One2many(
    #     string="Seller Products",
    #     comodel_name="product.template",
    #     inverse_name="global_product_tmpl_id",
    #     help=""
    # )
    # global_product_tmpl_id = fields.Many2one(
    #     string="Global Product",
    #     comodel_name="product.template",
    #     domain=[('is_seller_product', '=', False)],
    #     help="Related Global product.",
    # )
    # # Seller specific fields
    # min_order_qty = fields.Integer("Minimum Order Quantity")
    # order_multiple = fields.Integer("Order Multiple")
    # shelf_pack = fields.Integer("Shelf Pack")
    # items_per_box = fields.Integer("Items per box")
