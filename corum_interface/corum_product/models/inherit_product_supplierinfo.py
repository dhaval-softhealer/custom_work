from odoo import api, fields, models

class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    price_excl = fields.Float(string='Price', store=True)
    price = fields.Float(compute='_compute_price', required=True, store=True)
    company_id = fields.Many2one(default=False)
    min_qty = fields.Float(default=1)

    @api.depends('price_excl', 'product_tmpl_id.supplier_taxes_id')
    def _compute_price(self):
        for record in self:
            if record.product_tmpl_id.supplier_taxes_id:
                record.price = record.price_excl * 1.1
            else:
                record.price = record.price_excl