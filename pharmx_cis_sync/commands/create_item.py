from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, DataSyncMessage, Item, Product
from decimal import Decimal
from odoo import fields, models
from datetime import datetime
from typing import List
from dateutil import parser
from .shared import create_category, create_sub_category, create_attribute_value, update_barcodes, set_attribute, update_supplier_barcodes

def create_item(self, item: Item, global_product, fields=None):
        supplier = self.env['res.partner'].search([('pharmx_supplier_id', '=', item.Supplier.SiteID)])
        #supplier_type = self.env['pharmx.type'].search([('name','=', 'Supplier')])
        if not supplier:
            print('create supplier')
            supplier = self.env['res.partner'].create({
                'name' : item.Supplier.SiteName if len(item.Supplier.SiteName) > 0 else item.Supplier.SiteID,
                'company_type': 'company',
                'pharmx_supplier_id' : item.Supplier.SiteID,
                #'sh_pharmx_type': [ supplier_type ]
            })
        #else:
            #if supplier_type.id not in supplier.sh_pharmx_type.ids:
            #    supplier.write({'sh_pharmx_type': [(4, supplier_type.id)]})
                
        suppliers_products = self.env['product.supplierinfo'].with_context(active_test=False).search([('product_code', '=', item.ItemID), ('name', '=', supplier.id)])
        
        rrp = [price.Amount for price in (item.ItemPrice or []) if price.ValueTypeCode == "RegularSalesUnitPrice"]
        gst_status = [x.TaxGroupID for x in (item.TaxInformation or []) if x.TaxType == "GST"]
        department = [x.Value for x in (item.MerchandiseHierarchy or []) if x.Level == "Department"]
        subdepartment = [x.Value for x in (item.MerchandiseHierarchy or []) if x.Level == "SubDepartment"]
        
        seller_vals = {
            'name' : supplier.id,
            'product_name' : item.Display.Description.Text,
            'rrp' : rrp[0] if len(rrp) > 0 else 0,
            'min_order_qty' : item.OrderQuantityMinimum if item.OrderQuantityMinimum else 0.0,
            'order_multiple' : item.OrderQuantityMultiple,
            'shelf_pack' : item.SalesUnitPerPackUnitQuantity,
            'items_per_box' : item.ItemQuantityPerSalesUnit,
            'gst_status' : gst_status[0] if len(gst_status) > 0 else "Free",
            'department' : department[0] if len(department) > 0 else False,
            'subdepartment' : subdepartment[0] if len(subdepartment) > 0 else False
        }
        
        if not suppliers_products:
            
            seller_vals['price'] = 0.0
            seller_vals['min_qty'] = 0
            seller_vals['product_code'] = item.ItemID.strip()
            seller_vals['product_tmpl_id'] = global_product.id
            
            return self.env['product.supplierinfo'].create(seller_vals)
        else:
            for suppliers_product in suppliers_products:

                suppliers_product.write(seller_vals)

                # Apparently no taxes on a supplier_info card.        
                # if item.TaxInformation:
                #     gst = [x for x in item.TaxInformation if x.TaxType == "GST"][0]
                #     if gst:
                #         if  gst.TaxGroupID == "Yes" :
                #             domain = [('name', '=', "Sale (10%)")]
                #             find_tax = self.env['account.tax'].search(domain)
                #             if find_tax:
                #                 seller_vals['taxes_id'] = find_tax.ids
                #             else:
                #                 seller_vals['taxes_id'] = False
                #         if gst.TaxGroupID == "Yes" or gst.TaxGroupID == "Free":
                #                 domain = [('name', '=', "Purch (10%) (Goods)")]
                #                 find_tax = self.env['account.tax'].search(domain)
                #                 if find_tax:
                #                     seller_vals['supplier_taxes_id'] = find_tax.ids
                #                 else:
                #                     seller_vals['supplier_taxes_id'] = False

                # No barcodes on supplier info                
                # barcodes = list(set([x.ID for x in item.AlternativeItemIDs if x.Type == "UPC"])) # Need to get rid of duplicates barcodes.
                # if len(barcodes) > 0:
                #     # AS: Commented out (multiple barcode error, debugging, should only be one barcode per global product.)
                #     #product_vals['barcode'] = barcodes[0]['Barcode']
                #     barcode_list = update_supplier_barcodes(self, suppliers_product, barcodes)
                #     if len(barcode_list) > 0:
                #         seller_vals['barcode_line_ids'] = barcode_list
                #     #if barcode_list:
                #     #    seller_vals['barcode_line_ids'] = barcode_list
                #     # Commented out because a barcode can only be assigned to one product
                #     # if len(barcode_list) > 0:
                #     #     seller_vals['barcode'] = barcode_list[0][2]['name']
                
                # No vendor categories on supplier info card.
                # department = [x for x in item.MerchandiseHierarchy if x.Level == "Department"]
                # subDepartment = [x for x in item.MerchandiseHierarchy if x.Level == "SubDepartment"]
                # if len(department) == 1:
                #     department = department[0]
                #     domain = [('name', '=', department.Value), ('seller_id', '=', supplier.id)]
                #     department_categories = self.env['product.category'].search(domain)
                #     if department_categories:
                #         department_category = department_categories[0]
                #     else:
                #         department_category = create_category(self, department.Value, supplier.id)
                #     if len(subDepartment) > 0:
                #         subDepartment = subDepartment[0]
                #         domain = [('name', '=', subDepartment.Value), ('parent_id', '=', department_category.ids[0]), ('seller_id', '=', supplier.id)]
                #         subdepartment_categories = self.env['product.category'].search(domain)
                #         if subdepartment_categories:
                #             seller_vals['categ_id'] = subdepartment_categories[0].id
                #         else:
                #             subdepartment_category = create_sub_category(self, subDepartment.Value, department_category, supplier.id)
                #             seller_vals['categ_id'] = subdepartment_category.id
                # else:
                #     domain = [('name', '=', "Unknown")]
                #     unknown_category = self.env['product.category'].search(domain)
                #     if unknown_category:
                #         seller_vals['categ_id'] = unknown_category[0].id
                #     else:
                #         unknown_category = create_category(self, "Unknown")
                #         seller_vals['categ_id'] = unknown_category.id

                # if item.SupplierPrices:
                #     items_list = self.update_supplier_product_prices(None, item.SupplierPrices)
                #     if items_list:
                #         seller_vals['item_ids'] = items_list
                
            