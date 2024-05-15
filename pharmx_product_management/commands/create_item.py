from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, Attribute, DataSyncMessage, Item, Product
from decimal import Decimal
from odoo import fields, models
from datetime import datetime
from typing import List
from dateutil import parser
from .shared import create_category, create_sub_category, create_attribute_value, get_attribute_differences, get_identifier_differences, get_tax_differences, update_barcodes, set_attribute, update_supplier_barcodes

def create_item(self, item: Item, global_product, fields=None):
        supplier = self.env['res.partner'].search([('pharmx_supplier_id', '=', item.Supplier.SiteID)])
        supplier_type = self.env['pharmx.type'].search([('name','=', 'Supplier')])
        if not supplier:
            print('create supplier')
            supplier = self.env['res.partner'].create({
                'name' : item.Supplier.SiteName if len(item.Supplier.SiteName) > 0 else item.Supplier.SiteID,
                'company_type': 'company',
                'pharmx_supplier_id' : item.Supplier.SiteID,
                'pharmx_site_id' : item.Supplier.SiteID,
                'sh_pharmx_type': [ supplier_type.id ]
            })
        else:
            if supplier_type.id not in supplier.sh_pharmx_type.ids:
                supplier.write({'sh_pharmx_type': [(4, supplier_type.id)]})
                
        product_code = [id.ID for id in (item.AlternativeItemIDs or []) if id.Type == "SKU"] 
        suppliers_product = self.env['product.supplierinfo'].with_context(active_test=False).search([('product_code', '=', product_code), ('name', '=', supplier.id)])
        rrp = [price.Amount for price in (item.ItemPrice or []) if price.ValueTypeCode == "RegularSalesUnitPrice"]
        department = [x.Value for x in (item.MerchandiseHierarchy or []) if x.Level == "Department"]
        subdepartment = [x.Value for x in (item.MerchandiseHierarchy or []) if x.Level == "SubDepartment"]
        
        seller_vals = {
            'product_code' : product_code[0],
            'name' : supplier.id,
            'product_name' : item.Display.Description.Text,
            'rrp' : rrp[0] if len(rrp) > 0 else 0,
            'min_order_qty' : item.OrderQuantityMinimum if item.OrderQuantityMinimum else 0.0,
            'order_multiple' : item.OrderQuantityMultiple,
            'shelf_pack' : item.SalesUnitPerPackUnitQuantity,
            'items_per_box' : item.ItemQuantityPerSalesUnit,
            'department' : department[0] if len(department) > 0 else '',
            'subdepartment' : subdepartment[0] if len(subdepartment) > 0 else '',
            'price': 0.0,
            'min_qty': 0,
            'identifier_ids': get_identifier_differences(self, (item.AlternativeItemIDs  or []), suppliers_product.identifier_ids if suppliers_product else []),
            'attribute_ids': get_attribute_differences(self, (item.ItemAttributes  or []), suppliers_product.attribute_ids if suppliers_product else []),
            'tax_ids': get_tax_differences(self, (item.TaxInformation or []), suppliers_product.tax_ids if suppliers_product else []),
            'product_tmpl_id': global_product.id
        }
        
        if not suppliers_product:
            return self.env['product.supplierinfo'].create(seller_vals)
        else:
            suppliers_product.write(seller_vals)

