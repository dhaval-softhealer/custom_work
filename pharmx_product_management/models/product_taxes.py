from odoo import api, fields, models, _
import ast

class ProductAttribute(models.Model):
    _name = 'product.tax'
    _description = "Product Taxes"

    product_template_id = fields.Many2one('product.template', 'Product', index=True)
    supplierinfo_id = fields.Many2one('product.supplierinfo', 'SuppleirInfo', index=True)
    
    type = fields.Selection([
        ('GST', 'Goods and Services Tax (GST)')
    ], required=True, index=True)
    
    value = fields.Selection([
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Free', 'Free')
    ], required=True, index=True)