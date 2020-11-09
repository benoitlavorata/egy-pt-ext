# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from datetime import datetime


class SkitProjectBOQ(models.Model):
    _name = 'project.boq'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']
    _description = 'Bill Of Quantity'

    @api.onchange('phase_id')
    def _onchange_phase_id(self):
        tasks = self.env['project.task'].search([('id', 'not in', self.env['project.boq'].search([]).mapped("task_id").ids)
                                                 ])
        if self.phase_id:
            return {'domain': {'task_id': [('project_id', '=', self.project_id.id), ('phase_id', '=', self.phase_id.id ), ('id', 'in', tasks.ids)]
                               }}

    name = fields.Char(string='Reference Number', index=True, readonly=True,
                       copy=False, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string="Project")
    phase_id = fields.Many2one('project.phase', string="Phase",
                               domain="[('project_id', '=', project_id)]")
    task_id = fields.Many2one('project.task', string="Task", copy=False)
    allocated_budget = fields.Integer(string="Allocated Budget", readonly=True)
    qty = fields.Float(string="Quantity", readonly=True,
                       digits=dp.get_precision('Product Price'))
    uom_id = fields.Many2one('uom.uom', string="UOM", readonly=True,
                             help="Unit of Measure")
    state = fields.Selection([('draft', 'Draft'),
                            ('submitted','Submitted'),
                            ('confirmed', 'Confirmed'),
                            ('verified', 'Verified'),
                            ('approved', 'Approved'),
                            ('cancelled', 'Cancelled')], string='Status',
                             readonly=True, copy=False,
                             index=True,
                             track_visibility='onchange', default='draft')

    labor_total = fields.Float(string="Labor", compute='_compute_boq_labor')
    equipment_total = fields.Float(string="Equipment",
                                   compute='_compute_boq_equipment')
    scservice_total = fields.Float(string="Sub-Contractor Services",
                                   compute='_compute_boq_scservice')
    material_total = fields.Float(string="Material",
                                  compute='_compute_boq_material')
    overheadothers_total = fields.Float(string="Overheads and Others",
                                        compute='_compute_boq_overhead')
    total_boq = fields.Float(string="Total BOQ",
                             compute='_compute_tot_boq')
    notes = fields.Text("Notes")
    submitted_by = fields.Char("Submitted By", readonly=True, copy=False)
    confirmed_by = fields.Char("Confirmed By", readonly=True, copy=False)
    cancelled_by = fields.Char("Cancelled By", readonly=True, copy=False)
    verified_by = fields.Char("Verified By", readonly=True, copy=False)
    approved_by = fields.Char("Approved By", readonly=True, copy=False)
    submitted_date = fields.Datetime("Submitted Date", readonly=True, copy=False)
    confirmed_date = fields.Datetime("Confirmed Date", readonly=True, copy=False)
    cancelled_date = fields.Datetime("Cancelled Date", readonly=True, copy=False)
    verified_date = fields.Datetime("Verified Date", readonly=True, copy=False)
    approved_date = fields.Datetime("Approved Date", readonly=True, copy=False)
    change_order_count = fields.Integer(string='# of Change Order',
                                        compute="_get_project_eco",
                                        readonly=True)
    project_eco_ids = fields.Many2many("project.eco", string='ECO',
                                       compute="_get_project_eco",
                                       readonly=True, copy=False)
    boq_material_ids = fields.One2many('boq.material', 'boq_id',
                                       string='Materials')
    boq_equipment_ids = fields.One2many('boq.equipment', 'boq_id',
                                        string='Equipment')
    boq_scservice_ids = fields.One2many('boq.scservice', 'boq_id',
                                        string='SubContractor Service')
    boq_labor_ids = fields.One2many('boq.labor', 'boq_id', string="Labor")
    boq_overhead_ids = fields.One2many('boq.overhead', 'boq_id',
                                       string="OverHead")

    @api.depends('state')
    def _get_project_eco(self):
        for boq in self:
            project_eco_ids = self.env['project.eco'].sudo().search([('boq_id', '=', boq.id)])
            boq.update({
                'change_order_count': len(set(project_eco_ids.ids)),
                'project_eco_ids': project_eco_ids.ids
            })

    @api.depends('boq_material_ids')
    def _compute_boq_material(self):
        material_total = 0
        for ids in self:
            for material in ids.boq_material_ids:
                material_total = material_total+material.subtotal
            ids.update({'material_total': material_total})

    @api.depends('boq_equipment_ids')
    def _compute_boq_equipment(self):
        equipment_total = 0
        for ids in self:
            for equipment in ids.boq_equipment_ids:
                equipment_total = equipment_total+equipment.subtotal
            ids.update({'equipment_total': equipment_total})

    @api.depends('boq_scservice_ids')
    def _compute_boq_scservice(self):
        scservice_total = 0
        for ids in self:
            for service in ids.boq_scservice_ids:
                scservice_total = scservice_total + service.subtotal
            ids.update({'scservice_total': scservice_total})

    @api.depends('boq_labor_ids')
    def _compute_boq_labor(self):
        labor_total = 0
        for ids in self:
            for labor in ids.boq_labor_ids:
                labor_total = labor_total + labor.labor_total
            ids.update({'labor_total': labor_total})

    @api.depends('boq_overhead_ids')
    def _compute_boq_overhead(self):
        overhead_total = 0
        for ids in self:
            for overhead in ids.boq_overhead_ids:
                overhead_total = overhead_total+overhead.subtotal
            ids.update({'overheadothers_total': overhead_total})

    @api.depends('labor_total', 'equipment_total', 'scservice_total', 'material_total', 'overheadothers_total')
    def _compute_tot_boq(self):
        for ids in self:
            tot_val = (ids.labor_total+ids.equipment_total+ids.scservice_total+ids.material_total+ids.overheadothers_total)
            ids.update({'total_boq': tot_val})

    @api.onchange('task_id')
    def onchange_task(self):
        if self.task_id:
            task_id = self.task_id
            self.update({'allocated_budget': task_id.task_budget,
                        'qty': task_id.qty,
                        'uom_id':  task_id.uom_id.id
                        })

    @api.model
    def create(self, vals):
        if 'task_id' in vals:
            task_id = vals['task_id']
            task = self.env['project.task'].search([('id', '=', task_id)])
            vals['allocated_budget'] = task.task_budget
            vals['qty'] = task.qty
            vals['uom_id'] = task.uom_id.id
        result = super(SkitProjectBOQ, self).create(vals)
        return result

    def action_view_change_order(self):
        project_eco = self.mapped('project_eco_ids')
        action = self.env.ref('construction_boq_and_material_management.open_view_project_eco').read()[0]
        if len(project_eco) > 1:
            action['domain'] = [('id', 'in', project_eco.ids)]
        elif len(project_eco) == 1:
            action['views'] = [(self.env.ref('construction_boq_and_material_management.project_eco_view_form').id, 'form')]
            action['res_id'] = project_eco.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def write(self, values):
        if 'task_id' in values:
            task_id = values['task_id']
            task = self.env['project.task'].search([('id', '=', task_id)])
            values['allocated_budget'] = task.task_budget
            values['qty'] = task.qty
            values['uom_id'] = task.uom_id.id
        result = super(SkitProjectBOQ, self).write(values)
        return result

    def boq_action_submit(self):
        user = self.env['res.users'].browse(self.env.uid)
        self.write({'state': 'submitted',
                    'submitted_by': user.name,
                    'submitted_date': datetime.today(),
                    })
        if self.name == 'New':
            val = self.env['ir.sequence'].next_by_code('project.boq')
            self.write({'name': val})
        if self.task_id:
            task_id = self.task_id.id
            task = self.env['project.task'].search([('id', '=', task_id)])
            if not task.stock_location_id:
                raise UserError(_('Select Task Inventory Location and Picking Operation in Material status tab.'))
            if self.allocated_budget < self.total_boq:
                raise UserError(_('Total Bill of Quantity budget should not be greater than activity allocated budget.'))

    def boq_action_confirm(self):
        user = self.env['res.users'].browse(self.env.uid)
        self.write({'state': 'confirmed',
                    'confirmed_by': user.name,
                    'confirmed_date': datetime.today()})

    def boq_action_verify(self):
        user = self.env['res.users'].browse(self.env.uid)
        return self.write({'state': 'verified',
                           'verified_by': user.name,
                           'verified_date': datetime.today()})

    def boq_action_approve(self):
        user = self.env['res.users'].browse(self.env.uid)
        self.write({'state': 'approved',
                    'approved_by': user.name,
                    'approved_date': datetime.today()})
        ids = []
        qty = 0
        new_product_id = 0
        for material in (sorted(self.boq_material_ids, key=lambda k: k.product_id.id)):
            if(new_product_id == 0):
                new_product_id = material.product_id.id
            if(new_product_id != material.product_id.id):
                new_product_id = material.product_id.id
                qty = 0
            if self.task_id.material_consumption:
                for vals in self.task_id.material_consumption.filtered(lambda l: l.product_id.id == material.product_id.id):
                    ids.append(vals.product_id.id)
                    qty += material.qty
                    vals.write({
                                'product_id': material.product_id.id,
                                'task_id': self.task_id.id,
                                'uom_id': material.uom_id.id,
                                'estimated_qty': qty
                                })
                if material.product_id.id not in ids:
                    self.task_id.material_consumption.create({
                                            'product_id': material.product_id.id,
                                            'task_id': self.task_id.id,
                                            'uom_id': material.uom_id.id,
                                            'estimated_qty': material.qty
                                             })
            else:
                self.task_id.material_consumption.create({
                                            'product_id': material.product_id.id,
                                            'task_id': self.task_id.id,
                                            'uom_id': material.uom_id.id,
                                            'estimated_qty': material.qty
                                             })
        if self.task_id:
            self.task_id.write({'labor_budget': self.labor_total,
                                'equipment_budget': self.equipment_total,
                                'service_budget': self.scservice_total,
                                'material_budget': self.material_total,
                                'overhead_budget': self.overheadothers_total,
                                'total_budget': self.total_boq,
                                'boq_id': self.id})

    def boq_action_cancel(self):
        user = self.env['res.users'].browse(self.env.uid)
        return self.write({'state': 'cancelled',
                           'cancelled_by': user.name,
                           'cancelled_date': datetime.today()})

    def boq_action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancelled'])
        return orders.write({
            'state': 'draft',
        })


