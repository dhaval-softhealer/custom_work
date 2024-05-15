{
    "name" : "Corum Intercompany Management",
    "author" : "Corum Health",
    "website": "https://corumhealth.com.au/",
    "support": "https://corumhealth.com.au/",    
    "category": "Intercompany Management",
    "summary": "This module is used to handle intercompany operations.",
    "description": """Functions:
                    - Creates purchase orders for companies that are selected as the customer for sales orders.
                    - Creates sales orders for companies that are selected as the supplier for purchase orders.""",
    "application" : True,
    "version": "15.0.2",
    "depends" : [
        "corum_interface",
    ],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["sale", "purchase"],
    "data": ["views/res_config_settings_view.xml"],
}
