from odoo import api, fields, models, _, SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    project_id = fields.Many2one('project.project', string="Project")
    phase_id = fields.Many2one('project.phase', string="Phase")
    task_id = fields.Many2one('project.task', string="Task")

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
