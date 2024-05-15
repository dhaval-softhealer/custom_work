from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, DataSyncMessage, Item, Product, Return
from odoo import fields, models
from typing import List

def resolveProduct(self, company, itemID: str, alternativeItemIDs: List[AlternativeID]):
    product = None
    
    # First look for an organisation product
    upi = searchForAlternativeID("UPI", alternativeItemIDs)
    if (upi != None):
        product = self.env['product.product'].search([('company_id', '!=', None), ('cis_upi', '=', upi)])
    
    hoid = searchForAlternativeID("HOID", alternativeItemIDs)
    if (not product and hoid != None):
        product = self.env['product.product'].search([('company_id', '!=', None), ('default_code', '=', hoid)])
    
    barcodes = searchForAlternativeIDs("GTIN", alternativeItemIDs) + searchForAlternativeIDs("UPC", alternativeItemIDs) + searchForAlternativeIDs("EAN", alternativeItemIDs)
    for barcode in barcodes:
            if (not product):
                barcode = self.env['product.template.barcode'].search([('name', '=', barcode)])
                if not barcode:
                    product = barcode.product_id
    
    # If none exist create a company product
    if not product:
        product = self.env['product.product'].search([('company_id', '=', company.id), ('default_code', '=', itemID)])

    return product

def searchForAlternativeIDs(searchTerm : str, alternativeIDs : List[AlternativeID]):
    return [ x.ID for x in alternativeIDs if x.Type == searchTerm]

def searchForAlternativeID(searchTerm : str, alternativeIDs : List[AlternativeID]):
    matchingTerms = [ x.ID for x in alternativeIDs if x.Type == searchTerm]
    
    if len(matchingTerms) == 1:
        return matchingTerms[0]
    else:
        return None
    
def createProduct(self, company, name: str, itemID: str, type: str, AlternativeItemIDs: List[AlternativeID]):
        
    barcodes = [ (0, 0, { 'name': x.ID }) for x in AlternativeItemIDs if x.Type == "GTIN" or  x.Type == "UPC" or  x.Type == "EAN"]
    product = {
        'name' : name,
        'categ_id' : 1, # Needs to be some kind of resolve or create category method.
        'detailed_type': type, 
        'product_variant_ids': [],
        'uom_id': 1, # Probably best to have a resolving strategy here.
        'uom_po_id': 1, # Probably best to have a resolving strategy here.
        'company_id': company.id,
        'barcode_line_ids': barcodes,
        'default_code': itemID,
        'cis_upi': [ x.ID for x in AlternativeItemIDs if x.Type == "UPI"]
    }
    
    product = self.env['product.template'].create(product)
        
    return product
