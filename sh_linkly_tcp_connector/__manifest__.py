# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    'name': 'Linkly Connector TCP/IP',
    'version': '15.0.2',
    'author': 'Softhealer Technologies',
    'website': 'https://www.softhealer.com',
    'support': 'support@softhealer.com',
    'license': 'OPL-1',
    'description': """
        Linkly Connector Payment Terminal POS
    """,
    'sequence': 0,
    'depends': ['point_of_sale'],
    'data': [
        # 'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'sh_linkly_tcp_connector/static/src/js/**/*',
            'sh_linkly_tcp_connector/static/src/css/**/*',
        ],
        'web.assets_qweb': [
            'sh_linkly_tcp_connector/static/src/xml/**/*',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': True,
}
