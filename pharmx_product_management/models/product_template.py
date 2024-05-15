from odoo import api, fields, models
from ...pharmx_edi.dataclasses.datasyncmessage import AlternativeID, Attribute, BusinessUnit, Description, Display, ManufacturerInformation, MerchandiseHierarchy, Product, TaxInformation
from collections import Counter

class ProductInherit(models.Model):
    _inherit = 'product.template'

    upi = fields.Char(string='Universal Product Identifier', required=False)
    rrp = fields.Float('Recommended Retail Price', digits='Product Price', required=False, default=0.0)
    shelf_label = fields.Char(string='Shelf Label', required=False)
    
    # Merged fields
    is_merged = fields.Boolean("Merged")
    merged_product_id = fields.Many2one('product.template', string="Merged Product Id", index=True)
    
    # barcode_line_ids = fields.One2many(
    #     related='seller_ids.barcode_line_ids',
    #     readonly=False,
    #     ondelete='cascade')
    
    identifier_ids = fields.One2many('product.identifier', 'product_template_id', 'Identifiers', index=True)
    attribute_ids = fields.One2many('product.pharmx.attribute', 'product_template_id', 'Attributes', index=True)
    tax_ids = fields.One2many('product.tax', 'product_template_id', 'Taxes', index=True)
    default_code = fields.Char('PharmX Code', readonly=True, default=None)

    _sql_constraints = [
        (
            'unique_default_code',
            'unique(default_code)',
            'The default code must be Unique.'
        )
    ]

    # vendor_ids = fields.One2many(
    #     related='seller_ids.name',
    #     readonly=False,
    #     ondelete='cascade')
    

    # # Seller Fields
    # seller_id = fields.Many2one('res.partner', string="Seller Id", index=True)
    # is_seller_product = fields.Boolean("Is Seller Product")
    # seller_product_ids = fields.One2many(
    #     string="Seller Products",
    #     comodel_name="product.template",
    #     inverse_name="global_product_tmpl_id",
    #     help=""
    # )
    # global_product_tmpl_id = fields.Many2one(
    #     string="Global Product",
    #     comodel_name="product.template",
    #     domain=[('is_seller_product', '=', False)],
    #     help="Related Global product.",
    # )

    def basic_voting_scheme(self, lst):
        """
        Function to return the most frequent element in the list.
        """
        # Use Counter to count the frequency of each item, 
        # then take the most common one.
        return Counter(lst).most_common(1)[0][0]
    
    def flatten_list(self, nested_list):
        return [item for sublist in nested_list for item in sublist]
    
    def fuse_barcodes(self):
        identifier_sets = [item.identifier_ids for item in self.seller_ids]
        identifiers = []
        for identifier_set in identifier_sets:
            for identifier in sorted(identifier_set, key=lambda item: item.sequence):
                if identifier.type == "GTIN":
                    identifiers.append(identifier.value)
                    break # this means we will only get the highest ranked gtin

        # Here I am grouping the identifiers, and then sorting by count.
        count = Counter(identifiers)
        sorted_identifiers = sorted(count, key=count.get, reverse=True)

        return [(0, 0, {'type': 'GTIN', 'value': barcode, 'sequence': sequence}) for sequence, barcode in enumerate(sorted_identifiers, start=1)]
    
    def fuse_attributes(self):
        attribute_sets = [item.attribute_ids for item in self.seller_ids]
        attribute_types = ["ScheduleCode", "ManufacturerName", "BrandName"]
        attributes = []
        for attribute_type in attribute_types:
            attribute_group = []
            for attribute_set in attribute_sets:
                for attribute in attribute_set:
                    if attribute.type == attribute_type:
                        attribute_group.append(attribute.value)
            if len(attribute_group) > 0:
                attributes.append({ "type": attribute_type, "value": self.basic_voting_scheme(attribute_group)})
            

        return [(0, 0, {'type': attribute['type'], 'value': attribute['value']}) for attribute in attributes]
    
    def fuse_taxes(self):
        tax_sets = [item.tax_ids for item in self.seller_ids]
        tax_types = ["GST"]
        taxes = []
        for tax_type in tax_types:
            tax_group = []
            for tax_set in tax_sets:
                for tax in tax_set:
                    if tax.type == tax_type:
                        tax_group.append(tax.value)
            if len(tax_group) > 0:
                taxes.append({ "type": tax.type, "value": self.basic_voting_scheme(tax_group)})

        return [(0, 0, {'type': attribute['type'], 'value': attribute['value']}) for attribute in taxes]

    # Data Fusion related to the process of taking several perspectives of the same data (items) and combining them into a higher quality perspective (product)
    @api.depends('seller_ids')
    def recompute_product_by_data_fusion(self):
        # Update Object
        updated_vals = {
            'name': self.basic_voting_scheme([item.product_name for item in self.seller_ids]),
            'identifier_ids': self.fuse_barcodes(),
            'attribute_ids': self.fuse_attributes(),
            'tax_ids': self.fuse_taxes()
        }

        # Remove Existing Links
        self.identifier_ids.unlink()
        self.attribute_ids.unlink()
        self.tax_ids.unlink()

        # Update Product
        self.write(updated_vals)

    def get_product(self):
        product = Product(
            ProductID = str(self.default_code),
            StatusCode = 'Active' if self.active else 'Discontinued',
            AlternativeProductIDs = [
                AlternativeID(
                    Type = id.type,
                    ID = id.value
                )
                for id
                in self.identifier_ids
            ],
            ProductAttributes = [
                Attribute(
                    AttributeName= id.type,
                    AttributeValue = id.value
                )
                for id
                in self.attribute_ids
            ],
            MerchandiseHierarchy = []
            +
            (
                [
                    MerchandiseHierarchy(
                        Level = "SubDepartment",
                        Value = self.categ_id.name
                    )
                ] if self.categ_id else []
            )
            + 
            (
                [
                    MerchandiseHierarchy(
                        Level = "Department",
                        Value = self.categ_id.parent_id.name
                    )
                ] if self.categ_id and self.categ_id.parent_id.name else []
            ),
            ProductPrice =  [],
            ManufacturerInformation = ManufacturerInformation(
                Manufacturer = BusinessUnit(
                    SiteID = self.manufacturer.pharmx_site_id,
                    SiteName = self.manufacturer.name,
                )
            ) if self.manufacturer else None,
            TaxInformation = [
                TaxInformation(
                    TaxType = id.type,
                    TaxGroupID = id.value,
                    TaxPercent =  10.0 if id.value == "Yes" or id.value == "No" else 0.00,
                )
                for id
                in self.tax_ids
            ],
            Display = Display(
                Description= Description(
                    Text = (self.name or '').strip()[:100]
                ),
                ShelfLabel= Description(
                    Text = (self.shelf_label or '').strip()[:100] or None
                ) if len((self.shelf_label or '').strip()) <= 40 else None,
            ),
        )

        return product

    # on create method (PharmX Code)
    @api.model
    def create(self, vals):
        obj = super(ProductInherit, self).create(vals)
        if not obj.default_code:
            number = self.env['ir.sequence'].get('pharmx.code') or None
            obj.write({'default_code': number})
        return obj
    
    # on button click event (PharmX Code)
    def submit_application(self):
        if not self.default_code:
            sequence_id = self.env['ir.sequence'].search([('code', '=', 'pharmx.code')])
            sequence_pool = self.env['ir.sequence']
            default_code = sequence_pool.sudo().get_id(sequence_id.id)
            self.write({'default_code': default_code})