class SkitMaterial(models.Model):
    _name = 'boq.material'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string="Name",
                                 domain=[('type', '=', ('product'))])
    qty = fields.Float(string="Quantity",
                       digits=dp.get_precision('Product Price'))
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    unit_rate = fields.Float(string="Unit Rate",
                             digits=dp.get_precision('Product Price'))
    labor_cost = fields.Float(string="Labor Cost",
                              digits=dp.get_precision('Product Price'))
    equipment_cost = fields.Float(string="Equipment Cost",
                                  digits=dp.get_precision('Product Price'))
    subtotal = fields.Float(string="Subtotal",
                            compute='_compute_material_subtotal',
                            digits=dp.get_precision('Product Price'))
    boq_id = fields.Many2one('project.boq', string='BOQ',
                             required=True, ondelete='cascade',
                             index=True, copy=False)

    @api.depends('qty', 'unit_rate', 'labor_cost', 'equipment_cost')
    def _compute_material_subtotal(self):
        for material in self:
            subtotal = (material.unit_rate + material.labor_cost + material.equipment_cost) * material.qty
            material.update({'subtotal': subtotal})

    @api.onchange('product_id')
    def onchange_material_product(self):
        uom_id = self.product_id.uom_id.id
        unit_rate = self.product_id.standard_price
        self.update({'uom_id': uom_id,
                     'unit_rate': unit_rate})


