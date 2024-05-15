from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    invoice_date = fields.Date('Bill Date', required=False, store=True)
    date_order_formatted = fields.Date(string='Date', compute='_compute_date_order_formatted', store=False)

    # Change order_id display to only show purchase order name
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            result.append((record.id, name))
        return result
    
    def _compute_date_order_formatted(self):
        for order in self:
            order.date_order_formatted = order.date_order.date()
    
    # Update product_supplierinfo
    def update_supplier_info(self):
        for order in self:
            for line in order.order_line:
                supplier_infos = line.product_id.seller_ids.filtered(lambda s: s.name == order.partner_id)

                for supplier_info in supplier_infos:
                    update_vals = {
                        'product_code': line.sh_vendor_pro_code if line.sh_vendor_pro_code and line.sh_vendor_pro_code != supplier_info.product_code else supplier_info.product_code,
                        'delay': 1 if supplier_info.delay == 0 else supplier_info.delay,
                        'min_qty': 1 if supplier_info.min_qty == 0 else supplier_info.min_qty,
                    }
                    supplier_info.write(update_vals)

                closest_supplier_info = supplier_infos.filtered(lambda s: line.product_qty >= s.min_qty).sorted('min_qty', reverse=True)

                if closest_supplier_info:
                    closest_supplier_info = closest_supplier_info[0]
                    update_vals = {}
                    if line.price_unit_excl != closest_supplier_info.price_excl:
                        update_vals['price_excl'] = line.price_unit_excl
                    if line.price_unit_incl != closest_supplier_info.price:
                        update_vals['price'] = line.price_unit_incl
                    if update_vals:
                        closest_supplier_info.write(update_vals)

    # Validate stock_picking
    def validate_pickings(self):
        pickings = self.picking_ids.filtered(lambda p: p.state not in ['done', 'cancel'])
        for picking in pickings:
            picking.action_confirm()
            picking.action_assign()
            for move in picking.move_lines:
                move.quantity_done = move.product_uom_qty
            picking.button_validate()

    # Receive & Bill
    def action_receive_and_bill(self):

        self.update_supplier_info()
        self.validate_pickings()

        # Ensure partner_ref and invoice_date are populated
        self.ensure_one()
        if not self.partner_ref:
            raise UserError(_("Supplier Reference is required."))
        if not self.invoice_date:
            raise UserError(_("Bill Date is required."))

        # Update ref and invoice_date in account_move
        if self.invoice_count == 0:
            self.action_create_invoice()
            invoice = self.invoice_ids
            invoice.write({
                'ref': self.partner_ref,
                'invoice_date': self.invoice_date,
            })
            invoice.action_post()
        return True

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float(string='Discount (%)', digits='Discount', default=0, store=True, readonly=False)
    price_unit_excl = fields.Float(string='Unit Price', compute="compute_price_unit_excl", digits='Product Price', store=True, readonly=False)
    price_unit_incl = fields.Float(string='Unit Price (Incl. Tax)', digits='Product Price', store=True, readonly=False)

    price_unit_excl_color_type = fields.Selection(selection=[
            ('none', 'None'),
            ('less', 'Less'),
            ('greater', 'Greater'),
            ('equal', 'Equal'),
        ], string='Color Type',default = 'none',compute='_compute_price_unit_excl_color_type')
    
    price_unit_color_type = fields.Selection(selection=[
            ('none', 'None'),
            ('less', 'Less'),
            ('greater', 'Greater'),
            ('equal', 'Equal'),
        ], string='Unit Price Color Type ',default='none',compute='_compute_price_unit_color_type')

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if 'price_unit_incl' not in vals:
                vals['price_unit_incl'] = vals['price_unit']
                vals['discount'] = 0
        res=super(PurchaseOrderLine,self).create(vals_list)
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        result=super(PurchaseOrderLine,self).onchange_product_id()
        if self.price_unit >= 0:
            self.price_unit_incl = self.price_unit
            self.discount = 0

    @api.onchange('product_qty')
    def _onchange_quantity(self):
        result=super(PurchaseOrderLine,self)._onchange_quantity()
        for rec in self:
            rec.price_unit_incl = rec.price_unit
            rec.discount = rec.discount

    @api.onchange('price_unit_incl', 'discount')
    def _onchange_calculate_price_unit(self):
        for rec in self:
            if rec.price_unit_incl >= 0:
                price = rec.price_unit_incl * (1 - (rec.discount or 0) / 100)
                rec.price_unit = price

    @api.depends('taxes_id', 'price_unit_incl')
    def compute_price_unit_excl(self):
        if self:
            for data in self:
                price = data.price_unit_incl
                taxes = data.taxes_id.compute_all(
                                    price_unit = price,
                                    currency = data.currency_id,
                                    quantity = 1,
                                    product = data.product_id,
                                    partner = data.order_id.partner_id,
                                    handle_price_include = True
                                )
                data.price_unit_excl = taxes['total_excluded']
   
    @api.onchange('price_unit_excl')
    def _onchange_price_unit_excl(self):
        if self:
            for data in self:
                price = data.price_unit_excl
                data.taxes_id.price_include = False
                taxes = data.taxes_id.compute_all(
                            price_unit = price,
                            currency = data.currency_id,
                            quantity = 1,
                            product = data.product_id,
                            partner = data.order_id.partner_id,
                            handle_price_include = True
                        )
                data.taxes_id.price_include = True
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