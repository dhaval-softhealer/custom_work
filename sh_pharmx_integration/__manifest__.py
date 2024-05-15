# Part of Softhealer Technologies.
{
    "name": "PharmX Integration - Gateway 3",

    "author": "Softhealer Technologies",

    "website": "https://www.softhealer.com",

    "support": "support@softhealer.com",

    "version": "14.0.1",

    "license": "OPL-1",

    "category": "Website",

    "summary": "Connect PharmX with Odoo - Gateway 3",

    "description": """Connect PharmX with Odoo""",

    "depends": ['base','sale_management','purchase', 'sh_po_vendor_code'],

    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "cron/cron.xml",
        "views/sh_pharmx_configuration.xml",
        "views/popup_message.xml",
        "views/pharmx_gateways.xml",
        "views/sh_pharmx_base.xml",
        "views/inherit_purchase_order.xml",
        "views/inherit_res_partner.xml",
        "views/pharmx_account.xml",
        "views/inherit_menu_items.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "55",
    "currency": "EUR"
}
