from odoo import api, fields, models, _
import ast

class ProductAvailability(models.Model):
    _name = 'product.availability'
    _description = "Product Availability"

    supplierinfo_id = fields.Many2one('product.supplierinfo', 'SuppleirInfo', index=True)
    partner_id = fields.Many2one('res.partner', related="supplierinfo_id.name", string='Partner', store=True, index=True)
    state = fields.Selection([
        ('ACT', 'ACT'),
        ('NSW', 'NSW'),
        ('NT', 'NT'),
        ('QLD', 'QLD'),
        ('SA', 'SA'),
        ('VIC', 'VIC'),
        ('WA', 'WA'),
    ], required=False, index=True)
    warehouse_id = fields.Many2many(comodel_name='product.warehouse', string="Warehouse", domain="[('partner_id', '=?', partner_id)]", index=True)
    availability = fields.Selection([
        ('InStock', 'In stock'),
        ('BackOrder', 'Available for BackOrder'),
        ('PreOrder', 'Available for PreOrder'),
        ('OutOfStock', 'Out of stock'),
        ('NotAvailable', 'Not Available'),
        ('Discontinued', 'Discontinued'),
    ], required=True, index=True)

class ProductWarehouse(models.Model):
    _name = 'product.warehouse'
    _description = "Warehouse"
    _order = 'name asc'

    name = fields.Char('Name', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', index=True)
    availability_ids = fields.Many2many('product.availability', 'product_availability_warehouse_rel',  'warehouse_id', 'product_id', string='Availability')
