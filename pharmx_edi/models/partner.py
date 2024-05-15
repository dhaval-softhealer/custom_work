from odoo import models, fields

class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    pharmx_site_id = fields.Integer(string="Pharmx Site ID", required=False)
    pharmx_supplier_id = fields.Char(string='PharmX Supplier ID', required=False)
