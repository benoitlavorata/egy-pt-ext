'''
Created on 4 July 2019

@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class ProjectPhaseTemplate(models.Model):
    _name = 'project.phase.template'

    name = fields.Char(string="Phase Name", required=True)
    description = fields.Text(string="Description")
    

class ProjectPhase(models.Model):
    _name = 'project.phase'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'phase_name_id'

    def _compute_task_count(self):
        phase_data = self.env['project.task'].read_group([('phase_id', 'in', self.ids)], ['phase_id'], ['phase_id'])
        result = dict((data['phase_id'][0], data['phase_id_count']) for data in phase_data)
        for phase in self:
            phase.task_count = result.get(phase.id, 0)

    project_id = fields.Many2one('project.project', string="Project")
    name = fields.Char(string="Name", store=True, related="phase_name_id.name")
    phase_name_id = fields.Many2one('project.phase.template', string="Name", required=True)
    user_id = fields.Many2one('res.users', string="Assigned User")
    phase_weight = fields.Float(string="Weight", default=1.0)
    duration = fields.Integer(string="Number of Days", default=1)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    task_ids = fields.One2many('project.task', 'phase_id', string="Tasks")
    task_count = fields.Integer(compute='_compute_task_count', string="Phases")

    state = fields.Selection([('draft', 'Draft'),
                              ('inprogress', 'In Progress'),
                              ('closed', 'Closed'),
                              ('canceled', 'Canceled'),
                              ('halted', 'Halted')], string="Status", readonly=True, default='draft')
