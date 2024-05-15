# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api,_
import requests
import xmltodict
import json
from datetime import datetime

class PharmxFailedPO(models.Model):
    _name = 'failed.purchase.order.line'
    _description = 'Stores The Fail Product'

    name = fields.Char("Name")
    purchase_id = fields.Many2one("purchase.order","Purchase")
    product_id = fields.Many2one('product.product',"Product")
    quantity_ordered = fields.Float("Ordered Quantity",default=0.0)
    quantity_failed = fields.Float("Failed Quantity",default=0.0)
    quantity_final_ordered = fields.Float("Final Quanity Ordered",compute="_get_final_quantity")

    def _get_final_quantity(self):
        self.quantity_final_ordered = self.quantity_ordered - self.quantity_failed