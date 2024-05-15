# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models,fields,api,_
import requests
import xmltodict
import json

class PharmxGates(models.Model):
    _name = 'pharmx.gateways'
    _description = 'Stores all the available Gateways'

    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.company)
    name = fields.Char("Name")
    url = fields.Char("URL")
    available = fields.Boolean("Availablity")
    priority = fields.Integer("Priority")
    gateway_id = fields.Integer("Gateway ID")
    gateway_type = fields.Selection([('test','Test'),('live','Live')])

    @api.model
    def list_all_gateways(self):
        if self.env.company.test_enviroment:
            gateway_url = "https://testservices.pharmx.com.au/Gateway3/GatewayInterfaceManagement.asmx"
            headers = {
                "Host" : "testservices.pharmx.com.au",
                "Content-Type" : "text/xml; charset=utf-8",
                "Content-Length" : "length",
                "SOAPAction" : "http://www.pharmx.com.au/gateway3/gatewayinterfacemanagement/ListGateways",
            }
        else:
            gateway_url = "https://services.pharmx.com.au/Gateway3/GatewayInterfaceManagement.asmx"
            headers = {
                "Host" : "services.pharmx.com.au",
                "Content-Type" : "text/xml; charset=utf-8",
                "Content-Length" : "length",
                "SOAPAction" : "http://www.pharmx.com.au/gateway3/gatewayinterfacemanagement/ListGateways",
            }
        payload = u"""<?xml version="1.0" encoding="utf-8"?>
                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <ListGateways xmlns="http://www.pharmx.com.au/gateway3/gatewayinterfacemanagement">
                    <userDetail>
                        <Username>{0}</Username>
                        <Password>{1}</Password>
                    </userDetail>
                    </ListGateways>
                </soap:Body>
                </soap:Envelope>""".format('%s','%s') %(self.escape(self.env.company.pharmx_username),self.escape(self.env.company.pharmx_password))
        response = requests.post(url=gateway_url,data=payload,headers=headers)
        if response.status_code == 200:
            dict_data = xmltodict.parse(response.content)                  
            if dict_data['soap:Envelope']['soap:Body']['ListGatewaysResponse']['ListGatewaysResult']['Message'] == 'There was a problem getting user specific Gateway list.':
                return False
            else:
                if int(dict_data['soap:Envelope']['soap:Body']['ListGatewaysResponse']['ListGatewaysResult']['DocumentCount']) == 1:
                    data = dict_data['soap:Envelope']['soap:Body']['ListGatewaysResponse']['ListGatewaysResult']['Documents']['DocumentType']                    
                    self.handle_data(data)
                for data in dict_data['soap:Envelope']['soap:Body']['ListGatewaysResponse']['ListGatewaysResult']['Documents']['DocumentType']:                   
                    self.handle_data(data)
                return True

    def escape(self,str):
        str = str.replace("&", "&amp;")
        str = str.replace("<", "&lt;")
        str = str.replace(">", "&gt;")
        str = str.replace("\"", "&quot;")
        str = str.replace("'", "&apos;")
        return str


    def handle_data(self,data):
        gate_vals = {
            'name' : data['Name'] if data['Name'] else False,
            'url' : data['Url'] if data['Url'] else False,
            'priority' : data['Priority'] if data['Priority'] else False,
            'available' : data['Available'] if data['Available'] else False,
            'company_id' : self.env.company.id
        }
        if self.env.company.test_enviroment:
            gate_vals['gateway_type'] = 'test'
        else:
            gate_vals['gateway_type'] = 'live'
        domain = [('gateway_id', '=', data['Id'])]
        already_gate = self.search(domain)
        if already_gate:
            already_gate.write(gate_vals)
        else:                
            gate_vals['gateway_id'] = data['Id']            
            self.create(gate_vals)