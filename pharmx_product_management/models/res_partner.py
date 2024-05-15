from odoo import models, fields

class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    cached_partner = fields.Char(string='Cached Partner')
