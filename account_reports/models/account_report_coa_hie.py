# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from copy import deepcopy

from odoo import models, api, _, fields


class AccountChartOfAccountReportHierarchy(models.AbstractModel):
    _name = "account.coa.report.hierarchy"
    _description = "Chart of Account Report Hierarchy"
    _inherit = "account.report"

    filter_all_entries = None
    filter_unfold_all = False
    filter_cash_basis = None
    filter_hierarchy = False
    MAX_LINES = None

    @api.model
    def _get_templates(self):
        templates = super(AccountChartOfAccountReportHierarchy, self)._get_templates()
        templates['main_table_header_template'] = 'account_reports.template_coa_table_header_hierarchy'
        return templates

    @api.model
    def _get_columns_name(self, options):
        columns = [
            {'name': '', 'style': 'width:70%'}
        ]

        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        # Create new options with 'unfold_all' to compute the initial balances.
        # Then, the '_do_query' will compute all sums/unaffected earnings/initial balances for all comparisons.
        new_options = options.copy()
        new_options['unfold_all'] = True
        accounts_list = []
        acc_list = self.env['account.account'].search([('id', '!=', '1')])
        for acc in acc_list:
            accounts_list.append(acc)

        lines = []

        # Add lines, one per account.account record.
        for account in accounts_list:
            # account.account report line.
            columns = []

            name = account.name_get()[0][1]
            if len(name) > 40 and not self._context.get('print_mode'):
                name = name[:40]+'...'

            lines.append({
                'id': account.id,
                'name': name,
                'title_hover': name,
                'columns': columns,
                'unfoldable': False,
                'caret_options': 'account.account',
            })
        return lines

    @api.model
    def _get_report_name(self):
        return _("Chart of Account Hierarchy")
