{
    'name': 'Flous Flow - Manufacturing WIP Location',
    'summary': 'Route selected manufactured products to a company WIP location',
    'description': """
Flous Flow Manufacturing WIP Location
=====================================

Adds an opt-in product flag that sends the main finished product of a
manufacturing order directly to the Work in Progress (WIP) location configured
for the manufacturing company. Standard Odoo behavior remains unchanged for
products that are not marked Under Processing.
    """,
    'version': '20.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'author': 'Flous Flow',
    'website': 'https://flousflow.com',
    'license': 'LGPL-3',
    'depends': ['mrp', 'stock', 'product'],
    'data': [
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
