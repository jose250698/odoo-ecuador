# -*- coding: utf-8 -*-
{
    'name': "Payroll Payment",
    'summary': """Facilita el pago de roles de empleados.""",
    'description': """Facilita el pago de roles de empleados.""",
    'version': '9.0.1.0.0',
    'author': "Jonathan Finlay <jfinlay@riseup.net>",
    'maintainer': 'Jonathan Finlay',
    'website': 'http://www.lalibre.net',
    'license': 'AGPL-3',
    'category': 'Human resources',
    'depends': [
        'base',
        'account',
        'payment',
        'l10n_ec_hr_payroll',
        'hr_payroll',
    ],
    'data': [
        'views/hr_employee.xml',
        'views/hr_payslip_view.xml',
        'views/account_payment.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
}
