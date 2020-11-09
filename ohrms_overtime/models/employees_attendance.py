
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import pytz
from pytz import timezone


class HrEmployeesAttendance(models.Model):
    _name = 'hr.employees.attendance'

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
    project_id = fields.Many2one('project.project', default=get_default_project, domain=_get_project_domain)
    check_in = fields.Datetime(required=1)
    check_out = fields.Datetime(required=1)
    state = fields.Selection([('draft', 'Draft'), ('created', 'Created')], default="draft")

    @api.model
    def create(self, values):
        if len(values.get('employees_ids')[0][2]) > 0:
            if not values.get('name'):
                pro = values.get('project_id')
                txt = self.env['project.project'].search([('id', '=', pro)], limit=1).name
                dat = datetime.strptime(values.get('check_in'), '%Y-%m-%d %H:%M:%S')
                values['name'] = txt + " : " + str(dat.date())
            return super(HrEmployeesAttendance, self).create(values)
        else:
            raise UserError(_('You must select at least one employee...!'))

    def create_attendance(self):
        for item in self:
            for employee in item.employees_ids:
                self.env['hr.attendance'].create(
                    {
                            'employee_id': employee.id,
                            'check_in': self.check_in,
                            'check_out': self.check_out,
                        })
        self.state = 'created'

    @api.onchange('project_id')
    def get_employees_of_project(self):
        if self.project_id:
            day_num = datetime.today().weekday()
            calendar = self.project_id.resource_calendar_id.id
            sch = self.project_id.resource_calendar_id.attendance_ids.search([('dayofweek', '=',
                                                                               day_num),
                                                                              ('calendar_id', '=', calendar)],
                                                                             limit=1)
            if sch:
                combined_in = fields.Datetime.today() + timedelta(seconds=sch.hour_from*3600)
                combined_out = fields.Datetime.today() + timedelta(seconds=sch.hour_to*3600)
                tz = timezone(self.env.user.tz or 'UTC')
                local_time_in = tz.localize(combined_in).astimezone(pytz.utc)
                local_time_out = tz.localize(combined_out).astimezone(pytz.utc)
                self.check_in = local_time_in.strftime('%Y-%m-%d %H:%M')
                self.check_out = local_time_out.strftime('%Y-%m-%d %H:%M')
            employee_ids = self.env['hr.employee'].search(
                [('project_id', '=', self.project_id.id)])
            employees = []
            for employee in employee_ids:
                employees.append(employee.id)
            domain = {'employees_ids': [('id', 'in', employees)]}
            return {'domain': domain}
        else:
            domain = {'employees_ids': [('id', '=', 0)]}
            return {'domain': domain}

