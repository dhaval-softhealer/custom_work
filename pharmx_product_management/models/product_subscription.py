from datetime import date, datetime
import ast
import dateutil.parser
import uuid
from odoo import api, fields, models, _
from ...pharmx_edi.dataclasses.datasyncmessage import BusinessUnit, DataSyncMessage, Item, PartnerMaintenance, Price, PriceMaintenance, Product
from ...pharmx_edi.services.pharmxservice import PharmXService
from types import SimpleNamespace
import json
from dataclasses import dataclass
from dataclasses_json import dataclass_json

class ProductSubscriptionInherit(models.Model):
    _name = 'product.subscription'
    
    partner_id = fields.Many2one('res.partner', 'Subscriber')
    serviceendpoint = fields.Many2one('res.partner.serviceendpoint', string='Service Endpoint', domain="[('partner_id', '=', partner_id)]")
    rule_products_domain = fields.Char(string="Subscribed Products", default=[['sale_ok', '=', True]], help="Use the domain filter to select relevant products")
    rule_supplierinfo_domain = fields.Char(string="Subscribed Items", default=[], help="Use the domain filter to select relevant items")
    rule_prices_domain = fields.Char(string="Subscribed Prices", default=[], help="Use the domain filter to select relevant prices")
    rule_partners_domain = fields.Char(string="Subscribed Partners", default=[], help="Use the domain filter to select relevant partners")
    active = fields.Boolean(string='Active', default=True)

    @api.depends("rule_products_domain", "rule_items_domain", "rule_prices_domain")
    def resynchronize_all(self):
        self.resynchronize_products()
        self.resynchronize_items()
        self.resynchronize_prices()
        self.resynchronize_partners()

    def partition(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    @api.depends("rule_products_domain")
    def resynchronize_products(self):
        
        domain = ast.literal_eval(self.rule_products_domain)
        products = self.env["product.template"].search(domain)

        for chunk in self.partition(products, 500):

            productMessages = []

            cached_products = self.env["subscription.cache"].search([("type" ,"=", "product.template"),("object_id", 'in', chunk.ids)])

            for product in chunk:

                cached_product = [ cached_product for cached_product in cached_products if cached_product.object_id == product.id ]

                if len(cached_product) > 0:
                    productMessages.append(Product(**json.loads(cached_product[0].cached_value)))
                else:
                    product.on_product_template_updated(product)
                    cached_product = self.env["subscription.cache"].search([("type" ,"=", "product.template"),("object_id", '=', product.id)])
                    productMessages.append(Product(**json.loads(cached_product.cached_value)))
                    self.env.cr.commit()

            if len(productMessages) > 0:

                messageObjects = [
                    DataSyncMessage(
                        MessageId = uuid.uuid4(),
                        MessageDateTime= datetime.utcnow(),
                        MessageType = "ProductMaintenance",
                        MessageDirection = "Inbound",
                        OriginatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                        InitiatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                        DestinationBusinessUnit = BusinessUnit(SiteID= self.partner_id.pharmx_site_id, SiteName = self.partner_id.name, ServiceID= self.serviceendpoint.service_id, ServiceName= self.serviceendpoint.name),
                        NotifiedBusinessUnits = [],
                        ProductMaintenance = productMessage
                    )
                    for productMessage
                    in productMessages
                ]

                PharmXService.sendBatch(self, messageObjects, "15", "6")

    @api.depends("rule_supplierinfo_domain")
    def resynchronize_items(self):
        
        domain = ast.literal_eval(self.rule_supplierinfo_domain)
        items = self.env["product.supplierinfo"].search(domain)

        for chunk in self.partition(items, 500):

            itemMessages = []

            cached_items = self.env["subscription.cache"].search([("type" ,"=", "product.supplierinfo"),("object_id", 'in', chunk.ids)])
        
            for item in chunk:

                cached_item = [ cached_item for cached_item in cached_items if cached_item.object_id == item.id ]

                if len(cached_item) > 0:
                    itemMessages.append(Item(**json.loads(cached_item[0].cached_value)))
                else:
                    item.on_item_updated(item)
                    cached_item = self.env["subscription.cache"].search([("type" ,"=", "product.supplierinfo"),("object_id", '=', item.id)])
                    itemMessages.append(Item(**json.loads(cached_item.cached_value)))
                    self.env.cr.commit()

            if len(itemMessages) > 0:
                    
                messageObjects = [
                    DataSyncMessage(
                        MessageId = uuid.uuid4(),
                        MessageDateTime= datetime.utcnow(),
                        MessageType = "ItemMaintenance",
                        MessageDirection = "Inbound",
                        OriginatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                        InitiatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                        DestinationBusinessUnit = BusinessUnit(SiteID= self.partner_id.pharmx_site_id, SiteName = self.partner_id.name, ServiceID= self.serviceendpoint.service_id, ServiceName= self.serviceendpoint.name),
                        NotifiedBusinessUnits = [],
                        ItemMaintenance = itemMessage
                    )
                    for itemMessage
                    in itemMessages
                ]

                PharmXService.sendBatch(self, messageObjects, "15", "6")

    @api.depends("rule_prices_domain")
    def resynchronize_prices(self):
        
        domain = ast.literal_eval(self.rule_prices_domain)
        prices = self.env["product.pricelist.item"].search(domain)
        
        for chunk in self.partition(prices, 500):

            priceMessages = []
            cached_prices = self.env["subscription.cache"].search([("type" ,"=", "product.pricelist.item"),("object_id", 'in', chunk.ids)])

            for price in chunk:

                cached_price = [ cached_price for cached_price in cached_prices if cached_price.object_id == price.id ]

                if len(cached_price) > 0:
                    priceMessages.append(PriceMaintenance(**json.loads(cached_price[0].cached_value)))
                else:
                    price.on_price_updated(price)
                    cached_price = self.env["subscription.cache"].search([("type" ,"=", "product.pricelist.item"),("object_id", '=', price.id)])
                    priceMessages.append(PriceMaintenance(**json.loads(cached_price.cached_value)))
                    self.env.cr.commit()

            if len(priceMessages) > 0:
                messageObjects = [
                    DataSyncMessage(
                        MessageId = uuid.uuid4(),
                        MessageDateTime= datetime.utcnow(),
                        MessageType = "PriceMaintenance",
                        MessageDirection = "Inbound",
                        OriginatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                        InitiatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                        DestinationBusinessUnit = BusinessUnit(SiteID= self.partner_id.pharmx_site_id, SiteName = self.partner_id.name, ServiceID= self.serviceendpoint.service_id, ServiceName= self.serviceendpoint.name),
                        NotifiedBusinessUnits = [],
                        PriceMaintenance = priceMessage
                    )
                    for priceMessage
                    in priceMessages
                ]

                PharmXService.sendBatch(self, messageObjects, "15", "6")

    @api.depends("rule_partners_domain")
    def resynchronize_partners(self):
        
        domain = ast.literal_eval(self.rule_partners_domain)
        partners = self.env["res.partner"].search(domain)
        

        for chunk in self.partition(partners, 500):

            partnerMessages = []

            for partner in chunk:
                if partner.cached_partner:
                    partnerMessages.append(PartnerMaintenance(**json.loads(partner.cached_partner)))
                else:
                    partner.on_partner_updated(partner)
                    partnerMessages.append(PartnerMaintenance(**json.loads(partner.cached_partner)))
                    self.env.cr.commit()

            if len(partnerMessages) > 0:
                messageObjects = [
                    DataSyncMessage(
                        MessageId = uuid.uuid4(),
                        MessageDateTime= datetime.utcnow(),
                        MessageType = "PartnerMaintenance",
                        MessageDirection = "Inbound",
                        OriginatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                        InitiatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                        DestinationBusinessUnit = BusinessUnit(SiteID= self.partner_id.pharmx_site_id, SiteName = self.partner_id.name, ServiceID= self.serviceendpoint.service_id, ServiceName= self.serviceendpoint.name),
                        NotifiedBusinessUnits = [],
                        PartnerMaintenance = partnerMessage
                    )
                    for partnerMessage
                    in partnerMessages
                ]

                PharmXService.sendBatch(self, messageObjects, "15", "6")

    @api.depends("rule_products_domain")
    def _compute_valid_product_ids(self):
        for subscription in self:
            domain = ast.literal_eval(subscription.rule_products_domain) if subscription.rule_products_domain else []
            subscription.valid_product_ids = self.env["product.product"].search(domain).ids
    
    @api.depends("rule_supplierinfo_domain")
    def _compute_valid_supplierinfo_ids(self):
        for subscription in self:
            domain = ast.literal_eval(subscription.rule_supplierinfo_domain) if subscription.rule_supplierinfo_domain else []
            subscription.valid_supplierinfo_ids = self.env["product.supplierinfo"].search(domain).ids
    
    @api.depends("rule_prices_domain")
    def _compute_valid_prices_ids(self):
        for subscription in self:
            domain = ast.literal_eval(subscription.rule_prices_domain) if subscription.rule_prices_domain else []
            subscription.valid_prices_ids = self.env["product.pricelist.item"].search(domain).ids
    
    @api.depends("rule_partners_domain")
    def _compute_valid_partner_ids(self):
        for subscription in self:
            domain = ast.literal_eval(subscription.rule_partners_domain) if subscription.rule_partners_domain else []
            subscription.rule_partners_domain = self.env["res.partner"].search(domain).ids
