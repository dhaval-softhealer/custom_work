from typing import List
from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from ....pharmx_edi.dataclasses.datasyncmessage  import AlternativeID, DataSyncMessage, RetailTransaction, RetailTransactionLineItem, Return
import dateutil.parser
from ...commands.shared import resolveProduct, createProduct, searchForAlternativeID
from odoo.exceptions import AccessError, UserError, ValidationError

class OnInventoryControlTransactionReceivedEventListener(Component):
    _name = 'datasync.inventorycontroltransaction.received.listener'
    _inherit = 'base.event.listener'
    
    def on_Outbound_InventoryControlTransaction_received(self, record: DataSyncMessage, fields=None):
        _logger.info("%r has been created", record)
        print(record)
        
        # first find out if this store exists, if not exit.
        store = self.env['res.partner'].search([('pharmx_site_id', '=', record.InitiatingBusinessUnit.SiteID)])
        
        if not store:
            return
        
        company = self.env['res.company'].search([('partner_id', '=', store.id)])
        
        if not company:
            return
        
        inventoryControlTransaction = record.InventoryControlTransaction
        
        if inventoryControlTransaction.Order != None:
            
            order = inventoryControlTransaction.Order
            
            # Create Partner (if doesnt exist)
            
            if order.Supplier and order.Supplier.SiteID:
                supplier = self.env['res.partner'].search([('pharmx_site_id', '=', order.Supplier.SiteID)])
            
            if not supplier:
                supplier = self.env['res.partner'].search([('company_id', '=', order.SupplierID)])
            
            if not supplier:
                
                suppliertype = self.env['pharmx.type'].search([('name', '=', 'Supplier')])
                
                usi = searchForAlternativeID("USI", order.AlternativeSupplierIDs)
                
                if order.Supplier == None and order.Supplier.SiteID == None and usi == None:
                    
                    # Create a company product
                    
                    supplier = {
                        'name' : order.SupplierID,
                        'sh_pharmx_type' : [(4, suppliertype.id, 0)],
                        'pharmx_site_id' :  None,
                        'ref' : order.SupplierID,
                        'company_type': 'company',
                        'company_id': company.id
                    }
                     
                    supplier = self.env['res.partner'].create(supplier)
                    
                else:
                    
                    # Create a global product
                    
                    supplier = {
                        'name' : order.Supplier.SiteName or usi or order.Supplier.SiteID,
                        'sh_pharmx_type' : [(4, suppliertype.id, 0)],
                        'pharmx_site_id' :  order.Supplier.SiteID,
                        'ref' : usi,
                        'company_type': 'company',
                    }
                    
                    supplier = self.env['res.partner'].create(supplier)
            
            # Create PO
            
            existingPurchaseOrder = self.env['purchase.order'].search([('company_id', '=', company.id), ('origin', '=', order.DocumentID)])
        
            if existingPurchaseOrder and existingPurchaseOrder.create_date > dateutil.parser.isoparse(record.MessageDateTime).replace(tzinfo=None):
                return
        
            purchaseOrder = {
                #'amount_total' : sum([x.UnitCount * x.UnitBaseCostAmount for x in order.LineItem]),
                #'amount_tax' :  sum([x.Tax.Amount for x in order.LineItem if x.Tax != None]),
                #'amount_untaxed' : sum([x.UnitCount * x.UnitBaseCostAmount for x in order.LineItem]) - sum([x.Tax.Amount for x in order.LineItem if x.Tax != None]),
                'create_date' : dateutil.parser.isoparse(record.MessageDateTime).replace(tzinfo=None),
                'partner_id' : supplier.id,
                'company_id': company.id,
                'date_order' : dateutil.parser.isoparse(inventoryControlTransaction.DateTime).replace(tzinfo=None),
                'name': 'ORDER-' + order.DocumentID,
                'state': self.map_order_status(order.Status), # needs to be some mapping here.
                'currency_id': company.currency_id.id,
                'origin' : order.DocumentID,
                'order_line' : [],
                'date_planned': dateutil.parser.isoparse(inventoryControlTransaction.DateTime).replace(tzinfo=None), # Does LOTS POS have a planned delivery date?
                'invoice_status': '', # Need to map to lines.
            }
            
            for line in order.LineItem:
                
                product = resolveProduct(self, company, line.ItemID, line.AlternativeItemIDs)
                
                if not product:
                    product = createProduct(self, company, line.ItemDescription, line.ItemID, 'product', line.AlternativeItemIDs)
       
                
                purchaseOrderLine = {
                    'name' : line.ItemDescription, # Line No
                    'price_unit' : line.UnitBaseCostAmount,
                    'price_tax' : line.Tax.Amount,
                    #'currency_id': company.currency_id,
                    #'date_order': dateutil.parser.isoparse(inventoryControlTransaction.DateTime).replace(tzinfo=None),
                    'product_id' : product.id,
                    'product_uom' : product.uom_po_id.id,
                    'date_planned': dateutil.parser.isoparse(inventoryControlTransaction.DateTime).replace(tzinfo=None), # Does LOTS POS have a planned delivery date?
                    'product_qty' : line.UnitCount,
                    'qty_received' : line.UnitsShippedCount if hasattr(line, 'UnitsShippedCount') else 0,
                    'qty_invoiced' : line.UnitsInvoicedCount if hasattr(line, 'UnitsInvoicedCount') else 0,
                    'sh_vendor_pro_code': line.SupplierItemID,
                }
                 
                purchaseOrder['order_line'].append((0, 0, purchaseOrderLine))
                 
            
            if existingPurchaseOrder:
                existingPurchaseOrder.order_line.with_context(pos_sync=True).unlink()
                existingPurchaseOrder.write(purchaseOrder)
                return existingPurchaseOrder
            else:
                return self.env['purchase.order'].create(purchaseOrder)
            
    def map_order_status(self, status: str):
        if status == 'Open':
            return 'draft'
        elif status == 'Sent':
            return 'sent'
        elif status == 'Acknowledged':
            return 'purchase'
        elif status == 'Delivered':
            return 'done'
        elif status == 'Cancelled':
            return 'cancel'