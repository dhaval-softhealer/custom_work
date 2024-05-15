# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#  OpenERP, Open Source Management Solution.                                 #
#                                                                            #
#  @author @author Daikhi Oualid <o_daikhi@esi.dz>                           #
#                                                                            #
#  This program is free software: you can redistribute it and/or modify      #
#  it under the terms of the GNU Affero General Public License as            #
#  published by the Free Software Foundation, either version 3 of the        #
#  License, or (at your option) any later version.                           #
#                                                                            #
#  This program is distributed in the hope that it will be useful,           #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              #
#  GNU Affero General Public License for more details.                       #
#                                                                            #
#  You should have received a copy of the GNU Affero General Public License  #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.      #
#                                                                            #
##############################################################################

from odoo import models, fields, api, _


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    brand_id = fields.Many2one(comodel_name="product.brand", string="Brand")
    pos_category_id = fields.Many2one(comodel_name="pos.category", string="Pos Category")
    
    applied_on = fields.Selection(selection_add=[
        ('22_product_brand', 'Product Brand'),
        ('23_product_pos_category', 'Pos Category')
    ],ondelete={'22_product_brand': 'cascade','23_product_pos_category': 'cascade'})

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        """ clean fields based on applied on. """
        if self.applied_on != '0_product_variant':
            self.product_id = False
        if self.applied_on != '1_product':
            self.product_tmpl_id = False
        if self.applied_on != '2_product_category':
            self.categ_id = False
        if self.applied_on != '22_product_brand':
            self.brand_id = False
        if self.applied_on != '23_product_pos_category':
            self.brand_id = False

    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price', 'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge', 'brand_id')
    def _get_pricelist_item_name_price(self):
        """ handle name of item for new selection items. """
        super(ProductPricelistItem, self)._get_pricelist_item_name_price()
        for item in self.filtered(lambda i: i.applied_on in ('22_product_brand')):
            if item.brand_id and item.applied_on == '22_product_brand':
                item.name = _("Brand: %s") % (item.brand_id.name)
        for item in self.filtered(lambda i: i.applied_on in ('23_product_pos_category')):
            if item.pos_category_id and item.applied_on == '23_product_pos_category':
                item.name = _("Pos Category: %s") % (item.pos_category_id.name)

    def _is_applicable_for(self, product, qty_in_product_uom):
        """ hanndle brand and public categories. """
        res = super(ProductPricelistItem, self)._is_applicable_for(product, qty_in_product_uom)

        # new: handle brands
        if self.brand_id:
            if product.product_brand_id != self.brand_id:
                res = False
        
        # new: handle brands
        if self.pos_category_id:
            categ = product.pos_categ_id
            while categ:
                if categ == self.pos_category_id:
                    return res
                categ = categ.parent_id
            res = False


        return res
