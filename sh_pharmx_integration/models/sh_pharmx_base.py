# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields
from datetime import datetime

class PharmXBase(models.Model):
    _name = 'sh.pharmx.base'
    _description = "Base for storing all your information"
    
    name = fields.Char("Name",default="PharmX Configure")
    pharmx_logger_id = fields.One2many("sh.pharmx.log","sh_pharmx_id")

    def available_gateways(self,gateway_type):
        company_id = self.env.company
        domain = [('company_id', '=', company_id.id)]
        if gateway_type == 'test':
            domain.append(('gateway_type', '=', 'test'))
        elif gateway_type == 'live':
            domain.append(('gateway_type', '=', 'live'))        
        all_gates = self.env['pharmx.gateways'].search(domain,limit=1)
        all_gates = all_gates.sorted(key=lambda k: k.priority)
        final_url = ''             
        if all_gates:
            for gate in all_gates:
                if gate.available:
                    final_url = final_url + gate.url
        return final_url

    def generate_vals(self,state,type_,message):
        log_vals = {
                "name" : self.name,
                "sh_pharmx_id" : self.id,
                "state" : state,
                "type_" : type_,
                "error" : message,
                "datetime" : datetime.now()
            }
        self.env['sh.pharmx.log'].create(log_vals)

    def auto_pharmx_supplier_account(self):
        domain = [('id', '=', '1')]
        base_env = self.env['sh.pharmx.base'].search(domain)
        if base_env:
            if base_env.auto_import_pharmx_supplier:
                base_env.import_supplier()
            if base_env.auto_pharmx_supplier_account:
                base_env.import_account()