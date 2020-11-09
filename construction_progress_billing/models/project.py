
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

# class ProjectVisualInspection(models.Model):
#     _inherit = 'project.visual.inspection'
#
#     project_id = fields.Many2one('project.project', string="project", store=True, compute='_get_task_details')
#
#     @api.depends('task_id')
#     def _get_task_details(self):
#         for i in self:
#             if i.project_id = i.task_id.project_id.id


class ProjectProjectionAccomplishment(models.Model):
    _inherit = 'project.projection.accomplishment'

    actual = fields.Float(string="Actual Percentage", compute="_get_actual_accomplishment")

    # @api.depends('date','project_id', 'project_id.project_type', 'project_id.project_ids', 'project_id.project_ids.project_weight', 'project_id.phase_ids', 'project_id.phase_ids.phase_weight', 'project_id.phase_ids.task_ids.task_weight', 'project_id.phase_ids.task_ids.visual_inspection', 'project_id.phase_ids.task_ids.visual_inspection.actual_accomplishment')
    # def _get_actual_accomplishment(self):
    #     for i in self:
    #         total_phase_weight = sum(rec.phase_weight for rec in i.project_id.phase_ids)
    #         project_accomplishment = 0.0
    #         for phase in i.project_id.phase_ids:
    #             total_task_weight = sum(rec.task_weight for rec in phase.task_ids)
    #             phase_accomplishment = 0.0
    #             for task in phase.task_ids:
    #                 inspection = i.env['project.visual.inspection']
    #                 accomplishment = inspection.search([('date', '<=', i.date), ('task_id', '=', task.id)], order="date desc",limit=1)
    #                 if accomplishment[:1]:
    #                     phase_accomplishment += (task.task_weight / total_task_weight) * accomplishment.actual_accomplishment
    #             project_accomplishment += (phase.phase_weight / total_phase_weight) * phase_accomplishment
    #         i.actual = project_accomplishment

    # @api.depends('date','project_id', 'project_id.phase_ids', 'project_id.phase_ids.phase_weight', 'project_id.phase_ids.task_ids.task_weight', 'project_id.phase_ids.task_ids.visual_inspection', 'project_id.phase_ids.task_ids.visual_inspection.actual_accomplishment')
    def _get_actual_accomplishment(self):
        for i in self:
            project_accomplishment = 0.0
            if i.project_id.project_type == 'project':
                total_phase_weight = sum(rec.phase_weight for rec in i.project_id.phase_ids)
                for phase in i.project_id.phase_ids:
                    total_task_weight = sum(rec.task_weight for rec in phase.task_ids)
                    phase_accomplishment = 0.0
                    for task in phase.task_ids:
                        inspection = i.env['project.visual.inspection']
                        accomplishment = inspection.search([('date', '<=', i.date),
                                                            ('task_id', '=', task.id)],
                                                           order="date desc", limit=1)
                        if accomplishment[:1]:
                            phase_accomplishment += (task.task_weight / total_task_weight) * accomplishment.actual_accomplishment
                    project_accomplishment += (phase.phase_weight / total_phase_weight) * phase_accomplishment
                i.actual = project_accomplishment
            else:
                portfolio_accomplishment = 0.0
                total_project_weight = sum(rec.project_weight for rec in i.project_id.project_ids)
                for project in i.project_id.project_ids:
                    total_phase_weight = sum(rec.phase_weight for rec in project.phase_ids)
                    for phase in project.phase_ids:
                        total_task_weight = sum(rec.task_weight for rec in phase.task_ids)
                        phase_accomplishment = 0.0
                        for task in phase.task_ids:
                            inspection = i.env['project.visual.inspection']
                            accomplishment = inspection.search([('date', '<=', i.date),
                                                                ('task_id', '=', task.id)],
                                                               order="date desc", limit=1)
                            if accomplishment[:1]:
                                phase_accomplishment += (task.task_weight / total_task_weight) * accomplishment.actual_accomplishment
                        project_accomplishment += (phase.phase_weight / total_phase_weight) * phase_accomplishment
                    portfolio_accomplishment += (project.project_weight / total_project_weight) * project_accomplishment
                i.actual = portfolio_accomplishment


class Project(models.Model):
    _inherit = "project.project"

    retention_ratio = fields.Float(string="Retention", default=10, help="Retention Percentage Deduction per Billing", readonly=True, states={'draft': [('readonly', False)]})
    downpayment_paid = fields.Monetary(string="Down payment Paid", readonly=True, states={'draft': [('readonly', False)]})
    billing_ids = fields.One2many('project.progress.billing', 'project_id', string="Progress Billing")
    downpayment_invoice_ids = fields.Many2many('account.move', 'project_downpayment_invoice_rel', 'project_id', 'invoice_id', string="Downpayment Invoice", readonly=True, states={'draft': [('readonly', False)]})
    recoupment_additional_percentage = fields.Float(string="Additional Percentage for Recoupment", help="Additional Recoupment for every progress billing")
    # visual_inspection_ids = fields.One2many('project.visual.inspection', 'project_id')

    @api.onchange('downpayment_invoice_ids')
    def _onchange_downpayment_invoice_ids(self):
        for i in self:
            i.downpayment_paid = sum(line.amount_total for line in i.downpayment_invoice_ids)


class ProjectPhase(models.Model):
    _inherit = 'project.phase'

    billing_accomplishment_ids = fields.One2many('project.accomplishment.billing', 'phase_id', string="Billed Accomplishment")
    actual_accomplishment = fields.Float(store="True", compute="_actual_progress")

    @api.depends('task_ids', 'task_ids.visual_inspection')
    def _actual_progress(self):
        for i in self:
            total_task_weight = sum(rec.task_weight for rec in i.task_ids)
            actual_accomplishment = 0.0
            for task in i.task_ids:
                inspection = i.env['project.visual.inspection']
                accomplishment = inspection.search([('task_id', '=', task.id)], order="date desc",limit=1)
                if accomplishment[:1]:
                    actual_accomplishment += (task.task_weight / total_task_weight) * accomplishment.actual_accomplishment
            i.actual_accomplishment = actual_accomplishment
