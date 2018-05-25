# -*- coding: utf-8 -*-
from openerp import fields, models, api

import logging
import time
import os
import json
import shutil

_logger = logging.getLogger(__name__)

class pos_auto_cache(models.TransientModel):

    _name = "pos.auto.cache"

    @api.model
    def get_data(self):
        _logger.info('BEGIN loading get_data()')
        start_time = time.time()
        path_file = self.path_store_files()
        customers_file = path_file + '/customers_copy.txt'
        product_file = path_file + '/products_copy.txt'
        datas = {
            'product.product': [],
            'res.partner': [],
        }
        with open(product_file) as products_data:
            datas['product.product'] = json.load(products_data)
        with open(customers_file) as customers_data:
            datas['res.partner'] = json.load(customers_data)
        _logger.info('===: LOADING CACHE POS DATA ====:  %s' % (time.time() - start_time))
        return datas

    def path_store_files(self):
        if not os.path.exists(os.path.realpath(os.path.join(os.path.dirname(__file__), '../datas', self._cr.dbname))):
            os.makedirs(os.path.realpath(os.path.join(os.path.dirname(__file__), '../datas', self._cr.dbname)))
        path = os.path.realpath(os.path.join(os.path.dirname(__file__), '../datas', self._cr.dbname))
        return os.path.join(path)

    @api.model
    def auto_cache(self):
        _logger.info('===> BEGIN store data to Odoo Server')
        start_time = time.time()
        # stored product
        path = self.path_store_files()
        path_file = path + '/products.txt'
        product_template_fields = self.env['product.template'].fields_get()
        fields_will_load = []
        for field, value in product_template_fields.iteritems():
            if value['type'] not in ['binary', 'one2many'] and value['store'] == True:
                value['ttype'] = value['type']
                value['name'] = field
                fields_will_load.append(value)
        sql_select = ''
        fields_m2m_product_template = {}
        fields_m2o = {}
        for field_read in fields_will_load:
            if field_read['name'] in ['property_account_expense_id', 'property_account_income_id', 'supplier_taxes_id', 'property_account_creditor_price_difference']:
                continue
            if field_read['name'] == 'id':
                if not sql_select:
                    sql_select += 'SELECT pt.' + field_read['name'] + ' as pt_id'
                else:
                    sql_select += ', pt.' + field_read['name'] + ' as pt_id'
                continue
            if field_read['ttype'] != 'many2many':
                if not sql_select:
                    sql_select += 'SELECT pt.' + field_read['name']
                else:
                    sql_select += ', pt.' + field_read['name']
            if field_read['ttype'] == 'many2many':
                sub_query = "select * from ir_model_fields where name='%s' and model='product.template'" % field_read['name']
                self.env.cr.execute(sub_query)
                vals = self.env.cr.dictfetchall()
                if vals:
                    fields_m2m_product_template[field_read['name']] = vals[0]
            if field_read['ttype'] == 'many2one':
                fields_m2o[field_read['name']] = field_read
        sql_from = " FROM product_template AS pt, product_product AS pp "
        sql_where = " WHERE pt.active is True AND pt.sale_ok is True and pt.available_in_pos is True AND pt.id = pp.product_tmpl_id "

        product_fields = self.env['product.product'].fields_get()
        fields_will_load = []
        for field, value in product_fields.iteritems():
            if value['type'] not in ['binary', 'one2many'] and value['store'] == True:
                value['ttype'] = value['type']
                value['name'] = field
                fields_will_load.append(value)
        fields_m2m_product_product = {}
        for field_read in fields_will_load:
            if field_read['ttype'] != 'many2many':
                sql_select += ', pp.' + field_read['name']
            if field_read['ttype'] == 'many2one':
                fields_m2o[field_read['name']] = field_read
            if field_read['ttype'] == 'many2many':
                sub_query = "select * from ir_model_fields where name='%s' and model='product.product'" % field_read['name']
                self.env.cr.execute(sub_query)
                vals = self.env.cr.dictfetchall()
                if vals:
                    fields_m2m_product_product[field_read['name']] = vals[0]
        sql_order_by = ' ORDER BY pt.sequence, pp.default_code, pt.name'
        sql = sql_select + sql_from + sql_where + sql_order_by
        self.env.cr.execute(sql)
        product_datas = self.env.cr.dictfetchall()
        for dict_value in product_datas:
            for field, value in fields_m2m_product_template.iteritems():
                sub_sql = "select * from %s where %s=%s" % (value['relation_table'], value['column1'], dict_value['product_tmpl_id'])
                self.env.cr.execute(sub_sql)
                vals = self.env.cr.dictfetchall()
                dict_value[field] = []
                if vals:
                    for val in vals:
                        dict_value[field].append(val[value['column2']])
            for field, value in fields_m2m_product_product.iteritems():
                sub_sql = "select * from %s where %s=%s" % (
                value['relation_table'], value['column1'], dict_value['product_tmpl_id'])
                self.env.cr.execute(sub_sql)
                vals = self.env.cr.dictfetchall()
                dict_value[field] = []
                if vals:
                    for val in vals:
                        dict_value[field].append(val[value['column2']])
            for field, value in fields_m2o.iteritems():
                if dict_value.has_key(field) and dict_value[field]:
                    table_name = value['relation'].split('.')
                    table = ''
                    for i in range(0, len(table_name)):
                        if not table:
                            table += table_name[i]
                        else:
                            table += '_' + table_name[i]
                    sub_sql = None
                    if table != 'res_users':
                        sub_sql = "select id, name from %s where id=%s" % (table, dict_value[field])
                    else:
                        sub_sql = "select ru.id, rp.name from res_users as ru, res_partner as rp where ru.id=%s and ru.partner_id=rp.id" % (
                        dict_value[field])
                    if sub_sql:
                        self.env.cr.execute(sub_sql)
                        vals = self.env.cr.dictfetchall()
                        if vals:
                            sub_data = (vals[0]['id'], vals[0]['name'])
                            dict_value[field] = sub_data
            dict_value['product_tmpl_id'] = (dict_value['id'], dict_value['name'])
            dict_value['display_name'] = dict_value['name']
            dict_value['price'] = dict_value['list_price']
        with open(path_file, 'w') as outfile:
            json.dump(product_datas, outfile)
        dst_file = path + '/products_copy.txt'
        shutil.copy(path_file, dst_file)
        _logger.info('Stored product: %s row with file %s ' % (len(product_datas), dst_file))

        # stored partners
        path = self.path_store_files()
        path_file = path + '/customers.txt'
        res_partner_fields = self.env['res.partner'].fields_get()
        fields_will_load = []
        for field, value in res_partner_fields.iteritems():
            if value['type'] not in ['binary', 'one2many'] and value['store'] == True:
                value['ttype'] = value['type']
                value['name'] = field
                fields_will_load.append(value)
        sql_select = ''
        fields_m2m = {}
        fields_m2o = {}
        for field_read in fields_will_load:
            if field_read['name'] in ['property_account_payable_id', 'property_account_receivable_id', 'property_account_position_id', 'property_payment_term_id', 'property_supplier_payment_term_id', 'property_purchase_currency_id']:
                continue
            if field_read['ttype'] != 'many2many':
                if not sql_select:
                    sql_select += 'SELECT ' + field_read['name']
                else:
                    sql_select += ', ' + field_read['name']
            if field_read['ttype'] == 'many2one':
                fields_m2o[field_read['name']] = field_read
            if field_read['ttype'] == 'many2many':
                sub_query = "select * from ir_model_fields where name='%s' and model='res.partner'" % field_read['name']
                self.env.cr.execute(sub_query)
                vals = self.env.cr.dictfetchall()
                if vals:
                    fields_m2m[field_read['name']] = vals[0]
        sql_from = " FROM res_partner AS rp "
        sql_where = " WHERE rp.customer=True AND rp.active=True and rp.country_id is not Null "
        sql_order_by = ' ORDER BY rp.name'
        sql = sql_select + sql_from + sql_where + sql_order_by
        self.env.cr.execute(sql)
        customer_datas = self.env.cr.dictfetchall()
        for dict_value in customer_datas:
            for field, value in fields_m2o.iteritems():
                if dict_value.has_key(field) and dict_value[field]:
                    table_name = value['relation'].split('.')
                    table = ''
                    for i in range(0, len(table_name)):
                        if not table:
                            table += table_name[i]
                        else:
                            table += '_' + table_name[i]
                    sub_sql = None
                    if table != 'res_users':
                        sub_sql = "select id, name from %s where id=%s" % (table, dict_value[field])
                    else:
                        sub_sql = "select ru.id, rp.name from res_users as ru, res_partner as rp where ru.id=%s and ru.partner_id=rp.id" % (
                            dict_value[field])
                    if sub_sql:
                        self.env.cr.execute(sub_sql)
                        vals = self.env.cr.dictfetchall()
                        if vals:
                            sub_data = (vals[0]['id'], vals[0]['name'])
                            dict_value[field] = sub_data
            for field, value in fields_m2m.iteritems():
                sub_sql = "select * from %s where %s=%s" % (
                value['relation_table'], value['column1'], dict_value['id'])
                self.env.cr.execute(sub_sql)
                vals = self.env.cr.dictfetchall()
                dict_value[field] = []
                if vals:
                    for val in vals:
                        dict_value[field].append(val[value['column2']])
        with open(path_file, 'w') as outfile:
            json.dump(customer_datas, outfile)
        dst_file = path + '/customers_copy.txt'
        shutil.copy(path_file, dst_file)
        _logger.info('Stored customer : %s row with file : %s' % (len(customer_datas), dst_file))
        _logger.info('=== Stored POS DATA ====:  %s' % (time.time() - start_time))
        return 1
