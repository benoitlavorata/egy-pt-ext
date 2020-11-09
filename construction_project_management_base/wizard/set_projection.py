'''
Created on 4 July 2019

@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError




class SetProjection(models.TransientModel):
    _name = 'set.projection'

    survey_frequent = fields.Selection([('week', 'Week'),
                                         ('month', 'Month'),
                                          # ('quarter', 'Quarter')
                                          ], string="Frequent Status Review")
    extend_projection = fields.Boolean()
    number_of_frequent = fields.Integer(string="Frequent Duration", default="1", help="Number of Weeks/Months/Quarters")
    start_date = fields.Date(string="Start Date")

    @api.model
    def default_get(self, fields):
        res = super(SetProjection, self).default_get(fields)
        data = self.env['project.projection.accomplishment'].search([('project_id', '=',self._context.get('active_id'))], order='date desc', limit=1)
        res['start_date'] = data.date
        return res


    def set_projection(self):
        for i in self:
            if not i.survey_frequent:  raise ValidationError(_('Please set first "Review Cycle" in order to proceed.'))
            project = self.env['project.project'].browse(self._context.get('active_id'))
            if project.project_type == "project" and project.parent_id:
                portfolio_dates = []
                for accom in project.parent_id.projection_accomplishment_ids:
                    portfolio_dates.append(accom.date)
                if i.survey_frequent == 'week':
                    if portfolio_dates:
                        if min(portfolio_dates) > i.start_date or max(portfolio_dates) < i.start_date + relativedelta(days= (7*i.number_of_frequent)):
                            raise ValidationError(_("Project timeline should be within Project's Portfolio timeline %s to %s"%(min(portfolio_dates).strftime(DF), max(portfolio_dates).strftime(DF))))
                else:
                    months = 1
                    if i.survey_frequent == 'quarter': months = 4
                    if portfolio_dates:
                        if min(portfolio_dates) > i.start_date or max(portfolio_dates) < i.start_date + relativedelta(months= (months*i.number_of_frequent)):
                            raise ValidationError(_("Project timeline should be within Project's Portfolio timeline %s to %s"%(min(portfolio_dates).strftime(DF), max(portfolio_dates).strftime(DF))))
            start_date = i.start_date
            data_record = []
            if i.survey_frequent == 'week':
                if not i.extend_projection:
                    for line in project.projection_accomplishment_ids:
                        line.unlink()
                for r in range(i.number_of_frequent + 1):
                    self.env['project.projection.accomplishment'].create({
                        'project_id': self._context.get('active_id'),
                        'date': start_date
                    })
                    start_date = start_date + relativedelta(days=7)
                project_update = {}
                if i.extend_projection:
                    project_update['extention_date'] = start_date
                else:
                    project_update['start_date'] = i.start_date
                    project_update['projected_finished_date'] = start_date - relativedelta(days=7)
                project.write(project_update)
            else:
                months = 1
                if not i.extend_projection:
                    for line in project.projection_accomplishment_ids:
                        line.unlink()
                if i.survey_frequent == 'quarter': months = 4
                for r in range(i.number_of_frequent + 1):
                    self.env['project.projection.accomplishment'].create({
                        'project_id': self._context.get('active_id'),
                        'date': start_date
                    })
                    start_date = start_date + relativedelta(months=months)
                project_update = {}
                if i.extend_projection:
                    project_update['extention_date'] = start_date
                else:
                    project_update['start_date'] = i.start_date
                    project_update['projected_finished_date'] = start_date - relativedelta(months=months)
                project.write(project_update)
