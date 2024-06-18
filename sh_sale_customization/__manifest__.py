# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.
# -*- coding: utf-8 -*-

{
    "name": "Sale customization",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "",
    "license": "OPL-1",
    "summary": "",
    "description": """.""",
    "version": "16.0.1",
    'depends': ['sale' , 'purchase',"mrp"],
    "data": [
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/mrp_order.xml',
    ],
    'installable': True,
}
