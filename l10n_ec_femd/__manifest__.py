# -*- coding: utf-8 -*-
{
    'name': "Flujo de Efectivo (Directo) - Ecuador",
    'summary': """Clasifica cobros y pagos para el Flujo de Efectivo.""",
    'version': '11.0.0.0.0',
    'author': "Fabrica de Software Libre,Odoo Community Association (OCA)",
    'maintainer': 'Fabrica de Software Libre',
    'website': 'http://www.libre.ec',
    'license': 'AGPL-3',
    'category': 'Account',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'views/account_payment.xml',
        'views/account_journal.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
}
