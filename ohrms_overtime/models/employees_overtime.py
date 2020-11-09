from dateutil import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import pytz
from pytz import timezone


class EmployeesOvertime(models.Model):
    _name = 'hr.employee.overtime'

    @api.model
    def get_default_project(self):
        ids = self.env["project.project"].search([("user_id", "=", self.env.user.id)], limit=1).id
        return ids

    @api.model
    def _get_project_domain(self):
        domain = []
        if self.env.user.has_group('ohrms_overtime.group_hr_project_officer'):
            projects = self.env['project.project'].search(
                [('user_id', '=', self.env.user.id)])
            pro_list = []
            for pro in projects:
                pro_list.append(pro.id)
            domain = [('id', 'in', pro_list)]
        return domain

    name = fields.Char()
    employees_ids = fields.Many2many('hr.employee', string="Employees")
    date_from = fields.Datetime(string="From", default=datetime.today())
    state = fields.Selection([('draft', 'Draft'), ('created', 'Created')], default="draft")
    date_to = fields.Datetime(string="To", default=datetime.today())
    project_id = fields.Many2one('project.project', default=get_default_project, domain=_get_project_domain)
    overtime_hours = fields.Float(compute="_get_days_overtime", store=True)
    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')],
                                     string="Duration Type",
                                     default="hours",
                                     required=True)
    type = fields.Selection([('cash', 'Cash'), ('leave', 'leave')], default="leave",
                            required=True, string="Type")

    @api.model
    def create(self, values):
        if not self.overtime_hours > 0:
            raise UserError(_('Please check overtime hour field!'))
        if len(values.get('employees_ids')[0][2]) > 0:
            if not values.get('name'):
                pro = values.get('project_id')
                txt = self.env['project.project'].search([('id', '=', pro)], limit=1).name
                dat = datetime.strptime(values.get('date_from'), '%Y-%m-%d %H:%M:%S')
                values['name'] = txt + " : " + str(dat.date())
            return super(EmployeesOvertime, self).create(values)
        else:
            raise UserError(_('You must select at least one employee...!'))

    def create_overtime(self):
        for item in self:
            for employee in item.employees_ids:
                self.env['hr.overtime'].create(
                    {
                        'project_id': self.project_id.id,
                        'employee_id': employee.id,
                        'duration_type': self.duration_type,
                        'date_from': self.date_from,
                        'date_to': self.date_to,
                        'days_no_tmp': self.overtime_hours,
                        'type': self.type,
                        'state': 'draft',
                    })
        self.state = 'created'

    @api.onchange('project_id')
    def get_employees_of_project(self):
        if self.project_id:
            employee_ids = self.env['hr.employee'].search(
                [('project_id', '=', self.project_id.id)])
            employees = []
            for employee in employee_ids:
                employees.append(employee.id)
            domain = {'employees_ids': [('id', 'in', employees)]}
            day_num = datetime.today().weekday()
            calendar = self.project_id.resource_calendar_id.id
            sch = self.project_id.resource_calendar_id.attendance_ids.search([('dayofweek', '=',
                                                                               day_num),
                                                                              ('calendar_id', '=', calendar)],
                                                                             limit=1).hour_to
            if sch:
                combined_from = fields.Datetime.today() + timedelta(seconds=sch * 3600)
                combined_to = fields.Datetime.today() + timedelta(seconds=(sch+2) * 3600)
                tz = timezone(self.env.user.tz or 'UTC')
                local_time_from = tz.localize(combined_from).astimezone(pytz.utc)
                local_time_to = tz.localize(combined_to).astimezone(pytz.utc)
                self.update({
                     'date_from': local_time_from.strftime('%Y-%m-%d %H:%M'),
                     'date_to': local_time_to.strftime('%Y-%m-%d %H:%M')
                })
            return {'domain': domain}
        else:
            self.update({'employees_ids': False})
            domain = {'employees_ids': [('id', '=', 0)]}
            return {'domain': domain}

    @api.depends('date_from', 'date_to', 'duration_type')
    def _get_days_overtime(self):
        for recd in self:
            if recd.date_from and recd.date_to:
                if recd.date_from > recd.date_to:
                    raise ValidationError(_('Start Date must be less than End Date'))
        for sheet in self:
            if sheet.date_from and sheet.date_to:
                start_dt = fields.Datetime.from_string(sheet.date_from)
                finish_dt = fields.Datetime.from_string(sheet.date_to)
                s = finish_dt - start_dt
                difference = relativedelta.relativedelta(finish_dt, start_dt)
                hours = difference.hours
                minutes = difference.minutes
                days_in_mins = s.days * 24 * 60
                hours_in_mins = hours * 60
                days_no = ((days_in_mins + hours_in_mins + minutes) / (24 * 60))

                diff = sheet.date_to - sheet.date_from
                days, seconds = diff.days, diff.seconds
                hours = days * 24 + seconds // 3600
                sheet.update({
                    'overtime_hours': hours if sheet.duration_type == 'hours' else days_no,
                })
