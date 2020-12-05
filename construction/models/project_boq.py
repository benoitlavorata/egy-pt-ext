from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class ProjectBoq(models.Model):
    _name = 'project.boq'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Bill of Quantity"

    name = fields.Char(string='Reference Number', index=True, readonly=True,
                       copy=False, default=lambda self: _('New'))
    date = fields.Date(default=fields.Date.context_today, required=True, track_visibility='onchange')
    project_id = fields.Many2one('project.project', required=True, tracking=True, track_visibility="onchange")
    partner_id = fields.Many2one(related='project_id.partner_id', readonly=True, index=True, store=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Submitted'),
                              ('approved', 'Approved'),
                              ('cancelled', 'Cancelled')], string='Status',
                             readonly=True, copy=False, index=True,
                             track_visibility='onchange', default='draft')
    poq_line_ids = fields.One2many(comodel_name='project.boq.lines', inverse_name='boq_id',
                                   string=_("Lines"))
    boq_total_price = fields.Float(string="Total Price", readonly=True, store=True, index=True,
                                   compute="_compute_total")
    boq_total_qty = fields.Float(string="Total Quantity", readonly=True, store=True, index=True,
                                 compute="_compute_total")
    submitted_by = fields.Char("Submitted By", readonly=True, copy=False)
    cancelled_by = fields.Char("Cancelled By", readonly=True, copy=False)
    approved_by = fields.Char("Approved By", readonly=True, copy=False)
    submitted_date = fields.Datetime("Submitted Date", readonly=True, copy=False)
    cancelled_date = fields.Datetime("Cancelled Date", readonly=True, copy=False)
    approved_date = fields.Datetime("Approved Date", readonly=True, copy=False)
    notes = fields.Html()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('project.boq') or 'New'
        result = super(ProjectBoq, self).create(vals)
        return result

    @api.depends('poq_line_ids.total_price', 'poq_line_ids.qty')
    def _compute_total(self):
        for boq in self:
            total_price = 0.0
            total_qty = 0.0
            for line in boq.poq_line_ids:
                total_price += line.total_price
                total_qty += line.qty
            boq.boq_total_price = total_price
            boq.boq_total_qty = total_qty

    def boq_action_submit(self):
        if self.boq_total_price > 0:
            user = self.env['res.users'].browse(self.env.uid)
            self.write({'state': 'submitted',
                        'submitted_by': user.name,
                        'submitted_date': datetime.today()})
            if self.name == 'New':
                val = self.env['ir.sequence'].next_by_code('project.boq')
                self.write({'name': val})
        else:
            raise ValidationError(_("You Cannot submit BOQ without price"))

    def boq_action_approve(self):
        if self.boq_total_price > 0:
            user = self.env['res.users'].browse(self.env.uid)
            self.write({'state': 'approved',
                        'approved_by': user.name,
                        'approved_date': datetime.today()})
        else:
            raise ValidationError(_("You Cannot approve BOQ without cost and price"))

    def boq_action_cancel(self):
        user = self.env['res.users'].browse(self.env.uid)
        return self.write({'state': 'cancelled',
                           'cancelled_by': user.name,
                           'cancelled_date': datetime.today()})

    def boq_action_draft(self):
        return self.write({
            'state': 'draft',
        })


class ProjectBoqLine(models.Model):
    _name = 'project.boq.lines'
    _description = "Project Bill of Quantity Lines"

    boq_id = fields.Many2one('project.boq')
    product_id = fields.Many2one('product.product', domain="[('boq_type', '=', 'project_boq')]", required=True)
    name = fields.Char(required=True)
    uom = fields.Many2one("uom.uom", related='product_id.uom_id', required=True)
    qty = fields.Float(required=True, default=0.0)
    unit_price = fields.Float(string='Unit Price', required=True, default=0.0)
    total_price = fields.Float(string='Total Price', index=True, readonly=True, default=0.0)
    prev_qty = fields.Float(string='Previous', index=True, readonly=True, default=0.0)
    curr_qty = fields.Float(string='Current', index=True, readonly=True, default=0.0)
    Total_qty = fields.Float(string='Total', index=True, readonly=True, default=0.0)
    per = fields.Float(string='Percentage', index=True, readonly=True, default=0.0)
    qty_per = fields.Float(string='Tons', index=True, readonly=True, default=0.0)

    @api.onchange('qty', 'unit_price')
    def _onchange_total(self):
        for line in self:
            if line.qty > 0 and line.unit_price > 0:
                total_price = line.qty * line.unit_price
                line.total_price = total_price
