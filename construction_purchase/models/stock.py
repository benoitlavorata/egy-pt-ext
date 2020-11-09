from odoo import api, fields, models, _, SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", store=True, compute='_get_mr_deta')
    project_id = fields.Many2one('project.project', string="Project", store=True, compute='_get_mr_deta')
    phase_id = fields.Many2one('project.phase', string="Phase", store=True, compute='_get_mr_deta')
    task_id = fields.Many2one('project.task', string="Task", store=True, compute='_get_mr_deta')


    @api.depends('mr_bom_id')
    def _get_mr_deta(self):
        for i in self:
            if i.mr_bom_id:
                i.analytic_account_id = i.mr_bom_id.project_id.analytic_account_id.id
                i.project_id = i.mr_bom_id.project_id.id
                i.phase_id = i.mr_bom_id.phase_id.id
                i.task_id = i.mr_bom_id.task_id.id

    def create_purchase_request(self):
        res = super(StockPicking, self).create_purchase_request()
        if self.purchase_request_id:
            self.purchase_request_id.write({
                        'analytic_account_id': self.analytic_account_id.id,
                        'project_id': self.project_id.id,
                        'phase_id': self.phase_id.id,
                        'task_id': self.task_id.id,
            })
        return res
