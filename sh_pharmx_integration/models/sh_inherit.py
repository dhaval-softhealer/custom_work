# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from datetime import datetime
from odoo import models,fields, api
from random import randint

class PharmXSupplierInherit(models.Model):
    _inherit = 'res.partner'

    pharmx_supplier_id = fields.Char("Pharmx Supplier ID")
    stock_availability_requests = fields.Boolean("Stock Availability Request?")
    account_ids = fields.One2many("pharmx.accounts", "partner_id", string="Account Ids")

class PharmXInvoice(models.Model):
    _inherit = 'account.move'
    
    pharmx_invoice_id = fields.Char('PharmX Invoice Id')
    
class PharmXAccountMoveLine (models.Model):
    _inherit = 'account.move.line'

    pharmx_invoice_line_id = fields.Char("Invoice Line Id")

class PharmxPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _default_unique_generation(self):
        the_number = ''
        num = self.generate_random_number(8)
        the_number = the_number+str(num)+'-'
        num = self.generate_random_number(4)
        the_number = the_number+str(num)+'-'
        num = self.generate_random_number(4)
        the_number = the_number+str(num)+'-'
        num = self.generate_random_number(4)
        the_number = the_number+str(num)+'-'
        num = self.generate_random_number(12)
        the_number = the_number+str(num)       
        return the_number

    unique_pos_line_number = fields.Char("Unique 32 digit Code",default=_default_unique_generation,readonly="1")

    def generate_random_number(self,n):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return randint(range_start, range_end)
