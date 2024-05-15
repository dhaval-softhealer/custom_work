# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    'name': 'General Pricelist Changes',
    'author': 'Softhealer Technologies',
    'website': "https://www.softhealer.com",
    "support": "support@softhealer.com",
    'version': '15.0.1',
    'category': 'Productivity',
    "summary": "Pricelists",
    'description': """General Pricelist_Changes.""",
    'depends': [
        'base_setup',
        'point_of_sale',
        'product',
        'sh_pos_all_in_one_retail',
        'stock',
        'product_pricelist_extensions'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_product_pricelist.xml',
        'views/inherit_product_template.xml',
        'views/sh_label_queue_views.xml',
        'wizard/inherit_label_layout.xml',
        'report/pricelist_label.xml',
        'report/pricelist_template.xml',
        'report/product_pricelist_templates.xml'
    ],
    'images': [],
    "license": "OPL-1",
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "0",
    "currency": "EUR"
}
