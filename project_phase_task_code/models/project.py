
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class Project(models.Model):
    _inherit = "project.project"

    phase_sequence_id = fields.Many2one("ir.sequence", string="Phase Code Parameter")


class ProjectPhase(models.Model):
    _inherit = "project.phase"

    task_sequence_id = fields.Many2one("ir.sequence", string="Code Code Parameter")
    phase_code = fields.Char(string="Code", required=True, default="/")

    @api.model
    def create(self, vals):
        if vals.get('project_id') and (vals.get('phase_code') in [False, '/']):
            project = self.env['project.project'].browse(vals.get('project_id'))
            vals['phase_code'] = self.env['ir.sequence'].get(project.phase_sequence_id.code)
        res = super(ProjectPhase, self).create(vals)
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('phase_code', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        res = super(ProjectPhase, self).name_get()
        data = []
        for i in self:
            display_value = '%s [%s]'%(i.name, i.phase_code)
            data.append((i.id, display_value))
        if data:
            return data
        else: return res


class ProjectTask(models.Model):
    _inherit = "project.task"

    task_code = fields.Char(string="Code", required=True, default="/")

    @api.model
    def create(self, vals):
        if vals.get('phase_id') and (vals.get('task_code') in [False, '/']):
            project = self.env['project.phase'].browse(vals.get('phase_id'))
            vals['phase_code'] = self.env['ir.sequence'].get(project.task_sequence_id.code)
        res = super(ProjectTask, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('phase_id') and (vals.get('task_code') in [False, '/'] or self.task_code in [False, '/']):
            project = self.env['project.phase'].browse(vals.get('phase_id'))
            vals['task_code'] = self.env['ir.sequence'].get(project.task_sequence_id.code)
        res = super(ProjectTask, self).write(vals)
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('task_code', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        res = super(ProjectTask, self).name_get()
        data = []
        for i in self:
            display_value = '%s [%s]'%(i.name, i.task_code)
            data.append((i.id, display_value))
        if data:
            return data
        else: return res
