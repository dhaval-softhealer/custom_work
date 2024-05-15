# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from collections import defaultdict


class ComputedLabel(models.TransientModel):
    _inherit = 'product.label.layout'

    pricelist_label_ids = fields.Many2many("sh.label.queue")
    company_id = fields.Many2one("res.company","Company",default=lambda self: self.env.company)
    pricelist_id = fields.Many2one("product.pricelist",required=True)
    label_type = fields.Selection([
        ('goods', 'Goods Label'),
        ('shelf', 'Shelf Label')
    ], default='goods', string="Type", required=True)
    goods_label_format = fields.Selection([
        ('zpl', 'ZPL Labels'),
        ('zplxprice', 'ZPL Labels with price')
    ], default='zpl', string="Goods Label Format")
    shelf_label_format = fields.Selection([
        ('dymo', 'Dymo'),
        ('2x7xprice', '2 x 7 with price'),
        ('4x7xprice', '4 x 7 with price'),
        ('4x12', '4 x 12'),
        ('4x12xprice', '4 x 12 with price')
    ], default='dymo', string="Shelf Label Format")

    @api.onchange('label_type', 'goods_label_format' ,'shelf_label_format')
    def on_label_format_change(self):
        self.print_format = self.goods_label_format if self.label_type == 'goods' else self.shelf_label_format

    def _prepare_report_data(self):
        parent_model = self.env.context.get("active_model")        
        if self.custom_quantity <= 0:
            raise UserError(_('You need to set a positive quantity.'))

        products = False
        active_model = ''
        if self.product_tmpl_ids:
            products = self.product_tmpl_ids.ids
            active_model = 'product.template'
        elif self.product_ids:
            products = self.product_ids.ids
            active_model = 'product.product'
        elif self.pricelist_label_ids:
            products = self.pricelist_label_ids.ids
            active_model = 'sh.label.queue'
        # else:
        #     products = self.env[parent_model].browse(self.env.context.get('active_ids'))
        #     active_model = 'sh.label.queue'
        if not products:
            raise UserError(_("Please Select Items to Print"))

        # Get layout grid
        if parent_model in ['sh.label.queue','product.pricelist'] :
            if self.print_format == 'dymo':
                xml_id = 'sh_pricelists_labels.report_product_pricelist_label_dymo'
            elif 'zpl' in self.print_format:
                xml_id = 'sh_pricelists_labels.label_pricelist_product'
            elif 'x' in self.print_format:
                xml_id = 'sh_pricelists_labels.report_product_pricelist_label'            
            else:
                xml_id = ''
            products = self.env[active_model].browse(products)
            if 'zpl' in self.print_format:
                data = {
                    'active_model' : active_model,
                    'layout_wizard' : self.id,
                    'price_included' : 'xprice' in self.print_format,
                    'quantity_by_product': {p.id: p.quantity for p in products},
                }
                if self.picking_quantity == 'picking' and self.move_line_ids:
                    qties = defaultdict(int)
                    custom_barcodes = defaultdict(list)
                    uom_unit = self.env.ref('uom.product_uom_categ_unit', raise_if_not_found=False)
                    for line in self.move_line_ids:
                        if line.product_uom_id.category_id == uom_unit:
                            if (line.lot_id or line.lot_name) and int(line.qty_done):
                                custom_barcodes[line.product_id.id].append((line.lot_id.name or line.lot_name, int(line.qty_done)))
                                continue
                            qties[line.product_id.id] += line.qty_done
                    # Pass only products with some quantity done to the report
                    data['quantity_by_product'] = {p.id: int(q) for p, q in qties.items() if q}
                    data['custom_barcodes'] = custom_barcodes
            else:    
                data = {
                    'active_model': active_model,
                    'quantity_by_product': {p.id: p.quantity for p in products},
                    'layout_wizard': self.id,
                    'price_included': 'xprice' in self.print_format,
                }
            for labels in products:
                labels.write({
                    'active' : False
                })
        else:
            if self.print_format == 'dymo':
                xml_id = 'product.report_product_template_label_dymo'
            elif 'zpl' in self.print_format:
                xml_id = 'stock.label_product_product'
            elif 'x' in self.print_format:
                xml_id = 'product.report_product_template_label'            
            else:
                xml_id = ''
        
            if 'zpl' in self.print_format:
                data = {
                    'active_model' : active_model,
                    'layout_wizard' : self.id,
                    'price_included' : 'xprice' in self.print_format,
                    'quantity_by_product': {p: self.custom_quantity for p in products},
                }
                if self.picking_quantity == 'picking' and self.move_line_ids:
                    qties = defaultdict(int)
                    custom_barcodes = defaultdict(list)
                    uom_unit = self.env.ref('uom.product_uom_categ_unit', raise_if_not_found=False)
                    for line in self.move_line_ids:
                        if line.product_uom_id.category_id == uom_unit:
                            if (line.lot_id or line.lot_name) and int(line.qty_done):
                                custom_barcodes[line.product_id.id].append((line.lot_id.name or line.lot_name, int(line.qty_done)))
                                continue
                            qties[line.product_id.id] += line.qty_done
                    # Pass only products with some quantity done to the report
                    data['quantity_by_product'] = {p: int(q) for p, q in qties.items() if q}
                    data['custom_barcodes'] = custom_barcodes
            else:    
                data = {
                    'active_model': active_model,
                    'quantity_by_product': {p: self.custom_quantity for p in products},
                    'layout_wizard': self.id,
                    'price_included': 'xprice' in self.print_format,
                }
        return xml_id, data

    def add_lables_queue(self):
        if self.product_ids:
            product_template_ids = self.product_ids.mapped('product_tmpl_id')
        elif self.product_tmpl_ids:
            product_template_ids = self.product_tmpl_ids
        pricelist_id = self.pricelist_id
        for product in product_template_ids:
            domain = [('pricelist_id', '=', pricelist_id.id),('product_tmpl_id', '=', product.id)]
            find_price = self.env['sh.computed.price'].search(domain,limit=1)
            actual_price = find_price.overridden_price if find_price.source == 'overridden' else find_price.computed_price
            if find_price:
                discount = ((product.list_price - actual_price)/product.list_price) * 100 if product.list_price else 0.0
                margin = ((actual_price - product.standard_price)/actual_price) * 100
                domain = [('pricelist_id', '=', self.pricelist_id.id),('product_tmpl_id', '=', product.id),('label_type', '=', self.label_type)]
                label_queue_item = self.env['sh.label.queue'].search(domain, order="quantity asc", limit=1)
                label_vals = {
                    'pricelist_id' : pricelist_id.id,
                    'label_type' : self.label_type,
                    'product_tmpl_id' : product.id,
                    'company_id' : pricelist_id.company_id.id,
                    'print_format' :  self.print_format,
                    'quantity' : self.custom_quantity,
                    'price' : actual_price,
                    'discount' : discount,
                    'margin' : margin,
                    'extra_content' : self.extra_html,
                    'active' : True
                }
                if label_queue_item:
                    label_queue_item.write(label_vals)
                else:
                    self.env['sh.label.queue'].create(label_vals)
