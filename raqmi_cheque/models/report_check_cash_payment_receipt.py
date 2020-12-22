# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReceiptCashCheck(models.AbstractModel):
    _name = 'report.raqmi_cheque.receipt_check_cash_payment'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('raqmi_cheque.receipt_check_cash_payment')
        docargs = {
            'doc_ids': docids,
            'doc_model': 'normal.payments',
            'docs': self.env['normal.payments'].browse(docids),
            'payment_info': self._payment_info,
            'convert': self._convert
        }
        return docargs
