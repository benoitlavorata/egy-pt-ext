
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger("_name_")


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _convert_prepared_anglosaxon_line(self, line, partner):
        res = super(ProductProduct, self)._convert_prepared_anglosaxon_line(line, partner)
        res['phase_id'] = line.get('phase_id', False)
        res['task_id'] = line.get('task_id', False)
        res['project_boq_category'] = line.get('project_boq_category', False)
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    project_related = fields.Boolean(string="A PO Project Related Invoice?", default=True, readonly=True, states={'draft': [('readonly', False)]})

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        if self.project_related:
            data['phase_id'] = line.phase_id.id
            data['task_id'] = line.task_id.id
            data['project_boq_category'] = line.project_boq_category
            return data

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        for i in res:
            inv_line = self.env['account.invoice.line'].browse(i.get('invl_id'))
            i['phase_id'] = inv_line.phase_id and inv_line.phase_id.id
            i['task_id'] = inv_line.task_id and inv_line.task_id.id
            i['project_boq_category'] = inv_line.project_boq_category
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('analytic_account_id')
    def _get_project_value(self):
        for i in self:
            project = i.env['project.project'].search([('analytic_account_id', '=', i.analytic_account_id.id)], limit=1)
            if project[:1]:
                i.project_id = project.id

    project_id = fields.Many2one('project.project', string="Project", store=True, compute="_get_project_value")
    phase_id = fields.Many2one('project.phase', string="Phase",
                               domain="[('project_id.analytic_account_id', '=', analytic_account_id)]")
    task_id = fields.Many2one('project.task', string="Task")
    project_boq_category = fields.Selection([
                                        ('meterial', 'Material'),
                                        ('subcon', 'Subcontractor'),
                                        ('labor', 'Human Resource/Labor'),
                                        ('equipment', 'Equipment'),
                                        ('overhead', 'Overheads')], string="Category")
    recorded_analytic = fields.Boolean()

    @api.onchange("project_id", "phase_id")
    def _onchange_project(self):
        vals = {}
        if self.project_id.project_type == 'project' and self.phase_id:
            vals['domain'] = {
                "task_id": [("phase_id", "=", self.phase_id.id)],
            }
        elif self.project_id.project_type == 'portfolio':
            vals['domain'] = {
                "task_id": [("project_id", "=", self.project_id.id)],
            }
        return vals


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    phase_id = fields.Many2one('project.phase', string="Phase")
    task_id = fields.Many2one('project.task', string="Task")
    project_boq_category = fields.Selection([
                                        ('meterial', 'Material'),
                                        ('subcon', 'Subcontractor'),
                                        ('labor', 'Human Resource/Labor'),
                                        ('equipment', 'Equipment'),
                                        ('overhead', 'Overheads')], string="Category")

    def _prepare_analytic_line(self):
        data = super(AccountMoveLine, self)._prepare_analytic_line()
        data[0]['phase_id'] = self.phase_id.id
        data[0]['task_id'] = self.task_id.id
        data[0]['project_boq_category'] = self.project_boq_category
        return data

    def _prepare_analytic_distribution_line(self, distribution):
        data = super(AccountMoveLine, self)._prepare_analytic_distribution_line(distribution)
        data['phase_id'] = self.phase_id and self.phase_id.id or False
        data['task_id'] = self.task_id and self.task_id.id or False
        data['project_boq_category'] = self.project_boq_category
        return data
    #
    #
    #     for i in self.invoice_id.invoice_line_ids:
    #         if not i.recorded_analytic and self.name == i.name and self.analytic_account_id.id == i.account_analytic_id.id:# and self.unit_amount == i.quantity and self.general_account_id.id == i.account_id.id:
    #
    #
    #
    #
    #     """ Prepare the values used to create() an account.analytic.line upon validation of an account.move.line having
    #         analytic tags with analytic distribution.
    #     """
    #     self.ensure_one()
    #     amount = -self.balance * distribution.percentage / 100.0
    #     default_name = self.name or (self.ref or '/' + ' -- ' + (self.partner_id and self.partner_id.name or '/'))
    #     return {
    #         'name': default_name,
    #         'date': self.date,
    #         'account_id': distribution.account_id.id,
    #         'partner_id': self.partner_id.id,
    #         'tag_ids': [(6, 0, [distribution.tag_id.id] + self._get_analytic_tag_ids())],
    #         'unit_amount': self.quantity,
    #         'product_id': self.product_id and self.product_id.id or False,
    #         'product_uom_id': self.product_uom_id and self.product_uom_id.id or False,
    #         'amount': amount,
    #         'general_account_id': self.account_id.id,
    #         'ref': self.ref,
    #         'move_id': self.id,
    #         'user_id': self.invoice_id.user_id.id or self._uid,
    #         'company_id': distribution.account_id.company_id.id or self.env.user.company_id.id,
    #     }
