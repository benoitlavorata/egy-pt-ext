from odoo import api, fields, models, _

CONFIG_PARAM_MAX_OVERTIME = "max.over"


class HrContractOvertime(models.Model):
    _inherit = 'hr.contract'

    over_hour = fields.Monetary('Hour Wage')
    over_day = fields.Monetary('Day Wage')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    max_over = fields.Char(string='Max Over Time', default=104, required=1)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        max_over = ir_config.get_param(CONFIG_PARAM_MAX_OVERTIME, default=104)
        res.update(
            max_over=max_over
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        ir_config.set_param(CONFIG_PARAM_MAX_OVERTIME, self.max_over or 104)


