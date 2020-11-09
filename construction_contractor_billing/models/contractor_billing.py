from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger("\n\n\t\t\tTesting Module 1 2 3")


class ProjectContractorTask(models.Model):
    _name = 'project.contractor.task'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']
    _rec_name = 'task_id'

    contractor_id = fields.Many2one('project.contractor', string="Contractor", ondelete="cascade",
                                    track_visibility="always")
    task_id = fields.Many2one('project.task', string="Tasks/activities", required=True,
                              domain="[('project_id', '=', project_id), ('boq_id', 'not in', [False])]",
                              ondelete="cascade", track_visibility="always")
    phase_id = fields.Many2one('project.phase', string="Phase/Division", store=True,
                               related="task_id.phase_id")
    project_id = fields.Many2one('project.project', string="Project", track_visibility="always")
    currency_id = fields.Many2one('res.currency', related='project_id.company_id.currency_id',
                                  string="Company Currency")
    description = fields.Text(string="Description", track_visibility="always")
    category = fields.Selection([
                                ('meterial', 'Material Labor Cost'),
                                ('subcon', 'Subcontract/Outsource'),
                                ('equipment', 'Equipment')], string="Category", required=True)
    amount = fields.Monetary(string="Amount", required=True, track_visibility="always")
    accomplishment = fields.Float(string="Accomplishment", related="task_id.actual_accomplishment")
    billed = fields.Float(string="Billed")
    task_bill_ids = fields.Many2many('project.contractor.bill', 'contractor_task_bill_rel', string="Billed")

    @api.onchange('task_id', 'category')
    def _onchange_task(self):
        if self.task_id:
            if self.category == 'material':
                self.amount = sum((i.labor_cost + i.equipment_cost) * i.qty for i in self.task_id.boq_id.boq_material_ids)
            elif self.category == 'subcon':
                self.amount = self.task_id.service_budget
            else: self.amount = self.task_id.equipment_budget

    @api.constrains('amount', 'category')
    def check_amount(self):
        if self.category == 'material':
            bom = sum((i.labor_cost + i.equipment_cost) * i.qty for i in self.task_id.boq_id.boq_material_ids)
            if self.amount > sum((i.labor_cost + i.equipment_cost) * i.qty for i in self.task_id.boq_id.boq_material_ids):
                raise ValidationError(_('Amount should not greater than %s'%(bom)))
        elif self.category == 'subcon':
            if self.amount > self.task_id.service_budget:
                raise ValidationError(_('Amount should not greater than %s'%(self.task_id.service_budget)))
        elif self.category == 'equipment':
            if self.amount > self.task_id.equipment_budget:
                raise ValidationError(_('Amount should not greater than %s'%(self.task_id.service_budget)))
        if self.amount <= 0:
            raise ValidationError(_('Amount should be greater than Zero (0)'))

    @api.onchange('amount', 'category')
    def onchange_amount(self):
        if self.amount > 0 and self.category:
            self.check_amount()


