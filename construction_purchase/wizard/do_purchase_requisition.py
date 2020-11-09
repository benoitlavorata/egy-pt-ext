from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class DoPurchaseRequisition(models.TransientModel):
    _inherit = 'do.purchase.requisition'

    @api.model
    def default_get(self, fields):
        res = super(DoPurchaseRequisition, self).default_get(fields)
        data = self.env['sprogroup.purchase.request'].browse(self._context.get('active_ids')[0])
        res['analytic_account_id'] = data.analytic_account_id.id
        return res


    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    purchase_requisition_ids = fields.Many2one('purchase.requisition', string="Purchase Requition", domain="[('state', 'in', ['draft']), ('analytic_account_id', 'in', [analytic_account_id]), ('purchase_request_id', 'not in', [purchase_request_id])]")

    def create_purchase_requisition(self):
        ids = []
        requisition_data = self.env['purchase.requisition'].search([])
        for i in requisition_data:
            if i.purchase_request_id and i.purchase_request_id.id == self.purchase_request_id.id: ids.append(i.id)
            elif self.purchase_request_id.id in [line.id for line in i.purchase_request_merge_ids]: ids.append(i.id)
        if ids: raise ValidationError(_('Upon validation, This Purchase Request document has already linked to a Purchase Requition.'))
        po = self.env['purchase.order'].search([('purchase_request_id', '=', self.purchase_request_id.id), ('state', 'not in', ['cancel'])])
        if po[:1]: raise ValidationError(_('Upon validation, This Purchase Request document has already linked to a Purchase Order'))
        project_related = False
        if self.purchase_request_id.project_id: project_related = True
        if self.action in ['New']:
            view_id = self.env.ref('purchase_requisition.view_purchase_requisition_form')
            product_line = []
            for i in self.purchase_request_id.line_ids:
                product_line.append([0, 0, {
                    'product_id': i.product_id.id,
                    'product_qty': i.product_qty,
                    'product_uom_id': i.product_uom_id.id,
                    'schedule_date': i.date_required,
                    'project_id': self.purchase_request_id.project_id and self.purchase_request_id.project_id.id or False,
                    'phase_id': self.purchase_request_id.phase_id and self.purchase_request_id.phase_id.id or False,
                    'task_id': self.purchase_request_id.task_id and self.purchase_request_id.task_id.id or False,
                    'project_boq_category': self.purchase_request_id.task_id and 'meterial' or '',
                    'account_analytic_id': self.analytic_account_id and self.analytic_account_id.id or False,
                }])
            return {
                'name': _('New Purchase Requition'),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.requisition',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'view_id': view_id.id,
                'views': [(view_id.id, 'form')],
                'context': {
                        'default_line_ids': product_line,
                        'default_state': 'draft',
                        'default_type_id': self.purchase_requisition_type_id.id,
                        'default_purchase_request_id': self.purchase_request_id.id,
                        'default_account_analytic_id': self.analytic_account_id.id,
                        'default_project_related': project_related,
                        }
                    }
        else:
            for i in self.line_ids:
                found = False
                for line in self.purchase_requisition_ids.line_ids:
                    if project_related:
                        if i.product_id.id == line.product_id.id and i.product_uom_id.id == line.product_uom_id.id and line.project_id.id == self.purchase_request_id.project_id.id and line.phase_id.id == self.purchase_request_id.phase_id.id and line.task_id.id == self.purchase_request_id.task_id.id:
                            found = True
                            line.write({'product_qty': i.product_qty + line.product_qty})
                            continue
                    else:
                        if i.product_id.id == line.product_id.id:
                            found = True
                            line.write({'product_qty': i.product_qty + line.product_qty})
                            continue
                if not found:
                    self.purchase_requisition_ids.write({
                        'purchase_request_merge_ids': [(4, self.purchase_request_id.id)],
                        'line_ids': [(0, 0, {
                            'product_id': i.product_id.id,
                            'product_qty': i.product_qty,
                            'product_uom_id': i.product_uom_id.id,
                            'schedule_date': i.date_required,
                            'product_uom_id': i.product_uom_id.id,
                            'project_id': self.purchase_request_id.project_id and self.purchase_request_id.project_id.id or False,
                            'phase_id': self.purchase_request_id.phase_id and self.purchase_request_id.phase_id.id or False,
                            'task_id': self.purchase_request_id.task_id and self.purchase_request_id.task_id.id or False,
                            'project_boq_category': self.purchase_request_id.task_id and 'meterial' or '',
                            'account_analytic_id': self.analytic_account_id and self.analytic_account_id.id or False})]
                    })
            self.purchase_requisition_ids.write({
                'purchase_request_merge_ids': [(4, self.purchase_request_id.id)]
            })
            self.purchase_request_id.write({'purchase_requisition_id': self.purchase_requisition_ids.id})
            return {'type': 'ir.actions.act_window_close'}
