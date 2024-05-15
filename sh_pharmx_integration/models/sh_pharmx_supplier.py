# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api,_
import requests
import xmltodict
import json
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class PharmXSupplier(models.Model):

    _inherit = 'sh.pharmx.base'
    pharmx_import_supplier = fields.Boolean("Import Suppliers")
    auto_import_pharmx_supplier = fields.Boolean("Auto Import Suppliers")
    last_sync_pharmx_supplier = fields.Datetime("Last Sync Supplier",readonly="1")
    
    def import_pharmx_supplier(self):
        if self.pharmx_import_supplier:
            self.import_supplier()

    def import_supplier(self):
        company_id = self.env.company
        if company_id.pharmx_username and company_id.pharmx_password:
            headers = {                
                "Content-Type" : "text/xml; charset=utf-8",
                "Content-Length" : "length",
                "SOAPAction" : "http://www.pharmx.com.au/gateway3/gatewayinterfacemanagement/ListSuppliers",
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
                        <ListSuppliers xmlns="http://www.pharmx.com.au/gateway3/gatewayinterfacemanagement">
                        <userDetail>
                            <Username>{0}</Username>
                            <Password>{1}</Password>
                        </userDetail>
                        </ListSuppliers>
                    </soap:Body>
                    </soap:Envelope> """.format('%s','%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password))
            final_url = availbale_url + '/Gateway3/GatewayInterfaceManagement.asmx'           
            response = requests.post(url=final_url,data=payload,headers=headers)
            if response.status_code == 200:
                dict_data = xmltodict.parse(response.content)                
                if int(dict_data['soap:Envelope']['soap:Body']['ListSuppliersResponse']['ListSuppliersResult']['DocumentCount']) == 1:
                    data = dict_data['soap:Envelope']['soap:Body']['ListSuppliersResponse']['ListSuppliersResult']['Documents']['DocumentType']                    
                    self.handle_supplier_date(data)
                for data in dict_data['soap:Envelope']['soap:Body']['ListSuppliersResponse']['ListSuppliersResult']['Documents']['DocumentType']:                   
                    self.handle_supplier_date(data)
                self.generate_vals('success','supplier','Imported Successfully')
                self.last_sync_pharmx_supplier = datetime.now()                    
        else:               
            raise UserError(_("Please Configure your Credentials in Settings"))

    def handle_supplier_date(self,data):
        supplier_vals = {
            'name' : data['Description'] if data['Description'] else False,
            'company_type' : 'company',
            'supplier_rank' : 1,
        }
        if data['StockAvailabilityRequests'] == 'false':
            supplier_vals['stock_availability_requests'] = False
        elif data['StockAvailabilityRequests'] == 'true':
            supplier_vals['stock_availability_requests'] = True
        domain = [('pharmx_supplier_id', '=', data['SupplierId'])]
        already_supplier = self.env['res.partner'].search(domain)
        if already_supplier:
            already_supplier.write(supplier_vals)
        else:
            supplier_vals['pharmx_supplier_id'] = data['SupplierId']
            self.env['res.partner'].create(supplier_vals)
 