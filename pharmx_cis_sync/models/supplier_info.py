from odoo import models, fields

class ProductInherit(models.Model):
    _inherit = 'product.supplierinfo'

    # Seller specific fields
    min_order_qty = fields.Integer("Minimum Order Quantity")
    order_multiple = fields.Integer("Order Multiple")
    shelf_pack = fields.Integer("Shelf Pack")
    items_per_box = fields.Integer("Items per box")
    
    rrp = fields.Float('Suppliers Recommended Retail Price', digits='Product Price', required=False, default=0.0)
    gst_status = fields.Selection([('Yes','Yes'),('No','No'),('Free','Free')], string='Suppliers GST Status')
    department = fields.Char(string="Suppliers Department")
    subdepartment = fields.Char(string="Suppliers SubDepartment")
    
    # # Merged fields
    # is_merged = fields.Boolean("Merged")
    # merged_product_id = fields.Many2one('product.template', string="Merged Product Id", index=True)
    
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
