# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api, _
import datetime
import pytz

from itertools import chain
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_datetime
from odoo.tools.misc import formatLang, get_lang


class InheritProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    compute_price_lines = fields.One2many('sh.computed.price','pricelist_id',string="Prices",domain=lambda self: [('display', '=', True)])
    compute_label_lines = fields.One2many('sh.label.queue', 'pricelist_id',string="Label")

    brand_filter = fields.Many2one('product.brand',string="Brand")
    manufacturer_filter = fields.Many2one('res.partner',string="Manufacturer")
    pos_category_filter = fields.Many2one('pos.category',string="Category")
    tag_filter = fields.Many2one('sh.product.tag',string="Tags")
    source_filter = fields.Selection([('strategy','Strategy'),('overridden','Overridden')],string="Source")
    modified_date_start = fields.Datetime(string="Modified Date Start")
    modified_date_end = fields.Datetime(string="Modified Date End")
    cron_id = fields.Many2one('ir.cron',string="Cron",readonly=True)
    goods_label_format = fields.Selection([
        ('zpl', 'ZPL Labels'),
        ('zplxprice', 'ZPL Labels with price')
    ], string="Goods Label Format")
    shelf_label_format = fields.Selection([
        ('dymo', 'Dymo'),
        ('2x7xprice', '2 x 7 with price'),
        ('4x7xprice', '4 x 7 with price'),
        ('4x12', '4 x 12'),
        ('4x12xprice', '4 x 12 with price')
    ], string="Shelf Label Format")
    
    def compute_prices(self):
        self.with_delay().generate_pricelist_price()

    def generate_pricelist_items_product_domain(self, item, additional_domain=[]):
        domain = additional_domain
        if item.applied_on == '22_product_brand':
            domain.append(('product_brand_id', '=', item.brand_id.id))
        elif item.applied_on == '23_product_pos_category':
            domain.append(('pos_categ_id', 'child_of', item.pos_category_id.id))
        elif item.applied_on == '2_product_category':
            domain.append(('categ_id', 'child_of', item.categ_id.id))
        elif item.applied_on == '1_product':
            domain.append(('id', '=', item.product_tmpl_id.id))
        elif item.applied_on == '0_product_variant':
            domain.append(('product_variant_ids', 'in', [item.product_id.id]))
        if self.company_id:
            domain.append(('|'))
            domain.append(('company_id', '=', self.company_id.id))
            domain.append(('company_id', '=', False))
        return domain

    def enumerate_product_quants(self, additional_domain = []):
        quant_product = []
        for item in self.item_ids:
            ## If the item is a pricelist lookup merge the domains.
            if (item.base_pricelist_id):
                for base_items in item.base_pricelist_id.item_ids:
                    domain = item.base_pricelist_id.generate_pricelist_items_product_domain(base_items, self.generate_pricelist_items_product_domain(item, []))
                    get_all_products = self.env['product.template'].search(domain)
                    quant_product.extend([ (item.min_quantity, id) for id in get_all_products if (item.min_quantity, id) not in quant_product  ])
            else:
                domain = self.generate_pricelist_items_product_domain(item, [])
                get_all_products = self.env['product.template'].search(domain)
                quant_product.extend([ (item.min_quantity, id) for id in get_all_products if (item.min_quantity, id) not in quant_product  ])
        return quant_product

    def generate_pricelist_price(self):
        processed = []
        quant_product = self.enumerate_product_quants()

        for product in quant_product:
            min_quantity = product[0]
            prod_tmpl = product[1]
            result = self.with_context(ignoreOverrides=self.id).get_product_price(prod_tmpl, min_quantity, self.company_id.partner_id)
            domain = [
                ('product_tmpl_id', '=', prod_tmpl.id),
                ('pricelist_id', '=', self.id),
                ('min_quantity', '=', min_quantity)
            ]
            already_created = self.env['sh.computed.price'].search(domain, limit=1)

            if already_created :
                if already_created.computed_price != result:
                    already_created.write({
                        'computed_price' : result,
                        'display' : True
                    })
            else:
                price_vals = {
                    'pricelist_id' : self.id,
                    'product_tmpl_id' : prod_tmpl.id,
                    'computed_price' : result,
                    'min_quantity' : min_quantity,
                    'display' : True
                }
                self.env['sh.computed.price'].create(price_vals)
            processed.append(prod_tmpl)
        self.cleanup_prices(processed)

    def cleanup_prices(self, products_to_retain):
        domain = [
            ('pricelist_id', '=', self.id),
            ('product_tmpl_id', 'not in', [ product.id for product in products_to_retain]),
            ('source', '!=', 'overridden')
        ]
        to_delete = self.env['sh.computed.price'].search(domain)
        to_delete.unlink()
        return

    def apply_price_filters(self):
        find_before = self.env['sh.computed.price'].search([])
        if find_before:
            find_before.write({
                'display' : False
            })
        domain = self.generate_domain()
        find_records = self.env['sh.computed.price'].search(domain)
        if find_records:
            find_records.write({
                'display' : True
            })


    def generate_domain(self):
        domain = [('pricelist_id', '=', self.id)]
        if self.brand_filter:
            domain.append(('product_brand_id', '=', self.brand_filter.id))
        if self.manufacturer_filter:
            domain.append(('product_tmpl_id.manufacturer', '=', self.manufacturer_filter.id))
        if self.pos_category_filter:
            domain.append(('pos_categ_id', '=', self.pos_category_filter.id))
        if self.tag_filter:
            domain.append(('product_tmpl_id.sh_product_tag_ids', 'in', self.tag_filter.ids))
        if self.source_filter:
            domain.append(('source', '=', self.source_filter))
        if self.modified_date_start:
            domain.append(('write_date', '>=', self.modified_date_start))
        if self.modified_date_end:
            domain.append(('write_date', '<=', self.modified_date_end))
        return domain

    @api.model
    def create(self,vals):
        res = super(InheritProductPricelist,self).create(vals)
        next_execution = datetime.datetime.today().date() +  datetime.timedelta(days=1)
        nextcall = datetime.datetime.combine(next_execution,datetime.time(2, 00))
        localtimezone = pytz.timezone('Australia/Sydney')
        localmoment = localtimezone.localize(nextcall, is_dst=None)
        utcmoment = localmoment.astimezone(pytz.utc)
        final_next_Call = utcmoment.strftime("%Y-%m-%d %H:%M:%S")
        cron = self.env['ir.cron'].sudo().create({
                'user_id': self.env.ref('base.user_root').id,
                'active': True,
                'interval_type': 'days',
                'interval_number': 1,
                'numbercall': -1,
                'doall': False,
                'name': "%s Computation Task" %(res.name),
                'model_id': self.env['ir.model']._get_id(res._name),
                'state': 'code',
                'nextcall' : final_next_Call
            })
        res.cron_id = cron.id
        cron.write({
            'code' : 'model.compute_price_cron(%s)' %(cron.id)
        })
        return res

    @api.model
    def compute_price_cron(self,cron_id):
        domain=[('cron_id', '=', cron_id)]
        find_pricelist = self.env['product.pricelist'].search(domain)
        if find_pricelist:
            find_pricelist.with_delay().generate_pricelist_price()


    def action_open_label_layout(self):
        product_label_ids = self.compute_label_lines.filtered(lambda x:x.print_label == True).ids
        self.compute_label_lines.write({
            'print_label' : False
        })
        action = self.env['ir.actions.act_window']._for_xml_id('product.action_open_label_layout')
        action['context'] = {'default_pricelist_label_ids': product_label_ids}
        return action

    def unlink(self):
        for rec in self:
            if rec.cron_id:
                rec.cron_id.unlink()
            if rec.compute_price_lines:
                rec.compute_price_lines.unlink()
        return super(InheritProductPricelist, self).unlink()
