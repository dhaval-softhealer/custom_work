import base64
from logging import raiseExceptions
from tempfile import TemporaryFile
from types import SimpleNamespace
from typing import List
from odoo import models, fields, api
import tempfile
from ..dataclasses.migration import Brand, Migration, Operator, Partner, AlternativeID, Manufacturer, MerchandiseHierarchy, Item, Attribute, RetailTransaction,Order
import dateutil.parser

import json
    
class MigrationModel(models.Model):
    _name = 'corum.migration'
    
    READONLY_STATES = {
        'importing': [('readonly', True)],
        'complete': [('readonly', True)]
    }
    
    name = fields.Char(string="Migration Name")
    source = fields.Char(string="Source System")
    company_id = fields.Many2one('res.company', string='Company', required=True)
    state = fields.Selection([
        ('new', 'New'),
        ('mapping', 'Mapping'),
        ('importing', 'Importing'),
        ('complete', 'Complete')
    ], string='Status', readonly=True, index=True, copy=False, default='new', tracking=True)
    
    data_file = fields.Binary(states=READONLY_STATES)
    
    record_count = fields.Integer(string="records", readonly=True, index=False, store=True)
    succesful_record_count = fields.Integer(compute="_computed_succesful_record_count", index=False, store=True)
    failed_record_count = fields.Integer(compute="_computed_failed_record_count", index=False, store=True)
    
    # Mapping
    employee_mapping_rules = fields.One2many("corum.migration.employee.mapping", "migration_id", string="Employee Mapping Rules", states=READONLY_STATES)
    supplier_mapping_rules = fields.One2many("corum.migration.supplier.mapping", "migration_id", string="Supplier Mapping Rules", states=READONLY_STATES)
    brand_mapping_rules = fields.One2many("corum.migration.brand.mapping", "migration_id", string="Brand Mapping Rules", states=READONLY_STATES)
    manufacturer_mapping_rules = fields.One2many("corum.migration.manufacturer.mapping", "migration_id", string="Manufacturer Mapping Rules", states=READONLY_STATES)
    category_mapping_rules = fields.One2many("corum.migration.category.mapping", "migration_id", string="Category Mapping Rules", states=READONLY_STATES)
    customer_mapping_rules = fields.One2many("corum.migration.customer.mapping", "migration_id", string="Customer Mapping Rules", states=READONLY_STATES)
    item_mapping_rules = fields.One2many("corum.migration.item.mapping", "migration_id", string="Item Mapping Rules", states=READONLY_STATES)
    
    # Non-Mapped
    retail_transactions = fields.One2many("corum.migration.retailtransaction", "migration_id", string="Retail Transactions", states=READONLY_STATES)
    purchase_orders = fields.One2many("corum.migration.purchase.order", "migration_id", string="Purchase Orders", states=READONLY_STATES)

    def _computed_record_count(self):
        return len(self.employee_mapping_rules)
    
    def _computed_succesful_record_count(self):
        return 0
    
    def _computed_failed_record_count(self):
        return 0
    
    def process_file(self):
        
        #read file
        jsonData = base64.b64decode(self['data_file'])
        migration : Migration = json.loads(jsonData, object_hook=lambda d: SimpleNamespace(**d))
        
        updateValues = {
            "state": "mapping",
            "record_count": len(migration.Employees),
            "employee_mapping_rules": self.map_employees(migration.Employees),
            "supplier_mapping_rules": self.map_suppliers(migration.Suppliers),
            "brand_mapping_rules": self.map_brands(migration.Brands),
            "manufacturer_mapping_rules": self.map_manufacturers(migration.Manufacturers),
            "category_mapping_rules": self.map_categories(migration.Categories),
            "customer_mapping_rules": self.map_customers(migration.Customers),
            "item_mapping_rules": self.map_items(migration.Items),
            "retail_transactions": self.map_retailtransactions(migration.RetailTransactions),
            "purchase_orders": self.map_purchaseorders(migration.PurchaseOrders),
        }
    
        self.write(updateValues)
        
    def import_migration(self):
        
        jsonData = base64.b64decode(self['data_file'])
        migration : Migration = json.loads(jsonData, object_hook=lambda d: SimpleNamespace(**d))
        
        self.import_employees(migration.Employees, self.employee_mapping_rules)
        self.import_suppliers(migration.Suppliers, self.supplier_mapping_rules)
        self.import_brands(migration.Brands, self.brand_mapping_rules)
        self.import_manufacturers(migration.Manufacturers, self.manufacturer_mapping_rules)
        self.import_categories(migration.Categories, self.category_mapping_rules)
        self.import_customers(migration.Customers, self.customer_mapping_rules)
        self.import_items(migration.Items, self.item_mapping_rules)
        self.import_retailtransactions(migration.RetailTransactions, self.retail_transactions)
        self.import_purchaseorders(migration.PurchaseOrders, self.purchase_orders, self.supplier_mapping_rules, self.item_mapping_rules)

        updateValues = {
            "state": "complete"
        }
    
        self.write(updateValues)
        
        
        
    def map_employees(self, employees: List[Operator]):
        
        mappingRules = []
        
        for employee in employees:
            
            user = self.env['res.users'].search([('email', '=', employee.Email)])
            
            mappingRule = {
                'name': employee.Name,
                'email': employee.Email,
                'code': employee.ID,
                'target_create': not user,
                'target': user.id if user else None
            }
            
            #self.employee_mapping_rules.add(mappingRule) 
             
            mappingRules.append((0, 0, mappingRule))
        
        return mappingRules
    
    def map_suppliers(self, suppliers: List[Partner]):
        
        mappingRules = []
        
        for supplier in suppliers:
            
            domain = [
                '|',
                ('vat', '=', self.searchForAlternativeID("ABN", supplier.AlternateBusinessIDs)),
                '|',
                ('asx', '=', self.searchForAlternativeID("ASX", supplier.AlternateBusinessIDs)),
                ('pharmx_supplier_id', '=', supplier.BusinessUnit.SiteID),
            ]
            
            partner = self.env['res.partner'].search(domain, limit=1)
            
            mappingRule = {
                'name': supplier.Name,
                'abn': self.searchForAlternativeID("ABN", supplier.AlternateBusinessIDs),
                'asx': self.searchForAlternativeID("ASX", supplier.AlternateBusinessIDs),
                'pharmx_supplier_id': supplier.BusinessUnit.SiteID,
                'code': supplier.ID,
                'target_create': not partner,
                'target': partner.id if partner else None
            }

            mappingRules.append((0, 0, mappingRule))
        
        return mappingRules
    
    def map_customers(self, customers: List[Partner]):
        
        mappingRules = []
        
        for customer in customers:
            
            domain = [
                ('email', '=', customer.ContactInformation.Email),
                ('phone', '=', customer.ContactInformation.Telephone),
            ]
            
            partner = self.env['res.partner'].search(domain, limit=1)
            
            mappingRule = {
                'name': customer.Name,
                'email': customer.ContactInformation.Email,
                'phone': customer.ContactInformation.Telephone,
                'code': customer.ID,
                'target_create': not partner,
                'target': partner.id if partner else None
            }

            mappingRules.append((0, 0, mappingRule))
        
        return mappingRules
    
    def map_brands(self, brands: List[Brand]):
        
        mappingRules = []
        
        for brand in brands:
            
            domain = [
                ('name', '=', brand.Name),
            ]
            
            existingBrand = self.env['product.brand'].search(domain, limit=1)
            
            mappingRule = {
                'name': brand.Name,
                'target_create': not existingBrand,
                'target': existingBrand.id if existingBrand else None
            }

            mappingRules.append((0, 0, mappingRule))
        
        return mappingRules
    
    def map_manufacturers(self, manufacturers: List[Manufacturer]):
        
        mappingRules = []
        
        for manufacturer in manufacturers:
            
            domain = [
                ('name', '=', manufacturer.Name),
            ]
            
            existingManufacturer = self.env['res.partner'].search(domain, limit=1)
            
            mappingRule = {
                'name': manufacturer.Name,
                'target_create': not existingManufacturer,
                'target': existingManufacturer.id if existingManufacturer else None
            }

            mappingRules.append((0, 0, mappingRule))
        
        return mappingRules
    
    def map_categories(self, categories: List[MerchandiseHierarchy]):
        
        mappingRules = []
        
        for category in [category for category in categories if category.Level == "SubDepartment"]:
            
            domain = [
                ('name', '=', category.Value),
            ]
            
            existingCategory = self.env['product.category'].search(domain, limit=1)
            
            mappingRule = {
                'name': category.Value,
                'parent': category.ParentValue,
                'target_create': not existingCategory,
                'target': existingCategory.id if existingCategory else None
            }

            mappingRules.append((0, 0, mappingRule))
        
        return mappingRules
    
    def map_items(self, items: List[Item]):
        
        mappingRules = []
        
        for item in items:
            
            barcodes = self.searchForAlternativeIDs("GTIN", item.AlternativeItemIDs)
            
            domain = [
                ('barcode', 'in', barcodes),
            ]
            
            existingItem = self.env['product.template'].search(domain, limit=1)
            
            mappingRule = {
                'label':  item.Display.ShelfLabel.Text,
                'barcode': self.searchForAlternativeID("GTIN", item.AlternativeItemIDs),
                'brand': self.searchForAlternativeAttribute("BrandName", item.ItemAttributes),
                'code': item.ItemID,
                'target_create': not existingItem,
                'target': existingItem.id if existingItem else None
            }

            mappingRules.append((0, 0, mappingRule))
        
        return mappingRules
    
    def map_retailtransactions(self, retailTransactions: List[RetailTransaction]):
        
        mappingRules = []
        
        for retailTransaction in retailTransactions:                                    

            sale = {
                'date_order' : dateutil.parser.isoparse(retailTransaction.DateTime).replace(tzinfo=None),
                'amount_total' : retailTransaction.Total.Amount,
                'amount_tax' :  sum([x.Sale.Tax.Amount for x in retailTransaction.LineItems if hasattr(x, "Sale") and hasattr(x.Sale, "Tax")]),
                'amount_paid' : sum([x.Tender.Amount for x in retailTransaction.LineItems if hasattr(x, "Tender")]),
                'amount_return' : sum([x.Tender.Cashback for x in retailTransaction.LineItems if hasattr(x, "Tender")]),
                'code' :  retailTransaction.TransactionID,
            }

            mappingRules.append((0, 0, sale))
        
        return mappingRules

    def map_purchaseorders(self, purchaseorders : List[Order]):

        mappingRules = []

        for purchaseorder in purchaseorders:            
            purchase = {
                'date_order' : dateutil.parser.isoparse(purchaseorder.DateTime).replace(tzinfo=None),
                'amount_tax' : sum([x.UnitCount * x.Tax.Amount for x in purchaseorder.LineItem if hasattr(x, "Tax")]),
                'amount_untaxed' : sum([x.UnitCount * x.UnitBaseCostAmount for x in purchaseorder.LineItem]),
                'amount_total' : sum([(x.UnitCount * x.UnitBaseCostAmount) if x.TaxIncludedInPriceFlag == 'true' else x.UnitCount * (x.UnitBaseCostAmount + x.Tax.Amount) for x in purchaseorder.LineItem]),
                'code' :  purchaseorder.DocumentID,
            }
            mappingRules.append((0, 0, purchase))

        return mappingRules
    
    def import_employees(self, Employees : List[Operator], employeeMappingRules):
        
        for employee in Employees:
            
            # Find Map
            rule = [rule for rule in employeeMappingRules if employee.ID == rule.code]
            
            if len(rule) == 0:
                raise Exception("Employee Mapping rule not found for ID: " + str(employee.ID))
            
            if len(rule) == 1:
                rule = rule[0]
                if rule.target_create:
                    user = {
                        "name": employee.Name,
                        "email": employee.Email,
                        "login": employee.Email,
                        "company_id": self.company_id.id,
                        "company_ids": [self.company_id.id]
                    }
                    created_employee = self.env['res.users'].create(user)
                    rule.write({ 'target': created_employee.id })
                    
    def import_suppliers(self, Suppliers : List[Partner], supplierMappingRules):
        
        for supplier in Suppliers:
            
            # Find Map
            rule = [rule for rule in supplierMappingRules if supplier.ID == rule.code]
            
            if len(rule) == 0:
                raise Exception("Supplier Mapping rule not found for ID: " + str(supplier.ID))
            
            if len(rule) == 1:
                rule = rule[0]
                if rule.target_create:
                    partner = {
                        "name": supplier.Name,
                        "vat": self.searchForAlternativeID("ABN", supplier.AlternateBusinessIDs),
                        "asx": self.searchForAlternativeID("ASX", supplier.AlternateBusinessIDs),
                        "pharmx_supplier_id": supplier.BusinessUnit.SiteID,
                        "company_id": self.company_id.id
                    }
                    created_partner = self.env['res.partner'].create(partner)
                    rule.write({ 'target': created_partner.id })
                    
    def import_customers(self, Customers : List[Partner], customerMappingRules):
        
        for customer in Customers:
            
            # Find Map
            rule = [rule for rule in customerMappingRules if customer.ID == rule.code]
            
            if len(rule) == 0:
                raise Exception("Supplier Mapping rule not found for ID: " + str(customer.ID))
            
            if len(rule) == 1:
                rule = rule[0]
                if rule.target_create:
                    partner = {
                        "name": customer.Name,
                        'email': customer.ContactInformation.Email,
                        'phone': customer.ContactInformation.Telephone,
                        "company_id": self.company_id.id
                    }
                    created_partner = self.env['res.partner'].create(partner)
                    rule.write({ 'target': created_partner.id })
                    
    def import_brands(self, Brands : List[Brand], brandMappingRules):
        
        for brand in Brands:
            
            # Find Map
            rule = [rule for rule in brandMappingRules if brand.Name == rule.name]
            
            if len(rule) == 0:
                raise Exception("Brand Mapping rule not found for ID: " + str(brand.Name))
            
            if len(rule) == 1:
                rule = rule[0]
                if rule.target_create:
                    brand = {
                        "name": brand.Name
                    }
                    created_brand = self.env['product.brand'].create(brand)
                    rule.write({ 'target': created_brand.id })
                    
    def import_manufacturers(self, Manufacturers : List[Manufacturer], manufacturerMappingRules):
        
        for manufacturer in Manufacturers:
            
            # Find Map
            rule = [rule for rule in manufacturerMappingRules if manufacturer.Name == rule.name]
            
            if len(rule) == 0:
                raise Exception("Manufacturer Mapping rule not found for ID: " + str(manufacturer.Name))
            
            if len(rule) == 1:
                rule = rule[0]
                if rule.target_create:
                    manufacturer = {
                        "name": manufacturer.Name
                    }
                    created_partner = self.env['res.partner'].create(manufacturer)
                    rule.write({ 'target': created_partner.id })
                    
    def import_categories(self, Categories : List[MerchandiseHierarchy], categoryMappingRules):
        
        for category in [category for category in Categories if category.Level == "SubDepartment"]:
            
            # Find Map
            rule = [rule for rule in categoryMappingRules if category.Value == rule.name]
            
            if len(rule) == 0:
                raise Exception("Category Mapping rule not found for ID: " + str(category.Value))
            
            if len(rule) == 1:
                rule = rule[0]
                if rule.target_create:
                    category = {
                        "name": category.Level
                    }
                    created_category = self.env['product.category'].create(category)
                    rule.write({ 'target': created_category.id })
                    
    def import_items(self, Items : List[Item], itemMappingRules):
        
        for item in Items:
            
            # Find Map
            rule = [rule for rule in itemMappingRules if item.ItemID == rule.code]
            
            if len(rule) == 0:
                raise Exception("Item Mapping rule not found for ID: " + str(item.ItemID))
            
            if len(rule) == 1:
                rule = rule[0]
                if rule.target_create:
                    
                    item_vals = {
                        'name' : item.Display.Description.Text if item.Display.Description else False,
                        'default_code' : item.ItemID if item else False,
                        "barcode": self.searchForAlternativeID("GTIN", item.AlternativeItemIDs),
                        'taxes_id' : False,
                        'active': True if item.StatusCode == "Active" else False,
                        'attribute_line_ids' : [],
                        'list_price': 0.00,
                        'type': "product",
                        'company_id': self.company_id.id
                    }
                    
                    gst = [x for x in item.TaxInformation if x.TaxType == "GST"][0]
                    if gst:
                        if  gst.TaxGroupID == "Yes" :
                            item_vals['taxes_id'] = self.env['account.tax'].search([('name', '=', "Sale (10%)")]).ids
                        if gst.TaxGroupID == "Yes" or gst.TaxGroupID == "Free":
                            item_vals['supplier_taxes_id'] = self.env['account.tax'].search([('name', '=', "Purch (10%) (Goods)")]).ids
                    
                    created_item = self.env['product.template'].create(item_vals)
                    rule.write({ 'target': created_item.id })


    def import_retailtransactions(self, transactions : List[RetailTransaction], transactionMappingrule):

        for transaction in transactions:

            # Find Map
            rule = [rule for rule in transactionMappingrule if transaction.TransactionID == rule.code]

            if len(rule) == 0:
                raise Exception("Sale Mapping rule not found for ID: " + str(transaction.TransactionID))
            
            if len(rule) == 1:
                rule = rule[0]
                payment_list = []
                payment_type = [x.Tender.TenderType for x in transaction.LineItems if hasattr(x, "Tender")]
                payment_method = self.env['pos.payment.method'].search([('name', '=', payment_type[0])])
                if payment_method:
                    amount_vals = {
                        'payment_date' : dateutil.parser.isoparse(transaction.ReceiptDateTime).replace(tzinfo=None),
                        'name' : '(null)',
                        'amount' : rule.amount_paid,
                        'is_change' : False,
                        'payment_method_id' : payment_method.id
                    }
                    payment_list.append((0,0,amount_vals))
                    
                    return_vals = {
                        'payment_date' : dateutil.parser.isoparse(transaction.ReceiptDateTime).replace(tzinfo=None),
                        'name' : 'return',
                        'amount' : -rule.amount_return,
                        'is_change' : True,
                        'payment_method_id' : payment_method.id
                    }
                    payment_list.append((0,0,return_vals))

                order_vals = {
                    'name' : self.company_id.name + '/' + transaction.TransactionID,
                    'pricelist_id' : 1,
                    'session_id' : 296, #Null
                    'company_id' : self.company_id.id,
                    'amount_tax' : rule.amount_tax,
                    'amount_paid' : rule.amount_paid,
                    'amount_total' : rule.amount_total,
                    'amount_return' : -rule.amount_return,
                    'payment_ids' : payment_list
                }            
                self.env['pos.order'].sudo().create(order_vals)

    def import_purchaseorders(self, purchaseorders : List[Order], purchaseorderMappingrule, supplierMappingRules, itemMappingRules):

        for purchaseorder in purchaseorders:

            # Find Map
            rule = [rule for rule in purchaseorderMappingrule if purchaseorder.DocumentID == rule.code]

            if len(rule) == 0:
                raise Exception("Purchase Mapping rule not found for ID: " + str(purchaseorder.DocumentID))
            
            if len(rule) == 1:
                rule = rule[0]
                orderLines = []

                for line in purchaseorder.LineItem:                    

                    item_rule = [item_rule for item_rule in itemMappingRules if line.ItemID == item_rule.code]

                    if len(item_rule) == 0:
                        raise Exception("Item Mapping rule not found for ID: " + str(line.ItemID))

                    if len(item_rule) == 1:
                        item_rule = item_rule[0]
                        line_vals = {
                            'product_id' : item_rule.target.product_variant_id.id,
                            # 'sh_vendor_pro_code' : line.SupplierItemID,
                            'name' : line.ItemDescription,
                            'product_qty' : line.UnitCount,
                            'price_unit' : line.UnitBaseCostAmount,
                            # 'product_qty_received' : line.UnitsShippedCount,
                            'price_tax' : line.Tax.Amount
                        }
                        orderLines.append((0,0,line_vals))

                supplier_rule = [supplier_rule for supplier_rule in supplierMappingRules if purchaseorder.SupplierID == supplier_rule.code]

                if len(supplier_rule) == 0:
                    raise Exception("Supplier Mapping rule not found for ID: " + str(purchaseorder.DocumentID))

                if len(supplier_rule) == 1:
                    supplier_rule = supplier_rule[0]
                    purchase_vals = {
                        'name' : 'PO' + purchaseorder.DocumentID,
                        'date_order' : rule.date_order,
                        'amount_tax' : rule.amount_tax,
                        'amount_untaxed' : rule.amount_untaxed,
                        'amount_total' : rule.amount_total,
                        'currency_rate' : 1,
                        'currency_id' : 21,
                        'company_id' : self.company_id.id,
                        'state' : self.searchForPurchaseORderState(purchaseorder.Status),
                        'partner_id' : supplier_rule.target.id,
                        'order_line' : orderLines
                    }
                    created_purchase_orde = self.env['purchase.order'].create(purchase_vals)
                    if purchaseorder.Status in ['Acknowledged','Delivered']:
                        created_purchase_orde.button_confirm()
                    elif purchaseorder.Status == 'Cancelled':
                        created_purchase_orde.button_cancel()

    def searchForAlternativeID(self, searchTerm : str, alternativeIDs : List[AlternativeID]):
        matchingTerms = [ x.ID for x in alternativeIDs if x.Type == searchTerm]
        
        if len(matchingTerms) >= 1:
            return matchingTerms[0]
        else:
            return None
        
    def searchForAlternativeIDs(self, searchTerm : str, alternativeIDs : List[AlternativeID]):
        return [ x.ID for x in alternativeIDs if x.Type == searchTerm]
    
    
    def searchForAlternativeAttribute(self, searchTerm : str, alternativeIDs : List[Attribute]):
        matchingTerms = [ x.AttributeValue for x in alternativeIDs if x.AttributeName == searchTerm]
        
        if len(matchingTerms) == 1:
            return matchingTerms[0]
        else:
            return None

    def searchForPurchaseORderState(self, state):
        stateList = {
            'Open' : 'draft',
            'Sent' : 'sent',
            'Acknowledged' : 'purchase',
            'Delivered' : 'purchase',
            'Cancelled' : 'cancel'
        }
        for key,value in stateList.items():
            if key == state:
                return value
        return 'draft'
    
