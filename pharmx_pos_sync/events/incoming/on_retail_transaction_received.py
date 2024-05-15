from typing import List
from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from ....pharmx_edi.dataclasses.datasyncmessage  import AlternativeID, DataSyncMessage, RetailTransaction, RetailTransactionLineItem, Return
import dateutil.parser
from ...commands.shared import resolveProduct, createProduct

class OnRetailTransactionreceivedEventListener(Component):
    _name = 'datasync.retailtransaction.received.listener'
    _inherit = 'base.event.listener'
    
    def on_Outbound_RetailTransaction_received(self, record: DataSyncMessage, fields=None):
        _logger.info("%r has been created", record)
        
        # first find out if this store exists, if not exit.
        store = self.env['res.partner'].search([('pharmx_site_id', '=', record.InitiatingBusinessUnit.SiteID)])
        
        if not store:
            return
        
        company = self.env['res.company'].search([('partner_id', '=', store.id)])
        
        if not company:
            return
        
        retailTransaction = record.RetailTransaction
        
        # perhaps I need to create a point of sale if one doesnt exist (as its mandatory?)
        # create_config
        
        # see if a session is already open, if not, open one.
        
        # pos = self.env['pos.config'].search([('company_id', '=', company.id)], limit=1)
        
        # if not pos:
        #     return
        
        # session = self.env['pos.session'].search([('company_id', '=', company.id), ('state', '=', 'opened')])
        
        # if not session:
        #     session = {
        #         'display_name': retailTransaction.BusinessDayDate,
        #         'company_id': company.id,
        #         'name': retailTransaction.BusinessDayDate,
        #         'state': 'opened',
        #         'config_id': pos.id
        #     }
        
        #     session = self.env['pos.session'].create(session)
        
        # first create a sale (/there already could be a sale in which case update it.)
        
        existingSale = self.env['pos.order'].search([('company_id', '=', company.id), ('pos_reference', '=', retailTransaction.TransactionID)])
        
        if existingSale and existingSale.create_date > dateutil.parser.isoparse(record.MessageDateTime).replace(tzinfo=None):
            return
        
        sale = {
            'create_date' : dateutil.parser.isoparse(record.MessageDateTime).replace(tzinfo=None),
            'amount_total' : retailTransaction.Total.Amount,
            'amount_tax' :  sum([x.Sale.Tax.Amount for x in retailTransaction.LineItems if x.Sale != None and x.Sale.Tax != None and x.Sale.Tax.Amount > 0]),
            'amount_paid' : sum([x.Tender.Amount for x in retailTransaction.LineItems if x.Tender != None]),
            'amount_return' : sum([x.Return.ExtendedAmount for x in retailTransaction.LineItems if x.Return != None]),
            'company_id': company.id,
            'date_order' : dateutil.parser.isoparse(retailTransaction.DateTime).replace(tzinfo=None),
            'name': record.MessageType + '-' + retailTransaction.TransactionID,
            'pos_reference': retailTransaction.TransactionID,
            'session_id': None,
            'state': 'done',
            'pricelist_id': 1,
            'currency_id': company.currency_id
        }
        
        sale['lines'] = self.setLineItems(company, retailTransaction)
        
        sale['payment_ids'] = self.setPaymentItems(company, retailTransaction)
        
        print(record)
        
        if existingSale:
            existingSale.lines.unlink()
            existingSale.payment_ids.unlink()
            existingSale.write(sale)
            return existingSale
        else:
            return self.env['pos.order'].create(sale)

    def setLineItems(self, company, retailTransaction: RetailTransaction):
        
        saleItems = []
        
        for retailTransactionLine in [x for x in retailTransaction.LineItems if x.Sale != None or x.Return != None]:
            
            saleReturn = retailTransactionLine.Sale if retailTransactionLine.Sale != None else retailTransactionLine.Return

            # Create Product if it cannot be found:
            product = resolveProduct(self, company, saleReturn.ItemID, saleReturn.AlternativeItemIDs)
            if not product:
                product = createProduct(self, company, saleReturn.Description, saleReturn.ItemID, 'product' if saleReturn.ItemType == "StockItem" else 'service', saleReturn.AlternativeItemIDs)
            
            saleItem = {
                'name' : retailTransactionLine.SequenceNumber, # Line No
                'full_product_name': saleReturn.Description,
                'display_name' : saleReturn.Description,
                'price_subtotal' : saleReturn.ActualSalesUnitPrice - saleReturn.Tax.Amount, #Subtotal w/o Tax
                'price_subtotal_incl' : saleReturn.ActualSalesUnitPrice, #Subtotal
                'product_id' : product.id, # Product
                'qty' : saleReturn.Quantity,
                'price_unit' : saleReturn.ActualSalesUnitPrice,
                'total_cost' : saleReturn.UnitCostPrice * saleReturn.Quantity,
                'is_total_cost_computed' : True,
                'discount' : saleReturn.ExtendedDiscountAmount / saleReturn.ExtendedAmount if saleReturn.ExtendedAmount != 0 else 0 , #%
                #'taxes' : retailTransactionLine.Sale.Tax.Amount, # Actual Tax Codes here.
                'refunded_qty' : saleReturn.Quantity if retailTransactionLine.Return != None else 0,
                'currency_id': company.currency_id
            }
            
            saleItems.append((0,0,saleItem))
        
        return saleItems

    def setPaymentItems(self, company, retailTransaction):
        
        payments = []
        
        for retailTransactionLine in [x for x in retailTransaction.LineItems if x.Tender != None]:
            # Create Product if it cannot be found:
            tenderType = retailTransactionLine.Tender.TenderType
            paymentMethod = self.env['pos.payment.method'].search([('company_id', '=', company.id), ('name', '=', tenderType)])
            
            # Probably need to do something here around non-stockable items, e.g. fees etc.
            if not paymentMethod:
                paymentMethod = {
                    'name' : tenderType,
                    'company_id': company.id
                }
                
                paymentMethod = self.env['pos.payment.method'].create(paymentMethod)
                #pos['payment_method_ids'] = (4, paymentMethod.id, 0)
                #self.env['pos.config'].update(pos)
            
            paymentItem = {
                'payment_method_id' : paymentMethod.id, #mandatory
                'amount' : retailTransactionLine.Tender.Amount, #mandatory
                #'payment_date': retailTransactionLine.Tender.Da,  #trying to see if needed.
                'display_name': retailTransactionLine.Tender.TenderType + ' ' + str(retailTransactionLine.Tender.CoPayType), #mandatory
                'name' : retailTransactionLine.Tender.TenderType, #label
            }
            
            payments.append((0,0,paymentItem))
        
        return payments
