# -*- coding: utf-8 -*-
# Copyright 2017 Fábrica de Software Libre - Daniel Alejandro Mendieta
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import _, api, fields, models


class AccountStatementLineCreate(models.TransientModel):
    _inherit = 'account.statement.line.create'

    @api.model
    def default_get(self, field_list):
        res = super(AccountStatementLineCreate, self).default_get(field_list)
        statement = self.env[
            'account.bank.statement'].browse(self.env.context['active_id'])
        res.update({
            'due_date': statement.date,
            'journal_ids': [statement.journal_id.id],
            'invoice': False,
        })
        return res

    @api.multi
    def create_statement_lines(self):
        res = super(AccountStatementLineCreate, self).create_statement_lines()
        if res == True:
            for line in self.statement_id.line_ids:
                aml = line.source_move_line_id

                counterpart_aml_dicts = []
                payment_aml_rec = self.env['account.move.line']
                if aml.account_id.internal_type == 'liquidity':
                    payment_aml_rec = aml
                else:
                    # usamos el amount de la línea puesto que fué creada calculando el residual.
                    amount = line.amount

                    counterpart_aml_dicts.append({
                        'name': aml.name if aml.name != '/' else aml.move_id.name,
                        'debit': amount < 0 and -amount or 0,
                        'credit': amount > 0 and amount or 0,
                        'move_line': aml
                    })
                line.process_reconciliation(counterpart_aml_dicts=counterpart_aml_dicts, payment_aml_rec=payment_aml_rec)
