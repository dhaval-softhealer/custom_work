{
    "name": "Pharmx - POS Sync",
    "summary": "An extension to the PharmX EDI Service for synchronising data from external pos systems: inventory transactions, inventory actions, sales, products, prices & suppliers",
    "category": "Website",
    "description": "PharmX POS Sync",
    "author": "Corum Group",
    'price': 0,
    'currency': 'USD',
    "website": "https://pharmx.com.au",
    "depends": ['pharmx_edi', 'account', 'purchase', 'sale', 'stock', 'product', 'product_brand', 'sh_product_multi_barcode', 'product_manufacturer', 'pharmx_cis_sync', 'sh_po_vendor_code'],
    "data": [
        "security/ir.model.access.csv",
    ],
}