'''
Created on 09 August 2019

@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class Project(models.Model):
    _inherit = 'project.project'

    monitor_boq_item_qty_and_price = fields.Boolean(string="BOQ/BOM Item Quantity and Price", default=True, help="Applicable only for (Materials) products")
    monitor_boq_category_budget = fields.Boolean(string="BOQ Category Budget", default=True, help="Applicable for Materials, Equipment, Labor and Overheads Budget defined in the Task BOQ")
    monitor_budget_task_level = fields.Boolean(string="Task Budget", default=True)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    purchase_line_ids = fields.One2many('purchase.order.line', 'task_id', string="PO Lines")
