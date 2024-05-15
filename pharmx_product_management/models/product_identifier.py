from odoo import api, fields, models, _
import ast

class ProductIdentifier(models.Model):
    _name = 'product.identifier'
    
    product_template_id = fields.Many2one('product.template', 'Product', index=True)
    supplierinfo_id = fields.Many2one('product.supplierinfo', 'SuppleirInfo', index=True)
     
    type = fields.Selection([
        ('UPI', 'Universal Product Identifier (UPI)'),
        ('UPC', 'Universal Product Code (UPC)'),
        ('HOID', 'Head Office ID (HOID)'),
        ('SKU', 'Stock Keeping Unit (SKU)'),
        ('GTIN', 'Global Trade Item Number (GTIN)'),
        ('CTPP', 'AMT Containered Trade Product Pack (CTPP)'),
    ], required=True, index=True)
    value = fields.Char(string="Value", index=True)
    sequence = fields.Integer(default=10,help="Gives the sequence order when resolving identifiers.")
    
    @api.model
    def _name_search(self,
                     name,
                     args=None,
                     operator='ilike',
                     limit=100,
                     name_get_uid=None):
        res = super(ProductIdentifier, self)._name_search(name=name,
                                                  args=args,
                                                  operator=operator,
                                                  limit=limit,
                                                  name_get_uid=name_get_uid)
        identifier_search = list(
            self._search([('value', '=', name)] + args,
                         limit=limit,
                         access_rights_uid=name_get_uid))
        if identifier_search:
            return res + identifier_search
        return res
