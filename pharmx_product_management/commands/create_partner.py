from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, DataSyncMessage, Partner
from decimal import Decimal
from odoo import fields, models
from datetime import datetime
from typing import List
from dateutil import parser
from .shared import create_category, create_sub_category, create_attribute_value, update_barcodes, set_attribute, update_supplier_barcodes

def create_partner(self, partner: Partner, fields=None):
        supplier = self.env['res.partner'].search([('pharmx_supplier_id', '=', partner.BusinessUnit.SiteID)])
        supplier_type = self.env['pharmx.type'].search([('name','=', 'Supplier')])
        manufacturer_type = self.env['pharmx.type'].search([('name','=', 'Manufacturer')])
        
        types = []
        if len([id for id in (partner.OrganizationTypes or []) if id.Code == "Supplier"]) > 0:
            types.append(supplier_type.id)
            
        if len([id for id in (partner.OrganizationTypes or []) if id.Code == "Manufacturer"]) > 0:
            types.append(manufacturer_type.id)
        
        if not supplier:
            print('create supplier')
            
            supplier = self.env['res.partner'].create({
                'name' : partner.BusinessUnit.SiteName if len(partner.BusinessUnit.SiteName) > 0 else partner.BusinessUnit.SiteID,
                'company_type': 'company',
                'pharmx_supplier_id' : partner.BusinessUnit.SiteID,
                'pharmx_site_id' : partner.BusinessUnit.SiteID,
                'sh_pharmx_type': types
            })
        else:
            if supplier_type.id not in supplier.sh_pharmx_type.ids:
                supplier.write({'sh_pharmx_type': [(4, supplier_type.id)]})
            if manufacturer_type.id not in supplier.sh_pharmx_type.ids:
                supplier.write({'sh_pharmx_type': [(4, manufacturer_type.id)]})