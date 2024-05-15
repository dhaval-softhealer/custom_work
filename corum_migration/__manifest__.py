{
    "name": "Corum - Migration Tool",
    "summary": "An extension that imports retail data from a json file",
    "category": "Website",
    "description": "Corum Migration Tool",
    "author": "Corum Group",
    'price': 0,
    'currency': 'USD',
    "website": "https://corumhealth.com.au",
    "depends": ['pharmx_edi', 'account', 'purchase', 'sale', 'product', 'product_brand', 'sh_product_multi_barcode', 'product_manufacturer'],
    "data": [
        "security/ir.model.access.csv",
        "views/migrations.xml",
    ],
}