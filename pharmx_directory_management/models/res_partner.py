# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from datetime import datetime
from odoo import models, fields, api
from random import randint

class PharmXSupplierInherit(models.Model):
    _inherit = 'res.partner'

    pharmx_code = fields.Char('PharmX Code', readonly=True, default=None)
    pharmx_supplier_id = fields.Char("Pharmx Supplier ID")
    partner_services = fields.Many2many("res.partner.retailservices",string="Retail Services")
    identifier_ids = fields.One2many('res.partner.identifier', 'partner_id', 'Identifiers', index=True)

    trding_as = fields.Char("Trading As")
    asx = fields.Char("ASX")
    approval_number = fields.Char("Approval Number")
    pharmx_facebook = fields.Char("Facebook")
    pharmx_linkedin = fields.Char("Linkedin")
    pharmx_instagram = fields.Char("Instagram")
    pharmx_twitter = fields.Char("Twitter")
    pharmx_youtube = fields.Char("Youtube")
    sh_pharmx_type = fields.Many2many("pharmx.type",string="Type")

    store_manager = fields.Many2one("res.partner",domain=[('parent_id', '=', 'id')],string="Store Manager")
    timezone = fields.Selection([('awst','AWST'),('acwst','ACWST'),('aest','AEST'),('lhst','LHST')],string="Time Zone")
    floor_size = fields.Integer(string="Floor Size (SQM)")
    open_date = fields.Date("Open Date")
    close_date = fields.Date("Close Date")

    mon_open = fields.Float("Monday Open")
    mon_close = fields.Float("Monday Close")
    tue_open = fields.Float("Tuesday Open")
    tue_close = fields.Float("Tuesday Close")
    wed_open = fields.Float("Wednesday Open")
    wed_close = fields.Float("Wednesday Close")
    thu_open = fields.Float("Thursday Open")
    thu_close = fields.Float("Thursday Close")
    fri_open = fields.Float("Friday Open")
    fri_close = fields.Float("Friday Close")
    sat_open = fields.Float("Saturday Open")
    sat_close = fields.Float("Saturday Close")
    sun_open = fields.Float("Sunday Open")
    sun_close = fields.Float("Sunday Close")
    store_details_boolean = fields.Boolean("Store Details boolean")

    sh_parent_company = fields.Many2one('res.partner',string="Parent")
    level = fields.Selection([('state','State'),('area','Area'),('suburb','Suburb')],string="Level")
    level_value = fields.Char("Value")
    affiliate_company_line_ids = fields.One2many('affiliate.company','affiliate_company_id')
    proposed_changes_line_ids = fields.One2many('res.partner.proposed.changes','partner_id')

    _sql_constraints = [
        ('unique_pharmx_site_id', 'unique(pharmx_site_id)', "A partner already exists with this pharmx site id."),
        ('unique_pharmx_supplier_id', 'unique(pharmx_supplier_id)', "A partner already exists with this pharmx supplier id.")
    ]

    @api.onchange('sh_pharmx_type')
    def check_pharmx_type(self):
        self.store_details_boolean = False
        if self.sh_pharmx_type:
            for data in self.sh_pharmx_type:
                if data.name == 'Retail Store' or data.name == 'Supplier':
                    self.store_details_boolean = True

    @api.model
    def create(self,vals):
        res = super(PharmXSupplierInherit,self).create(vals)
        domain = [('name', '=', 'base_geolocalize')]
        find_module = self.env['ir.module.module'].sudo().search(domain)
        if find_module.state == 'installed':
            res.update_partner_geolocation(res)
        return res

    def write(self,vals):
        print("\n\n\n",vals)
        for rec in self:
            domain = [('name', '=', 'base_geolocalize')]
            find_module = self.env['ir.module.module'].sudo().search(domain)
            if find_module.state == 'installed':
                rec.update_partner_geolocation(rec)
        return super(PharmXSupplierInherit,self).write(vals)
        
    def get_partner_geolocation(self):
        active_ids = self.env['res.partner'].browse(self.env.context.get('active_ids'))
        domain = [('name', '=', 'base_geolocalize')]
        find_module = self.env['ir.module.module'].sudo().search(domain)        
        if find_module.state == 'installed':
            for data in active_ids:
                data.update_partner_geolocation(data)

    def update_partner_geolocation(self,partner):
        result = partner._geo_localize(
                partner.street, partner.zip, partner.city,
                partner.state_id.name, partner.country_id.name
            )
        if result:
            partner.write({
                'partner_latitude': result[0],
                'partner_longitude': result[1]
            })

    @api.model
    def default_get(self, fields):
        rec = super(PharmXSupplierInherit, self).default_get(fields)
        domain = [('code', '=', 'AU'),('name','=','Australia')]
        find_country = self.env['res.country'].search(domain)
        if find_country:
            rec['country_id'] = find_country.id
        return rec
    
    # on create method (PharmX Code)
    @api.model
    def create(self, vals):
        obj = super(PharmXSupplierInherit, self).create(vals)
        if not obj.pharmx_code:
            number = self.env['ir.sequence'].get('pharmx.code') or None
            obj.write({'pharmx_code': number})
        return obj
    
    # on button click event (PharmX Code)
    def submit_application(self):
        if not self.pharmx_code:
            sequence_id = self.env['ir.sequence'].search([('code', '=', 'pharmx.code')])
            sequence_pool = self.env['ir.sequence']
            pharmx_code = sequence_pool.sudo().get_id(sequence_id.id)
            self.write({'pharmx_code': pharmx_code})