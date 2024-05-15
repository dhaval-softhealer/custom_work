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

def partition(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

class ProductSubscriptionInherit(models.Model):
    _name = 'subscription.cache'

    _sql_constraints = [
        (
            'uniq_cache_key',
            'unique(type, object_id)',
            'Cache Key must be uniqueu!'
        )
    ]
    
    ## id
    object_id = fields.Integer('Model Id', required=False, index=True)
    type = fields.Char(string='Model Type', required=False, index=True)
    cached_value = fields.Text('Cached Value', required=False)

    def rebuild_cache(self):

        self.with_delay().rebuild_product_cache()

        ## suppliers = self.env["res.partner"].search(["sh_pharmx_type", "in", ["Supplier", "Wholesaler"]]) # Apparently not right syntax for many 2  many.
        suppliers = self.env["res.partner"].search([])

        for supplier in suppliers:
            
            self.with_delay().rebuild_supplier_cache(supplier)

    def rebuild_product_cache(self):

        all_products = self.env["product.template"].search([])

        for products in partition(all_products, 500):

            messages = []

            cached_products = self.env["subscription.cache"].search([("type" ,"=", "product.template"),("object_id", 'in', products.ids)])

            for record in products:

                product = record.get_product()

                json = product.to_json(indent=4, )

                cached_product = [ cached_product for cached_product in cached_products if cached_product.object_id == record.id ]

                # Only send out messages if the product has actually changed.
                if len(cached_product) == 0 or cached_product[0].cached_value != json:
                    
                    if len(cached_product) == 0:
                        self.env["subscription.cache"].create({
                            "type": "product.template",
                            "object_id": record.id,
                            "cached_value": json
                        })
                    else:
                        cached_product[0].write({ 'cached_value': json })

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

                        messages.append(message)

            if len(messages) > 0:
                PharmXService.sendBatch(self, messages, "15", "6")

            self.env.cr.commit()
    
    def rebuild_supplier_cache(self, supplier):

        items = self.env["product.supplierinfo"].search([("name", "=", supplier.id)])

        for chunk in partition(items, 500):

            self.rebuild_item_cache(chunk)

            prices = self.env["product.pricelist.item"].search([("supplier_info", "in", chunk.ids)])

            self.rebuild_price_cache(prices)
                    
            self.env.cr.commit()

    def rebuild_item_cache(self, items):

        messages = []

        cached_items = self.env["subscription.cache"].search([("type" ,"=", "product.supplierinfo"),("object_id", 'in', items.ids)])
        
        for record in items:

            item = record.get_item()
        
            json = item.to_json(indent=4, )

            cached_item = [ cached_item for cached_item in cached_items if cached_item.object_id == record.id ]

            # Only send out messages if the product has actually changed.
            if len(cached_item) == 0 or cached_item[0].cached_value != json:

                if len(cached_item) == 0:
                    self.env["subscription.cache"].create({
                        "type": "product.supplierinfo",
                        "object_id": record.id,
                        "cached_value": json
                    })
                else:
                    cached_item[0].write({ 'cached_value': json })

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

                    messages.append(message)

        if len(messages) > 0:
            PharmXService.sendBatch(self, messages, "15", "6")


    def rebuild_price_cache(self, prices):

        messages = []

        cached_prices = self.env["subscription.cache"].search([("type" ,"=", "product.pricelist.item"),("object_id", 'in', prices.ids)])
        
        for record in prices:

            price = record.get_price()
    
            json = price.to_json(indent=4)

            cached_price = [ cached_price for cached_price in cached_prices if cached_price.object_id == record.id ]

            # Only send out messages if the product has actually changed.
            if len(cached_price) == 0 or cached_price[0].cached_value != json:

                if len(cached_price) == 0 == False:
                    self.env["subscription.cache"].create({
                        "type": "product.pricelist.item",
                        "object_id": record.id,
                        "cached_value": json
                    })
                else:
                    cached_price[0].write({ 'cached_value': json })

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

                    messages.append(message)

        if len(messages) > 0:
            PharmXService.sendBatch(self, messages, "15", "6")