class SkitEquipment(models.Model):
    _name = 'boq.equipment'

    name = fields.Char(string='Name')
    qty = fields.Float(string="Quantity",
                       digits=dp.get_precision('Product Price'))
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    unit_rate = fields.Float(string="Unit Rate",
                             digits=dp.get_precision('Product Price'))
    no_of_hrs = fields.Float(string="Durations",
                             digits=dp.get_precision('Product Price'))
    subtotal = fields.Float(string="Subtotal",
                            compute='_compute_equipment_subtotal',
                            digits=dp.get_precision('Product Price'))
    boq_id = fields.Many2one('project.boq', string='BOQ',
                             required=True, ondelete='cascade',
                             index=True, copy=False)

    @api.depends('qty', 'unit_rate', 'no_of_hrs')
    def _compute_equipment_subtotal(self):
        for eqp in self:
            subtotal = (eqp.no_of_hrs * eqp.unit_rate * eqp.qty)
            eqp.update({'subtotal': subtotal})


class SkitSubContractorService(models.Model):
    _name = 'boq.scservice'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string="Name",
                           domain=[('type', '=', ('service'))])
    qty = fields.Float(string="Quantity",
                       digits=dp.get_precision('Product Price'))
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    unit_rate = fields.Float(string="Unit Rate",
                             digits=dp.get_precision('Product Price'))
    description = fields.Char(string='Description')
    subtotal = fields.Float(string="Subtotal",
                            compute='_compute_scservice_subtotal',
                            digits=dp.get_precision('Product Price'))
    boq_id = fields.Many2one('project.boq', string='BOQ',
                             required=True, ondelete='cascade',
                             index=True, copy=False)

    @api.depends('qty', 'unit_rate')
    def _compute_scservice_subtotal(self):
        for service in self:
            subtotal = (service.unit_rate * service.qty)
            service.update({'subtotal': subtotal})

    @api.onchange('product_id')
    def _onchange_product(self):
        uom_id = self.product_id.uom_id.id
        self.update({'description': self.product_id.description_pickingout,
                    'uom_id': uom_id})


