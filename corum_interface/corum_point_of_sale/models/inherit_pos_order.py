from odoo import models, api, fields, _

class POSOrder(models.Model):
    _inherit = 'pos.order'
    
    cost = fields.Monetary(string=' Total Cost', compute='_compute_cost', store=True)
    margin = fields.Monetary(string="Margin", compute='_compute_margin', store=True)
    margin_percent = fields.Float(string="Margin (%)", compute='_compute_margin', store=True, digits=(12, 4), group_operator='avg')

    @api.depends('lines.total_cost')
    def _compute_cost(self):
        for order in self:
            cost = sum(line.total_cost for line in order.lines)
            order.cost = cost

class POSOrderLine(models.Model):
    _inherit = 'pos.order.line'

    tax = fields.Monetary(string='Tax', compute='_compute_tax', store=True)
    margin = fields.Monetary(string="Margin", compute='_compute_margin', store=True)
    margin_percent = fields.Float(string="Margin (%)", compute='_compute_margin', store=True, digits=(12, 4), group_operator='avg')

    @api.depends('price_subtotal_incl', 'price_subtotal')
    def _compute_tax(self):
        for line in self:
            line.tax = line.price_subtotal_incl - line.price_subtotal