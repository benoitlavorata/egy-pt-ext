from odoo import models, fields,api,_
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_max_overtime(self):
        ids = self.env['ir.config_parameter'].sudo().get_param('max.over')
        return ids

    project_id = fields.Many2one('project.project')
    max_over = fields.Char("Max Overtime", default=get_max_overtime)
    overtime_limit = fields.Float(compute="get_overtime_currentmonth", string="Overtime")

    def get_overtime_currentmonth(self):
        for item in self:
            start_date = datetime(year=datetime.now().year,month=datetime.now().month, day=1)
            end_date = datetime(year=datetime.now().year, month=datetime.now().month, day=30)
            counter = 0
            overtime_ids = self.env['hr.overtime'].search([('create_date', '>=', str(start_date))
                                                           , ('create_date', '<=', str(end_date))
                                                           , ('employee_id', '=', item.id)])
            for overtime in overtime_ids:
                if overtime.duration_type == 'hours':
                    counter += overtime.days_no_tmp
                else:
                    counter += overtime.days_no_tmp*24

            item.overtime_limit = counter
