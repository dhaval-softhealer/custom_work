import json
from ....pharmx_edi.dataclasses.datasyncmessage import DataSyncMessage, BusinessUnit, Item, AlternativeID, Display, Description, Attribute, ManufacturerInformation, MerchandiseHierarchy, Price, Product, TaxInformation
from ....pharmx_edi.services.pharmxservice import PharmXService
from odoo.addons.component.core import Component, AbstractComponent # type: ignore
from odoo import api, fields, models, _
import uuid
from datetime import date, datetime
import ast
import logging
_logger = logging.getLogger(__name__)

class SupplierInfoTemplate(models.AbstractModel):
    _inherit = 'product.supplierinfo'

    def on_item_updated(self, record, fields=None):
        _logger.info("%r has been created", record)

        item = record.get_item()
    
        json = item.to_json(indent=4, )

        cached_item = self.env["subscription.cache"].search([("type" ,"=", "product.supplierinfo"),("object_id", '=', record.id)])

        # Only send out messages if the product has actually changed.
        if cached_item.id == False or cached_item.cached_value != json:

            if cached_item.id == False:
                self.env["subscription.cache"].create({
                    "type": "product.supplierinfo",
                    "object_id": record.id,
                    "cached_value": json
                })
            else:
                cached_item.write({ 'cached_value': json })

            subscriptions = self.env['product.subscription'].search([])

            endpoints = []

            for subscription in subscriptions:
                if subscription.rule_supplierinfo_domain:
                    domain = ast.literal_eval(subscription.rule_supplierinfo_domain)
                    domain.append(('id', '=', record.id))
                    supplierinfo = self.env["product.supplierinfo"].search(domain, limit=1)
                    if supplierinfo.id == record.id:
                        endpoints.append(subscription.serviceendpoint)

            if len(endpoints) > 0:

                message = DataSyncMessage(
                    MessageId = uuid.uuid4(),
                    MessageDateTime= datetime.utcnow(),
                    MessageType = "ItemMaintenance",
                    MessageDirection = "Inbound",
                    OriginatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                    InitiatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                    NotifiedBusinessUnits = [BusinessUnit(SiteID= endpoint.partner_id.pharmx_site_id, SiteName = endpoint.partner_id.name, ServiceID= endpoint.service_id, ServiceName= endpoint.name) for endpoint in endpoints],
                    ItemMaintenance = item
                )

                _logger.info('creating catalog' + str(message))

                PharmXService.sendMessage(self, message)
