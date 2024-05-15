# Copyright (C) Softhealer Technologies.

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    sh_change_or_remove_logo = fields.Boolean(string="Change or Remove Logo ?")

    sh_customer_display_logo = fields.Binary(
        string='Logo For Custom Display')
    
    sh_is_logo_replace_remove = fields.Selection([('replace_logo','Replace Logo'),('remove_logo','Remove Logo')],default="remove_logo",string="Is Logo Remove or Replace ?")
    
