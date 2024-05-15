# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields,models,api
from random import randint
import requests
import xmltodict
import json
from datetime import datetime
import dateutil
import pytz

class PharmXInvoiceFlow(models.Model):
    _inherit = 'account.move'

    def escape(self,str):
        str = str.replace("&", "&amp;")
        str = str.replace("<", "&lt;")
        str = str.replace(">", "&gt;")
        str = str.replace("\"", "&quot;")
        str = str.replace("'", "&apos;")
        return str

    def list_pharmx_invoice(self):
        # Method 3.6 ListNewInvoices
        
        companies = self.env['res.company'].search([])
        for company_id in companies:
            if company_id.pharmx_username and company_id.pharmx_password:
                self = self.with_company(company_id)
                domain = [('id', '=', '1')]        
                get_base = self.env['sh.pharmx.base'].search(domain)
                headers = {                
                    "Content-Type" : "text/xml; charset=utf-8",
                    "Content-Length" : "length",
                    "SOAPAction" : "http://www.pharmx.com.au/gateway3/invoicemanagement/ListNewInvoices",
                }
                if company_id.test_enviroment:
                    url = 'https://testservices.pharmx.com.au'
                    headers['Host'] = 'testservices.pharmx.com.au'
                else:
                    url = 'https://services.pharmx.com.au'
                    headers['Host'] = 'services.pharmx.com.au'
                payload = """<?xml version="1.0" encoding="utf-8"?>
                            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                            <soap:Body>
                                <ListNewInvoices xmlns="http://www.pharmx.com.au/gateway3/invoicemanagement">
                                <userDetail>
                                    <Username>{0}</Username>
                                    <Password>{1}</Password>
                                </userDetail>
                                </ListNewInvoices>
                            </soap:Body>
                            </soap:Envelope>""".format('%s', '%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password))
                            
                invoice_id_list = []
                final_url = url + '/Gateway3/InvoiceManagement.asmx'
                response = requests.post(url=final_url,data=payload,headers=headers)            
                if response.status_code == 200:
                    dict_data = xmltodict.parse(response.content)                
                    if dict_data['soap:Envelope']['soap:Body']['ListNewInvoicesResponse']['ListNewInvoicesResult']['Documents']:
                        doc_count = dict_data['soap:Envelope']['soap:Body']['ListNewInvoicesResponse']['ListNewInvoicesResult']['DocumentCount']
                        if int(doc_count) > 1:
                            for data in dict_data['soap:Envelope']['soap:Body']['ListNewInvoicesResponse']['ListNewInvoicesResult']['Documents']['DocumentType']:
                                invoice_id_list.append(data['Id'])
                        else:
                            data_id = dict_data['soap:Envelope']['soap:Body']['ListNewInvoicesResponse']['ListNewInvoicesResult']['Documents']['DocumentType']['Id']
                            invoice_id_list.append(data_id)

                # Method 3.7 GetInvoice
                if invoice_id_list:
                    success_invoice_list = []
                    for invoice in invoice_id_list:
                        headers = {                
                            "Content-Type" : "text/xml; charset=utf-8",
                            "Content-Length" : "length",
                            "SOAPAction" : "http://www.pharmx.com.au/gateway3/invoicemanagement/GetInvoice",
                        }
                        if company_id.test_enviroment:                            
                            headers['Host'] = 'testservices.pharmx.com.au'
                        else:
                            headers['Host'] = 'services.pharmx.com.au'
                        payload = """<?xml version="1.0" encoding="utf-8"?>
                                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                                <soap:Body>
                                    <GetInvoice xmlns="http://www.pharmx.com.au/gateway3/invoicemanagement">
                                    <userDetail>
                                        <Username>{0}</Username>
                                        <Password>{1}</Password>
                                    </userDetail>
                                    <invoiceId>{2}</invoiceId>
                                    </GetInvoice>
                                </soap:Body>
                                </soap:Envelope>""".format('%s', '%s','%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password),invoice)
                        get_invoice_url = url + '/Gateway3/InvoiceManagement.asmx'
                        response = requests.post(url=get_invoice_url,data=payload,headers=headers)                           
                        if response.status_code == 200:
                            dict_data = xmltodict.parse(response.content)                       
                            if dict_data['soap:Envelope']['soap:Body']['GetInvoiceResponse']['GetInvoiceResult']['Documents']:
                                data = dict_data['soap:Envelope']['soap:Body']['GetInvoiceResponse']['GetInvoiceResult']['Documents']['DocumentType']
                                find_po = self.env['purchase.order'].search([('company_id' ,'=', company_id.id),('pharmx_order_id', '=', data['OrderId'])])
                                find_supplier = self.env['res.partner'].search([('pharmx_supplier_id', '=', data['SupplierId']), ('company_id' ,'=', False)])
                                if not find_supplier:
                                    continue
                                invoice_dict = {
                                    'move_type' : 'in_invoice',
                                    'purchase_id' : find_po.id if find_po else False,
                                    'partner_id' : find_po.partner_id.id if find_po else find_supplier.id,
                                    'ref' : data['InvoiceNumber'] if data['InvoiceNumber'] else False,
                                }
                                if 'DueDate' in data:
                                    invoice_dict['invoice_date_due'] = dateutil.parser.isoparse(data['DueDate']).astimezone(pytz.timezone('Australia/Sydney')).date()
                                if 'Created' in data:
                                    invoice_dict['invoice_date'] = dateutil.parser.isoparse(data['Created']).astimezone(pytz.timezone('Australia/Sydney')).date()
                                line_count = int(data['LineCount'])
                                move_line_list = []
                                if line_count == 1:
                                    data['Lines']['GatewayInvoiceLine'] = [data['Lines']['GatewayInvoiceLine']]
                                if line_count >= 1:
                                    for lines in data['Lines']['GatewayInvoiceLine']:
                                        line_vals = {
                                            'purchase_order_id' : find_po.id,
                                            'quantity' : float(lines['QuantitySupplied']),
                                            'price_unit' : float(lines['ExtendedCostIncGst']) / float(lines['QuantitySupplied']) if float(lines['QuantitySupplied']) > 0 else float(lines['NormalCostIncGst']) or 0,
                                            'discount' : 0.00,
                                            'price_unit_excl': float(lines['ExtendedCostExGst']) / float(lines['QuantitySupplied']) if float(lines['QuantitySupplied']) > 0 else float(lines['NormalCostExGst']) or 0,
                                            'price_unit_incl': float(lines['ExtendedCostIncGst']) / float(lines['QuantitySupplied']) if float(lines['QuantitySupplied']) > 0 else float(lines['NormalCostIncGst']) or 0,
                                            'sh_product_code' : lines['ReorderNumber']
                                        }
                                        
                                        find_product = False

                                        # Match Lines using the Line UID, ReOrderNumberOrdered or ReOrderNumber
                                        if find_po:
                                            po_line = [x for x in find_po.order_line if x.unique_pos_line_number == lines['OrderLineUID']]
                                            
                                            if len(po_line) == 1:
                                                po_line = po_line[0].id

                                            if not po_line:
                                                po_line = [x for x in find_po.order_line if x.sh_vendor_pro_code == lines['ReorderNumberOrdered']]

                                            if not po_line:
                                                po_line = [x for x in find_po.order_line if x.sh_vendor_pro_code == lines['ReorderNumber']]

                                            if po_line:
                                                line_vals['purchase_line_id'] = po_line[0].id
                                                find_product = po_line[0].product_id

                                        
                                        # Find Product by Vendor Product Code
                                        if not find_product:
                                            supplier_info = self.env['product.supplierinfo'].search([('name', '=', find_supplier.id),('product_code', '=', lines['ReorderNumber'])])
                                            if supplier_info:
                                                find_product = supplier_info.product_id
                                        
                                        # Find Product by Primary Barcode
                                        if not find_product:
                                            find_product = self.env['product.template'].search([('barcode', '=', lines['Ean'])])
                                        
                                        # Find Product by Alternate Barcodes
                                        if not find_product:
                                            barcode = self.env['product.template.barcode'].search([('name', '=', lines['Ean'])])
                                            if barcode:
                                                find_product = barcode.product_id
                                        
                                        # Find Product by Description
                                        if not find_product:
                                            find_product = self.env['product.template'].search([('name', '=', lines['Description'])])
                                        
                                        if find_product:
                                            line_vals['product_id'] =  find_product.product_variant_id.id
                                        else:
                                            line_vals['name'] = lines['Description']

                                        if (lines['GstStatus'] == 'Y' or lines['GstStatus'] == 'N' or lines['GstStatus'] == 'U'):
                                            sales_tax = company_id.account_purchase_tax_id
                                            if sales_tax:
                                                line_vals['tax_ids'] = [sales_tax.id]
                                                
                                        ph_uom = lines['UOM']
                                        domain = [('name', '=', ph_uom)]
                                        find_uom = self.env['uom.uom'].search(domain)
                                        if find_uom:
                                            line_vals['product_uom_id'] = find_uom.id
                                        domain = [('pharmx_invoice_line_id', '=', lines['InvoiceLineUID'])]
                                        find_account_line = self.env['account.move.line'].search(domain)
                                        if find_account_line:
                                            find_account_line.write(line_vals)
                                        else:
                                            line_vals['pharmx_invoice_line_id'] = lines['InvoiceLineUID']
                                            move_line_list.append((0,0,line_vals))
                                    if move_line_list:
                                        invoice_dict['invoice_line_ids'] = move_line_list
                                    domain = [('company_id' ,'=', company_id.id),('pharmx_invoice_id', '=', data['Id'])]
                                    find_invoice = self.env['account.move'].search(domain)
                                    if find_invoice:
                                        find_invoice.write(invoice_dict)
                                    else:
                                        invoice_dict['pharmx_invoice_id'] = data['Id']
                                        created_invoice = self.env['account.move'].create(invoice_dict)                                    
                                        success_invoice_list.append(created_invoice.pharmx_invoice_id)
                                        if find_po:
                                            find_po.write({
                                                'invoice_ids' : created_invoice.ids
                                            })
                                            find_po.invoice_count = len(created_invoice.ids)
                                            find_po.partner_ref = data['InvoiceNumber']
                                            find_po.invoice_date = dateutil.parser.isoparse(data['Created']).astimezone(pytz.timezone('Australia/Sydney')).date()
                                            
                    # Method 3.8 MarkInvoiceAsReceived
                    if success_invoice_list:                   
                        headers = {                
                            "Content-Type" : "text/xml; charset=utf-8",
                            "Content-Length" : "length",
                            "SOAPAction" : "http://www.pharmx.com.au/gateway3/invoicemanagement/MarkInvoiceAsReceived",
                        }
                        if company_id.test_enviroment:                            
                            headers['Host'] = 'testservices.pharmx.com.au'
                        else:
                            headers['Host'] = 'services.pharmx.com.au'
                        invoice_received_url = url + '/Gateway3/InvoiceManagement.asmx'
                        for rec_inv in success_invoice_list:                    
                            payload = """<?xml version="1.0" encoding="utf-8"?>
                                    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                                    <soap:Body>
                                        <MarkInvoiceAsReceived xmlns="http://www.pharmx.com.au/gateway3/invoicemanagement">
                                        <userDetail>
                                            <Username>{0}</Username>
                                            <Password>{1}</Password>
                                        </userDetail>
                                        <invoiceId>{2}</invoiceId>
                                        </MarkInvoiceAsReceived>
                                    </soap:Body>
                                    </soap:Envelope>""".format('%s', '%s','%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password),rec_inv)
                            response = requests.post(url=invoice_received_url,data=payload,headers=headers)                           
                            if response.status_code == 200:
                                dict_data = xmltodict.parse(response.content)

    def list_pharmx_credit_note(self):
        # Method 3.9 ListNewCredits
        companies = self.env['res.company'].search([])
        for company_id in companies:
            if company_id.pharmx_username and company_id.pharmx_password:
                domain = [('id', '=', '1')]        
                get_base = self.env['sh.pharmx.base'].search(domain)
                headers = {                
                    "Content-Type" : "text/xml; charset=utf-8",
                    "Content-Length" : "length",
                    "SOAPAction" : "http://www.pharmx.com.au/gateway3/creditmanagement/ListNewCredits",
                }
                if company_id.test_enviroment:
                    url = 'https://testservices.pharmx.com.au'
                    headers['Host'] = 'testservices.pharmx.com.au'
                else:
                    url = 'https://services.pharmx.com.au'
                    headers['Host'] = 'services.pharmx.com.au'
                payload = """<?xml version="1.0" encoding="utf-8"?>
                        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                        <soap:Body>
                            <ListNewCredits xmlns="http://www.pharmx.com.au/gateway3/creditmanagement">
                            <userDetail>
                                <Username>{0}</Username>
                                <Password>{1}</Password>
                            </userDetail>
                            </ListNewCredits>
                        </soap:Body>
                        </soap:Envelope>""".format('%s', '%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password))

                credit_id_list = []
                list_Credit_url = url + '/Gateway3/CreditManagement.asmx'
                response = requests.post(url=list_Credit_url,data=payload,headers=headers)            
                if response.status_code == 200:
                    dict_data = xmltodict.parse(response.content)                
                    doc_count = dict_data['soap:Envelope']['soap:Body']['ListNewCreditsResponse']['ListNewCreditsResult']['DocumentCount']
                    if int(doc_count) > 1:
                        for data in dict_data['soap:Envelope']['soap:Body']['ListNewCreditsResponse']['ListNewCreditsResult']['Documents']['DocumentType']:
                            credit_id_list.append(data['Id'])
                    elif int(doc_count) == 1:
                        data_id = dict_data['soap:Envelope']['soap:Body']['ListNewCreditsResponse']['ListNewCreditsResult']['Documents']['DocumentType']['Id']
                        credit_id_list.append(data_id)
                
                # Method 3.10 GetCredit
                if credit_id_list:
                    success_credit_list = []
                    for credit in credit_id_list:
                        headers = {                
                            "Content-Type" : "text/xml; charset=utf-8",
                            "Content-Length" : "length",
                            "SOAPAction" : "http://www.pharmx.com.au/gateway3/creditmanagement/GetCredit",
                        }
                        if company_id.test_enviroment:                            
                            headers['Host'] = 'testservices.pharmx.com.au'
                        else:
                            headers['Host'] = 'services.pharmx.com.au'
                        payload = """<?xml version="1.0" encoding="utf-8"?>
                                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                                <soap:Body>
                                    <GetCredit xmlns="http://www.pharmx.com.au/gateway3/creditmanagement">
                                    <userDetail>
                                        <Username>{0}</Username>
                                        <Password>{1}</Password>
                                    </userDetail>
                                    <creditId>{2}</creditId>
                                    </GetCredit>
                                </soap:Body>
                                </soap:Envelope>""".format('%s', '%s','%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password),credit)
                        get_credit_url = url + 'Gateway3/CreditManagement.asmx'
                        response = requests.post(url=get_credit_url,data=payload,headers=headers)                           
                        if response.status_code == 200:
                            dict_data = xmltodict.parse(response.content)
                            print(json.dumps(dict_data,indent=4))
                            
                            # No credit Note To Code Ahead

                    # Method 3.11 MarkCreditAsReceived
                    if success_credit_list:                   
                        headers = {                
                            "Content-Type" : "text/xml; charset=utf-8",
                            "Content-Length" : "length",
                            "SOAPAction" : "http://www.pharmx.com.au/gateway3/creditmanagement/MarkCreditAsReceived",
                        }
                        if company_id.test_enviroment:
                            url = 'https://testservices.pharmx.com.au'
                            headers['Host'] = 'testservices.pharmx.com.au'
                        else:
                            url = 'https://services.pharmx.com.au'
                            headers['Host'] = 'services.pharmx.com.au'
                        credit_received_url = url + '/Gateway3/CreditManagement.asmx'
                        for rec_cre in success_credit_list:                    
                            payload = """<?xml version="1.0" encoding="utf-8"?>
                                    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                                    <soap:Body>
                                    <MarkCreditAsReceived xmlns="http://www.pharmx.com.au/gateway3/creditmanagement">
                                        <userDetail>
                                            <Username>{0}</Username>
                                            <Password>{1}</Password>
                                        </userDetail>
                                        <creditId>int</creditId>
                                        </MarkCreditAsReceived>
                                    </soap:Body>
                                    </soap:Envelope>""".format('%s', '%s','%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password),rec_cre)
                            response = requests.post(url=credit_received_url,data=payload,headers=headers)                           
                            if response.status_code == 200:
                                dict_data = xmltodict.parse(response.content)