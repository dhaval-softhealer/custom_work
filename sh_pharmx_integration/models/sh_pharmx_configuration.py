# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api,_

class ResCompany(models.Model):
    _inherit='res.company'
    
    pharmx_username = fields.Char("Username")
    pharmx_password = fields.Char("Password")
    test_enviroment = fields.Boolean("Test Enviroment")
    connection_success = fields.Boolean("Successfull Connection")
    failure_responsible_user = fields.Many2one("res.users","Responsible USer")


class PharmXConfiguarion(models.TransientModel):
    _inherit='res.config.settings'

    pharmx_username = fields.Char("Username",related='company_id.pharmx_username',readonly=False)
    pharmx_password = fields.Char("Password",related='company_id.pharmx_password',readonly=False)
    test_enviroment = fields.Boolean("Test Enviroment",related='company_id.test_enviroment',readonly=False)
    connection_success = fields.Boolean("Successful Connection",related='company_id.connection_success',readonly=False)
    failure_responsible_user = fields.Many2one("res.users","Responsible User For Failed Orders (PharmX)",related='company_id.failure_responsible_user',readonly=False)

    def check_configuration(self):
        check = self.env['pharmx.gateways'].list_all_gateways()
        if check:
            self.connection_success = True
            popup_view_id = self.env.ref('sh_pharmx_integration.sh_export_successful_view').id
            return {
                'name': _('Notification'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sh.popup.message',                
                'view_id': popup_view_id,
                'target': 'new',
            }
        else:
            self.connection_success = False
            popup_view_id = self.env.ref('sh_pharmx_integration.sh_export_failure_view').id
            return {
                'name': _('Notification'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sh.popup.message',                
                'view_id': popup_view_id,
                'target': 'new',
            }
    
    def list_gates(self):
        tree_view_id = self.env.ref('sh_pharmx_integration.sh_pharmx_gateways_tree').id        
        return {
            "type": "ir.actions.act_window",
            "name": "PharmX Gateways",
            "view_mode": "tree",
            "res_model": "pharmx.gateways",            
            "domain": [],
            "view_id" : tree_view_id
        }