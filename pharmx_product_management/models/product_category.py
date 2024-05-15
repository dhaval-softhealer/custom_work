from odoo import models, fields

class ProductInherit(models.Model):
    _inherit = 'product.category'

    seller_id = fields.Many2one('res.partner', string="Seller Id", index=True)