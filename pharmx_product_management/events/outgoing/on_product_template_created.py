import json
from ....pharmx_edi.dataclasses.datasyncmessage import Attribute, DataSyncMessage, BusinessUnit, ManufacturerInformation, MerchandiseHierarchy, Product, AlternativeID, Display, Description, TaxInformation
from ....pharmx_edi.services.pharmxservice import PharmXService
from odoo.addons.component.core import Component, AbstractComponent # type: ignore
from odoo import api, fields, models, _
import uuid
from datetime import date, datetime
import ast
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.AbstractModel):
    _inherit = 'product.template'

    def on_product_template_updated(self, record, fields=None):
        _logger.info("%r has been created", record)

        product = record.get_product()

        json = product.to_json(indent=4, )

        cached_product = self.env["subscription.cache"].search([("type" ,"=", "product.template"),("object_id", '=', record.id)])

        # Only send out messages if the product has actually changed.
        if cached_product.id == False or cached_product.cached_value != json:
            
            if cached_product.id == False:
                self.env["subscription.cache"].create({
                    "type": "product.template",
                    "object_id": record.id,
                    "cached_value": json
                })
            else:
                cached_product.write({ 'cached_value': json })

            subscriptions = self.env['product.subscription'].search([])

            endpoints = []

            for subscription in subscriptions:
                if subscription.rule_products_domain:
                    domain = ast.literal_eval(subscription.rule_products_domain)
                    domain.append(('id', '=', record.id))
                    template = self.env["product.template"].search(domain, limit=1)
                    if template.id == record.id:
                        endpoints.append(subscription.serviceendpoint)

            if len(endpoints) > 0:

                message = DataSyncMessage(
                    MessageId = uuid.uuid4(),
                    MessageDateTime= datetime.utcnow(),
                    MessageType = "ProductMaintenance",
                    MessageDirection = "Inbound",
                    OriginatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                    InitiatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                    NotifiedBusinessUnits = [BusinessUnit(SiteID= endpoint.partner_id.pharmx_site_id, SiteName = endpoint.partner_id.name, ServiceID= endpoint.service_id, ServiceName= endpoint.name) for endpoint in endpoints],
                    ProductMaintenance = product
                )

                _logger.info('creating catalog' + str(message))

                PharmXService.sendMessage(self, message)
