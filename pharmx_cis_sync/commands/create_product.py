from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, DataSyncMessage, Item, Product
from odoo import fields, models
from .shared import create_category, create_sub_category, create_attribute_value, update_barcodes, set_attribute

def create_product(self, product: Product, fields=None):
        domain = [('default_code', '=', product.ProductID)]
        existing_product = self.env['product.template'].with_context(active_test=False).search(domain)

        new_product = {
            'name' : product.Display.Description.Text if product.Display.Description else False,
            'default_code' : product.ProductID if product else False,
            'taxes_id' : False,
            'active': True if product.StatusCode == "Active" else False,
            'attribute_line_ids' : [],
            'list_price': 0.00,
            'type': "product",
            'cis_upi': product.ProductID if product else False,
            'cis_department': next((x.Value for x in (product.MerchandiseHierarchy or []) if x.Level == "Department"), None),
            'cis_subdepartment': next((x.Value for x in (product.MerchandiseHierarchy or []) if x.Level == "SubDepartment"), None),
            'cis_description': product.Display.Description.Text,
            'cis_shelflabel': product.Display.ShelfLabel.Text,
            'cis_gststatus': next((x.TaxGroupID for x in (product.TaxInformation or []) if x.TaxType == "GST"), None)
        }
                        
        # Map the category to unknown, it will be remapped later.
        all_category = self.env['product.category'].search([('name', '=', "All")])
        if not all_category:
            all_category = create_category(self, "All")
        new_product['categ_id'] = all_category[0].id
        
        # We dont have the superseded by attribute in the messages...        
        # # Merged Products
        # if product.Merge_Product_Id:
        #     product_vals['is_merged'] = True
        #     domain = [('cis_product_id', '=', product.Merge_Product_Id), '|', ('active', '=', True), ('active', '=', False)]
        #     find_merged_product = self.env['product.template'].with_context(active_test=False).search(domain)
        #     if find_merged_product:
        #         product_vals['merged_product_id'] = find_merged_product.id
        
        # Barcodes
        barcodes = list(set([x.ID for x in product.AlternativeProductIDs if x.Type == "GTIN"])) # Need to get rid of duplicates barcodes.
        if len(barcodes) > 0:
            # AS: Commented out (multiple barcode error, debugging, should only be one barcode per global product.)
            #product_vals['barcode'] = barcodes[0]['Barcode']
            barcode_list = update_barcodes(self, existing_product, barcodes)
            if len(barcode_list) > 0:
                new_product['barcode_line_ids'] = barcode_list

        # AS: Commented out for now, as we are not yet using attributes.
        # # Packaging Id
        packaging = [x for x in product.ProductAttributes if x.AttributeName == "Packaging"]
        if len(packaging) > 0:
            attributes = set_attribute(self, "Packaging", packaging[0].AttributeValue, existing_product)
            if attributes:
                new_product['attribute_line_ids'].extend(attributes)
        
        # Manufacturer
        if hasattr(product, "ManufacturerInformation") and product.ManufacturerInformation:
            manufacturer = self.env['res.partner'].search([('pharmx_supplier_id', '=', product.ManufacturerInformation.Manufacturer.SiteID)])
            if not manufacturer:
                manufacturer = self.env['res.partner'].create({
                    'name' : product.ManufacturerInformation.Manufacturer.SiteName if len(product.ManufacturerInformation.Manufacturer.SiteName) > 0 else product.ManufacturerInformation.Manufacturer.SiteID,
                    'company_type': 'company',
                    'pharmx_supplier_id' : product.ManufacturerInformation.Manufacturer.SiteID
                })
            #manufacturer_type = self.env['pharmx.type'].search([('name','=', 'Manufacturer')])
            #if manufacturer_type.id not in manufacturer.sh_pharmx_type.ids:
            #    manufacturer.write({'sh_pharmx_type': [(4, manufacturer_type.id)]})
            new_product['manufacturer'] = manufacturer.id
            
        # Brand
        brands = [x.AttributeValue for x in product.ProductAttributes if x.AttributeName == "BrandName"]
        if len(brands) > 0:
            brand = brands[0]
            matchingBrand = self.env['product.brand'].search([('name', '=', brand)])
            if not matchingBrand:
                matchingBrand = self.env['product.brand'].create({
                    'name' : brand
                })
            new_product['product_brand_id'] = matchingBrand.id
        
        # Final Create/Update Decision
        if existing_product:
            existing_product.write(new_product)
            return existing_product
        else:
            return self.env['product.template'].create(new_product)