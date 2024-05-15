from odoo import fields, models,api,_
import json

class AccountMove(models.Model):
    _inherit = 'account.move'

    ref = fields.Char(required=True)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')

    # Count related sale orders
    @api.depends('invoice_line_ids.sale_line_ids.order_id')
    def _compute_sale_order_count(self):
        for record in self:
            record.sale_order_count = len(record.invoice_line_ids.mapped('sale_line_ids.order_id'))

    # Open related sale orders
    def action_view_sale_orders(self):
        self.ensure_one()
        sale_orders = self.invoice_line_ids.mapped('sale_line_ids.order_id')
        action = self.env.ref('sale.action_orders').read()[0]
        if len(sale_orders) > 1:
            action['domain'] = [('id', 'in', sale_orders.ids)]
        elif sale_orders:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = sale_orders.id
        return action
    
    # Count related purchase orders
    @api.depends('invoice_line_ids.purchase_line_id.order_id')
    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.invoice_line_ids.mapped('purchase_line_id.order_id'))

    # Open related purchase orders
    def action_view_purchase_orders(self):
        self.ensure_one()
        purchase_orders = self.invoice_line_ids.mapped('purchase_line_id.order_id')
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        if len(purchase_orders) > 1:
            action['domain'] = [('id', 'in', purchase_orders.ids)]
        elif purchase_orders:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = purchase_orders.id
        return action
    
    # Update action_post button
    def action_post(self):
        result = super(AccountMove, self).action_post()

        for move in self:
            if move.pharmx_invoice_id:

                purchase_order = move.invoice_line_ids.mapped('purchase_line_id.order_id')
                for line in move.invoice_line_ids:
    
                    if line.purchase_line_id:
                        purchase_order_line = line.purchase_line_id
                        vals = {}

                        if line.sh_product_code != purchase_order_line.sh_vendor_pro_code:
                            vals['sh_vendor_pro_code'] = line.sh_product_code
                        if line.quantity != purchase_order_line.product_qty:
                            vals['product_qty'] = line.quantity
                        if line.price_unit_excl != purchase_order_line.price_unit_excl:
                            vals['price_unit_excl'] = line.price_unit_excl
                        if line.price_unit_incl != purchase_order_line.price_unit_incl:
                            vals['price_unit_incl'] = line.price_unit_incl
                        if line.price_unit != purchase_order_line.price_unit:
                            vals['price_unit'] = line.price_unit
                        if line.discount != purchase_order_line.discount:
                            vals['discount'] = line.discount

                        if vals:
                            purchase_order_line.write(vals)
                            purchase_order_line._compute_amount()
                            purchase_order._amount_all()

                purchase_order.action_receive_and_bill()

        return result

    @api.onchange('partner_id')
    def _onchange_partner_product_code(self):
        for rec in self:
            invoice_line_ids = rec.invoice_line_ids
            for line in invoice_line_ids:
                supplier_info = line.product_id.seller_ids.filtered(
                    lambda code: (
                        code.product_id == line.product_id
                        and code.name == line.partner_id
                    )
                )
                if supplier_info:
                    code = supplier_info[0].product_code or ''
                    line.sh_product_code = code
                else:
                    supplier_info = line.product_id.seller_ids.filtered(
                        lambda code: (code.name == line.partner_id))
                    if supplier_info:
                        code = supplier_info[0].product_code or ''
                        line.sh_product_code = code
                    else:
                        line.sh_product_code = ''

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_id = fields.Many2one(options="{'no_create': True, 'no_create_edit': True}")
    sh_product_code = fields.Char('Product Code', store=True, readonly=False)
    sh_price_bool = fields.Boolean('Price Bool', compute='_compute_unit_price')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0, store=True, readonly=False)
    price_tax = fields.Float('Tax Amount', compute="_compute_price_tax")
    price_unit_excl = fields.Float(string='Unit Price', compute="compute_price_unit_excl", digits='Product Price', store=True, readonly=False)
    price_unit_incl = fields.Float(string='Unit Price (Incl. Tax)', digits='Product Price', store=True, readonly=False)

    price_unit_excl_color_type = fields.Selection(selection=[
            ('none', 'None'),
            ('less', 'Less'),
            ('greater', 'Greater'),
            ('equal', 'Equal'),
        ], string='Base Unit Price Color Type ',default='none',compute='_compute_price_unit_excl_color_type')
    
    price_unit_color_type = fields.Selection(selection=[
            ('none', 'None'),
            ('less', 'Less'),
            ('greater', 'Greater'),
            ('equal', 'Equal'),
        ], string='Price Unit Color Type',default='none', compute='_compute_price_unit_color_type')

    @api.model
    def create(self, vals):
        vals['price_unit_incl'] = vals.get('price_unit', 0)
        return super(AccountMoveLine, self).create(vals)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(AccountMoveLine,self)._onchange_product_id()
        for rec in self:
            if rec.price_unit:
                rec.price_unit_incl = rec.price_unit

    @api.onchange('price_unit', 'price_unit_incl', 'discount')
    def _onchange_new_unit_price(self):
        for rec in self:
            if rec.price_unit_incl:
                price = rec.price_unit_incl * (1 - (rec.discount or 0) / 100)
                rec.price_unit = price

    @api.depends('price_unit', 'price_unit_incl', 'discount')
    def _compute_unit_price(self):
        for rec in self:
            if rec.price_unit_incl:
                price = rec.price_unit_incl * (1 - (rec.discount or 0) / 100)
                rec.with_context(check_move_validity=False).price_unit = price
                rec.move_id.with_context(check_move_validity=False)._recompute_dynamic_lines()
            rec.sh_price_bool=True

    @api.depends('quantity', 'price_unit', 'discount')
    def _compute_price_tax(self):
        if self:
            for data in self:
                data.price_tax = data.price_total - data.price_subtotal

    # Direct product code
    def get_supplier_info(self, invoice_line_ids):
        supplier_info = invoice_line_ids.product_id.seller_ids.filtered(
            lambda code: (
                code.product_id == invoice_line_ids.product_id
                and code.name == invoice_line_ids.partner_id
            )
        )
        if supplier_info:
            return supplier_info[0]
        else:
            supplier_info = invoice_line_ids.product_id.seller_ids.filtered(
                    lambda code: (
                        code.name == invoice_line_ids.partner_id
                )
            )
            if supplier_info:
                return  supplier_info[0]
        return False

    @api.onchange('partner_id', 'product_id')
    def _onchange_sh_product_code(self):
        for line in self:
            supplier_info = self.get_supplier_info(line)
            if supplier_info:
                line.sh_product_code = supplier_info.product_code
            else:
                line.sh_product_code = ''

    def write(self, vals):
        res = super(AccountMoveLine, self).write(vals)
        for rec in self:
            if rec.product_id != False and rec.sh_product_code == False:
                supplier_info = self.get_supplier_info(rec)
                if supplier_info:
                    rec.write({'sh_product_code': supplier_info.product_code or ''})
        return res

    @api.depends('tax_ids', 'price_unit_incl')
    def compute_price_unit_excl(self):
        if self:
            for data in self:
                price = data.price_unit_incl
                taxes = data.tax_ids.compute_all(
                                    price_unit = price,
                                    currency = data.currency_id,
                                    quantity = 1,
                                    product = data.product_id,
                                    partner = data.partner_id,
                                    handle_price_include = True
                                )
                data.price_unit_excl = taxes['total_excluded']

    @api.onchange('price_unit_excl')
    def _onchange_price_unit_excl(self):
        if self:
            for data in self:
                price = data.price_unit_excl
                data.tax_ids.price_include = False
                taxes = data.tax_ids.compute_all(
                            price_unit = price,
                            currency = data.currency_id,
                            quantity = 1,
                            product = data.product_id,
                            partner = data.partner_id,
                            handle_price_include = True
                        )
                data.tax_ids.price_include = True
                data.price_unit_incl = taxes['total_included']

    @api.depends('price_unit_excl')
    def _compute_price_unit_excl_color_type(self):
        for rec in self:
            if rec.product_id:
                if rec.price_unit_excl > rec.product_id.standard_price:
                    rec.price_unit_excl_color_type = 'greater'
                elif rec.price_unit_excl < rec.product_id.standard_price:
                    rec.price_unit_excl_color_type = 'less'
                elif rec.price_unit_excl == rec.product_id.standard_price:
                    rec.price_unit_excl_color_type = 'equal'
                else:
                    rec.price_unit_excl_color_type = 'none'
            else:
                rec.price_unit_excl_color_type = 'none'

    @api.depends('price_unit')
    def _compute_price_unit_color_type(self):
        for rec in self:
            if rec.product_id:
                if rec.price_unit > rec.product_id.standard_price:
                    rec.price_unit_color_type = 'greater'
                elif rec.price_unit < rec.product_id.standard_price:
                    rec.price_unit_color_type = 'less'
                elif rec.price_unit == rec.product_id.standard_price:
                    rec.price_unit_color_type = 'equal'
                else:
                    rec.price_unit_color_type = 'none'
            else:
                rec.price_unit_color_type = 'none'