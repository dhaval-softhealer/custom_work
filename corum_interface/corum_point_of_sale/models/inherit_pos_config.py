from odoo import models, api, fields, _

class POSConfig(models.Model):
    _inherit = 'pos.config'

    allow_quotation_order = fields.Boolean(string="Disable Quotation/Orders")