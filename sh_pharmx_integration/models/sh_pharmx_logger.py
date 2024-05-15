# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models

class PharmXLogger(models.Model):
    _name = 'sh.pharmx.log'
    _description = 'Helps you to maintain the activity done'
    _order = 'id desc'

    name = fields.Char("Name")
    error = fields.Char("Message")
    datetime = fields.Datetime("Date & Time")
    sh_pharmx_id = fields.Many2one('sh.pharmx.base')
    state = fields.Selection([('success','Success'),('error','Failed')])
    type_ = fields.Selection([('supplier','Suppliers'),('account','Accounts')])


class PurchaseOrderLogger(models.Model):
    _name = 'purchase.order.log'
    _description = 'Helps you to maintain the activity done'
    _order = 'id desc'

    name = fields.Char("Name")
    error = fields.Char("Message")
    datetime = fields.Datetime("Date & Time")
    purchase_order_id = fields.Many2one('purchase.order')
    sale_order_id = fields.Many2one('sale.order')
    state = fields.Selection([('success','Success'),('error','Failed')])
    type_ = fields.Selection([('order_compliance','Order Compliance'),('create_order','Create Order'),('order_ackn','Order Acknowledgement')])