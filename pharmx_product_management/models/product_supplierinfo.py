from odoo import api, models, fields

from ...pharmx_edi.dataclasses.datasyncmessage import Availability, AlternativeID, Attribute, BusinessUnit, Description, Display, Item, ManufacturerInformation, MerchandiseHierarchy, Price, Product, TaxInformation

class ProductInherit(models.Model):
    _inherit = 'product.supplierinfo'
    
    # categ_id = fields.Many2one(
    #     comodel_name='product.category',
    #     string='Product Category',
    #     change_default=True,
    #     group_expand='_read_group_categ_id',
    #     required=True,
    #     help="Select category for the current product"
    # ) # Needs a domain filter for seller categories only.
    
    active = fields.Boolean(string="Active", default=True)
    pharmx_code = fields.Char('PharmX Code', readonly=True, default=None)
    product_code = fields.Char("Internal Reference", index=True)
    min_order_qty = fields.Integer("Minimum Order Quantity")
    order_multiple = fields.Integer("Order Multiple")
    shelf_pack = fields.Integer("Shelf Pack")
    items_per_box = fields.Integer("Items per box")
    rrp = fields.Float('Suppliers Recommended Retail Price', digits='Product Price', required=False, default=0.0)
    department = fields.Char(string="Suppliers Department")
    subdepartment = fields.Char(string="Suppliers SubDepartment")
    brand = fields.Char(string="Brand")
    prices = fields.One2many("product.pricelist.item", "supplier_info", "Supplier Code", domain="[('product_tmpl_id', '=', product_tmpl_id)]")
    identifier_ids = fields.One2many('product.identifier', 'supplierinfo_id', 'Identifiers', index=True)
    attribute_ids = fields.One2many('product.pharmx.attribute', 'supplierinfo_id', 'Attributes', index=True)
    tax_ids = fields.One2many('product.tax', 'supplierinfo_id', 'Taxes', index=True)
    availability = fields.One2many('product.availability', 'supplierinfo_id', 'Availability', index=True)
    discontinued_date = fields.Date(string='Discontinued Date')
    superseded_by = fields.Char(string='Superseded By')

    _sql_constraints = [
        (
            'unique_product_code',
            'unique(name, product_code)',
            'For a given supplier, the product code must be unique.'
        )
    ]

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(['product_name', 'product_code'])
        return [(template.id, '%s%s' % (template.product_code and '[%s] ' % template.product_code or '', template.product_name))
                for template in self]
    
    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.product_tmpl_id:
            record.product_tmpl_id.recompute_product_by_data_fusion()
        return record

    def write(self, vals):
        res = super().write(vals)
        if self.product_tmpl_id:
            self.product_tmpl_id.recompute_product_by_data_fusion()
        return res

    def get_item(self):
        item = Item(
            ItemID = str(self.product_code),
            SupplierID = str(self.name.pharmx_site_id),
            Supplier = BusinessUnit(
                SiteID = self.name.pharmx_site_id,
                SiteName = self.name.name
            ),
            AlternativeSupplierIDs = [
                AlternativeID(
                    Type = id.type,
                    ID = id.value
                )
                for id
                in self.name.identifier_ids
            ],
            StatusCode = 'Active', #if record.active else 'Discontinued',
            AlternativeItemIDs = [
                AlternativeID(
                    Type = id.type,
                    ID = id.value
                )
                for id
                in self.identifier_ids
            ],
            ItemAttributes = [
                Attribute(
                    AttributeName = id.type,
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
                        Value = self.subdepartment
                    )
                ] if self.subdepartment else []
            )
            + 
            (
                [
                    MerchandiseHierarchy(
                        Level = "Department",
                        Value = self.department
                    )
                ] if self.department else []
            ),
            ItemPrice = 
                [
                    Price(
                        ValueTypeCode = 'RegularSalesUnitPrice',
                        Amount = self.rrp
                    ) 
                ] if self.rrp else []
            ,
            SupplierInformation = None,
            ManufacturerInformation = None,
            TaxInformation = [
                TaxInformation(
                    TaxType = id.type,
                    TaxGroupID = id.value,
                    TaxPercent =  10.0 if id.value == "Yes" or id.value == "No" else 0.00,
                )
                for id
                in self.tax_ids
            ],
            Availability = [
                Availability(
                    StatusCode = id.availability,
                    WarehouseID = id.warehouse_id.name if id.warehouse_id.id != False else None,
                    Region =  id.state,
                    Country = 'AUS',
                )
                for id
                in self.availability
            ],
            Display = Display(
                Description= Description(
                    Text = self.product_name
                ),
            ),
            Product = self.product_tmpl_id.get_product(),
            SalesUnitPerPackUnitQuantity = self.shelf_pack,
            ItemQuantityPerSalesUnit = self.items_per_box,
            OrderQuantityMinimum = self.min_order_qty,
            OrderQuantityMaximum = None,
            OrderQuantityMultiple = self.order_multiple
        )

        return item

    # on create method (PharmX Code)
    @api.model
    def create(self, vals):
        obj = super(ProductInherit, self).create(vals)
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