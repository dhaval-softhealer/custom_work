from typing import List
from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from ....pharmx_edi.dataclasses.datasyncmessage  import AlternativeID, DataSyncMessage, RetailTransaction, RetailTransactionLineItem, Return
import dateutil.parser
from ...commands.shared import resolveProduct, createProduct

class OnInventoryPositionReceivedEventListener(Component):
    _name = 'datasync.inventoryposition.received.listener'
    _inherit = 'base.event.listener'
    
    def on_Outbound_InventoryAction_received(self, record: DataSyncMessage, fields=None):
        _logger.info("%r has been created", record)
        print(record)
        
        # first find out if this store exists, if not exit.
        store = self.env['res.partner'].search([('pharmx_site_id', '=', record.InitiatingBusinessUnit.SiteID)])
        
        if not store:
            return
        
        company = self.env['res.company'].search([('partner_id', '=', store.id)])
        
        if not company:
            return
        
        inventoryAction = record.InventoryAction
        
        for inventoryPosition in inventoryAction.InventoryPosition.Items:
            
            if inventoryPosition.State != "AvailableOnHand":
                continue
        
            product = resolveProduct(self, company, inventoryPosition.ItemID, inventoryPosition.AlternativeItemIDs)
            if not product:
                product = createProduct(self, company, inventoryPosition.ItemID, inventoryPosition.ItemID, 'product', inventoryPosition.AlternativeItemIDs)
        
            location = self.env['stock.location'].search([('active', '=', True), ('usage', '=', 'internal'), ('company_id', '=', company.id)])
            
            existingQuant = self.env['stock.quant'].search([('location_id', '=', location.id), ('product_id', '=', product.id)])
        
            if existingQuant and existingQuant.inventory_date > dateutil.parser.isoparse(record.MessageDateTime).replace(tzinfo=None).date():
                return
            
            quant = {
                'product_id': product.id,
                #'company_id': company.id,
                'inventory_date': dateutil.parser.isoparse(record.MessageDateTime).replace(tzinfo=None),
                #'on_hand': True if inventoryPosition.State == "AvailableOnHand" else False, #??
                'location_id': location.id,
                'inventory_quantity': inventoryPosition.Quantity
            }
        
            self.env['stock.quant'].with_context(inventory_mode=True).create(quant)._apply_inventory()