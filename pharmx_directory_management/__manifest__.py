{
    "name": "Pharmx - Directory Management",
    "summary": "An extension to the PharmX EDI Service for managing the contact directory",
    "category": "Website",
    "description": "PharmX Directory Management",
    "author": "Corum Group",
    'price': 0,
    'currency': 'USD',
    "website": "https://pharmx.com.au",
    "depends": ['base', 'contacts', 'pharmx_edi', 'account'],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/data.xml",
        "views/inherit_res_partner_bank.xml",
        "views/inherit_res_partner.xml",
    ],
}
