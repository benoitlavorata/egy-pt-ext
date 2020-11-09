from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class ProjectAccomplishmentBilling(models.Model):
    _name = 'project.accomplishment.billing'

    billing_id = fields.Many2one('project.progress.billing', string="Billing")
    phase_id = fields.Many2one('project.phase', string="Phase/Division")
    phase_weight = fields.Float(string="Phase Weight", store=True, related='phase_id.phase_weight')
    phase_status = fields.Float(string="Status")
    accomplishment = fields.Float(string="Billable(%)")
    cycle_date = fields.Date(string="Billing Cycle Date", store=True, compute='_get_billing_details')

    billing_state = fields.Selection([
                        ('draft', 'Draft'),
                        ('submitted', 'Waiting for Verification'),
                        ('verified', 'Waiting for Approval'),
                        ('approved', 'Approved'),
                        ('canceled', 'Cancelled')
                    ], string="Status", store=True, compute='_get_billing_details')

    @api.depends('billing_id', 'billing_id.state')
    def _get_billing_details(self):
        for i in self:
            if i.billing_id:
                i.billing_state = i.billing_id.state
                i.cycle_date = i.billing_id.cycle_date


class ProjectProgressBilling(models.Model):
    _name = 'project.progress.billing'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    def _get_invoice_state(self):
        for i in self:
            if i.invoice_id:
                i.invoice_state = i.invoice_id.state

    @api.depends('billing_accomplishment_ids', 'billing_accomplishment_ids.accomplishment')
    def _get_total_accomplishment(self):
        for i in self:
            i.total_accomplishment = sum(line.accomplishment for line in i.billing_accomplishment_ids)

    @api.depends('project_id', 'total_accomplishment', 'billing_accomplishment_ids')
    def _compute_billing_details(self):
        for i in self:
            if i.project_id:
                i.partner_id = i.project_id.partner_id.id
                i.retention_ratio = i.project_id.retention_ratio
                i.project_contract = i.project_id.project_contract_amount
                i.billable = i.project_contract * (i.total_accomplishment / 100)
                i.current_billable = i.billable
                i.retention = i.billable * (i.retention_ratio / 100)
                i.invoiceable = i.billable - i.retention
                recoupment = i.project_id.downpayment_paid *\
                             ((i.total_accomplishment + i.project_id.recoupment_additional_percentage) / 100)
                total_billed = 0.0
                total_retention = 0.0
                total_recoupment = 0.0
                total_invoiced = 0.0
                hirstory_ids = []

                for line in i.project_id.billing_ids:
                    if line.state in ['approved']:
                        hirstory_ids.append(line.id)
                        total_billed += line.billable
                        total_retention += line.retention
                        total_recoupment += line.recoupment
                        total_invoiced += line.invoiceable
                i.billing_history_ids = [(6, 0, hirstory_ids)]
                i.previous_billed = total_billed
                if (i.project_contract - total_billed - i.billable) < 0.0:
                    i.billable = i.project_contract - total_billed
                i.remaining_billable = i.project_contract - total_billed - i.billable
                if (recoupment + total_recoupment) <= i.project_id.downpayment_paid:
                    i.recoupment = recoupment
                else:
                    i.recoupment = i.project_id.downpayment_paid - total_recoupment

    @api.onchange('billing_cycle_id')
    def _onchange_billing_cycle(self):
        for i in self:
            if i.billing_cycle_id:
                i.cycle_date = i.billing_cycle_id.date

    currency_id = fields.Many2one('res.currency', related='project_id.company_id.currency_id',
                                  string="Company Currency")
    partner_id = fields.Many2one('res.partner', string="Customer", compute='_compute_billing_details',
                                 store=True)
    project_id = fields.Many2one('project.project', string="Project", readonly=True,
                                 states={'draft': [('readonly', False)]})
    name = fields.Char(string="Reference", default='/')
    note = fields.Text(string="Notes")
    billing_cycle_id = fields.Many2one('project.projection.accomplishment',
                                       string="Billing Cycle", readonly=True,
                                       states={'draft': [('readonly', False)]}, copy=False)
    cycle_date = fields.Date(string="Billing Cycle Date", required=True, readonly=True,
                             states={'draft': [('readonly', False)]})
    date_run = fields.Date(string="Date Run", readonly=True)
    user_id = fields.Many2one('res.users', srtring="Run By", readonly=True)
    retention_ratio = fields.Float(string="Retention", compute='_compute_billing_details', store=True)
    billing_accomplishment_ids = fields.One2many('project.accomplishment.billing', 'billing_id',
                                                 string="Actual Accomplishment of the Month",
                                                 readonly=True, states={'draft': [('readonly', False)]})
    billing_history_ids = fields.Many2many('project.progress.billing', 'project_billing_rel',
                                           'billing_id', 'history_id', string="Billing History",
                                           store=True, compute='_compute_billing_details')
    total_accomplishment = fields.Float(string="Total Accomplishment", store=True,
                                        compute='_get_total_accomplishment')
    current_billable = fields.Monetary(string="Billable", store=True,
                                       compute='_compute_billing_details')
    billable = fields.Monetary(string="Billable", store=True, compute='_compute_billing_details')
    retention = fields.Monetary(string="Retention", store=True, compute='_compute_billing_details')
    recoupment = fields.Monetary(string="Recoupment", store=True, compute='_compute_billing_details')
    recoupment_invoice_id = fields.Many2one('account.move', string="Invoice")
    invoiceable = fields.Monetary(string="Invoiceable", store=True, compute='_compute_billing_details')
    project_contract = fields.Monetary(string="Contract Value", store=True,
                                       compute='_compute_billing_details')
    previous_billed = fields.Monetary(string="Total Previously Billed", store=True,
                                      compute='_compute_billing_details')
    remaining_billable = fields.Monetary(string="Total Remaining Billable", store=True,
                                         compute='_compute_billing_details')
    include_unfinished_activity = fields.Boolean(string="Include Unfinished Activity/Task")
    state = fields.Selection([
                        ('draft', 'Draft'),
                        ('submitted', 'Waiting for Verification'),
                        ('verified', 'Waiting for Approval'),
                        ('approved', 'Approved'),
                        ('canceled', 'Cancelled')
                    ], string="Status", default='draft', readonly=True)
    invoice_id = fields.Many2one('account.move', string="Invoice")
    invoice_state = fields.Selection([
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated."
             " It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid."
             " Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.",
        compute="_get_invoice_state")

    submitted_date = fields.Datetime(string="Submitted Date", readonly=True)
    submitted_by = fields.Many2one('res.users', string="Submitted By", readonly=True)
    verified_date = fields.Datetime(string="Verified Date", readonly=True)
    verified_by = fields.Many2one('res.users', string="Verified By", readonly=True)
    approved_date = fields.Datetime(string="Approved Date", readonly=True)
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True)
    canceled_date = fields.Datetime(string="Canceled Date", readonly=True)
    canceled_by = fields.Many2one('res.users', string="Canceled By", readonly=True)
    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Number of documents attached")

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            if not self.project_id.partner_id: raise ValidationError(_("Please assign a Customer first"
                                                                       " to the Project"))
            accomplishment = self.env['project.projection.accomplishment'].\
                search([('project_id', '=', self.project_id.id)])
            return {'domain': {'billing_cycle_id': [('id', 'in', accomplishment.ids)]}}

    def compute_phase_accomplishment(self):
        for i in self:
            billable = []
            for line in i.billing_accomplishment_ids:
                line.unlink()
            total_phase_weight = sum(rec.phase_weight for rec in i.project_id.phase_ids)

            for phase in i.project_id.phase_ids:
                previous_accomplishement = self.env['project.accomplishment.billing'].\
                    search([('cycle_date', '<=', i.cycle_date), ('phase_id', '=', phase.id),
                            ('billing_state', 'not in', ['draft'])])#, order="cycle_date desc", limit=1)
                total_task_weight = sum(rec.task_weight for rec in phase.task_ids)
                phase_accomplishment = 0.0
                for task in phase.task_ids:
                    inspection = i.env['project.visual.inspection']
                    accomplishment = inspection.search([('date', '<=', i.cycle_date),
                                                        ('task_id', '=', task.id)],
                                                       order="date desc", limit=1)
                    if accomplishment[:1]:
                        if i.include_unfinished_activity:
                            phase_accomplishment += (task.task_weight / total_task_weight) * accomplishment.actual_accomplishment
                        else:
                            if accomplishment.actual_accomplishment >= 100.00:
                                phase_accomplishment += (task.task_weight / total_task_weight) * accomplishment.actual_accomplishment
                project_phase_accomplishment = (phase.phase_weight / total_phase_weight) * phase_accomplishment

                billable_accomplishment = (project_phase_accomplishment - sum([line.accomplishment for line in previous_accomplishement]))
                if billable_accomplishment > 0.0:
                    billable.append([0, 0, {
                        'phase_id': phase.id,
                        'phase_status': phase_accomplishment,
                        'accomplishment': billable_accomplishment,
                    }])
            i.write({'billing_accomplishment_ids': billable})
        return True

    def _compute_attached_docs_count(self):
        Attachment = self.env['ir.attachment']
        for i in self:
            i.doc_count = Attachment.search_count([
                ('res_model', '=', 'project.progress.billing'), ('res_id', 'in', i.ids)
            ])

    def attachment_tree_view(self):
        self.ensure_one()
        domain = [('res_model', '=', 'project.progress.billing'), ('res_id', 'in', self.ids)]
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Documents are attached to the Progress Billing of your project.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your project.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }

    @api.model
    def create(self, vals):
        vals['user_id'] = self._uid
        vals['date_run'] = datetime.now()
        return super(ProjectProgressBilling, self).create(vals)

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
            journal= self.env['account.journal'].search(journal_domain, limit=1)
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
            'user_id': self.user_id and self.user_id.id,
            'invoice_line_ids': [[0,0, self._prepare_invoice_line(type)]]
        }
        return invoice_vals

    def _prepare_invoice_line(self, type):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        if type == 'out_invoice':
            product = self.env.ref('construction_progress_billing.product_project_billing',
                                   raise_if_not_found=False)
            if not product:
                return False
            amount = self.invoiceable
            account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
            taxes = [(6, 0, product.taxes_id.ids)]
            name = '%s percent Project Accomplishment as of %s billing cycle'%(self.total_accomplishment, self.cycle_date)
            if not account:
                raise UserError(_('Please define income account for '
                                  'this product: "%s" (id:%d) - or for its category: "%s".') %
                                (product.name, product.id, product.categ_id.name))
        else:
            product = self.env.ref('construction_progress_billing.product_project_recoupment',
                                   raise_if_not_found=False)
            if not product:
                return False
            amount = self.recoupment
            account = product.property_account_expense_id or product.categ_id.property_account_expense_categ_id
            taxes = [(6, 0, product.supplier_taxes_id.ids)]

            name = '%s percent Recoupment as of %s billing cycle'%(self.total_accomplishment, self.cycle_date)
            if not account:
                raise UserError(_('Please define income account for this '
                                  'product: "%s" (id:%d) - or for its category: "%s".') %
                                (product.name, product.id, product.categ_id.name))
        fpos = self.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'product_id': product.id or False,
            'name': name,
            'origin': self.name,
            'account_id': account.id,
            'price_unit': amount,
            'quantity': 1,
            'invoice_line_tax_ids': taxes,
            'account_analytic_id': self.project_id.analytic_account_id.id,
        }
        return res

    def create_billing_invoice(self):
        for i in self:
            found = False
            invoice = i.env['account.move']
            if i.total_accomplishment == 0.0:
                raise ValidationError(_('Nothing to Invoice!'))
            if not i.invoice_id or i.invoice_id.state in ['cancel'] and i.invoiceable != 0.00:
                found = True
                i.write({
                    'invoice_id':  invoice.create(i._prepare_invoice('out_invoice')).id})
            if not i.recoupment_invoice_id or i.recoupment_invoice_id.state in ['cancel'] and i.recoupment != 0.00:
                found = True
                i.write({
                    'recoupment_invoice_id': invoice.create(i._prepare_invoice('in_invoice')).id})
            if not found:
                raise  ValidationError(_('Good Job! All invoice have been created. ^_^'))
            return True

    def submit_record(self):
        for i in self:
            if i.total_accomplishment == 0.0:
                raise ValidationError(_('Nothing to Bill!'))
            i.write({
                'submitted_date': datetime.now(),
                'submitted_by': i._uid,
                'state': 'submitted',
            })
        return True

    def verify_record(self):
        for i in self:
            i.write({
                'verified_date': datetime.now(),
                'verified_by': i._uid,
                'state': 'verified',
            })
        return True

    def approve_record(self):
        for i in self:
            i.write({
                'approved_date': datetime.now(),
                'approved_by': i._uid,
                'state': 'approved',
                'name': self.env['ir.sequence'].next_by_code('project.billing.doc')
            })
        return True

    def cancel_record(self):
        for i in self:
            i.write({
                'canceled_date': datetime.now(),
                'canceled_by': i._uid,
                'state': 'canceled',
            })
        return True