class EmployeeMigrationMappingModel(models.Model):
    _name = 'corum.migration.employee.mapping'
    
    name = fields.Char(string="Employee Name")
    email = fields.Char(string="Employee Email")
    code = fields.Char(string="Employee Code")
    target_create = fields.Boolean(string="Create", default=True)
    target = fields.Many2one('res.users', string='Map to Employee')
    migration_id = fields.Many2one("corum.migration", string="Migration")

class SupplierMigrationMappingModel(models.Model):
    _name = 'corum.migration.supplier.mapping'
    
    name = fields.Char(string="Supplier Name")
    abn = fields.Char(string="Supplier ABN")
    asx = fields.Char(string="Supplier ASX")
    pharmx_supplier_id = fields.Char(string="PharmX Supplier ID")
    code = fields.Char(string="Supplier Code")
    target_create = fields.Boolean(string="Create", default=True)
    target = fields.Many2one('res.partner', string='Map to Supplier')
    migration_id = fields.Many2one("corum.migration", string="Migration")

class BrandMigrationMappingModel(models.Model):
    _name = 'corum.migration.brand.mapping'
    
    name = fields.Char(string="Brand Name")
    target_create = fields.Boolean(string="Create", default=True)
    target = fields.Many2one('product.brand', string='Map to Brand')
    migration_id = fields.Many2one("corum.migration", string="Migration")
    
