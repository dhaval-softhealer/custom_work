import math
from odoo import models, fields, api
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, Attribute, BusinessUnit, Description, Display, Eligibility, Item, ManufacturerInformation, MerchandiseHierarchy, Price, PriceMaintenance, Product, TaxInformation, ThresholdQuantity

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    pricelist_type = fields.Selection(selection=[
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
    ], string="Applied on")
    partner_id = fields.Many2one("res.partner", string="Partner")
    allowed_partner_ids = fields.Many2many("res.partner", string="Allowed Partner List")

class ProductPriceListItem(models.Model):
    _inherit = 'product.pricelist.item'
    
    supplier_info = fields.Many2one("product.supplierinfo", "Supplier Code", domain="[('product_tmpl_id', '=', product_tmpl_id)]", index=True)
    supplier_code = fields.Char(related="supplier_info.product_code", string="Supplier Code")
    supplier_name = fields.Char(related="supplier_info.product_name", string="Supplier Name")
    price_code = fields.Char(string="Price Code")
    allowed_partner_ids = fields.Many2many(related="pricelist_id.allowed_partner_ids", string="Allowed Partner List")
    cached_price = fields.Char(string='Cached Price')
    pharmx_code = fields.Char('PharmX Code', readonly=True, default=None)

    def get_price(self):
        return PriceMaintenance(
            PriceID = self.price_code,
            ItemID = self.supplier_info.product_code,
            RequestType = "Add",
            SupplierID = str(self.supplier_info.name.pharmx_site_id),
            Supplier = BusinessUnit(
                SiteID = self.supplier_info.name.pharmx_site_id,
                SiteName = self.supplier_info.name.name
            ),
            AlternativeSupplierIDs = [
                AlternativeID(
                    Type = id.type,
                    ID = id.value
                )
                for id
                in self.supplier_info.name.identifier_ids
            ],
            AlternativeItemIDs = [
                AlternativeID(
                    Type = id.type,
                    ID = id.value
                )
                for id
                in self.supplier_info.identifier_ids
            ],
            ItemPrice = Price(
                Currency = self.currency_id.name,
                ValueTypeCode = "UnitListPrice",
                Amount = self.fixed_price,
                Eligibility = Eligibility(
                    ThresholdQuantity= ThresholdQuantity(
                        Units = math.floor(self.min_quantity),
                        UnitOfMeasureCode = 'EA'
                    )
                ),
                EffectiveDateTimestamp = self.date_start if self.date_start else None,
                ExpirationDateTimestamp = self.date_end if self.date_end else None
            )
        )
    
    # on create method (PharmX Code)
    @api.model
    def create(self, vals):
        obj = super(ProductPriceListItem, self).create(vals)
        if not obj.pharmx_code:
            number = self.env['ir.sequence'].get('pharmx.code') or None
            obj.write({'pharmx_code': number})
        return obj
    
    # on button click event (PharmX Code)
    def submit_application(self):
        if not self.pharmx_code:
            sequence_id = self.env['ir.sequence'].search([('code', '=', 'pharmx.code')])
            sequence_pool = self.env['ir.sequence']
            pharmx_code = sequence_pool.sudo().get_id(sequence_id.id)
            self.write({'pharmx_code': pharmx_code})