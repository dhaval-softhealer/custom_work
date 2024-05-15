{
    "name": "Pharmx EDI",
    "summary": "An EDI Service to exchange PharmX Messages",
    "category": "Website",
    "description": "PharmX EDI",
    "author": "Corum Group",
    'price': 0,
    'currency': 'USD',
    "website": "https://pharmx.com.au",
    "depends": ['component','component_event', 'queue_job'],
    "data": [
        "cron/cron.xml",
        "views/datasync_message_view.xml",
        "views/menu_items.xml",
        "security/ir.model.access.csv",
        "data/pharmx_identifier_seq.xml"
    ],
    'installable': True,
    'application': True,
}
