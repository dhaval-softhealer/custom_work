# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields,models,api
from odoo.exceptions import UserError
from random import randint
import requests
import xmltodict
import json
from datetime import datetime
import xml.etree.ElementTree as ET
from datetime import date

class PharmxPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_unique_generation(self):
        the_number = ''
        num = self.generate_random_number(8)
        the_number = the_number+str(num)+'-'
        num = self.generate_random_number(4)
        the_number = the_number+str(num)+'-'
        num = self.generate_random_number(4)
        the_number = the_number+str(num)+'-'
        num = self.generate_random_number(4)
        the_number = the_number+str(num)+'-'
        num = self.generate_random_number(12)
        the_number = the_number+str(num)       
        return the_number

    unique_pos_number = fields.Char("Unique 32 digit Code",default=_default_unique_generation,readonly="1")
    purchase_logger_id = fields.One2many("purchase.order.log","purchase_order_id")
    pharmx_order_status = fields.Selection([('Queued','Queued'),('Sending','Sending'),('Dispatched','Dispatched'),('Sent','Sent'),('Cancelled', 'Cancelled'),('Retry','Retry'),('Error','Error')],string="PharmX Order Status")
    pharmx_order_id = fields.Char("PharmX Order Id")
    failed_po = fields.One2many("failed.purchase.order.line","purchase_id",string="Failed Lines")
    connection_success = fields.Boolean("Connection",related="company_id.connection_success")
    account_id = fields.Many2one("pharmx.accounts", "Account", domain="[('partner_id', '=?', partner_id),('company_id', '=?', company_id)]")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    
    pharmx_supplier_id = fields.Char(related='partner_id.pharmx_supplier_id')
    
    @api.onchange('partner_id', 'company_id')
    def _partner_changed(self):
        self.account_id = self.env["pharmx.accounts"].search([('partner_id', '=', self.partner_id.id),('company_id', '=', self.company_id.id)], limit= 1)
    
    def generate_purchase_logs(self,state,type_,message):       
        log_vals = {
                "name" : self.name,
                "purchase_order_id" : self.id,
                "state" : state,
                "type_" : type_,
                "error" : message,
                "datetime" : datetime.now()
            }
        self.env['purchase.order.log'].create(log_vals)

    def generate_random_number(self,n):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return randint(range_start, range_end)
    
    def send_by_pharmx(self):
        code = self.do_compliance_check()
        if code == str(0):
            if self.partner_id.stock_availability_requests:
                self.do_stock_availability()
            self.create_the_order()

    def escape(self,str):
        str = str.replace("&", "&amp;")
        str = str.replace("<", "&lt;")
        str = str.replace(">", "&gt;")
        str = str.replace("\"", "&quot;")
        str = str.replace("'", "&apos;")
        return str

    def do_compliance_check(self):        
        company_id = self.company_id
        if company_id.pharmx_username and company_id.pharmx_password:
            payload = self.prepare_main_payload().encode('utf-8')
            headers = {                
                "Content-Type" : "text/xml; charset=utf-8",
                "Content-Length" : str(len(payload)),
                "SOAPAction" : "http://www.pharmx.com.au/gateway3/ordermanagement/CheckOrderCompliance",
            }
            if company_id.test_enviroment:
                url = 'https://testservices.pharmx.com.au'
                headers['Host'] = 'testservices.pharmx.com.au'
            else:
                url = 'https://services.pharmx.com.au'
                headers['Host'] = 'services.pharmx.com.au'
                     
            code = ''
            if not code:
                final_url = url + '/Gateway3/Ordermanagement.asmx'
                response = requests.post(url=final_url,data=payload,headers=headers)
                dict_data = xmltodict.parse(response.content)                        
                if response.status_code == 200:
                    dict_data = xmltodict.parse(response.content)                           
                    code = dict_data['soap:Envelope']['soap:Body']['CheckOrderComplianceResponse']['CheckOrderComplianceResult']['ResultCode']
                    message = ''
                    message = dict_data['soap:Envelope']['soap:Body']['CheckOrderComplianceResponse']['CheckOrderComplianceResult']['Message']
                    succesful = dict_data['soap:Envelope']['soap:Body']['CheckOrderComplianceResponse']['CheckOrderComplianceResult']['Success'] == 'true'
                    if succesful:
                        if not message:
                            self.generate_purchase_logs("success","order_compliance","Successful")
                        else:
                            self.generate_purchase_logs("success","order_compliance",message)                            
                    else:
                        raise UserError(dict_data['soap:Envelope']['soap:Body']['CheckOrderComplianceResponse']['CheckOrderComplianceResult']['Message']) 
                if not code:
                    self.generate_purchase_logs("error","order_compliance","Failed at Order Compliance")
            return code

    def do_stock_availability(self):
        company_id = self.company_id
        if company_id.pharmx_username and company_id.pharmx_password:    
            payload = self.prepare_stock_avail_payload().encode('utf-8')
            headers = {                
                "Content-Type" : "text/xml; charset=utf-8",
                "Content-Length" : str(len(payload)),
                "SOAPAction" : "http://www.pharmx.com.au/gateway3/documentmanagement/GetStockAvailability",
            }
            if company_id.test_enviroment:
                url = 'https://testservices.pharmx.com.au'
                headers['Host'] = 'testservices.pharmx.com.au'
            else:
                url = 'https://services.pharmx.com.au'
                headers['Host'] = 'services.pharmx.com.au'
                            
            final_url = url + '/Gateway3/DocumentManagement.asmx'                   
            response = requests.post(url=final_url,data=payload,headers=headers)
            if response.status_code == 200:
                dict_data = xmltodict.parse(response.content)
                print(json.dumps(dict_data,indent=4))
                # No Stock available request to continue
    
    def create_the_order(self):
        company_id = self.company_id
        if company_id.pharmx_username and company_id.pharmx_password:      
            payload = self.prepare_order_payload().encode('utf-8')  
            headers = {                
                "Content-Type" : "text/xml; charset=utf-8",
                "Content-Length" : str(len(payload)),
                "SOAPAction" : "http://www.pharmx.com.au/gateway3/ordermanagement/CreateOrder",
            }
            if company_id.test_enviroment:
                url = 'https://testservices.pharmx.com.au'
                headers['Host'] = 'testservices.pharmx.com.au'
            else:
                url = 'https://services.pharmx.com.au'
                headers['Host'] = 'services.pharmx.com.au'
            
            final_url = url + '/Gateway3/OrderManagement.asmx'
            response = requests.post(url=final_url,data=payload,headers=headers)
            if response.status_code == 200:
                dict_data = xmltodict.parse(response.content)                        
                code = dict_data['soap:Envelope']['soap:Body']['CreateOrderResponse']['CreateOrderResult']['ResultCode']
                message = ''
                if int(code) == 0:                            
                    self.pharmx_order_id = dict_data['soap:Envelope']['soap:Body']['CreateOrderResponse']['CreateOrderResult']['Documents']['DocumentType']['Id']                       
                    #self.partner_ref = dict_data['soap:Envelope']['soap:Body']['CreateOrderResponse']['CreateOrderResult']['Documents']['DocumentType']['Reference']     
                    status = dict_data['soap:Envelope']['soap:Body']['CreateOrderResponse']['CreateOrderResult']['Documents']['DocumentType']['Status']
                    if status == 'Queued':
                        self.pharmx_order_status = 'Queued'
                    elif status == 'Cancelled':
                        self.pharmx_order_status = 'Cancelled'
                    elif status == 'Sent':
                        self.pharmx_order_status = 'Sent'
                    elif status == 'Dispatched':
                        self.pharmx_order_status = 'Dispatched'
                    if code == str(0):
                        if not message:
                            self.generate_purchase_logs("success","create_order","Successful Ordered")
                        else:
                            self.generate_purchase_logs("success","create_order",message)
                        self.state = 'sent'
                    elif code == str(99):
                        if not message:
                            self.generate_purchase_logs("error","create_order","Failed To Order")
                        else:
                            self.generate_purchase_logs("error","create_order",message)
                else:
                    message = dict_data['soap:Envelope']['soap:Body']['CreateOrderResponse']['CreateOrderResult']['Message']
                    if not message:
                        self.generate_purchase_logs("error","create_order","Failed TO Order")
                    else:
                        self.generate_purchase_logs("error","create_order",message)
                                
    def list_order_acknowledgement(self):
        # Method 3.3 ListNewOrderAcks
        domain = [('id', '=', '1')]        
        get_base = self.env['sh.pharmx.base'].search(domain)
        
        companies = self.env['res.company'].search([])
        for company_id in companies:
            if company_id.pharmx_username and company_id.pharmx_password:
                headers = {                
                    "Content-Type" : "text/xml; charset=utf-8",
                    "Content-Length" : "length",
                    "SOAPAction" : "http://www.pharmx.com.au/gateway3/ordermanagement/ListNewOrderAcks",
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
                            <ListNewOrderAcks xmlns="http://www.pharmx.com.au/gateway3/ordermanagement">
                            <userDetail>
                                <Username>{0}</Username>
                                <Password>{1}</Password>
                            </userDetail>
                            </ListNewOrderAcks>
                        </soap:Body>
                        </soap:Envelope>""".format('%s','%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password))
                order_id_list = []
                final_url = url + '/Gateway3/OrderManagement.asmx'
                response = requests.post(url=final_url,data=payload,headers=headers)                           
                if response.status_code == 200:
                    dict_data = xmltodict.parse(response.content)               
                    doc_count = dict_data['soap:Envelope']['soap:Body']['ListNewOrderAcksResponse']['ListNewOrderAcksResult']['DocumentCount']
                    if dict_data['soap:Envelope']['soap:Body']['ListNewOrderAcksResponse']['ListNewOrderAcksResult']['Documents']:
                        if int(doc_count) > 1:
                            for data in dict_data['soap:Envelope']['soap:Body']['ListNewOrderAcksResponse']['ListNewOrderAcksResult']['Documents']['DocumentType']:
                                order_id_list.append(data['Id'])
                        else:
                            data_id = dict_data['soap:Envelope']['soap:Body']['ListNewOrderAcksResponse']['ListNewOrderAcksResult']['Documents']['DocumentType']['Id']                        
                            order_id_list.append(data_id)
                
                # Method 3.4 GetOrderAck
                if order_id_list:
                    final_purchase_list = []
                    for orders in order_id_list:                    
                        headers = {                
                            "Content-Type" : "text/xml; charset=utf-8",
                            "Content-Length" : "length",
                            "SOAPAction" : "http://www.pharmx.com.au/gateway3/ordermanagement/GetOrderAck",
                        }
                        if company_id.test_enviroment:                            
                            headers['Host'] = 'testservices.pharmx.com.au'
                        else:
                            headers['Host'] = 'services.pharmx.com.au'
                        payload = """<?xml version="1.0" encoding="utf-8"?>
                                    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                                    <soap:Body>
                                        <GetOrderAck xmlns="http://www.pharmx.com.au/gateway3/ordermanagement">
                                            <userDetail>
                                                <Username>{0}</Username>
                                                <Password>{1}</Password>
                                            </userDetail>
                                            <orderId>{2}</orderId>
                                        </GetOrderAck>
                                    </soap:Body>
                                    </soap:Envelope>""".format('%s','%s','%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password),orders)
                        get_order = url + '/Gateway3/OrderManagement.asmx'
                        response = requests.post(url=get_order,data=payload,headers=headers)                           
                        if response.status_code == 200:
                            dict_data = xmltodict.parse(response.content)
                            if dict_data['soap:Envelope']['soap:Body']['GetOrderAckResponse']['GetOrderAckResult']['Documents']:
                                order_unfulfilled = []
                                ack_status = dict_data['soap:Envelope']['soap:Body']['GetOrderAckResponse']['GetOrderAckResult']['Documents']['DocumentType']['Status']
                                pharm_purchase_id = dict_data['soap:Envelope']['soap:Body']['GetOrderAckResponse']['GetOrderAckResult']['Documents']['DocumentType']['Id']
                                domain = [('pharmx_order_id', '=', pharm_purchase_id)]
                                find_po = self.env['purchase.order'].search(domain)
                                line_count = dict_data['soap:Envelope']['soap:Body']['GetOrderAckResponse']['GetOrderAckResult']['Documents']['DocumentType']['LineCount']
                                if int(line_count) > 1:
                                    data = dict_data['soap:Envelope']['soap:Body']['GetOrderAckResponse']['GetOrderAckResult']['Documents']['DocumentType']['Lines']['GatewayOrderAcknowledgmentLine']
                                    for line in data:
                                        if int(line['QuantityBackordered']) != 0 or int(line['QuantityOutOfStock']) != 0:
                                            order_unfulfilled.append(line['ReorderNumber'])
                                            self.create_unfulfilled_line(line,find_po)
                                            self.send_po_notification(find_po, 'Some items are unavailable at your supplier', 'Please review and arrange for either different stock, or a different supplier.')
                                            find_po.write({'state' : 'to approve'})
                                else:
                                    data = dict_data['soap:Envelope']['soap:Body']['GetOrderAckResponse']['GetOrderAckResult']['Documents']['DocumentType']['Lines']['GatewayOrderAcknowledgmentLine']
                                    if int(data['QuantityBackordered']) != 0 or int(data['QuantityOutOfStock']) != 0:
                                        order_unfulfilled.append(data['ReorderNumber'])
                                        self.create_unfulfilled_line(data,find_po)
                                        self.send_po_notification(find_po, 'Some items are unavailable at your supplier', 'Please review and arrange for either different stock, or a different supplier.')
                                        find_po.write({'state' : 'to approve'})

                                if ack_status in ("Error", "Cancelled", "Retry" ):
                                    self.send_po_notification(find_po, 'There was an error submitting your order.', 'Please review the pharmx logs, try again, contact your pos vendor or send via email.')
                                    
                                elif not order_unfulfilled:                                
                                    if find_po:
                                        find_po.write({
                                            'pharmx_order_status' : ack_status
                                        })
                                        find_po.button_confirm()

                                # Notifications here
                                

                                final_purchase_list.append(pharm_purchase_id)

                # Method 3.5 (MarkOrderAckAsReceived)
                    if final_purchase_list:                   
                        headers = {
                            "Content-Type" : "text/xml; charset=utf-8",
                            "Content-Length" : "length",
                            "SOAPAction" : "http://www.pharmx.com.au/gateway3/ordermanagement/MarkOrderAckAsReceived",
                        }
                        if company_id.test_enviroment:                            
                            headers['Host'] = 'testservices.pharmx.com.au'
                        else:
                            headers['Host'] = 'services.pharmx.com.au'
                        order_ack = url + '/Gateway3/OrderManagement.asmx'
                        for pur in final_purchase_list:
                            payload = """<?xml version="1.0" encoding="utf-8"?>
                                    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                                    <soap:Body>
                                        <MarkOrderAckAsReceived xmlns="http://www.pharmx.com.au/gateway3/ordermanagement">
                                        <userDetail>
                                            <Username>{0}</Username>
                                            <Password>{1}</Password>
                                        </userDetail>
                                        <orderId>{2}</orderId>
                                        </MarkOrderAckAsReceived>
                                    </soap:Body>
                                    </soap:Envelope>""".format('%s','%s','%s') %(self.escape(company_id.pharmx_username),self.escape(company_id.pharmx_password),pur)                        
                            response = requests.post(url=order_ack,data=payload,headers=headers)
                            if response.status_code == 200:
                                dict_data = xmltodict.parse(response.content)                            
                                ack_status = dict_data['soap:Envelope']['soap:Body']['MarkOrderAckAsReceivedResponse']['MarkOrderAckAsReceivedResult']['Message']                           
                                find_po.generate_purchase_logs("success","order_ackn",ack_status)

    def send_po_notification(self, po, summary, note):
        
        todos = {
            'res_id': po.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'purchase.order')]).id,
            'user_id': po.user_id.id,
            'summary': summary,
            'note': note,
            'activity_type_id': 4,
            'date_deadline': date.today()
        }

        self.env['mail.activity'].create(todos)
    
    def create_unfulfilled_line(self,line,find_po):
        # product Id will be added oon the basis of reorder number, this is for temporary purpose
        # product = [rec.product_id for rec in find_po.order_line]
        failed_vals = {
            # 'product_id' : product[0].id,
            'name' : line['Description'],
            'purchase_id' : find_po.id,
            'quantity_ordered' : line['QuantityOrdered'],
            'quantity_failed' : line['QuantityOutOfStock']
        }
        self.env['failed.purchase.order.line'].create(failed_vals)
        
    def available_gateways(self,gateway_type):
        company_id = self.env.company
        domain = [('company_id', '=', company_id.id)]
        if gateway_type == 'test':
            domain.append(('gateway_type', '=', 'test'))
        elif gateway_type == 'live':
            domain.append(('gateway_type', '=', 'live'))        
        all_gates = self.env['pharmx.gateways'].search(domain,limit=1)
        all_gates = all_gates.sorted(key=lambda k: k.priority)
        final_url = []                
        if all_gates:
            for gate in all_gates:
                if gate.available:
                    final_url.append(gate.url)
        return final_url

    def prepare_main_payload(self):
        
        company_id = self.env.company
        polines = len(self.order_line)
        polines = str(polines)
        payload = """<?xml version="1.0" encoding="utf-8"?>
                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <CheckOrderCompliance xmlns="http://www.pharmx.com.au/gateway3/ordermanagement">
                    <userDetail>
                        <Username>{0}</Username>
                        <Password>{1}</Password>
                    </userDetail>
                    <po>
                        <BuyerAbn>{2}</BuyerAbn>
                        <BillToAccountNumber>{3}</BillToAccountNumber>
                        <DeliveryAccountNumber>{4}</DeliveryAccountNumber>
                        <Purchaser>{5}</Purchaser>
                        <Backup></Backup>
                        <Code></Code>
                        <DeliverNoEarlierThan>{6}</DeliverNoEarlierThan>
                        <DeliverNoLaterThan>{7}</DeliverNoLaterThan>
                        <Group></Group>
                        <Method></Method>
                        <Reference>{8}</Reference>
                        <SupplierId>{9}</SupplierId>
                        <Type></Type>
                        <LineCount>{11}</LineCount>
                        <Freight>99</Freight>
                        <POSuniqueMessageID>{12}</POSuniqueMessageID>
                        <Lines></Lines>
                    </po>
                    </CheckOrderCompliance>
                </soap:Body>
                </soap:Envelope>""".format('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s') %(self.escape(company_id.pharmx_username),
                self.escape(company_id.pharmx_password),company_id.vat,self.account_id.name,
                self.account_id.name,company_id.name,(self.date_order or date.min).isoformat(),
                (self.date_order or date.min).isoformat(),self.name,self.partner_id.pharmx_supplier_id,
                polines,self.unique_pos_number)
        root = ET.fromstring(payload)       
        a = ET.SubElement(root,'soap:Body')
        b = ET.SubElement(a, 'po')
        c = ET.SubElement(b, 'Lines')
        for value in self.order_line:
            params = {'order_id': self.id}
            seller = value.product_id._select_seller(
                partner_id=self.partner_id,
                quantity=value.product_qty,
                date=self.date_order and self.date_order.date(),
                uom_id=value.product_uom,
                params=params)
            m1 = ET.Element("PurchaseOrderLine")
            b1 = ET.SubElement(m1, "OrderLineUID")
            b1.text = "%s" % (value.unique_pos_line_number)
            b2 = ET.SubElement(m1, "ReorderNumber")
            b2.text = "%s" % (value.sh_vendor_pro_code)
            b3 = ET.SubElement(m1, "EAN")
            b3.text = "%s" %(value.product_id.barcode)
            b4 = ET.SubElement(m1, "Description")
            b4.text = "%s" %(value.product_id.name)
            b5 = ET.SubElement(m1, "QuantityOrdered")
            b5.text = "%s" %(int(value.product_qty))
            b6 = ET.SubElement(m1, "UOM")
            b6.text = "%s" %(value.product_id.uom_po_id.name)
            b7 = ET.SubElement(m1, "UnitCostexGST")
            b7.text = "%s" %(value.price_unit)            
            c.append(m1)       
        lines_str = ET.tostring(c, encoding='unicode')
        payload = payload.replace("""<Lines></Lines>""",lines_str)
        return payload
    
    def prepare_order_payload(self):
        company_id = self.env.company
        polines = len(self.order_line)
        payload = """<?xml version="1.0" encoding="utf-8"?>
                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <CreateOrder xmlns="http://www.pharmx.com.au/gateway3/ordermanagement">
                    <userDetail>
                        <Username>{0}</Username>
                        <Password>{1}</Password>
                    </userDetail>
                    <po>
                        <BuyerAbn>{2}</BuyerAbn>
                        <BillToAccountNumber>{3}</BillToAccountNumber>
                        <DeliveryAccountNumber>{4}</DeliveryAccountNumber>
                        <Purchaser>{5}</Purchaser>
                        <Backup></Backup>
                        <Code></Code>
                        <DeliverNoEarlierThan>{6}</DeliverNoEarlierThan>
                        <DeliverNoLaterThan>{7}</DeliverNoLaterThan>
                        <Group></Group>
                        <Method></Method>
                        <Reference>{8}</Reference>
                        <SupplierId>{9}</SupplierId>
                        <Type></Type>
                        <LineCount>{11}</LineCount>
                        <Freight>99</Freight>
                        <POSuniqueMessageID>{12}</POSuniqueMessageID>
                        <Lines></Lines>
                    </po>
                    </CreateOrder>
                </soap:Body>
                </soap:Envelope>""".format('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s') %(self.escape(company_id.pharmx_username),
                self.escape(company_id.pharmx_password),company_id.vat,self.account_id.name,
                self.account_id.name,company_id.name,(self.date_order or date.min).isoformat(),
                (self.date_order or date.min).isoformat(),self.name,self.partner_id.pharmx_supplier_id,
                polines,self.unique_pos_number)
        root = ET.fromstring(payload)       
        a = ET.SubElement(root,'soap:Body')
        b = ET.SubElement(a, 'po')
        c = ET.SubElement(b, 'Lines')
        for value in self.order_line:
            params = {'order_id': self.id}
            seller = value.product_id._select_seller(
                partner_id=self.partner_id,
                quantity=value.product_qty,
                date=self.date_order and self.date_order.date(),
                uom_id=value.product_uom,
                params=params)
            m1 = ET.Element("PurchaseOrderLine")
            b1 = ET.SubElement(m1, "OrderLineUID")
            b1.text = "%s" % (value.unique_pos_line_number)
            b2 = ET.SubElement(m1, "ReorderNumber")
            b2.text = "%s"  %(seller.product_code)
            b3 = ET.SubElement(m1, "EAN")
            b3.text = "%s" %(value.product_id.barcode)
            b4 = ET.SubElement(m1, "Description")
            b4.text = "%s" %(value.product_id.name)
            b5 = ET.SubElement(m1, "QuantityOrdered")
            b5.text = "%s" %(int(value.product_qty))
            b6 = ET.SubElement(m1, "UOM")
            b6.text = "%s" %(value.product_id.uom_po_id.name)
            b7 = ET.SubElement(m1, "UnitCostexGST")
            b7.text = "%s" %(value.price_unit)            
            c.append(m1)       
        lines_str = ET.tostring(c, encoding='unicode')
        payload = payload.replace("""<Lines></Lines>""",lines_str)
        return payload

    def prepare_stock_avail_payload(self):        
        company_id = self.env.company
        polines = len(self.order_line)
        payload = """<?xml version="1.0" encoding="utf-8"?>
                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <GetStockAvailability xmlns="http://www.pharmx.com.au/gateway3/documentmanagement">
                    <userDetail>
                        <Username>{0}</Username>
                        <Password>{1}</Password>
                    </userDetail>
                    <stockAvailabilityRequest>
                        <SupplierId>{2}</SupplierId>
                        <AccountNumber>{3}</AccountNumber>
                        <BillingAccountNumber>{4}</BillingAccountNumber>
                        <LineCount>{5}</LineCount>
                        <Lines></Lines>
                    </stockAvailabilityRequest>
                    </GetStockAvailability>
                </soap:Body>
                </soap:Envelope>""".format('%s','%s','%s','%s','%s','%s') %(self.escape(company_id.pharmx_username),self.esccape(company_id.pharmx_password),
                self.partner_id.pharmx_supplier_id,self.partner_id.pharmx_bill_to_account_number,self.account_id.name,
                polines)
        root = ET.fromstring(payload)       
        a = ET.SubElement(root,'soap:Body')
        b = ET.SubElement(a, 'stockAvailabilityRequest')
        c = ET.SubElement(b, 'Lines')
        for value in self.order_line:
            params = {'order_id': self.id}
            seller = value.product_id._select_seller(
                partner_id=self.partner_id,
                quantity=value.product_qty,
                date=self.date_order and self.date_order.date(),
                uom_id=value.product_uom,
                params=params)
            m1 = ET.Element("StockAvailabilityRequestLine")
            b2 = ET.SubElement(m1, "ReorderNumber")
            b2.text = "%s" %(seller.product_code)
            b3 = ET.SubElement(m1, "EAN")
            b3.text = "%s" %(value.product_id.barcode)
            b5 = ET.SubElement(m1, "Quantity")
            b5.text = "%s" %(int(value.product_qty))
            b6 = ET.SubElement(m1, "UOM")
            b6.text = "%s" %(value.product_id.uom_po_id.name)        
            c.append(m1)       
        lines_str = ET.tostring(c, encoding='unicode')
        payload = payload.replace("""<Lines></Lines>""",lines_str)
        return payload