class ProjectContractor(models.Model):
    _name = 'project.contractor'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']

    def _compute_amount(self):
        for i in self:
            total_amount = sum(rec.amount for rec in i.contractor_task_ids)
            i.total_amount = total_amount
            total_billed = sum(rec.total_amount for rec in self.env['project.contractor.bill'].
                               search([('project_contract_id', '=', i.id),
                                       ('state', '!=', 'canceled')]))
            i.total_billed = total_billed
            i.total_billable = total_amount - total_billed

    name = fields.Char(string="Reference", default='/')
    currency_id = fields.Many2one('res.currency', related='project_id.company_id.currency_id',
                                  string="Company Currency")
    project_id = fields.Many2one('project.project', string="Project", required=True,
                                 domain="[('project_type', '=', 'project')]",
                                 readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string="Contractor", domain="[('supplier', '=', True)]",
                                 required=True, readonly=True, states={'draft': [('readonly', False)]})
    contract_doc = fields.Binary(string="Memorandum", track_visibility="always", readonly=True,
                                 states={'draft': [('readonly', False)]})
    contractor_task_ids = fields.One2many('project.contractor.task', 'contractor_id',
                                          string="Tasks", readonly=True,
                                          states={'draft': [('readonly', False)]})
    bill_complete_only = fields.Boolean(string="100% completion should be billed only",
                                        readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date(string="Date", default=date.today(), required=True, readonly=True,
                       states={'draft': [('readonly', False)]})
    total_amount = fields.Monetary(string="Total Amount", compute="_compute_amount")
    total_billed = fields.Monetary(string="Total Billed", compute="_compute_amount")
    total_billable = fields.Monetary(string="Total Billable", compute="_compute_amount")

    def approve_request(self):
        super(ProjectContractor, self).approve_request()
        self.write({'name': self.env['ir.sequence'].next_by_code('project.contractor')})
        return True


class ProjectContractorBillTask(models.Model):
    _name = 'project.contractor.bill.task'

    bill_id = fields.Many2one('project.contractor.bill', string="Billing", ondelete="cascade")
    task_id = fields.Many2one('project.task', string="Tasks/activities")
    currency_id = fields.Many2one('res.currency', related='task_id.project_id.company_id.currency_id',
                                  string="Company Currency")
    amount = fields.Monetary(string="Contract Amount")
    accomplishment = fields.Float(string="Accomplishment", related="task_id.actual_accomplishment")
    billable_accomplishment = fields.Float(string="Billable Accomplishment")
    billable_amount = fields.Monetary(string="Billable Amount")
    category = fields.Selection([
                                ('meterial', 'Material'),
                                ('subcon', 'Subcontract/Outsource'),
                                ('labor', 'Human Resource/Labor'),
                                ('equipment', 'Equipment')], string="Category", required=True)


class ProjectContractorBill(models.Model):
    _name = 'project.contractor.bill'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'document.default.approval']

    def _compute_amount(self):
        for i in self:
            i.total_amount = sum(rec.billable_amount for rec in i.line_ids)

    name = fields.Char(string="Reference", default='/')
    project_contract_id = fields.Many2one('project.contractor', string="Contract", required=True,
                                          domain="[('partner_id', '=', partner_id)]", readonly=True,
                                          states={'draft': [('readonly', False)]})
    project_id = fields.Many2one('project.project', string="Project", store=True,
                                 related="project_contract_id.project_id")
    currency_id = fields.Many2one('res.currency', related='project_id.company_id.currency_id',
                                  string="Company Currency")
    partner_id = fields.Many2one('res.partner', string="Contractor",
                                 domain="[('supplier', '=', True)]", required=True,
                                 readonly=True, states={'draft': [('readonly', False)]})
    bill_date = fields.Date(string="Billing Date", required=True, default=date.today(),
                            states={'draft': [('readonly', False)]})
    note = fields.Text(string="Notes")
    line_ids = fields.One2many('project.contractor.bill.task', 'bill_id', string="Activities")
    billing_history = fields.Many2many('project.contractor.bill', 'history_contractor_bill_rel',
                                       'bill_id', 'history_id', string="History")
    total_amount = fields.Monetary(string="Total Amount", compute="_compute_amount")
    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True)
    invoice_state = fields.Selection([
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Status', related="invoice_id.state", store=True,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated."
             " It stays in the open status till the user pays the invoice.\n"
             " * The 'In Payment' status is used when payments have been registered for "
             "the entirety of the invoice in a journal configured to post entries "
             "at bank reconciliation only, and some of them haven't been reconciled with"
             " a bank statement line yet.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related"
             " journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    def _prepare_invoice(self, type):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        if type == 'out_invoice':
            account = self.partner_id.property_account_receivable_id.id
            payment_term = self.partner_id.property_payment_term_id.id
            journal_id = self.env['account.move'].default_get(['journal_id'])['journal_id']
            if not journal_id:
                raise UserError(_('Please define an accounting sales journal for this company.'))
        else:
            account = self.partner_id.property_account_payable_id.id
            payment_term = self.partner_id.property_supplier_payment_term_id.id
            journal_domain = [
                ('type', '=', 'purchase'),
                ('company_id', '=', self.project_id.company_id.id),
                ('currency_id', '=', self.partner_id.property_purchase_currency_id.id),
            ]
            journal = self.env['account.journal'].search(journal_domain, limit=1)
            if not journal[:1]:
                raise UserError(_('Please define an accounting purchase journal for this company.'))
            else: journal_id = journal.id
        invoice_vals = {
            'name': self.name,
            'origin': self.name,
            'type': type,
            'account_id': account,
            'partner_id': self.partner_id.id,
            'journal_id': journal_id,
            'currency_id': self.currency_id.id,
            'comment': self.note,
            'payment_term_id': payment_term,
            'fiscal_position_id': self.partner_id.property_account_position_id.id,
            'company_id': self.project_id.company_id.id,
            'invoice_line_ids': self._prepare_invoice_line(type)
        }
        return invoice_vals

    def _prepare_invoice_line(self, type):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = []
        if type == 'in_invoice':
            product = self.env.ref('construction_contractor_billing.product_project_contractor_billing',
                                   raise_if_not_found=False)
            if not product:
                return False
            account = product.property_account_expense_id or product.categ_id.property_account_expense_categ_id
            taxes = [(6, 0, product.supplier_taxes_id.ids)]
            if not account:
                raise UserError(_('Please define income account for '
                                  'this product: "%s" (id:%d) - or for its category: "%s".') %
                                (product.name, product.id, product.categ_id.name))
        fpos = self.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)
        for i in self.line_ids:
            amount = i.billable_amount
            name = '%s:\n %spercent accomplishment for billing cycle %s' % (i.task_id.name, i.billable_accomplishment,
                                                                            self.bill_date.strftime(DF))
            res += [(0, 0, {
                'product_id': product.id or False,
                'name': name,
                'origin': self.name,
                'account_id': account.id,
                'price_unit': amount,
                'quantity': 1,
                'invoice_line_tax_ids': taxes,
                'account_analytic_id': self.project_id.analytic_account_id.id,
                'phase_id': i.task_id.phase_id.id,
                'project_boq_category': i.category,
                'task_id': i.task_id.id,
            })]
        return res

    def create_billing_invoice(self):
        for i in self:
            found = False
            invoice = i.env['account.move']
            if i.total_amount == 0.0:
                raise  ValidationError(_('Nothing to Invoice!'))
            if not i.invoice_id or i.invoice_id.state in ['cancel']:
                found = True
                i.write({
                    'invoice_id': invoice.create(i._prepare_invoice('in_invoice')).id})
            if not found:
                raise ValidationError(_('Good Job! All invoice have been created. ^_^'))
            return True

    def compute_billable_task(self):
        data = []
        for i in self.project_contract_id.contractor_task_ids:
            billible = 0
            if self.project_contract_id.bill_complete_only:
                if i.task_id.actual_accomplishment == 100:
                    billible = 100.00
            else:
                billed = self.env['project.contractor.bill.task'].search(
                    [('task_id', '=', i.task_id.id),
                     ('bill_id', '!=', self.id),
                     ('bill_id.state', '!=', 'canceled')])
                billible = i.task_id.actual_accomplishment - sum(rec.billable_accomplishment for rec in billed)
            if billible > 0:
                data.append([0, 0, {
                    'task_id': i.task_id.id,
                    'amount': i.amount,
                    'accomplishment': i.task_id.actual_accomplishment,
                    'billable_accomplishment': billible,
                    'billable_amount': i.amount * (billible / 100.0),
                    'category': i.category
                    }])
        history_ids = self.search(
            [('project_contract_id', '=', self.project_contract_id.id),
             ('state', 'not in', ['canceled']),
             ('id', 'not in', [self.id])]).ids
        for line in self.line_ids:
            line.unlink()
        self.write({'line_ids': data, 'billing_history': [(6, 0, history_ids)]})
        return True

    def approve_request(self):
        super(ProjectContractorBill, self).approve_request()
        self.write({'name': self.env['ir.sequence'].next_by_code('project.contractor.billing')})
        return True
