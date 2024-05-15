from odoo import api, fields, models

class PosSession(models.Model):
    _inherit = 'pos.session'

    opening_balance = fields.Monetary(compute='_compute_balances', string='Opening Balance', store=False)
    closing_balance = fields.Monetary(compute='_compute_balances', string='Closing Balance', store=False)
    total_cost = fields.Monetary(compute='_compute_total_cost', string='Cost of Goods Sold', store=False)
    total_tax = fields.Monetary(compute='_compute_total_tax', string='Total Tax', store=False)
    total_margin = fields.Monetary(compute='_compute_total_margin', string='Total Margin', store=False)
    total_returns = fields.Monetary(compute='_compute_total_returns', string='Total Returns', store=False)
    total_sales_excl = fields.Monetary(compute='_compute_total_sales_excl', string='Total Sales Excl.', store=False)
    total_sales_incl = fields.Monetary(compute='_compute_total_sales_incl', string='Total Sales Incl.', store=False)
    total_rounding = fields.Monetary(compute='_compute_total_rounding', string='Total Rounding', store=False)
    margin_percent = fields.Float(compute='_compute_margin_percent', string='Margin %', store=False)
    margin_display = fields.Char(compute='_compute_margin_display', store=False)

    @api.depends('statement_ids', 'statement_ids.balance_start', 'statement_ids.balance_end_real', 'statement_ids.state')
    def _compute_balances(self):
        for session in self:
            posted_statements = session.statement_ids.filtered(lambda s: s.state == 'posted')
            if posted_statements:
                session.opening_balance = 0
                # session.opening_balance = sum(posted_statements.mapped('balance_start'))
                session.closing_balance = sum(posted_statements.mapped('balance_end_real'))
            else:
                session.opening_balance = False
                session.closing_balance = False

    @api.depends('order_ids', 'order_ids.lines', 'order_ids.lines.total_cost')
    def _compute_total_cost(self):
        for session in self:
            total_cost = 0.0
            for order in session.order_ids:
                total_cost += sum(order.lines.mapped('total_cost'))
            session.total_cost = total_cost

    @api.depends('order_ids', 'order_ids.lines', 'order_ids.lines.price_subtotal_incl', 'order_ids.lines.price_subtotal')
    def _compute_total_tax(self):
        for session in self:
            total_tax = 0.0
            for order in session.order_ids:
                total_tax += sum(line.price_subtotal_incl - line.price_subtotal for line in order.lines)
            session.total_tax = total_tax

    @api.depends('order_ids', 'order_ids.lines', 'order_ids.lines.price_subtotal', 'order_ids.lines.total_cost')
    def _compute_total_margin(self):
        for session in self:
            total_margin = 0.0
            for order in session.order_ids:
                total_margin += sum(line.price_subtotal - line.total_cost for line in order.lines)
            session.total_margin = total_margin

    @api.depends('order_ids', 'order_ids.lines', 'order_ids.lines.price_subtotal_incl', 'order_ids.lines.qty')
    def _compute_total_returns(self):
        for session in self:
            total_returns = 0.0
            for order in session.order_ids:
                total_returns += sum(line.price_subtotal_incl for line in order.lines if line.qty < 0)
            session.total_returns = total_returns

    @api.depends('order_ids', 'order_ids.lines', 'order_ids.lines.price_subtotal')
    def _compute_total_sales_excl(self):
        for session in self:
            total_sales_excl = 0.0
            for order in session.order_ids:
                total_sales_excl += sum(order.lines.mapped('price_subtotal'))
            session.total_sales_excl = total_sales_excl

    @api.depends('order_ids', 'order_ids.lines', 'order_ids.lines.price_subtotal_incl')
    def _compute_total_sales_incl(self):
        for session in self:
            total_sales_incl = 0.0
            for order in session.order_ids:
                total_sales_incl += sum(order.lines.mapped('price_subtotal_incl'))
            session.total_sales_incl = total_sales_incl

    @api.depends('order_ids.amount_paid', 'order_ids.amount_total')
    def _compute_total_rounding(self):
        for session in self:
            amount_paid = sum(session.order_ids.mapped('amount_paid'))
            amount_total = sum(session.order_ids.mapped('amount_total'))
            session.total_rounding = amount_paid - amount_total

    @api.depends('total_sales_incl', 'total_sales_excl', 'total_tax', 'total_cost')
    def _compute_margin_percent(self):
        for session in self:
            if session.total_sales_excl > 0 or session.total_sales_incl > 0:
                session.margin_percent = (session.total_sales_excl - session.total_cost) / (session.total_sales_excl) * 100
            else:
                session.margin_percent = 0

    @api.depends('total_margin', 'margin_percent')
    def _compute_margin_display(self):
        for session in self:
            formatted_margin = "$ {:,.2f}".format(session.total_margin)
            formatted_margin_percent = "{:.2f}%".format(session.margin_percent)
            session.margin_display = f"{formatted_margin} ({formatted_margin_percent})"