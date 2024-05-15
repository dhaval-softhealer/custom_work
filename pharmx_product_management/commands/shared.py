from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, Attribute, DataSyncMessage, Item, Product, TaxInformation
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
    if not attribute:
        attribute = self.env['product.attribute'].create({ 'name': attributeName })
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

def create_category(self, category, seller_id = None):
    newParent = {
        'name' : category,
        'seller_id': seller_id
    }
    return self.env['product.category'].create(newParent)
        

def create_sub_category(self, category, parent_category, seller_id = None):
    sub_dept_vals = {
        'parent_id' : parent_category.id,
        'name' : category,
        'seller_id': seller_id
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

def get_identifier_differences(self, alternativeItemIds: List[AlternativeID], identifiers):
    
    deltas = []
    
    for id in alternativeItemIds:
        match = [x.value for x in identifiers if x.type == id.Type]
        if len(match) == 0:
            deltas.append((0, 0, { 'type' : id.Type, 'value': id.ID}))
            
    for identifier in identifiers:
        match = [x.ID for x in alternativeItemIds if x.Type == identifier.type]
        if len(match) == 0:
            deltas.append((2, identifier.id))
            
    return deltas

def get_attribute_differences(self, Attributes: List[Attribute], attributes):
    
    deltas = []
    
    for id in Attributes:
        match = [x.value for x in attributes if x.type == id.AttributeName]
        if len(match) == 0:
            deltas.append((0, 0, { 'type' : id.AttributeName, 'value': id.AttributeValue}))
            
    for attribute in attributes:
        match = [x.AttributeValue for x in Attributes if x.AttributeName == attribute.type]
        if len(match) == 0:
            deltas.append((2, attribute.id))
            
    return deltas

def get_tax_differences(self, Taxes: List[TaxInformation], taxes):
    
    deltas = []
    
    for id in Taxes:
        match = [x.value for x in taxes if x.type == id.TaxType]
        if len(match) == 0:
            deltas.append((0, 0, { 'type' : id.TaxType, 'value': id.TaxGroupID}))
            
    for attribute in taxes:
        match = [x.TaxGroupID for x in Taxes if x.TaxType == attribute.type]
        if len(match) == 0:
            deltas.append((2, attribute.id))
            
    return deltas
