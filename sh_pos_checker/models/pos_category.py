# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.


from odoo import models, fields


class ShPosCategory(models.Model):
    _inherit = "pos.category"
    
    sh_age = fields.Integer(string='Age',)
    