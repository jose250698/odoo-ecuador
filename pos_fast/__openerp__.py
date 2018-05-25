{
    'name': 'POS Big Datas, Fast loading POS',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 0,
    'author': 'TL Technology',
    'website': 'http://posodoo.com',
    'price': '100',
    'description': 'Only need 2s for loading 60,000 rows',
    "currency": 'EUR',
    'depends': ['pos_sale_pricelist', 'bus', 'web'],
    'data': [
        '__import__/template.xml',
        'datas/parameter.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'application': True,
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
    'support': 'thanhchatvn@gmail.com'
}
