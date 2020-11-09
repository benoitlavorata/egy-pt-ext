'''
Created on 4 July 2019

@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.depends('project_id', 'project_id.stock_location_id')
    def _get_project_location(self):
        for i in self:
            if i.project_id and i.project_id.stock_location_id:
                i.project_stock_location_id = i.project_id.stock_location_id.id

    @api.depends('name', 'phase_id', 'phase_id.name', 'project_id', 'project_id.name')
    def _get_location_name(self):
        for i in self:
            if i.phase_id and i.name:
                i.stock_location_name = '%s/%s/%s' % (i.project_id.name, i.phase_id.name, i.name)

    phase_id = fields.Many2one('project.phase', string="Project Phase", track_visibility="always")
    task_weight = fields.Float(string="Weight", default=1.0)
    task_budget = fields.Float(string="Budget Amount", track_visibility="always")
    qty = fields.Float(string="Quantity", default=1.0, track_visibility="always")
    uom_id = fields.Many2one('uom.uom', string="UOM", help="Unit of Measure", track_visibility="always")
    project_stock_location_id = fields.Many2one('stock.location', string="Project Inventory Location",
                                                compute="_get_project_location", store=True)
    stock_location_id = fields.Many2one('stock.location', string="Task Inventory Location",
                                        domain="[('location_id', '=', project_stock_location_id)]",
                                        track_visibility="always")
    stock_location_name = fields.Char(string="Location Name", store=True, compute="_get_location_name", )
    picking_type_id = fields.Many2one('stock.picking.type', string="Picking Operation")

    # Budget And Actual Expeditures
    #Todo: Make all this field a "Computed fields" Badget: based on the BOQs; Expense: Based on the actual expense recored in the Analytic Account
    material_budget = fields.Float(string="Material Budget")
    material_expense = fields.Float(string="Material Expense")
    material_balance = fields.Float(string="Material Balance")
    service_budget = fields.Float(string="Service Budget")
    service_expense = fields.Float(string="Service Expense")
    service_balance = fields.Float(string="Service Balance")
    labor_budget = fields.Float(string="Labor Budget")
    labor_expense = fields.Float(string="Labor Expense")
    labor_balance = fields.Float(string="Labor Balance")
    equipment_budget = fields.Float(string="Equipment Budget")
    equipment_expense = fields.Float(string="Equipment Expense")
    equipment_balance = fields.Float(string="Equipment Balance")
    overhead_budget = fields.Float(string="Overhead Budget")
    overhead_expense = fields.Float(string="Overhead Expense")
    overhead_balance = fields.Float(string="Overhead balance")
    total_budget = fields.Float(string="Total Budget")
    total_expense = fields.Float(string="Total Expense")
    total_balance = fields.Float(string="Total Balance")
