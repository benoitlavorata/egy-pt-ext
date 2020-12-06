from odoo import models, fields, api
from datetime import datetime


class MoveLines(models.Model):
    _inherit = 'account.move.line'

    cheque_pay_id = fields.Integer(string="Cheque Payment", index=True)
    cheque_id = fields.Integer(string="Cheque", index=True)
    normal_pay_id = fields.Integer(string="Cheque Pay", index=True)
    con_pay_id = fields.Integer(string="Con Cheque", index=True)
    date_maturity = fields.Date(string='Due date', index=True, required=False,
                                help="This field is used for payable and receivable journal entries."
                                     " You can put the limit date for the payment of this line.")
    cheques = fields.Boolean('cheques')

    @api.model_create_multi
    def create(self, vals):
        res = super(MoveLines, self).create(vals)
        res.date_maturity = False
        return res


class CreateMoves(models.Model):
    _name = 'create.moves'

    def create_move_lines(self, **kwargs):
        self.accounts_agg(**kwargs)
        self.adjust_move_percentage(**kwargs)
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        company_currency = self.env['res.users'].search([('id', '=', self._uid)]).company_id.currency_id
        debit, credit, amount_currency, currency_id = 0, 0, kwargs['src_currency'],  company_currency
        move_vals = {
            'name': kwargs['move']['name'],
            'journal_id': kwargs['move']['journal_id'],
            'date': datetime.today(),
            'ref': kwargs['move']['ref'],
            'company_id': kwargs['move']['company_id'],
            #'cheques':True
        }

        move = self.env['account.move'].with_context(check_move_validity=False).create(move_vals)
        for index in kwargs['debit_account']:
            debit_line_vals = {
                'name': kwargs['move_line']['name'],
                'account_id': index['account'],
                'partner_id': kwargs['move_line']['partner_id'],
                'debit': (index['percentage'] / 100) * kwargs['amount'],
                'credit': credit,
                'amount_currency': 0,
                'cheques': True
            }
            if 'analytic_id' in index:
                debit_line_vals['analytic_account_id'] = index['analytic_id']
            if 'cheque_pay_id' in kwargs['move_line']:
                debit_line_vals['cheque_pay_id'] = kwargs['move_line']['cheque_pay_id']
            if 'cheque_id' in kwargs['move_line']:
                debit_line_vals['cheque_id'] = kwargs['move_line']['cheque_id']
            if 'normal_pay_id' in  kwargs['move_line']:
                debit_line_vals['normal_pay_id'] = kwargs['move_line']['normal_pay_id']
            if 'con_pay_id' in kwargs['move_line']:
                debit_line_vals['con_pay_id'] = kwargs['move_line']['con_pay_id']
            debit_line_vals['move_id'] = move.id
            debit_line_vals['cheques'] = True

            aml_obj.create(debit_line_vals)

        for index in kwargs['credit_account']:
            credit_line_vals = {
                'name': kwargs['move_line']['name'],
                'account_id': index['account'],
                'partner_id': kwargs['move_line']['partner_id'],
                'debit': credit,
                'credit': (index['percentage'] / 100) * kwargs['amount'],
                'amount_currency': 0,
            }
            if 'analytic_id' in index:
                credit_line_vals['analytic_account_id'] = index['analytic_id']
            if 'cheque_pay_id' in kwargs['move_line']:
                credit_line_vals['cheque_pay_id'] = kwargs['move_line']['cheque_pay_id']
            if 'cheque_id' in  kwargs['move_line']:
                credit_line_vals['cheque_id'] = kwargs['move_line']['cheque_id']
            if 'normal_pay_id' in  kwargs['move_line']:
                credit_line_vals['normal_pay_id'] = kwargs['move_line']['normal_pay_id']
            credit_line_vals['move_id'] = move.id
            credit_line_vals['cheques'] = True
            aml_obj.create(credit_line_vals)
        # move.post()

    def adjust_move_percentage(self, **kwargs):
        # Debit
        tot_dens = 0.0
        tot_crds = 0.0
        for debs in kwargs['debit_account']:
            tot_dens += debs['percentage']
        for crds in kwargs['credit_account']:
            tot_crds += crds['percentage']
        percent = 100.0
        if tot_crds < 99 or tot_crds > 101:
            percent = tot_crds
        for i in range(len(kwargs['debit_account'])):
            kwargs['debit_account'][i]['percentage'] = round(kwargs['debit_account'][i]['percentage'], 8)
        for index in kwargs['debit_account']:
            percent -= index['percentage']
        diff = 0.0
        if percent != 0.0:
            diff = percent / len(kwargs['debit_account'])
            for i in range(len(kwargs['debit_account'])):
                kwargs['debit_account'][i]['percentage'] += diff
        #Credit
        percent = 100.0
        if tot_crds < 99 or tot_crds > 101:
            percent = tot_crds
        for i in range(len(kwargs['credit_account'])):
            kwargs['credit_account'][i]['percentage'] = round(kwargs['credit_account'][i]['percentage'], 8)
        for index in kwargs['credit_account']:
            percent -= index['percentage']
        diff = 0.0
        if percent != 0.0:
            diff = percent / len(kwargs['credit_account'])
            for i in range(len(kwargs['credit_account'])):
                kwargs['credit_account'][i]['percentage'] += diff

    def accounts_agg(self, **kwargs):
        all_crd_accs = {}
        for crd_accs in kwargs['credit_account']:
            if all_crd_accs and crd_accs['account'] in all_crd_accs:
                all_crd_accs[crd_accs['account']] += crd_accs['percentage']
            else:
                all_crd_accs[crd_accs['account']] = crd_accs['percentage']
        credit_account = []
        for acc_key in all_crd_accs:
            credit_account.append({'account': acc_key, 'percentage': all_crd_accs[acc_key]})
        kwargs['credit_account'] = credit_account
        all_crd_accs = {}
        for crd_accs in kwargs['debit_account']:
            if all_crd_accs and crd_accs['account'] in all_crd_accs:
                all_crd_accs[crd_accs['account']] += crd_accs['percentage']
            else:
                all_crd_accs[crd_accs['account']] = crd_accs['percentage']
        debit_account = []
        for acc_key in all_crd_accs:
            debit_account.append({'account': acc_key, 'percentage': all_crd_accs[acc_key]})
        kwargs['debit_account'] = debit_account
