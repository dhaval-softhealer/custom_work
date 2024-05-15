# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api, _

class ComputedLabel(models.Model):
    _name = 'sh.label.queue'
    _description = 'queue To Print Lables'

    active = fields.Boolean("Active",default=True)
    product_tmpl_id  = fields.Many2one('product.template',string="Product")
    pricelist_id = fields.Many2one('product.pricelist',string="Pricelist", required=True)
    company_id = fields.Many2one('res.company',string="Company")
    label_type = fields.Selection([
        ('goods', 'Goods Label'),
        ('shelf', 'Shelf Label')
    ], string="Type", required=True)
    print_format = fields.Selection([
        ('dymo', 'Dymo'),
        ('2x7xprice', '2 x 7 with price'),
        ('4x7xprice', '4 x 7 with price'),
        ('4x12', '4 x 12'),
        ('4x12xprice', '4 x 12 with price'),
        ('zpl', 'ZPL Labels'),
        ('zplxprice', 'ZPL Labels with price')], string="Label Format", required=True)
    quantity = fields.Float(string="Quantity",default=1)
    cost_price = fields.Float("Cost",related="product_tmpl_id.standard_price")
    sales_price = fields.Float("Sales Price",related="product_tmpl_id.list_price")
    price = fields.Monetary("Actual Price", compute="calculate_price")
    discount = fields.Char("Discount %", compute="calculate_discount")
    margin = fields.Char("Margin",readonly="True", compute="calculate_margin")
    qty_on_hand = fields.Float("Stock On Hand",related="product_tmpl_id.qty_available")
    extra_content = fields.Char("Extra Content")
    sh_computed_price = fields.Many2one('sh.computed.price',string="Computed Price")
    currency_id = fields.Many2one('res.currency', 'Currency', related="pricelist_id.currency_id")

    @api.depends("pricelist_id","product_tmpl_id")
    def calculate_price(self):
        for record in self:
            if not record.pricelist_id or not record.product_tmpl_id:
                record.price = 0
            else:
                record.price = record.pricelist_id.get_product_price(record.product_tmpl_id, 0, self.env.user.partner_id)

    @api.depends("price","product_tmpl_id")
    def calculate_discount(self):
        for record in self:
            if record.product_tmpl_id.list_price == 0:
                record.discount = ""
            elif (record.product_tmpl_id.list_price <= record.price):
                record.discount = ""
            else:
                discount = "{:.2f}".format(((record.product_tmpl_id.list_price - record.price)/record.product_tmpl_id.list_price) * 100)
                record.discount = _("%s %%", discount)
    
    @api.depends("price","cost_price")
    def calculate_margin(self):
        for record in self:
            if record.price == 0:
                record.margin = ""
            else:
                markup_percentage = "{:.2f}".format(((record.price-record.cost_price)/record.price) * 100)
                record.margin = _("%s %%", markup_percentage)
    
    def action_open_label_layout(self):
        if self.env.context.get('active_ids'):
            label_queue_ids = self.env['sh.label.queue'].browse(self.env.context.get('active_ids'))
            label_vals = {
                'pricelist_label_ids' : self.env.context.get('active_ids'),
                'custom_quantity' : 1,
                'print_format' : label_queue_ids.mapped('print_format')[0],
                'pricelist_id' : label_queue_ids[0].pricelist_id.id
            }
            create_ref = self.env['product.label.layout'].create(label_vals)
            return create_ref.process()
