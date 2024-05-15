
# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api, _
import datetime
import pytz


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    computed_prices = fields.One2many('sh.computed.price',  'product_tmpl_id', string="Computed Prices")
