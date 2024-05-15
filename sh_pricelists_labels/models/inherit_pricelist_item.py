# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models,tools ,fields, api, _
from odoo.tools.misc import formatLang
from odoo.exceptions import ValidationError

class InheritPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    def _compute_price(self, price, price_uom, product, quantity=1.0, partner=False):
        """Compute the unit price of a product in the context of a pricelist application.
           The unused parameters are there to make the full context available for overrides.
        """
        self.ensure_one()
        convert_to_price_uom = (lambda price: product.uom_id._compute_price(price, price_uom))

        # Lookup overridden prices
        ignoreOverrides = self._context.get('ignoreOverrides') == self.pricelist_id.id
        overriden_price = False
        if not ignoreOverrides:
            id = product.product_tmpl_id.id if type(product)._name == 'product.product' else product.id
            domain = [
                ('product_tmpl_id', '=', id),
                ('pricelist_id', '=', self.pricelist_id.id),
                ('source', '=', 'overridden'),
                ('min_quantity', '>=', quantity)
            ]
            overriden_price = self.env['sh.computed.price'].search(domain, order="min_quantity desc", limit=1)
        if (overriden_price):
            price = convert_to_price_uom(overriden_price.overridden_price)
        elif self.compute_price == 'fixed':
            price = convert_to_price_uom(self.fixed_price)
        elif self.compute_price == 'percentage':
            price = (price - (price * (self.percent_price / 100))) or 0.0
        else:
            # complete formula
            price_limit = price
            price = (price - (price * (self.price_discount / 100))) or 0.0
            if self.price_round:
                price = tools.float_round(price, precision_rounding=self.price_round)

            if self.price_surcharge:
                price_surcharge = convert_to_price_uom(self.price_surcharge)
                price += price_surcharge

            if self.price_min_margin:
                price_min_margin = convert_to_price_uom(self.price_min_margin)
                price = max(price, price_limit + price_min_margin)

            if self.price_max_margin:
                price_max_margin = convert_to_price_uom(self.price_max_margin)
                price = min(price, price_limit + price_max_margin)
        return price
