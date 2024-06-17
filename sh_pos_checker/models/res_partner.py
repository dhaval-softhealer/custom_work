# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api

class ShResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    Sh_birthdate = fields.Date(string='Birthdate')
    