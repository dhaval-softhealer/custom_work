from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, DataSyncMessage, Item, Product
from odoo import fields, models
from .shared import create_category, create_sub_category, create_attribute_value, update_barcodes, set_attribute

def remap_product(self, existing_product, fields=None):

        mappingrules = self.env['product.category.mappingrule']
        updated_product = {}
        
        # Product Mapping Rules
        department = existing_product.cis_department
        subDepartment = existing_product.cis_subdepartment
        if department and subDepartment:
            print('found.')
            domain = [('type', '=', 'cis'), ('partner', '=', False), ('department', '=', department), ('subdepartment', '=', subDepartment)]
            product_mappingrules = self.env['product.category.mappingrule'].search(domain, limit=1, order="sequence asc")
            mappingrules |= product_mappingrules
        
        # Supplier Mapping Rules
        domain = [('product_tmpl_id', '=', existing_product.id)]
        supplierinformation = self.env['product.supplierinfo'].search(domain)
        for supplierinfo in supplierinformation:
            domain = [('type', '=', 'supplier'), ('partner', '=', supplierinfo.name.id), ('department', '=', supplierinfo.department), ('subdepartment', '=', supplierinfo.subdepartment)]
            supplier_mappingrules = self.env['product.category.mappingrule'].search(domain, limit=1, order="sequence asc")
            if len(supplier_mappingrules) > 0:
                mappingrules |= supplier_mappingrules
                
        # Resort
        mappingrules.sorted(key=lambda x: x.sequence)

        if len(mappingrules) > 0:

            # Remap Product Name
            namingrule = mappingrules.filtered(lambda r: r.map_product_names == True).sorted(key=lambda x: x.sequence)
            if len(namingrule) > 0:
                supplierinfo = supplierinformation.filtered(lambda r: r.name == namingrule.partner)
                if len(supplierinfo) > 0:
                    updated_product['name'] = supplierinfo[0].product_name

            # Remap Category
            category = mappingrules.filtered(lambda r: r.map_categories == True).sorted(key=lambda x: x.sequence)
            if len(category) > 0:
                updated_product['pos_categ_id'] = category[0].pos_category.id

            # Remap RRP
            rrprules = mappingrules.filtered(lambda r: r.map_rrp == True).sorted(key=lambda x: x.sequence)
            for rrprule in rrprules:
                supplierinfo = supplierinformation.filtered(lambda r: r.name == rrprule.partner)
                if len(supplierinfo) > 0:
                    updated_product['list_price'] = supplierinfo[0].rrp
                    break
                
            # Remap GST Status
            gstrules = mappingrules.filtered(lambda r: r.map_gst_status == True).sorted(key=lambda x: x.sequence)
            for gstrule in gstrules:
                supplierinfo = supplierinformation.filtered(lambda r: r.name == gstrule.partner)
                if len(supplierinfo) > 0:
                    gst = supplierinfo[0].gst_status
                    break
            if not gst:
                gst = existing_product.cis_gststatus
            
            if gst:
                if  gst == 'Yes':
                    domain = [('name', 'ilike', "GST"), ('type_tax_use', '=', 'sale')]
                    find_tax = self.env['account.tax'].search(domain)
                    if find_tax:
                        updated_product['taxes_id'] = find_tax.ids
                    else:
                        updated_product['taxes_id'] = False

                if gst == 'Yes' or gst == 'Free':
                        domain = [('name', 'ilike', "GST"), ('type_tax_use', '=', 'purchase')]
                        find_tax = self.env['account.tax'].search(domain)
                        if find_tax:
                            updated_product['supplier_taxes_id'] = find_tax.ids
                        else:
                            updated_product['supplier_taxes_id'] = False
        else:
            print('no mapping rules found.')
        
        existing_product.write(updated_product)
