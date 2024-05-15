# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api

class PosConfig(models.Model):
    _inherit = "pos.config"

    sh_update_real_time_qty = fields.Boolean(
        string="Update Quantity Real Time")
    sh_invoice_ids = fields.Many2many('account.journal', string="Invoices")
    sh_update_quantity_cart_change = fields.Boolean(
        string="Update Quantity When POS Cart Change")

class StockQuantity(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def create(self, vals):
        res = super(StockQuantity, self).create(vals)
        if res.location_id.usage == 'internal':
            self.env['stock.update'].broadcast(res)
        return res

    def write(self, vals):
        record = self.filtered(lambda x: x.location_id.usage == 'internal')
        res = super(StockQuantity, self).write(vals)
        self.env['stock.update'].broadcast(record)
        return res

class PosStockChannel(models.TransientModel):
    _name = 'stock.update'

    def broadcast(self, stock_quant):
        data = stock_quant.read(['product_id', 'location_id', 'quantity'])
        if data and len(data) > 0:
            pos_session = self.env['pos.session'].search(
                [('state', 'in', ['opened', 'opening_control'])])
            if pos_session:
                for each_session in pos_session:
                    self.env['bus.bus']._sendmany(
                        [[(self._cr.dbname, 'stock.update', each_session.user_id.id), 'stock_update', data]])
