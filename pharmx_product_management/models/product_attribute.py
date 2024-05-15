from odoo import api, fields, models, _
import ast

class ProductAttribute(models.Model):
    _name = 'product.pharmx.attribute'
    _description = "PharmX Item and Product Attributes"

    product_template_id = fields.Many2one('product.template', 'Product', index=True)
    supplierinfo_id = fields.Many2one('product.supplierinfo', 'SuppleirInfo', index=True)
    
    type = fields.Selection([
        ('BrandName', 'Brand Name'),
        ('ManufacturerName', 'Manufacturer Name'),
        ('ScheduleCode', 'Schedule Code'),
    ], required=True, index=True)
    value = fields.Char(string="Value", index=True)
