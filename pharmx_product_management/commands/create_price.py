from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, DataSyncMessage, Item, PriceMaintenance, Product
from odoo import fields, models
import dateutil.parser

def create_price(self, price: PriceMaintenance, fields=None):
    
        supplier = self.env['res.partner'].search([('pharmx_supplier_id', '=', price.Supplier.SiteID)])
        if not supplier:
            raise Exception("Supplier doesn't exist. Potentially message is out of order.")

        product_code = [id.ID for id in (price.AlternativeItemIDs or []) if id.Type == "SKU"]
        if not product_code:
            raise Exception("Product SKU Doesnt Exist on price message.")
        
        supplier_info = self.env['product.supplierinfo'].with_context(active_test=False).search(
            [
                ('name', '=', supplier.id),
                ('product_code', '=', product_code[0])
            ], limit=1
        )
        
        if not supplier_info:
            raise Exception("Supplier Info doesn't exist. Potentially message is out of order.")
            # Could probably create the price with the information we have, match on barcode(s), have everything except product name
            
        public_pricelist = self.env['product.pricelist'].with_context(active_test=False).search(
            [
                ('partner_id', '=', supplier.id)
            ], limit=1
        )
        
        if not public_pricelist:
            public_pricelist = self.env['product.pricelist'].create({
                'active': True,
                'display_name':  supplier.name + ' Pricelist',
                'name':  supplier.name + ' Pricelist',
                'pricelist_type': 'purchase',
                'partner_id': supplier.id
            })
        
        existingPrice = self.env['product.pricelist.item'].with_context(active_test=False).search(
            [
                ('price_code', '=', price.PriceID),
                ('supplier_info', '=', supplier_info.id)
            ], limit=1
        )

        price_vals = {
            'price_code' : price.PriceID,
            'min_quantity' : price.ItemPrice.Eligibility.ThresholdQuantity.Units,
            'fixed_price' : price.ItemPrice.Amount,
            'date_start' : dateutil.parser.isoparse(price.ItemPrice.EffectiveDateTimestamp).replace(tzinfo=None),
            'date_end' : dateutil.parser.isoparse(price.ItemPrice.ExpirationDateTimestamp).replace(tzinfo=None) if price.ItemPrice.ExpirationDateTimestamp else False,
            'supplier_info': supplier_info.id,
            'pricelist_id': public_pricelist.id
        }
        
        if not existingPrice:
                return self.env['product.pricelist.item'].create(price_vals)
        else:
            existingPrice.write(price_vals)