class ManufacturerMigrationMappingModel(models.Model):
    _name = 'corum.migration.manufacturer.mapping'
    
    name = fields.Char(string="Manufacturer Name")
    target_create = fields.Boolean(string="Create", default=True)
    target = fields.Many2one('res.partner', string='Map to Manufacturer')
    migration_id = fields.Many2one("corum.migration", string="Migration")

class CategoryMigrationMappingModel(models.Model):
    _name = 'corum.migration.category.mapping'
    
    name = fields.Char(string="Category Name")
    parent = fields.Char(string="Parent Category Name")
    target_create = fields.Boolean(string="Create", default=True)
    target = fields.Many2one('product.category', string='Map to Category')
    migration_id = fields.Many2one("corum.migration", string="Migration")

class CustomerMigrationMappingModel(models.Model):
    _name = 'corum.migration.customer.mapping'
    
    name = fields.Char(string="Customer Name")
    email = fields.Char(string="Customer Email")
    phone = fields.Char(string="Customer Phone")
    code = fields.Char(string="Customer Code")
    target_create = fields.Boolean(string="Create", default=True)
    target = fields.Many2one('res.partner', string='Map to Customer')
    migration_id = fields.Many2one("corum.migration", string="Migration")

class ItemMigrationMappingModel(models.Model):
    _name = 'corum.migration.item.mapping'
    
    label = fields.Char(string="Item Label")
    barcode = fields.Char(string="Item Barcode")
    brand = fields.Char(string="Item Brand")
    code = fields.Char(string="Item Code")
    target_create = fields.Boolean(string="Create", default=True)
    target = fields.Many2one('product.template', string='Map to Item')
    migration_id = fields.Many2one("corum.migration", string="Migration")

class SaleMigrationMappingModel(models.Model):
    _name = 'corum.migration.retailtransaction'
    
    code = fields.Char(string="Sale Code")
    date_order = fields.Datetime(string="Sale Date")
    amount_total = fields.Float(string="Total Amount")
    amount_tax = fields.Float(string="Tax Amount")
    amount_paid = fields.Float(string="Paid Amount")
    amount_return = fields.Float(string="Return Amount")

    migration_id = fields.Many2one("corum.migration", string="Migration")

class PurchaseMigrationMappingModel(models.Model):
    _name = 'corum.migration.purchase.order'

    code = fields.Char(string="Purchase Code")
    date_order = fields.Datetime(string="Purchase Date")
    amount_total = fields.Float(string="Total Amount")
    amount_tax = fields.Float(string="Tax Amount")
    amount_untaxed = fields.Float(string="Untaxed Amount")
    migration_id = fields.Many2one("corum.migration", string="Migration")