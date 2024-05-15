from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, Attribute, DataSyncMessage, Item, Product
from odoo import fields, models
from .shared import create_category, create_sub_category, create_attribute_value, get_attribute_differences, get_identifier_differences, get_tax_differences, update_barcodes, set_attribute
from typing import List

def create_product(self, product: Product, fields=None):
        domain = [('default_code', '=', product.ProductID)]
        existing_product = self.env['product.template'].with_context(active_test=False).search(domain)

        new_product = {
            'name' : product.Display.Description.Text if product.Display.Description else False,
            'shelf_label' : product.Display.ShelfLabel.Text if product.Display.ShelfLabel else False,
            'default_code' : product.ProductID if product else False,
            'taxes_id' : False,
            'active': True if product.StatusCode == "Active" else False,
            'attribute_line_ids' : [],
            'list_price': 0.00,
            'type': "consu",
            'identifier_ids': get_identifier_differences(self, (product.AlternativeProductIDs or []), existing_product.identifier_ids if existing_product else []),
            'attribute_ids': get_attribute_differences(self, (product.ProductAttributes or []), existing_product.attribute_ids if existing_product else []),
            'tax_ids': get_tax_differences(self, (product.TaxInformation or []), existing_product.tax_ids if existing_product else []),
        }

        # find_manufacturer = self.env['cis.manufacturer'].search([('manufacturer_id', '=', product.ManufacturerInformation.Manufacturer.SiteID)])
        # if find_manufacturer:
        #     new_product['cis_manufacturer_id'] = find_manufacturer.id
        
        # Category ID
        department = [x for x in product.MerchandiseHierarchy if x.Level == "Department"][0]
        subDepartment = [x for x in product.MerchandiseHierarchy if x.Level == "SubDepartment"][0]
        if department:
            domain = [('name', '=', department.Value), ('seller_id', '=', False)]
            department_categories = self.env['product.category'].search(domain)
            if department_categories:
                department_category = department_categories[0]
            else:
                department_category = create_category(self, department.Value)
            if subDepartment:
                domain = [('name', '=', subDepartment.Value), ('parent_id', '=', department_category.ids[0]), ('seller_id', '=', False)]
                subdepartment_categories = self.env['product.category'].search(domain)
                if subdepartment_categories:
                    new_product['categ_id'] = subdepartment_categories[0].id
                else:
                    subdepartment_category = create_sub_category(self, subDepartment.Value, department_category)
                    new_product['categ_id'] = subdepartment_category.id
        else:
            domain = [('name', '=', "Unknown")]
            unknown_category = self.env['product.category'].search(domain)
            if unknown_category:
                new_product['categ_id'] = unknown_category[0].id
            else:
                unknown_category = create_category(self, "Unknown")
                new_product['categ_id'] = unknown_category.id

        # We dont have the superseded by attribute in the messages...        
        # # Merged Products
        # if product.Merge_Product_Id:
        #     product_vals['is_merged'] = True
        #     domain = [('cis_product_id', '=', product.Merge_Product_Id), '|', ('active', '=', True), ('active', '=', False)]
        #     find_merged_product = self.env['product.template'].with_context(active_test=False).search(domain)
        #     if find_merged_product:
        #         product_vals['merged_product_id'] = find_merged_product.id
        
        # # Barcodes
        # if product.AlternativeProductIDs:
        #     barcodes = list(set([x.ID for x in product.AlternativeProductIDs if x.Type in ["UPC", "EAN", "GTIN"]])) # Need to get rid of duplicates barcodes.
        #     if len(barcodes) > 0:
        #         # AS: Commented out (multiple barcode error, debugging, should only be one barcode per global product.)
        #         #product_vals['barcode'] = barcodes[0]['Barcode']
        #         barcode_list = update_barcodes(self, existing_product, barcodes)
        #         if len(barcode_list) > 0:
        #             new_product['barcode_line_ids'] = barcode_list

        # AS: Commented out for now, as we are not yet using attributes.
        # # Packaging Id
        # if product.ProductAttributes:
        #     for attribute in product.ProductAttributes:
        #         attributes = set_attribute(self, attribute.AttributeName, attribute.AttributeValue, existing_product)
        #         if attributes:
        #             new_product['attribute_line_ids'].extend(attributes)
                
        
        # Manufacturer
        if product.ManufacturerInformation:
            manufacturer = self.env['res.partner'].search([('pharmx_supplier_id', '=', product.ManufacturerInformation.Manufacturer.SiteID)])
            if not manufacturer:
                manufacturer = self.env['res.partner'].create({
                    'name' : product.ManufacturerInformation.Manufacturer.SiteName if len(product.ManufacturerInformation.Manufacturer.SiteName) > 0 else product.ManufacturerInformation.Manufacturer.SiteID,
                    'company_type': 'company',
                    'pharmx_supplier_id' : product.ManufacturerInformation.Manufacturer.SiteID
                })
            manufacturer_type = self.env['pharmx.type'].search([('name','=', 'Manufacturer')])
            if manufacturer_type.id not in manufacturer.sh_pharmx_type.ids:
                manufacturer.write({'sh_pharmx_type': [(4, manufacturer_type.id)]})
            new_product['manufacturer'] = manufacturer.id
        
        # Final Create/Update Decision
        if existing_product:
            existing_product.write(new_product)
            return existing_product
        else:
            return self.env['product.template'].create(new_product)
