# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from datetime import datetime
from odoo import models,fields, api
from random import randint

class PharmxAffilateCompany(models.Model):
    _name = 'affiliate.company'

    affiliate_company_id = fields.Many2one('res.partner')
    relationship = fields.Char("Relationship")

class PharmxContactProposedChanges(models.Model):
    _name = 'res.partner.proposed.changes'

    partner_id = fields.Many2one("res.partner",string="Partner")
    source = fields.Char("Source")
    status = fields.Selection([('Pending','Pending'),('Approved','Approved'),('Rejected','Rejected')],default="Pending")
    create_date = fields.Date("Create Date")
    close_date = fields.Date("Close Date")
    field_name = fields.Char("Field name")
    field_value = fields.Char("Field Value")
    old_value = fields.Char("Old Value")

    @api.model
    def create(self,vals):
        res = super(PharmxContactProposedChanges,self).create(vals)
        if res.field_name:
            value = res.partner_id[res.field_name]
            if value:
                res.old_value = value
            else:                
                res.old_value = ''
        return res
    

    @api.onchange('status')
    def update_stage_process(self):
        if self.status == 'Approved' or self.status == 'Rejected':
            self.close_date = datetime.now().date()
        if self.status == 'Approved':                 
            self.partner_id._origin[self.field_name] = self.field_value
            self.old_value = self.partner_id._origin[self.field_name]
            
class PharmxBank(models.Model):
    _inherit = 'res.bank'

    bsb = fields.Char("BSB",required="1")

class PharmxBankAccount(models.Model):
    _inherit = 'res.partner.bank'

    pharmx_bank_types = fields.Many2many('pharmx.bank.type',string="Bank Type")
    bsb = fields.Char("BSB",related="bank_id.bsb",readonly=False)

class PharmxBankType(models.Model):
    _name = 'pharmx.bank.type'
    _description = "New Bank Types of PharmX"

    name = fields.Char("PharmX Bank Type")

class NewPharmxType(models.Model):
    _name= "pharmx.type"
    _description = "New Types of PharmX Types"

    name = fields.Char("PharmX Type")

class PharmxServices(models.Model):
    _name = 'res.partner.retailservices'

    name = fields.Char("Service")

class PharmXStateSupplier(models.Model):
    _name = 'pharmx.state.supplier'
    _description = 'Holds all the values of the State Supplier'

    name = fields.Char("State Supplier")
    supplier_id = fields.Many2one('res.partner')
    pharmx_state_supplier_id = fields.Char("State Supplier Id")
