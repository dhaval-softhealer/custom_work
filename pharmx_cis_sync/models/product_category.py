from odoo import models, fields

class ProductInherit(models.Model):
    _inherit = 'product.category'

    suppliermapping = fields.One2many('product.category.mappingrule', "category")

class ProductCategorySupplierMapping(models.Model):
    _name = 'product.category.mappingrule'
    
    sequence = fields.Integer(index=True, help="ranks suppliers for mapping", default=1)
    type = fields.Selection([('cis', 'CIS'), ('supplier', 'Supplier')], default="cis", required=True)
    category = fields.Many2one('product.category', 'Product Category')
    partner = fields.Many2one('res.partner', string="Partner")

    # Categories
    department = fields.Char(string="Department Mapping")
    subdepartment = fields.Char(string="SubDepartment Mapping")
    map_categories = fields.Boolean(string="Map Categories")
    pos_category = fields.Many2one('pos.category', 'Pos Category')

    # Other Mapping Options
    map_product_names = fields.Boolean(string="Map Product Names")
    map_product_codes = fields.Boolean(string="Map Product Codes") ## Not sure about this one.
    map_gst_status = fields.Boolean(string="Map GST Names")
    map_rrp = fields.Boolean(string="Map RRP")
    map_cost_price = fields.Boolean(string="Map Cost Price")

    # Currently greyed out because brand is at a product level and not a product supplier level.
    #map_product_brand = fields.Boolean(string="Map Product Brand")
    # Currently greyed out because there is no label name at a product supplier level.
    #map_product_labels = fields.Boolean(string="Map Product Labels")