from odoo import api, fields, models
from datetime import date


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'
    
    one_week = fields.Integer(string='1 Week', compute='_compute_populate_from_sql', help='Units sold in the last week.')
    two_weeks = fields.Integer(string='2 Weeks', compute='_compute_populate_from_sql', help='Units sold in the last two weeks.')
    three_weeks = fields.Integer(string='3 Weeks', compute='_compute_populate_from_sql', help='Units sold in the last three weeks.')
    one_month = fields.Integer(string='1 Month', compute='_compute_populate_from_sql', help='Units sold in the last month.')
    two_months = fields.Integer(string='2 Months', compute='_compute_populate_from_sql', help='Units sold in the last two months.')
    three_months = fields.Integer(string='3 Months', compute='_compute_populate_from_sql', help='Units sold in the three months.')
    on_order = fields.Float(string='On Order', compute='_compute_populate_from_sql', help='Units in draft/sent purchase orders.')
    product_brand_id = fields.Many2one('product.brand', related='product_id.product_brand_id', string='Brand', readonly=True)

    def _compute_populate_from_sql(self):
        company_id = self.env.company.id

        self.env.cr.execute("""
        SELECT
            product.id,
            on_order.product_uom_qty AS on_order,
            CASE WHEN one_week.qty = 0 THEN NULL ELSE one_week.qty END AS one_week,
            CASE WHEN two_weeks.qty = 0 THEN NULL ELSE two_weeks.qty END AS two_weeks,
            CASE WHEN three_weeks.qty = 0 THEN NULL ELSE three_weeks.qty END AS three_weeks,
            CASE WHEN one_month.qty = 0 THEN NULL ELSE one_month.qty END AS one_month,
			CASE WHEN two_months.qty = 0 THEN NULL ELSE two_months.qty END AS two_months,
			CASE WHEN three_months.qty = 0 THEN NULL ELSE three_months.qty END AS three_months
			
        FROM product_product AS product

        LEFT JOIN (
            SELECT product_id, SUM(product_uom_qty) AS product_uom_qty
            FROM purchase_order_line
            WHERE company_id = %(company_id)s AND state IN ('draft','sent','to approve')
            GROUP BY product_id
        ) AS on_order ON on_order.product_id = product.id

        LEFT JOIN (
            SELECT product_id, SUM(orders.qty) AS qty
            FROM (
                SELECT product_id, SUM(pos_order_line.qty) AS qty
                FROM pos_order_line
                INNER JOIN pos_order ON pos_order.id = pos_order_line.order_id
                AND CAST(pos_order.date_order AS DATE) <= NOW()
                AND CAST(pos_order.date_order AS DATE) >= CAST(NOW() - INTERVAL '1 week' AS DATE)
                AND pos_order.state IN ('paid','invoiced','done')
                WHERE pos_order.company_id = %(company_id)s
                GROUP BY product_id
            ) orders
            GROUP BY product_id
        ) AS one_week ON one_week.product_id = product.id

        LEFT JOIN (
            SELECT product_id, SUM(orders.qty) AS qty
            FROM (
                SELECT product_id, sum(pos_order_line.qty) as qty
                FROM pos_order_line
                INNER JOIN pos_order ON pos_order.id = pos_order_line.order_id
                AND CAST(pos_order.date_order AS DATE) <= NOW()
                AND CAST(pos_order.date_order AS DATE) >= CAST(NOW() - INTERVAL '2 week' AS DATE)
                AND pos_order.state IN ('paid','invoiced','done')
                WHERE pos_order.company_id = %(company_id)s
                GROUP BY product_id
            ) orders
            GROUP BY product_id
        ) AS two_weeks ON two_weeks.product_id = product.id

        LEFT JOIN (
            SELECT product_id, SUM(orders.qty) AS qty
            FROM (
                SELECT product_id, SUM(pos_order_line.qty) AS qty
                FROM pos_order_line
                INNER JOIN pos_order ON pos_order.id = pos_order_line.order_id
                AND CAST(pos_order.date_order AS DATE) <= NOW()
                AND CAST(pos_order.date_order AS DATE) >= CAST(NOW() - INTERVAL '3 week' AS DATE)
                AND pos_order.state IN ('paid','invoiced','done')
                WHERE pos_order.company_id = %(company_id)s
                GROUP BY product_id
            ) orders
            GROUP BY product_id
        ) AS three_weeks ON three_weeks.product_id = product.id

        LEFT JOIN (
            SELECT product_id, SUM(orders.qty) AS qty
            FROM (
                SELECT product_id, SUM(pos_order_line.qty) AS qty
                FROM pos_order_line
                INNER JOIN pos_order ON pos_order.id = pos_order_line.order_id
                AND CAST(pos_order.date_order AS DATE) <= NOW()
                AND CAST(pos_order.date_order AS DATE) >= CAST(NOW() - INTERVAL '1 month' AS DATE)
                AND pos_order.state IN ('paid','invoiced','done')
                WHERE pos_order.company_id = %(company_id)s
                GROUP BY product_id
            ) orders
            GROUP BY product_id
        ) AS one_month ON one_month.product_id = product.id
		
		LEFT JOIN (
            SELECT product_id, SUM(orders.qty) AS qty
            FROM (
                SELECT product_id, SUM(pos_order_line.qty) AS qty
                FROM pos_order_line
                INNER JOIN pos_order ON pos_order.id = pos_order_line.order_id
                AND CAST(pos_order.date_order AS DATE) <= NOW()
                AND CAST(pos_order.date_order AS DATE) >= CAST(NOW() - INTERVAL '2 month' AS DATE)
                AND pos_order.state IN ('paid','invoiced','done')
                WHERE pos_order.company_id = %(company_id)s
                GROUP BY product_id
            ) orders
            GROUP BY product_id
        ) AS two_months ON two_months.product_id = product.id
		
		LEFT JOIN (
            SELECT product_id, SUM(orders.qty) AS qty
            FROM (
                SELECT product_id, SUM(pos_order_line.qty) AS qty
                FROM pos_order_line
                INNER JOIN pos_order ON pos_order.id = pos_order_line.order_id
                AND CAST(pos_order.date_order AS DATE) <= NOW()
                AND CAST(pos_order.date_order AS DATE) >= CAST(NOW() - INTERVAL '3 month' AS DATE)
                AND pos_order.state IN ('paid','invoiced','done')
                WHERE pos_order.company_id = %(company_id)s
                GROUP BY product_id
            ) orders
            GROUP BY product_id
        ) AS three_months ON three_months.product_id = product.id

        WHERE product.id IN %(product_ids)s
        """, {
            'company_id': company_id,
            'product_ids': tuple(self.product_id.ids)
        })

        res = self.env.cr.dictfetchall()

        for list_rec in self:
            if list_rec.product_id:
                matched_result = [ result for result in res if list_rec.product_id.id == result['id']][0]
                list_rec.on_order = matched_result['on_order']
                list_rec.one_week = matched_result['one_week']
                list_rec.two_weeks = matched_result['two_weeks']
                list_rec.three_weeks = matched_result['three_weeks']
                list_rec.one_month = matched_result['one_month']
                list_rec.two_months = matched_result['two_months']
                list_rec.three_months = matched_result['three_months']
                list_rec.product_brand_id = list_rec.product_id.product_brand_id.id if list_rec.product_id.product_brand_id else False
            else:
                list_rec.product_brand_id = False
    
    # Automatically populate fields when a product is selected
    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(StockWarehouseOrderpoint,self)._onchange_product_id()
        buy_route = self.env['stock.location.route'].search([('name', '=', 'Buy')], limit=1)
        if self.product_id:
            self.route_id = buy_route.id if buy_route else False
            self.product_brand_id = self.product_id.product_brand_id.id if self.product_id.product_brand_id else False
        else:
            self.product_brand_id = False
            self.route_id = False
        return res