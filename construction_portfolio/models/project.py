'''
Created on 11 August 2019

@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class AnalyticAccountTag(models.Model):
    _inherit = 'account.analytic.tag'

    def destribute_expense_evenly(self):
        for i in self.analytic_distribution_ids:
            i.write({'percentage': 100 / len(self.analytic_distribution_ids.ids)})

class Project(models.Model):
    _inherit = 'project.project'

    analytic_tag_id = fields.Many2one('account.analytic.tag', string="Analytic Tag", help="For all Expenses be able to distribute to projects related to the pofolion")
    analytic_group_id = fields.Many2one('account.analytic.group', string="Analytic Group")

    @api.onchange('parent_id', 'project_type')
    def _onchange_portfolio(self):
        if self.project_type == 'project' and self.parent_id:
            self.user_id = self.parent_id.user_id and self.parent_id.user_id.id or False
            self.partner_id = self.parent_id.partner_id and self.parent_id.partner_id.id or False

    @api.model
    def create(self, vals):
        if vals.get('project_type') != 'project':
            vals['analytic_group_id'] = self.env['account.analytic.group'].create({'name': vals.get('name'), 'description': 'Project Portfolio'}).id
            vals['analytic_tag_id'] = self.env['account.analytic.tag'].create({'name': vals.get('name'), 'active_analytic_distribution': True}).id
        res = super(Project, self).create(vals)
        if res.project_type == 'project' and res.parent_id:
            if res.analytic_account_id and res.parent_id and res.parent_id.analytic_group_id:
                res.analytic_account_id.write({
                    'group_id': res.parent_id.analytic_group_id.id
                })
            if res.parent_id.analytic_tag_id:
                res.parent_id.analytic_tag_id.write({'analytic_distribution_ids': [(0, 0, {'account_id': res.analytic_account_id.id, 'percentage': 100})]})
                res.parent_id.analytic_tag_id.destribute_expense_evenly()
        return res
