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
import logging
from itertools import chain

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class product_pricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
        """  extract brand and public categs and pass them in context. """
        self.ensure_one()

        brand_ids = []
        product_pos_category_ids = []

        for p in (item[0] for item in products_qty_partner):

            # brands
            if p.product_brand_id:
                brand_ids.append(p.product_brand_id.id)

            # pos categories
            if p.pos_categ_id:
                product_pos_category_ids.append(p.pos_categ_id.id)


        return super(product_pricelist, self.with_context(brand_ids=brand_ids,product_pos_category_ids=product_pos_category_ids)).\
            _compute_price_rule( products_qty_partner, date=date, uom_id=uom_id)

    def _compute_price_rule_get_items(self, products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids):
        """ filter returned items based on brands and pos categories. """
        self.ensure_one()
        items = super(product_pricelist, self)._compute_price_rule_get_items(products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids)
        if not items:
            return items

        brand_ids = self._context.get('brand_ids', [0]),
        product_pos_category_ids = self._context.get('product_pos_category_ids', [0]),
        self.env.cr.execute(
            """
            SELECT
                item.id
            FROM
                product_pricelist_item AS item
            LEFT JOIN product_category AS categ ON item.categ_id = categ.id
            WHERE
                item.id in %s
                AND (
                    ((brand_id IS NULL) OR (brand_id = any(%s)))
                    OR
                    ((item.pos_category_id IS NULL) OR (item.pos_category_id = any(%s)))
                )
            ORDER BY
                item.applied_on, item.min_quantity desc, categ.complete_name desc, item.id desc
            """,
            (tuple(items.ids), brand_ids, product_pos_category_ids))
        # NOTE: make sure to keep the same order defined in pricelist.item

        item_ids = [x[0] for x in self.env.cr.fetchall()]
        return self.env['product.pricelist.item'].browse(item_ids)
