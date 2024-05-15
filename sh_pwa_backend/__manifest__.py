# Part of Softhealer Technologies.
{
    "name": "PWA (Progressive Web Application) Backend",

    "author": "Softhealer Technologies",

    "website": "https://www.softhealer.com",

    "support": "support@softhealer.com",

    "version": "15.0.1",

    "category": "Extra Tools",

    "license": "OPL-1",

    "summary": "Get Backend PWA App, Build PWA Backend App From Website, Progressive Web Apps Backend Module, Make Backend PWA From Odoo, Create PWA Backend Application Odoo",

    "description": """The PWA (progressive web application) backend works like a normal application on the mobile. It allows you to adjust the custom style as your requirement. We provide icon size, name, display orientation, colors, etc options to make quickly app format. You get a combination of a native app with the website. PWA Backend Odoo, Get Backend PWA App, Build PWA Backend App From Website, Progressive Web Apps Backend Module, Make Backend PWA From Odoo, Create PWA Backend Application Odoo, Get Backend PWA App, Build PWA Backend App From Website, Progressive Web Apps Backend Module, Make Backend PWA From Odoo, Create PWA Backend Application Odoo""",

    "depends": ['base', 'web','base_setup'],

    "data": [
        "data/pwa_configuraion_data.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/views.xml",
        "views/send_notifications.xml",
        "views/web_push_notification.xml",
        "views/pwa_configuration_view.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'https://www.gstatic.com/firebasejs/8.4.3/firebase-app.js',
            'https://www.gstatic.com/firebasejs/8.4.3/firebase-messaging.js',
            'sh_pwa_backend/static/index.js',
            'sh_pwa_backend/static/src/js/firebase.js',
        ]
    },
    "images": ["static/description/background.png", ],
    "live_test_url": "https://youtu.be/7fCQN-N5k9w",
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "50",
    "currency": "EUR"
}
