from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, DataSyncMessage, Item, Product
from odoo import fields, models
from typing import List

def update_barcodes(self, existingProduct, newBarcodes: List[AlternativeID]):
        barcode_list = []
        for newBarcode in newBarcodes:
            unlinked = False
            barcode_vals = {
                'name' : newBarcode,
            }
            if existingProduct:
                domain = [('name', '=', newBarcode)]
                currentBarcodes = self.env['product.template.barcode'].search(domain)
                for currentBarcode in currentBarcodes:
                    if barcodes_match(self, currentBarcode, barcode_vals):
                        print('barcodes match, no update required')
                    else:
                        barcode_list.append((2,currentBarcode.id))
                        unlinked = True
                if len(currentBarcodes) == 0 or unlinked == True:
                    barcode_list.append((0,0,barcode_vals))
            else:
                barcode_list.append((0,0,barcode_vals))

        return barcode_list
    
def barcodes_match(self, oldBarcode, newBarcode):
    if (
        oldBarcode.name == newBarcode['name']
    ):
        return True
    else:
        return False
    
def create_attribute_value(self, attribute, attributeValue: str):
    pack_value_vals = {
        'attribute_id' : attribute.id,
        'name' : attributeValue
    }
    return self.env['product.attribute.value'].create(pack_value_vals)

def set_attribute(self, attributeName: str, attributeValue: str, existing_product_template):
    attr_list = []
    attribute = self.env['product.attribute'].search([('name', '=', attributeName)])
    if attribute:
        attribute_value = self.env['product.attribute.value'].search([('attribute_id', '=', attribute.id),('name', '=', attributeValue)],limit=1)
        if not attribute_value:
            attribute_value = create_attribute_value(self, attribute, attributeValue)
        if existing_product_template:
            domain = [('product_tmpl_id', '=', existing_product_template.id),('attribute_id', '=', attribute.id)]
            attribute_line = self.env['product.template.attribute.line'].search(domain)                       
            if attribute_line:
                if attribute_line.value_ids.ids != [attribute_value.id]:
                    attribute_vals = {
                                'attribute_id' : attribute.id,
                                'value_ids' : attribute_value.ids
                            }
                    attr_list.append((1,attribute_line.id,attribute_vals))
            else:
                attributes_vals = {
                            'attribute_id' : attribute.id,
                            'value_ids' : attribute_value.ids
                        }
                attr_list.append((0,0,attributes_vals))
        else:
            attributes_vals = {
                        'attribute_id' : attribute.id,
                        'value_ids' : attribute_value.ids
                    }
            attr_list.append((0,0,attributes_vals))
    else:
        raise Exception("Attribute (not attribute value) does not exist. Ensure {attributeName}. Exiting.")
    if attr_list:
        return attr_list

def create_category(self, category):
    newParent = {
        'name' : category
    }
    return self.env['product.category'].create(newParent)
        

def create_sub_category(self, category, parent_category):
    sub_dept_vals = {
        'parent_id' : parent_category.id,
        'name' : category
    }
    return self.env['product.category'].create(sub_dept_vals)

def update_supplier_barcodes(self, existingProduct, barcodes: List[str]):
    barcode_list = []
    for bar in barcodes:
        barcode_vals = {                    
            'name' : bar
        }
        if existingProduct:
            product = self.env['product.product'].search([('product_tmpl_id', '=', existingProduct.id)])
            domain = [('product_id', '=', product.id), ('name', '=', bar)]
            find_barcode = self.env['product.template.barcode'].search(domain)
            if not find_barcode:
                barcode_list.append((0,0,barcode_vals))
        else:
            barcode_list.append((0,0,barcode_vals))
    return barcode_list
