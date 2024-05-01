# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Point Of Sale By Product Category Report",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Point Of Sale",
    "summary": "POS Report By Product Category Point Of Sale Order Report Based On Product Category Point Of Sale Order From Product Categories Point Of Sale Order By Product Category Report POS By Category Product By Category Odoo",
    "description": """This module helps to generate and print product point of sale reports by product category in PDF as well as excel format. You can generate reports between any date range. You can generate reports based on any product category. We provide the option to print reports of more than one company.""",
    "version": "16.0.2",
    "depends": ['point_of_sale'],
    "data": [
        'security/pos_by_category.xml',
        'security/ir.model.access.csv',
        'report/sh_pos_by_category_report_templates.xml',
        'wizard/sh_pos_category_wizard_views.xml',
        'views/sh_pos_by_product_category_views.xml',
    ],
    "images": ["static/description/background.png", ],
    "license": "OPL-1",
    "application": True,
    "auto_install": False,
    "installable": True,
    "price": 25,
    "currency": "EUR"
}
