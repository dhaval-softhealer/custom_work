# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api,_
import requests
import xmltodict
import json
from datetime import datetime

# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api

class PharmxAccounts(models.Model):
    _name = 'pharmx.accounts'
    _description = 'Stores the account details'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    name = fields.Char("Account",required="1")
    partner_id = fields.Many2one("res.partner", string="Partner")

class PharmXAccounts(models.Model):

    _inherit = 'sh.pharmx.base'

    pharmx_import_account = fields.Boolean("Import Accounts")
    auto_import_pharmx_account = fields.Boolean("Auto Import Accounts")
    last_sync_pharmx_account = fields.Datetime("Last Sync Accounts",readonly="1")

    def import_pharmx_account(self):
        if self.pharmx_import_account:
            self.import_account()

    def escape(self,str):
        str = str.replace("&", "&amp;")
        str = str.replace("<", "&lt;")
        str = str.replace(">", "&gt;")
        str = str.replace("\"", "&quot;")
        str = str.replace("'", "&apos;")
        return str

    def import_account(self):       
       
        companies = self.env['res.company'].search([])
        for company_id in companies:
            if company_id.pharmx_username and company_id.pharmx_password:
                headers = {                
                    "Content-Type" : "text/xml; charset=utf-8",
                    "Content-Length" : "length",
                    "SOAPAction" : "http://www.pharmx.com.au/gateway3/gatewayinterfacemanagement/ListAccounts",
                }
                if company_id.test_enviroment:
                    availbale_url = self.available_gateways('test')
                    headers['Host'] = 'testservices.pharmx.com.au'
                else:
                    availbale_url = self.available_gateways('live')
                    headers['Host'] = 'services.pharmx.com.au'
                payload = u"""<?xml version="1.0" encoding="utf-8"?>
                    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                    <soap:Body>
                        <ListAccounts xmlns="http://www.pharmx.com.au/gateway3/gatewayinterfacemanagement">
                        <userDetail>
                            <Username>{0}</Username>
                            <Password>{1}</Password>       
                        </userDetail>
                        </ListAccounts>
                    </soap:Body>
                    </soap:Envelope>""".format('%s','%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password))
                final_url = availbale_url + '/Gateway3/GatewayInterfaceManagement.asmx'
                response = requests.post(url=final_url,data=payload,headers=headers)
                if response.status_code == 200:
                    dict_data = xmltodict.parse(response.content)
                    if int(dict_data['soap:Envelope']['soap:Body']['ListAccountsResponse']['ListAccountsResult']['DocumentCount']) != 0:
                        if int(dict_data['soap:Envelope']['soap:Body']['ListAccountsResponse']['ListAccountsResult']['DocumentCount']) == 1:
                            data = dict_data['soap:Envelope']['soap:Body']['ListAccountsResponse']['ListAccountsResult']['Documents']['DocumentType']
                            self.handle_account_data(data, company_id)
                        else:
                            for data in dict_data['soap:Envelope']['soap:Body']['ListAccountsResponse']['ListAccountsResult']['Documents']['DocumentType']:                   
                                self.handle_account_data(data, company_id)
                        self.generate_vals('success','account','Imported Successfully')
                        self.auto_import_pharmx_account = datetime.now()
                    else:
                        self.generate_vals('success','account','No Accounts Found')

    def handle_account_data(self,data, company):
        
        domain = [('pharmx_supplier_id', '=', data['SupplierId'])]
        find_supplier = self.env['res.partner'].search(domain)
        
        if not find_supplier:
            return
        
        domain = [('name', '=', data['DeliveryAccountNumber']), ('partner_id', '=', find_supplier.id), ('company_id', '=', company.id)]
        find_account = self.env['pharmx.accounts'].search(domain)
        
        if not find_account:
            account_vals = {
                'name':  data['DeliveryAccountNumber'],
                'company_id': company.id
            }
            
            find_supplier.write({
                "account_ids": [(0, 0, account_vals)]
            })
