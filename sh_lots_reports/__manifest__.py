# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    'name': 'Lots Reports',
    "author": "Softhealer Technologies",
    'version': '15.0.2',
    "website": "https://www.softhealer.com",
    'category': 'Extra Tools',
    "support": "support@softhealer.com",
    'summary': 'hospital patient records',
    'description': """
        Lots Reports 
    """,
    'depends': ['base_setup','point_of_sale'],
    'data': [        
         "security/ir.model.access.csv",
         "views/sh_eod_screen_report.xml",
         "wizard/sh_myob_wizard.xml",
         "wizard/sh_eod_wizard.xml",
         "wizard/sh_myob_purchase_wizard.xml",
         "views/sh_lots_reports_menus.xml",
    ],
    'assets': {
        'web.assets_backend': [
            "sh_lots_reports/static/src/js/sh_eod_report.js",
        ],
        'web.assets_qweb': [
            'sh_lots_reports/static/src/xml/sh_eod_report_template.xml',
        ],              
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'application':True,
}   

