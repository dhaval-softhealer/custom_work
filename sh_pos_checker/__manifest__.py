# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

{
    "name": "Pos Age Checker",
    "author": "Softhealer Technologies",
    "license": "OPL-1",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Point of Sale",
    "summary": "",
    "description": """""",
    "version": "16.0.1",
    "depends": ["point_of_sale",],
    "application": True,
    "data": [
        # 'views/res_config_settings_views.xml',
        'views/pos_category.xml',
        'views/res_partner.xml',
        ],
    'assets': {'point_of_sale.assets': [
                'sh_pos_checker/static/src/js/**/*',
                'sh_pos_checker/static/src/xml/**/*',
                # 'sh_pos_checker/static/src/js/screen/ProductScreen.js',
                # 'sh_pos_checker/static/src/js/screen/popup/sh_checking_popup.js',
                # 'sh_pos_checker/static/src/xml/popup/sh_checking_popup.xml',
                # 'sh_pos_checker/static/src/js/screen/iao-alert.jquery.js',
                # 'sh_pos_checker/static/src/js/screen/ZXing.js',
                # 'sh_pos_checker/static/src/xml/products_widget.xml',
            ],
                
            },
    "auto_install": False,
    "installable": True,
}
