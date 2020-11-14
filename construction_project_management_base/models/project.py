"""
Created on 24 June 2019

@author: Dennis
"""
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class ProjectProjectionAccomplishment(models.Model):
    _name = 'project.projection.accomplishment'
    _rec_name = 'date'
    _order = 'date'

    project_id = fields.Many2one('project.project', string="Project", ondelete='cascade')
    date = fields.Date(string="Date")
    projected = fields.Float(string="Projected Percentage")
    actual = fields.Float(string="Actual Percentage")


class Project(models.Model):
    _name = "project.project"
    _inherit = ['mail.activity.mixin', 'project.project']

    def _compute_phase_count(self):
        phase_data = self.env['project.phase'].read_group([('project_id', 'in', self.ids)], ['project_id'], ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in phase_data)
        for project in self:
            project.phase_count = result.get(project.id, 0)

    image = fields.Binary(string="Report Image")
    project_type = fields.Selection([('project', 'Project'),
                                     ('portfolio', 'Portfolio')], string="Project Type", default='project',
                                    required=True)
    project_weight = fields.Float(string="Project Weight", default=1.0)
    project_ids = fields.One2many("project.project", "parent_id", string="Projects")

    phase_ids = fields.One2many('project.phase', 'project_id', string="Project Phases", readonly=True, states={'draft': [('readonly', False)]})
    phase_count = fields.Integer(compute='_compute_phase_count', string="Phases")
    projected_finished_date = fields.Date('Projected Finished Date', track_visibility="always")
    projected_end_date = fields.Date('Projected Closed and Turned Over Date', track_visibility="always")
    start_date = fields.Date('Start Date', track_visibility="always")
    finished_date = fields.Date('Finished Date', track_visibility="always")
    end_date = fields.Date(string='Closed and Turned Over Date', track_visibility="always")
    extention_date = fields.Date(string='Requested Extension Date', track_visibility="always")
    state = fields.Selection([('draft', 'Draft'),
                              ('inprogress', 'In Progress'),
                              ('finished', 'Finished'),
                              ('closed', 'Closed and Turned Over'),
                              ('canceled', 'Canceled'),
                              ('halted', 'Halted')], string="Status", readonly=True, default='draft',
                             track_visibility="always")
    stock_location_id = fields.Many2one('stock.location', string="Project Inventory Location", track_visibility="always")
    picking_type_id = fields.Many2one('stock.picking.type', string="Picking Operation", track_visibility="always")
    boq_setting = fields.Selection([('1', 'Project + Phase + Task + BOQ'),
                                    ('2', 'Project + Phase + Task + BOQ')], string="Project Setting", default="1")
    survey_frequent = fields.Selection([('week', 'Week'),
                                        ('month', 'Month'),
                                          # ('quarter', 'Quarter')
                                        ], string="Review Cycle", default="month", readonly=True,
                                       states={'draft': [('readonly', False)]})
    projection_accomplishment_ids = fields.One2many('project.projection.accomplishment', 'project_id',
                                                    string="Projection Accomplishment Timeline", readonly=True,
                                                    states={'draft': [('readonly', False)]})
    projection_set = fields.Boolean(store=True, compute="_get_projection_status")
    # Budget And Actual Expeditures
    # Todo: Make all this field a "Computed fields" Badget: based on the BOQs;
    # Expense: Based on the actual expense recored in the Analytic Account
    material_budget = fields.Float(string="Material Budget", store=True, compute="_get_budget_summary")
    material_expense = fields.Float(string="Material Expense")
    service_budget = fields.Float(string="Service Budget", store=True, compute="_get_budget_summary")
    service_expense = fields.Float(string="Service Expense")
    labor_budget = fields.Float(string="Labor Budget", store=True, compute="_get_budget_summary")
    labor_expense = fields.Float(string="Labor Expense")
    equipment_budget = fields.Float(string="Equipment Budget", store=True, compute="_get_budget_summary")
    equipment_expense = fields.Float(string="Equipment Expense")
    overhead_budget = fields.Float(string="Overhead Budget", store=True, compute="_get_budget_summary")
    overhead_expense = fields.Float(string="Overhead Expense")
    total_budget = fields.Float(string="Total Budget", store=True, compute="_get_budget_summary")
    total_expense = fields.Float(string="Total Expense")
    #Porfolio
    parent_id = fields.Many2one("project.project", string="Portfolio", domain="[('project_type', 'in', ['portfolio'])]",
                                track_visibility="always")
    project_count = fields.Integer(string="Projects", compute="_compute_project_count")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", copy=False,
                                          ondelete='set null', help="Link this project to an analytic account "
                                                                    "if you need financial management on projects. "
                                                                    "It enables you to connect projects with budgets,"
                                                                    " planning, cost and revenue analysis,"
                                                                    " timesheets on projects, etc.",
                                          track_visibility="always")

    employee_id = fields.Many2one("hr.employee", string="Employee")

    @api.constrains("start_date", "finished_date", "end_date")
    def chec_dates(self):
        if self.finished_date and self.start_date >= self.finished_date:
            raise ValidationError(_(" Finished Date must be greater than Start date"))
        if self.end_date and self.finished_date >= self.end_date:
            raise ValidationError(_("Turned Over date should be greater than Finished Date"))

    @api.depends('projection_accomplishment_ids')
    def _get_projection_status(self):
        for i in self:
            for line in i.projection_accomplishment_ids:
                i.projection_set = True
                continue
            # else: i.projection_set = False

    @api.model
    def name_create(self, name):
        """ Create a project with name_create should generate analytic account creation """
        values = {
            'name': name,
        }
        return self.create(values).name_get()[0]

    @api.model
    def create(self, values):
        if not values.get('analytic_account_id'):
            if values.get('project_type') == 'project':
                analytic_account = self.env['account.analytic.account'].create({
                    'name': values.get('name', _('Unknown Analytic Account')),
                    'company_id': values.get('company_id', self.env.user.company_id.id),
                    'partner_id': values.get('partner_id'),
                    'active': True,
                })
                values['analytic_account_id'] = analytic_account.id
        res = super(Project, self).create(values)
        return res

    def write(self, values):
        for project in self:
            if not project.analytic_account_id and project.project_type == 'project' and not values.get('analytic_account_id'):
                project._create_analytic_account()
            elif values.get('name') and project.analytic_account_id:
                project.analytic_account_id.write({'name': values.get('name')})
            # project.analytic_account_id.write({'parent_id': project.parent_id and project.parent_id.analytic_account_id.id or False})
        result = super(Project, self).write(values)
        return result

    def unlink(self):
        """ Delete the empty related analytic account """
        analytic_accounts_to_delete = self.env['account.analytic.account']
        for project in self:
            if project.analytic_account_id and not project.analytic_account_id.line_ids:
                analytic_accounts_to_delete |= project.analytic_account_id
        result = super(Project, self).unlink()
        analytic_accounts_to_delete.unlink()
        return result

    @api.model
    def _init_data_analytic_account(self):
        self.search([('analytic_account_id', '=', False)])._create_analytic_account()

    def _create_analytic_account(self):
        for project in self:
            analytic_account = self.env['account.analytic.account'].create({
                'name': project.name,
                'company_id': project.company_id.id,
                'partner_id': project.partner_id.id,
                'active': True,
            })
            project.write({'analytic_account_id': analytic_account.id})

    @api.onchange('parent_id', 'name')
    def _onchange_portfolio(self):
        for i in self:
            if i.parent_id:
                i.user_id = i.parent_id.user_id.id
                i.partner_id = i.parent_id.partner_id.id

    def _compute_project_count(self):
        for record in self:
            record.project_count = self.env['project.project'].search_count([
                                        ('project_type', '=', 'project'),
                                        ('parent_id', '=', record.id)
                                    ])

    @api.depends('task_ids', 'task_ids.material_budget', 'task_ids.service_budget', 'task_ids.overhead_budget',
                 'task_ids.equipment_budget', 'task_ids.labor_budget')
    def _get_budget_summary(self):
        for i in self:
            material = service = labor = equipment = overhead = 0.0
            for task in i.task_ids:
                material += task.material_budget
                service += task.service_budget
                labor += task.labor_budget
                equipment += task.equipment_budget
                overhead += task.overhead_budget
            i.material_budget = material
            i.service_budget = service
            i.labor_budget = labor
            i.equipment_budget = equipment
            i.overhead_budget = overhead
            i.total_budget = sum([material, service, labor, equipment, overhead])

    def view_phases(self):
        tree_id = self.env.ref('construction_project_management_base.project_phase_view_tree').id
        form_id = self.env.ref('construction_project_management_base.project_phase_view_form').id
        return {'name': 'Phases',
                'type': 'ir.actions.act_window',
                'res_model': 'project.phase',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(tree_id, 'tree'), (form_id, 'form')],
                'target': 'main',
                'domain': [('project_id', '=', active_id)],
                'context': {'default_project_id': active_id,
                            'default_user_id': self._user_id,
                            }
                }

    def lock_projection(self):
        for i in self:
            i.write({'projection_set': True})
        return True

    def set_inprogress(self):
        for i in self:
            if (not i.stock_location_id or not i.start_date or not i.picking_type_id) and i.project_type == 'project':
                raise ValidationError(_('You must supply value on the fields:\n '
                                        '1. Start Date\n 2. Project Inventory Location\n 3. Picking Operation'))
            elif not i.start_date and i.project_type == 'portfolio':
                raise ValidationError(_('You must supply value on the fields:\n 1. Start Date'))
            if not i.projection_set:
                raise ValidationError(_('Please set project Timeline Projection'))
            i.write({'state': 'inprogress'})
        return True

    def set_finished(self):
        for i in self:
            if not i.finished_date:
                raise ValidationError(_('You must supply value on the fields:\n 1. Finished Date'))
            i.write({'state': 'finished'})
        return True

    def set_close(self):
        for i in self:
            if not i.end_date:
                raise ValidationError(_('You must supply value on the fields:\n 1. Closed and Turned Over Date'))
            i.write({'state': 'closed'})
        return True

    def set_cancel(self):
        for i in self:
            i.write({'state': 'canceled'})
        return True

    def reset_to_draft(self):
        for i in self:
            i.write({'state': 'draft'})
        return True

    def set_halt(self):
        for i in self:
            i.write({'state': 'halted'})
        return True
