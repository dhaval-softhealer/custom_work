# Copyright (C) Softhealer Technologies.
from odoo import fields,models,api

class POSOrderLine(models.Model):
    _inherit = 'pos.order.line'
    
    secondary_qty = fields.Float("Secondary Qty")
    secondary_uom_id = fields.Many2one('uom.uom',string="Secondary UOM")

class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_seconadry = fields.Boolean(string="Enable Change UOM Feature")
    select_uom_type = fields.Selection([('primary', 'Primary'), ('secondary', 'Secondary')], string='Select Default UOM type', default='primary')
    display_uom_in_receipt = fields.Boolean(string='Display UOM in Receipt')
    enable_price_to_display = fields.Boolean(string='Display price in Secondary UOM ?')