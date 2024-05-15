from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, DataSyncMessage, Item, PriceMaintenance, Product
from odoo import fields, models
import dateutil.parser

def create_price(self, price: PriceMaintenance, fields=None):
    
        supplier = self.env['res.partner'].search([('pharmx_supplier_id', '=', price.Supplier.SiteID)])
        if not supplier:
            raise Exception("Supplier doesn't exist. Potentially message is out of order.")
        
        supplier_info = self.env['product.supplierinfo'].with_context(active_test=False).search(
            [
                ('name', '=', supplier.id),
                ('product_code', '=', price.ItemID)
            ], limit=1
        )
        
        if not supplier_info:
            raise Exception("Supplier Info doesn't exist. Potentially message is out of order.")
            # Could probably create the price with the information we have, match on barcode(s), have everything except product name 
        
        exact_supplier_info = self.env['product.supplierinfo'].with_context(active_test=False).search(
            [
                ('name', '=', supplier.id),
                ('product_code', '=', price.ItemID),
                ('min_qty', '=', price.ItemPrice.Eligibility.ThresholdQuantity.Units),
                ('price', '=', price.ItemPrice.Amount),
                ('date_start', '=', dateutil.parser.parse(price.ItemPrice.EffectiveDateTimestamp)),
            ]
        )
        
        if exact_supplier_info:
            updated_price = {
                'date_end' : price.ItemPrice.ExpirationDateTimestamp
            }
            return exact_supplier_info.write(updated_price)
        
        spare_supplier_info = self.env['product.supplierinfo'].with_context(active_test=False).search(
            [
                ('name', '=', supplier.id),
                ('product_code', '=', price.ItemID),
                ('min_qty', '=', 0.0),
                ('price', '=', 0.0)
            ]
        )
        
        if spare_supplier_info:
            price_vals = {
                'min_qty' : price.ItemPrice.Eligibility.ThresholdQuantity.Units,
                'price' : price.ItemPrice.Amount,
                'date_start' : price.ItemPrice.EffectiveDateTimestamp,
                'date_end' : price.ItemPrice.ExpirationDateTimestamp
            }
            return spare_supplier_info.write(price_vals)
        
        ## Else there is no spare supplier_info I can re-use, so I will create a new one.
        price_vals = {
            'name' : supplier.id,
            'product_tmpl_id': supplier_info['product_tmpl_id'].id,
            'product_code' : price.ItemID,
            'product_name' : supplier_info['product_name'],

            # Copying across price fields from the message
            'min_qty' : price.ItemPrice.Eligibility.ThresholdQuantity.Units,
            'price' : price.ItemPrice.Amount,
            'date_start' : price.ItemPrice.EffectiveDateTimestamp,
            'date_end' : price.ItemPrice.ExpirationDateTimestamp,

            # Copying across item fields from the existing supplierinfo
            'min_order_qty': supplier_info['min_order_qty'],
            'order_multiple': supplier_info['order_multiple'],
            'shelf_pack': supplier_info['shelf_pack'],
            'items_per_box': supplier_info['items_per_box'],
            'rrp': supplier_info['rrp'],
            'gst_status': supplier_info['gst_status'],
            'department': supplier_info['department'],
            'subdepartment': supplier_info['subdepartment'],
            'delay': supplier_info['delay'],
        }
        
        return self.env['product.supplierinfo'].create(price_vals)
