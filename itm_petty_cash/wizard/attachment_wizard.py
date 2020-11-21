# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import json


class PettyCashAttachmentWizard(models.TransientModel):
    _name = 'petty_cash.attachmnet.wizard'
    
    name = fields.Char(string="Document Attachment", default='Attachment')
    attachmnet_widget = fields.Text(string="Attachment", compute='_get_new_info_JSON')

    @api.depends('name')
    def _get_new_info_JSON(self):
        context = self.env.context
        self.attachmnet_widget = json.dumps(False)
        line_id = self.env['petty.cash.line'].browse(context.get('active_ids'))
        if line_id:
            info = {'title': line_id.memo or  '' , 'line_id':line_id.id or '', 'attachment_ids':line_id.attachment_ids.ids or []}
            self.attachmnet_widget = json.dumps(info)