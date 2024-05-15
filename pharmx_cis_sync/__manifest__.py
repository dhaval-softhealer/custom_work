{
    "name": "Pharmx - CIS Sync",
    "summary": "An extension to the PharmX EDI Service for synchronising products, prices & suppliers",
    "category": "Website",
    "description": "PharmX CIS Sync",
    "author": "Corum Group",
    'price': 0,
    'currency': 'USD',
    "website": "https://pharmx.com.au",
    "depends": ['pharmx_edi', 'account', 'purchase', 'sale', 'product', 'product_brand', 'sh_product_multi_barcode', 'product_manufacturer'],
    "data": [
        "views/product_view.xml",
        #"views/menu_view.xml",
        "views/supplierinfo_view.xml",
        "views/product_category_view.xml",
        "security/ir.model.access.csv",
        "security/mappingrule_security.xml"
    ],
}