import json
import math
from ....pharmx_edi.dataclasses.datasyncmessage import DataSyncMessage, BusinessUnit, Eligibility, Item, AlternativeID, Display, Description, Attribute, PriceMaintenance, Price, ThresholdQuantity
from ....pharmx_edi.services.pharmxservice import PharmXService
from odoo.addons.component.core import Component, AbstractComponent # type: ignore
from odoo import api, fields, models, _
import uuid
from datetime import date, datetime
import ast
import dateutil.parser
import logging
_logger = logging.getLogger(__name__)

class ProductPricelistItem(models.AbstractModel):
    _inherit = 'product.pricelist.item'

    def on_price_updated(self, record, fields=None):
        _logger.info("%r has been created", record)

        price = record.get_price()
    
        json = price.to_json(indent=4)

        cached_price = self.env["subscription.cache"].search([("type" ,"=", "product.pricelist.item"),("object_id", '=', record.id)])

        # Only send out messages if the product has actually changed.
        if cached_price.id == False or cached_price.cached_value != json:

            if cached_price.id == False:
                self.env["subscription.cache"].create({
                    "type": "product.pricelist.item",
                    "object_id": record.id,
                    "cached_value": json
                })
            else:
                cached_price.write({ 'cached_value': json })

            subscriptions = self.env['product.subscription'].search([])

            endpoints = []

            for subscription in subscriptions:
                if subscription.rule_prices_domain:
                    domain = ast.literal_eval(subscription.rule_prices_domain)
                    domain.append(('id', '=', record.id))
                    item = self.env["product.pricelist.item"].search(domain, limit=1)
                    if item.id == record.id:
                        endpoints.append(subscription.serviceendpoint)

            if len(endpoints) > 0:

                message = DataSyncMessage(
                    MessageId = uuid.uuid4(),
                    MessageDateTime= datetime.utcnow(),
                    MessageType = "PriceMaintenance",
                    MessageDirection = "Inbound",
                    OriginatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                    InitiatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                    NotifiedBusinessUnits = [BusinessUnit(SiteID= endpoint.partner_id.pharmx_site_id, SiteName = endpoint.partner_id.name, ServiceID= endpoint.service_id, ServiceName= endpoint.name) for endpoint in endpoints],
                    PriceMaintenance = price
                )

                _logger.info('creating catalog' + str(message))

                PharmXService.sendMessage(self, message)