class SkitLabor(models.Model):
    _name = 'boq.labor'
    _rec_name = 'job_id'

    job_id = fields.Many2one('hr.job', string='Name')
    description = fields.Char(string='Description')
    head_count = fields.Integer("Headcount")
    budget_head_count = fields.Integer("Budget/Headcount")
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    dur_payment_term = fields.Float("Duration of Payment Terms",
                                    digits=dp.get_precision('Product Price'))
    labor_subtotal = fields.Float(string="Subtotal",
                                  compute='_compute_labor_subtotal',
                                  digits=dp.get_precision('Product Price'))
    labor_total = fields.Float(string="Total", compute='_compute_labor_total',
                               digits=dp.get_precision('Product Price'))
    boq_id = fields.Many2one('project.boq', string='BOQ',
                             ondelete='cascade', index=True, copy=False)

    @api.depends('head_count', 'budget_head_count')
    def _compute_labor_subtotal(self):
        for labor in self:
            subtotal = (labor.head_count*labor.budget_head_count)
            labor.update({'labor_subtotal': subtotal})

    @api.depends('labor_subtotal', 'dur_payment_term')
    def _compute_labor_total(self):
        for labor in self:
            total = (labor.labor_subtotal*labor.dur_payment_term)
            labor.update({'labor_total': total})

    @api.onchange('job_id')
    def _onchange_hr_jobs(self):
        self.update({'description': self.job_id.description})


class SkitOverheads(models.Model):
    _name = 'boq.overhead'

    category_id = fields.Many2one('boq.overhead.category', string='Category')
    name = fields.Char(string='Name')
    qty = fields.Float(string="Quantity",
                       digits=dp.get_precision('Product Price'))
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    unit_rate = fields.Float(string="Unit Rate",
                             digits=dp.get_precision('Product Price'))
    subtotal = fields.Float(string="Subtotal",
                            compute='_compute_overhead_subtotal',
                            digits=dp.get_precision('Product Price'))
    boq_id = fields.Many2one('project.boq', string='BOQ',
                             ondelete='cascade', index=True, copy=False)

    @api.depends('qty', 'unit_rate')
    def _compute_overhead_subtotal(self):
        for overhead in self:
            subtotal = (overhead.unit_rate * overhead.qty)
            overhead.update({'subtotal': subtotal})


class skitoverheadcategory(models.Model):
    _name = 'boq.overhead.category'

    name = fields.Char("Name", required=True)
