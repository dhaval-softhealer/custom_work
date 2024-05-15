# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api,_

class ComputedPrice(models.Model):
    _name = 'sh.computed.price'
    _description = 'Stores values based on price strategy'

    pricelist_id = fields.Many2one('product.pricelist',string="Pricelist", index=True)
    product_tmpl_id = fields.Many2one('product.template',string="Product Name", index=True)
    pos_categ_id = fields.Many2one('pos.category',string="Category",related="product_tmpl_id.pos_categ_id")
    product_brand_id = fields.Many2one('product.brand',string="Brand",related="product_tmpl_id.product_brand_id")
    min_quantity = fields.Float(string="Quantity")
    qty_available = fields.Float(string="On Hand", related="product_tmpl_id.qty_available")
    source = fields.Selection([('strategy','Strategy'),('overridden','Overridden')],default="strategy",string="Source", index=True)
    sales_price = fields.Float(string="Sales Price",related="product_tmpl_id.list_price")
    computed_price = fields.Float(string="Computed Price")
    overridden_price = fields.Float(string="Overridden Price")
    actual_price = fields.Float(string="Actual Price", compute="calculate_actual_price", store=True)
    cost_price = fields.Float(string="Cost",related="product_tmpl_id.standard_price")
    display = fields.Boolean("Display")
    markup_price = fields.Float(string="Markup", compute="calculate_markup")
    markup_percentage = fields.Char(string="Margin %", compute="calculate_markup_percentage")
    currency_id = fields.Many2one('res.currency', 'Currency', related="pricelist_id.currency_id")
    company_id = fields.Many2one("res.company", related="pricelist_id.company_id")

    @api.depends("computed_price","source","overridden_price")
    def calculate_actual_price(self):
        for record in self:
            if record.source == 'overridden':
                record.actual_price = record.overridden_price
            else:
                record.actual_price = record.computed_price

    @api.depends("actual_price", "cost_price", "product_tmpl_id.taxes_id", "product_tmpl_id.taxes_id.amount")
    def calculate_markup(self):
        for record in self:
            tax_amount = sum(record.actual_price / 110 * tax.amount for tax in record.product_tmpl_id.taxes_id)
            record.markup_price = record.actual_price - record.cost_price - tax_amount

    @api.depends("markup_price","actual_price")
    def calculate_markup_percentage(self):
        for record in self:
            if record.actual_price == 0:
                record.markup_percentage = ""
            else:
                markup_percentage = "{:.2f}".format((record.markup_price/record.actual_price) * 100)
                record.markup_percentage = _("%s %%", markup_percentage)

    @api.model
    def create(self, values): 
        result = super(ComputedPrice, self).create(values)
        self.print_labels()
        return result
        

    def write(self, vals):
        # Should be some kind of dictionary where actual prices are compared for multiple items.
        if len(self.ids) == 1:
            beginning = self.actual_price
            res = super(ComputedPrice, self).write(vals)
            if (beginning != self.actual_price):
                self.print_labels()
            return res
        else:
            return super(ComputedPrice, self).write(vals)

    def print_labels(self):
        #If 'Goods Label Format' and 'Shelf Label Format' fields are empty then don't add any labels to the label queue
        #If Stock on Hand for the product is <=0 then don't add the label to the label queue
        if self.product_tmpl_id.qty_available > 0:
            
            if self.pricelist_id.goods_label_format:
                domain = [('pricelist_id', '=', self.pricelist_id.id),('product_tmpl_id', '=', self.product_tmpl_id.id),('label_type', '=', 'goods'), ('active', '=', True)]
                goods_label = self.env['sh.label.queue'].search(domain)
                label_vals = {
                    'label_type' : 'goods',
                    'pricelist_id' : self.pricelist_id.id,
                    'product_tmpl_id' : self.product_tmpl_id.id,
                    'company_id' : self.pricelist_id.company_id.id,
                    'print_format' : self.pricelist_id.goods_label_format,
                    'quantity' : self.product_tmpl_id.qty_available,
                    'price' : self.actual_price,
                    'active' : True
                }
                if goods_label:
                    goods_label.write(label_vals)
                else:
                    self.env['sh.label.queue'].create(label_vals)

            if self.pricelist_id.shelf_label_format:
                domain = [('pricelist_id', '=', self.pricelist_id.id),('product_tmpl_id', '=', self.product_tmpl_id.id),('label_type', '=', 'shelf'), ('active', '=', True)]
                shelf_label = self.env['sh.label.queue'].search(domain)
                label_vals = {
                    'label_type' : 'shelf',
                    'pricelist_id' : self.pricelist_id.id,
                    'product_tmpl_id' : self.product_tmpl_id.id,
                    'company_id' : self.pricelist_id.company_id.id,
                    'print_format' : self.pricelist_id.shelf_label_format,
                    'quantity' : 1,
                    'price' : self.actual_price,
                    'active' : True
                }
                if shelf_label:
                    shelf_label.write(label_vals)
                else:
                    self.env['sh.label.queue'].create(label_vals)
