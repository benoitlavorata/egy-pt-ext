# -*- coding: utf-8 -*-

from odoo import fields, models,api,_
from odoo.addons import decimal_precision as dp
from datetime import datetime


class SkitProjectECO(models.Model):
    _name = 'project.eco'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']
    _description = 'Engineering Change Order'

    name = fields.Char(string='Number', index=True, readonly=True, copy=False, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string="Project")
    phase_id = fields.Many2one('project.phase', string="Phase",
                               domain="[('project_id', '=', project_id)]")
    task_id = fields.Many2one('project.task', string="Task",
                              domain="[('project_id', '=', project_id),('phase_id', '=', phase_id)]")
    boq_id = fields.Many2one('project.boq', "BOQ",
                             domain="[('project_id', '=', project_id),('phase_id', '=', phase_id),('task_id', '=', task_id)]")
    request_date = fields.Date("Date", default=fields.Date.context_today)
    labor_cost = fields.Float(string="Labor Cost (%)", digits=dp.get_precision('Product Price'))
    markup_cost = fields.Float(string="Markup Cost (%)", digits=dp.get_precision('Product Price'))
    state = fields.Selection([('draft', 'Draft'),
                            ('submitted','Submitted'),
                            ('confirmed', 'Confirmed'),
                            ('verified', 'Verified'),
                            ('approved', 'Approved'),
                            ('cancelled', 'Cancelled')], string='Status', readonly=True, copy=False,
                             index=True, track_visibility='onchange', default='draft')
    notes = fields.Text("Notes")
    submitted_by = fields.Char("Submitted By", readonly=True)
    confirmed_by = fields.Char("Confirmed By", readonly=True)
    cancelled_by = fields.Char("Cancelled By", readonly=True)
    verified_by = fields.Char("Verified By", readonly=True)
    approved_by = fields.Char("Approved By", readonly=True)
    submitted_date = fields.Datetime("Submitted Date", readonly=True)
    confirmed_date = fields.Datetime("Confirmed Date", readonly=True)
    cancelled_date = fields.Datetime("Cancelled Date", readonly=True)
    verified_date = fields.Datetime("Verified Date", readonly=True)
    approved_date = fields.Datetime("Approved Date", readonly=True)
    material_previous = fields.Float(string="Material Previous",
                                     compute='_compute_eco_material')
    material_current = fields.Float(string="Material Current",
                                    compute='_compute_eco_material')
    material_budget = fields.Float(string="Material Budget",
                                   compute='_compute_eco_material')
    service_previous = fields.Float(string="Service Previous",
                                    compute='_compute_eco_service')
    service_current = fields.Float(string="Service Current",
                                   compute='_compute_eco_service')
    service_budget = fields.Float(string="Service Budget",
                                  compute='_compute_eco_service')
    labor_previous = fields.Float(string="Labor Previous",
                                  compute='_compute_eco_labor')
    labor_current = fields.Float(string="Labor Current",
                                 compute='_compute_eco_labor')
    labor_budget = fields.Float(string="Labor Budget",
                                compute='_compute_eco_labor')
    equipment_previous = fields.Float(string="Equipment Previous",
                                      compute='_compute_eco_equipment')
    equipment_current = fields.Float(string="Equipment Current",
                                     compute='_compute_eco_equipment')
    equipment_budget = fields.Float(string="Equipment Budget",
                                    compute='_compute_eco_equipment')
    overhead_previous = fields.Float(string="Overhead Previous",
                                     compute='_compute_eco_overhead')
    overhead_current = fields.Float(string="Overhead Current",
                                    compute='_compute_eco_overhead')
    overhead_budget = fields.Float(string="Overhead Budget",
                                   compute='_compute_eco_overhead')
    total_previous = fields.Float(string="Total Previous",
                                  compute='_compute_eco_total')
    total_current = fields.Float(string="Total Current",
                                 compute='_compute_eco_total')
    total_budget = fields.Float(string="Total Budget",
                                compute='_compute_eco_total')
    eco_material_ids = fields.One2many('eco.material', 'eco_id', string='Materials')
    eco_equipment_ids = fields.One2many('eco.equipment', 'eco_id',
                                        string='Equipment')
    eco_scservice_ids = fields.One2many('eco.scservice', 'eco_id',
                                        string='SubContractor Service')
    eco_labor_ids = fields.One2many('eco.labor', 'eco_id', string="Labor")
    eco_overhead_ids = fields.One2many('eco.overhead', 'eco_id',
                                       string="OverHead")

    @api.depends('eco_material_ids')
    def _compute_eco_material(self):
        material_current = 0
        material_previous = 0
        material_budget = 0
        for mid in self:
            for material in mid.eco_material_ids:
                material_current = material_current + material.boq_equipment_budget_diff
            for boq in mid.boq_id:
                material_previous = material_previous + boq.material_total
            material_budget = material_previous + material_current
            mid.update({'material_current': material_current,
                        'material_previous': material_previous,
                        'material_budget': material_budget})

    @api.depends('eco_scservice_ids')
    def _compute_eco_service(self):
        service_current = 0
        service_previous = 0
        service_budget = 0
        for sid in self:
            for service in sid.eco_scservice_ids:
                service_current = service_current + service.boq_equipment_budget
            for boq in sid.boq_id:
                service_previous = service_previous + boq.scservice_total
            service_budget = service_previous + service_current
            sid.update({'service_current': service_current,
                        'service_previous': service_previous,
                        'service_budget': service_budget})

    @api.depends('eco_labor_ids')
    def _compute_eco_labor(self):
        labor_current = 0
        labor_previous = 0
        labor_budget = 0
        for lid in self:
            for labor in lid.eco_labor_ids:
                labor_current = labor_current + labor.boq_equipment_budget
            for boq in lid.boq_id:
                labor_previous = labor_previous + boq.labor_total
            labor_budget = labor_previous + labor_current
            lid.update({'labor_current': labor_current,
                        'labor_previous': labor_previous,
                        'labor_budget': labor_budget})

    @api.depends('eco_equipment_ids')
    def _compute_eco_equipment(self):
        equipment_current = 0
        equipment_previous = 0
        equipment_budget = 0
        for eid in self:
            for equipment in eid.eco_equipment_ids:
                equipment_current = equipment_current + equipment.boq_equipment_budget
            for boq in eid.boq_id:
                equipment_previous = equipment_previous + boq.equipment_total
            equipment_budget = equipment_previous + equipment_current
            eid.update({'equipment_current': equipment_current,
                        'equipment_previous': equipment_previous,
                        'equipment_budget': equipment_budget})

    @api.depends('eco_overhead_ids')
    def _compute_eco_overhead(self):
        overhead_current = 0
        overhead_previous = 0
        overhead_budget = 0
        for oid in self:
            for overhead in oid.eco_overhead_ids:
                overhead_current = overhead_current + overhead.boq_equipment_budget
            for boq in oid.boq_id:
                overhead_previous = overhead_previous + boq.overheadothers_total
            overhead_budget = overhead_previous + overhead_current
            oid.update({'overhead_current': overhead_current,
                        'overhead_previous': overhead_previous,
                        'overhead_budget': overhead_budget})

    @api.depends('eco_equipment_ids')
    def _compute_eco_total(self):
        for tid in self:
            total_previous = (tid.labor_previous + tid.equipment_previous + tid.service_previous + tid.material_previous + tid.overhead_previous)
            total_current = (tid.labor_current + tid.equipment_current + tid.service_current + tid.material_current + tid.overhead_current)
            total_budget = (tid.labor_budget + tid.equipment_budget + tid.service_budget + tid.material_budget + tid.overhead_budget)
            tid.update({'total_previous': total_previous,
                        'total_current': total_current,
                        'total_budget': total_budget})

    def eco_action_submit(self):
        user = self.env['res.users'].browse(self.env.uid)
        self.write({'state': 'submitted',
                    'submitted_by': user.name,
                    'submitted_date': datetime.today(),
                    })
        if self.name == 'New':
            val = self.env['ir.sequence'].next_by_code('project.eco')
            self.write({'name': val})

    def eco_action_confirm(self):
        user = self.env['res.users'].browse(self.env.uid)
        self.write({'state': 'confirmed',
                    'confirmed_by': user.name,
                    'confirmed_date': datetime.today()})

    def eco_action_verify(self):
        user = self.env['res.users'].browse(self.env.uid)
        return self.write({'state': 'verified',
                           'verified_by': user.name,
                           'verified_date': datetime.today()})

    def eco_action_approve(self):
        user = self.env['res.users'].browse(self.env.uid)
        self.write({'state': 'approved',
                    'approved_by': user.name,
                    'approved_date': datetime.today()})
        for material in self.eco_material_ids:
            boq_material = self.env['boq.material'].sudo().search([
                ('boq_id', '=', self.boq_id.id), ('id', '=', material.boq_material_id.id)])
            if(material.eco_mode == 'new'):
                new_boq_material = self.env['boq.material']
                new_boq_material.create({'product_id': material.product_id.id,
                                         'qty': material.boq_qty,
                                         'uom_id': material.uom_id.id,
                                         'unit_rate': material.boq_unit_rate,
                                         'labor_cost': material.boq_labor_cost,
                                         'equipment_cost': material.boq_equipment_budget,
                                         'subtotal': material.subtotal,
                                         'boq_id': self.boq_id.id})

            if(material.eco_mode == 'update'):
                qty = material.boq_qty
                unit_rate = material.boq_unit_rate
                labor_cost = material.boq_labor_cost
                equipment_budget = material.boq_equipment_budget
                if(material.qty > 0):
                    qty = qty + material.qty
                else:
                    qty = qty - (-material.qty)
                if(material.unit_rate > 0):
                    unit_rate = unit_rate + material.unit_rate
                else:
                    unit_rate = unit_rate - (-material.unit_rate)
                if(material.labor_cost > 0):
                    labor_cost = labor_cost + material.labor_cost
                else:
                    labor_cost = labor_cost - (-material.labor_cost)
                if(material.equipment_budget > 0):
                    equipment_budget = equipment_budget + material.equipment_budget
                else:
                    equipment_budget = equipment_budget - (-material.equipment_budget)
                boq_material.update({'qty': qty,
                                     'unit_rate': unit_rate,
                                     'labor_cost': labor_cost,
                                     'equipment_cost': equipment_budget})
        for equipment in self.eco_equipment_ids:
            boq_equipment = self.env['boq.equipment'].sudo().search([
                ('boq_id', '=', self.boq_id.id), ('id', '=', equipment.boq_equipment_id.id)])
            if(equipment.eco_mode == 'new'):
                new_boq_equipment = self.env['boq.equipment']
                new_boq_equipment.create({
                    'name': equipment.name,
                    'qty': equipment.boq_qty,
                    'uom_id': equipment.uom_id.id,
                    'no_of_hrs': equipment.boq_no_of_hrs,
                    'unit_rate': equipment.boq_unit_rate,
                    'subtotal': equipment.subtotal,
                    'boq_id': self.boq_id.id
                })
            if(equipment.eco_mode == 'update'):
                qty = equipment.boq_qty
                no_of_hrs = equipment.boq_no_of_hrs
                if(equipment.qty > 0):
                    qty = qty + equipment.qty
                else:
                    qty = qty - (-equipment.qty)
                if(equipment.no_of_hrs > 0):
                    no_of_hrs = no_of_hrs + equipment.no_of_hrs
                else:
                    no_of_hrs = no_of_hrs - (-equipment.no_of_hrs)
                boq_equipment.update({'qty': qty,
                                      'no_of_hrs': no_of_hrs})
        for scservice in self.eco_scservice_ids:
            boq_scservice = self.env['boq.scservice'].sudo().search([
                ('boq_id', '=', self.boq_id.id), ('id', '=', scservice.boq_scservice_id.id)])
            if(scservice.eco_mode == 'new'):
                new_boq_scservice = self.env['boq.scservice']
                new_boq_scservice.create({
                    'product_id': scservice.product_id.id,
                    'qty': scservice.boq_qty,
                    'uom_id': scservice.uom_id.id,
                    'unit_rate': scservice.boq_unit_rate,
                    'subtotal': scservice.subtotal,
                    'boq_id': self.boq_id.id
                    })
            if(scservice.eco_mode == 'update'):
                qty = scservice.boq_qty
                if(scservice.qty > 0):
                    qty = qty + scservice.qty
                else:
                    qty = qty - (-scservice.qty)
                boq_scservice.update({'qty': qty})

        for labor in self.eco_labor_ids:
            boq_labor = self.env['boq.labor'].sudo().search([
                ('boq_id', '=', self.boq_id.id), ('id', '=', labor.boq_labor_id.id)])
            if(labor.eco_mode == 'new'):
                new_boq_labor = self.env['boq.labor']
                new_boq_labor.create({
                    'job_id': labor.job_id.id,
                    'description': labor.description,
                    'head_count': labor.boq_head_count,
                    'budget_head_count': labor.budget_head_count,
                    'uom_id': labor.uom_id.id,
                    'dur_payment_term': labor.dur_payment_term,
                    'labor_subtotal': labor.subtotal,
                    'labor_total': labor.total,
                    'boq_id': self.boq_id.id
                    })
            if(labor.eco_mode == 'update'):
                head_count = labor.boq_head_count
                if(labor.head_count > 0):
                    head_count = head_count + labor.head_count
                else:
                    head_count = head_count - (-labor.head_count)
                boq_labor.update({'head_count': head_count})

        for overhead in self.eco_overhead_ids:
            boq_overhead = self.env['boq.overhead'].sudo().search([
                ('boq_id', '=', self.boq_id.id), ('id', '=', overhead.boq_overhead_id.id)])
            if(overhead.eco_mode == 'new'):
                new_boq_overhead = self.env['boq.overhead']
                new_boq_overhead.create({
                    'category_id': overhead.category_id.id,
                    'name': overhead.name,
                    'qty': overhead.boq_qty,
                    'uom_id': overhead.uom_id.id,
                    'unit_rate': overhead.unit_rate,
                    'subtotal': overhead.subtotal,
                    'boq_id': self.boq_id.id
                    })
            if(overhead.eco_mode == 'update'):
                qty = overhead.boq_qty
                if(overhead.qty > 0):
                    qty = qty + overhead.qty
                else:
                    qty = qty - (-overhead.qty)
                boq_overhead.update({'qty': qty})

        ids = []
        for material in self.boq_id.boq_material_ids:
            if self.boq_id.task_id.material_consumption:
                for vals in self.boq_id.task_id.material_consumption.filtered(lambda l: l.product_id.id == material.product_id.id):
                    ids.append(vals.product_id.id)
                    vals.write({
                                'product_id': material.product_id.id,
                                'task_id': self.boq_id.task_id.id,
                                'uom_id': material.uom_id.id,
                                'estimated_qty': material.qty
                                })
                if material.product_id.id not in ids:
                    self.boq_id.task_id.material_consumption.create({
                                            'product_id': material.product_id.id,
                                            'task_id': self.boq_id.task_id.id,
                                            'uom_id': material.uom_id.id,
                                            'estimated_qty': material.qty
                                             })
            else:
                self.boq_id.task_id.material_consumption.create({
                                            'product_id': material.product_id.id,
                                            'task_id': self.boq_id.task_id.id,
                                            'uom_id': material.uom_id.id,
                                            'estimated_qty': material.qty
                                             })
        if self.boq_id.task_id:
            self.boq_id.task_id.write({
                'labor_budget': self.boq_id.labor_total,
                'equipment_budget': self.boq_id.equipment_total,
                'service_budget': self.boq_id.scservice_total,
                'material_budget': self.boq_id.material_total,
                'overhead_budget': self.boq_id.overheadothers_total,
                'total_budget': self.boq_id.total_boq,
                'boq_id': self.boq_id.id})

    def eco_action_cancel(self):
        user = self.env['res.users'].browse(self.env.uid)
        return self.write({'state': 'cancelled',
                           'cancelled_by': user.name,
                           'cancelled_date': datetime.today()})

    def eco_action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancelled'])
        return orders.write({
            'state': 'draft',
        })


class SkitECOMaterial(models.Model):
    _name = 'eco.material'

    eco_mode = fields.Selection([('new', 'New'),
                              ('update', 'Update'),], string='Mode')
    boq_material_id = fields.Many2one('boq.material','BOQ')
    product_id = fields.Many2one('product.product',"Name")
    boq_qty = fields.Float("Quantity")
    qty = fields.Float("Quantity (-+)")
    uom_id = fields.Many2one('uom.uom', 'UOM')
    boq_unit_rate = fields.Float("Unit Rate")
    unit_rate = fields.Float("Unit Rate (-+)")
    boq_labor_cost = fields.Float("Labor Cost")
    labor_cost = fields.Float("Labor Cost (-+)")
    boq_equipment_budget_diff = fields.Float("Budget Difference",
                                             compute='_compute_eco_material_total', store=True)
    boq_equipment_budget = fields.Float("Equipment Budget")
    equipment_budget = fields.Float("Equipment Budget (-+)")
    subtotal = fields.Float("Subtotal", compute='_compute_eco_material_total', store=True)
    eco_id = fields.Many2one('project.eco', string='ECO', required=True, ondelete='cascade', index=True, copy=False)

    @api.depends('boq_qty', 'qty', 'boq_unit_rate', 'boq_labor_cost', 'labor_cost', 'boq_equipment_budget', 'equipment_budget')
    def _compute_eco_material_total(self):
        for material in self:
            if material.eco_mode == 'update':
                budget_diff = (material.qty * (material.boq_unit_rate + material.labor_cost + material.equipment_budget))
                sub_total = (material.boq_qty * (material.boq_unit_rate + material.boq_labor_cost + material.boq_equipment_budget)) + budget_diff
                material.update({'subtotal': sub_total,
                                 'boq_equipment_budget_diff': budget_diff})
            else:
                budget_diff = (material.boq_qty * (material.boq_unit_rate + material.boq_labor_cost + material.boq_equipment_budget))
                sub_total = budget_diff
                material.update({'subtotal': sub_total,
                                 'boq_equipment_budget_diff': budget_diff})

    @api.onchange('eco_mode')
    def onchange_eco_mode(self):
        rest_of_vals = self.eco_id.eco_material_ids - self
        self.boq_material_id = False
        self.product_id = False
        self.boq_qty = 0.0
        self.qty = 0.0
        self.uom_id = False
        self.boq_unit_rate = 0.0
        self.boq_labor_cost = 0.0
        self.labor_cost = 0.0
        self.boq_equipment_budget = 0.0
        self.equipment_budget = 0.0
        self.boq_equipment_budget_diff = 0.0
        self.subtotal = 0.0
        if self.eco_mode == 'update':
            boq_material_ids = []
            for record in rest_of_vals:
                if(record.boq_material_id):
                    boq_material_ids.append(record.boq_material_id.id)
            return {'domain': {'boq_material_id': [('boq_id', '=', self.eco_id.boq_id.id),
                                                   ('id', 'not in', boq_material_ids)]}}

    @api.onchange('boq_material_id')
    def onchange_boq_material(self):
        if self.eco_mode == 'update':
            if self.boq_material_id:
                self.update({'product_id': self.boq_material_id.product_id.id,
                             'uom_id': self.boq_material_id.uom_id.id,
                             'boq_qty': self.boq_material_id.qty,
                             'boq_unit_rate': self.boq_material_id.unit_rate,
                             'boq_labor_cost': self.boq_material_id.labor_cost,
                             'boq_equipment_budget': self.boq_material_id.equipment_cost})

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.update({
                'uom_id': self.product_id.uom_id.id
                })

    @api.model
    def create(self, vals):
        boq_material = self.env['boq.material'].sudo().search([
            ('id', '=', vals.get('boq_material_id'))])
        if boq_material:
            vals['product_id'] = boq_material.product_id.id
            vals['uom_id'] = boq_material.uom_id.id
            vals['boq_qty'] = boq_material.qty
            vals['boq_unit_rate'] = boq_material.unit_rate
            vals['boq_labor_cost'] = boq_material.labor_cost
            vals['boq_equipment_budget'] = boq_material.equipment_cost
        result = super(SkitECOMaterial, self).create(vals)
        for material in result:
            val = ((material.boq_unit_rate) + (material.boq_labor_cost+material.labor_cost) + (material.boq_equipment_budget+material.equipment_budget))
            qty = (material.boq_qty + material.qty)
            subtotal = (val)*(qty)
            material.write({'subtotal': subtotal})

        return result


class SkitECOEquipment(models.Model):
    _name = 'eco.equipment'

    eco_mode = fields.Selection([('new', 'New'),
                                 ('update', 'Update')], string='Mode')
    boq_equipment_id = fields.Many2one('boq.equipment', 'BOQ')
    name = fields.Char(string='Name')
    boq_qty = fields.Float("Quantity")
    qty = fields.Float("Quantity (-+)")
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    boq_no_of_hrs = fields.Float(string="No.of Hours",
                                 digits=dp.get_precision('Product Price'))
    no_of_hrs = fields.Float(string="No.of Hours (-+)",
                             digits=dp.get_precision('Product Price'))
    boq_unit_rate = fields.Float("Unit Rate")
    boq_equipment_budget = fields.Float("Budget Difference")
    subtotal = fields.Float("Subtotal", compute='_compute_eco_equipment_total',
                            store=True)
    eco_id = fields.Many2one('project.eco', string='ECO', required=True,
                             ondelete='cascade', index=True, copy=False)

    @api.depends('boq_qty', 'qty', 'boq_unit_rate', 'boq_no_of_hrs',
                 'no_of_hrs')
    def _compute_eco_equipment_total(self):
        for equipment in self:
            if equipment.eco_mode == 'update':
                budget_diff = (equipment.qty * (equipment.boq_unit_rate * equipment.no_of_hrs))
                sub_total = (equipment.boq_qty * (equipment.boq_unit_rate * equipment.boq_no_of_hrs)) + budget_diff
                equipment.update({'subtotal': sub_total,
                                 'boq_equipment_budget': budget_diff})
            else:
                budget_diff = (equipment.boq_qty * (equipment.boq_unit_rate * equipment.boq_no_of_hrs))
                sub_total = budget_diff
                equipment.update({'subtotal': sub_total,
                                 'boq_equipment_budget': budget_diff})

    @api.onchange('eco_mode')
    def onchange_eco_mode(self):
        rest_of_vals = self.eco_id.eco_equipment_ids - self
        self.boq_equipment_id = False
        self.name = ""
        self.boq_qty = 0.0
        self.qty = 0.0
        self.uom_id = False
        self.boq_no_of_hrs = 0.0
        self.no_of_hrs = 0.0
        self.boq_equipment_budget = 0.0
        self.subtotal = 0.0
        if self.eco_mode == 'update':
            boq_equipment_ids = []
            for record in rest_of_vals:
                if(record.boq_equipment_id):
                    boq_equipment_ids.append(record.boq_equipment_id.id)
            return {'domain': {'boq_equipment_id': [('boq_id', '=', self.eco_id.boq_id.id),
                                                   ('id', 'not in', boq_equipment_ids)]}}

    @api.onchange('boq_equipment_id')
    def onchange_boq_equipment(self):
        if self.eco_mode == 'update':
            if self.boq_equipment_id:
                self.update({'name': self.boq_equipment_id.name,
                             'boq_qty': self.boq_equipment_id.qty,
                             'uom_id': self.boq_equipment_id.uom_id.id,
                             'boq_unit_rate': self.boq_equipment_id.unit_rate,
                             'boq_no_of_hrs': self.boq_equipment_id.no_of_hrs})

    @api.model
    def create(self, vals):
        boq_equipment = self.env['boq.equipment'].sudo().search([
            ('id', '=', vals.get('boq_equipment_id'))])
        if boq_equipment:
            vals['boq_qty'] = boq_equipment.qty
            vals['uom_id'] = boq_equipment.uom_id.id
            vals['boq_unit_rate'] = boq_equipment.unit_rate
            vals['boq_no_of_hrs'] = boq_equipment.no_of_hrs
        result = super(SkitECOEquipment, self).create(vals)
        for equipment in result:
            val = ((equipment.boq_unit_rate) + (equipment.boq_no_of_hrs + equipment.no_of_hrs) + (equipment.boq_equipment_budget))
            qty = (equipment.boq_qty + equipment.qty)
            subtotal = (val)*(qty)
            equipment.write({'subtotal': subtotal})
        return result


class SkitECOSCService(models.Model):
    _name = 'eco.scservice'

    eco_mode = fields.Selection([('new', 'New'),
                                 ('update', 'Update')], string='Mode')
    boq_scservice_id = fields.Many2one('boq.scservice', 'BOQ')
    product_id = fields.Many2one('product.product', 'Name')
    boq_qty = fields.Float("Quantity")
    qty = fields.Float("Quantity (-+)")
    uom_id = fields.Many2one('uom.uom', 'UOM Measure')
    boq_unit_rate = fields.Float("Unit Rate")
    boq_equipment_budget = fields.Float("Budget Difference")
    subtotal = fields.Float("Subtotal", compute='_compute_eco_scservice_total',
                            store=True)
    eco_id = fields.Many2one('project.eco', string='ECO', required=True,
                             ondelete='cascade', index=True, copy=False)

    @api.depends('boq_qty', 'qty', 'boq_unit_rate')
    def _compute_eco_scservice_total(self):
        for service in self:
            if service.eco_mode == 'update':
                budget_diff = (service.qty * (service.boq_unit_rate))
                sub_total = (service.boq_qty * (service.boq_unit_rate)) + budget_diff
                service.update({'subtotal': sub_total,
                                'boq_equipment_budget': budget_diff})
            else:
                budget_diff = (service.boq_qty * (service.boq_unit_rate))
                sub_total = budget_diff
                service.update({'subtotal': sub_total,
                                'boq_equipment_budget': budget_diff})

    @api.onchange('eco_mode')
    def onchange_eco_mode(self):
        rest_of_vals = self.eco_id.eco_scservice_ids - self
        self.boq_scservice_id = False
        self.product_id = False
        self.boq_qty = 0.0
        self.qty = 0.0
        self.uom_id = False
        self.boq_unit_rate = 0.0
        self.boq_equipment_budget = 0.0
        self.subtotal = 0.0
        if self.eco_mode == 'update':
            boq_scservice_ids = []
            for record in rest_of_vals:
                if(record.boq_scservice_id):
                    boq_scservice_ids.append(record.boq_scservice_id.id)
            return {'domain': {'boq_scservice_id': [('boq_id', '=', self.eco_id.boq_id.id),
                                                   ('id', 'not in', boq_scservice_ids)]}}

    @api.onchange('boq_scservice_id')
    def onchange_boq_scservice(self):
        if self.eco_mode == 'update':
            if self.boq_scservice_id:
                self.update({'product_id': self.boq_scservice_id.product_id.id,
                             'uom_id': self.boq_scservice_id.uom_id.id,
                             'boq_qty': self.boq_scservice_id.qty,
                             'boq_unit_rate': self.boq_scservice_id.unit_rate})

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.update({
                'uom_id': self.product_id.uom_id.id
                })

    @api.model
    def create(self, vals):
        boq_scservice = self.env['boq.scservice'].sudo().search([
            ('id', '=', vals.get('boq_scservice_id'))])
        if boq_scservice:
            vals['product_id'] = boq_scservice.product_id.id
            vals['uom_id'] = boq_scservice.uom_id.id
            vals['boq_qty'] = boq_scservice.qty
            vals['boq_unit_rate'] = boq_scservice.unit_rate
        result = super(SkitECOSCService, self).create(vals)
        for service in result:
            val = ((service.boq_unit_rate) + (service.boq_equipment_budget))
            qty = (service.boq_qty + service.qty)
            subtotal = (val)*(qty)
            service.write({'subtotal': subtotal})
        return result


class SkitECOLabor(models.Model):
    _name = 'eco.labor'

    eco_mode = fields.Selection([('new', 'New'),
                                 ('update', 'Update')], string='Mode')
    boq_labor_id = fields.Many2one('boq.labor', 'BOQ')
    job_id = fields.Many2one('hr.job', string='Name')
    description = fields.Char(string='Description')
    boq_head_count = fields.Integer("Headcount")
    head_count = fields.Integer("Headcount (-+)")
    budget_head_count = fields.Integer("Budget/Head Count")
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    subtotal = fields.Float(string="Subtotal",
                            compute='_compute_labor_subtotal',
                            digits=dp.get_precision('Product Price'))
    dur_payment_term = fields.Float("Duration of Payment Terms",
                                    digits=dp.get_precision('Product Price'))
    boq_equipment_budget = fields.Float("Budget Difference")
    total = fields.Float(string="Total", compute='_compute_labor_total',
                               digits=dp.get_precision('Product Price'))
    eco_id = fields.Many2one('project.eco', string='ECO', required=True,
                             ondelete='cascade', index=True, copy=False)

    @api.depends('boq_head_count', 'head_count', 'budget_head_count')
    def _compute_labor_subtotal(self):
        for labor in self:
            if labor.eco_mode == 'update':
                budget_diff = (labor.head_count * (labor.budget_head_count))
                sub_total = (labor.boq_head_count * (labor.budget_head_count)) + budget_diff
                labor.update({'subtotal': sub_total,
                              'boq_equipment_budget': budget_diff})
            else:
                budget_diff = (labor.boq_head_count * (labor.budget_head_count))
                sub_total = budget_diff
                labor.update({'subtotal': sub_total,
                              'boq_equipment_budget': budget_diff})

    @api.depends('subtotal', 'dur_payment_term')
    def _compute_labor_total(self):
        for labor in self:
            total = (labor.subtotal*labor.dur_payment_term)
            labor.update({'total': total})

    @api.onchange('eco_mode')
    def onchange_eco_mode(self):
        rest_of_vals = self.eco_id.eco_labor_ids - self
        self.boq_labor_id = False
        self.job_id = False
        self.description = ""
        self.boq_head_count = 0
        self.head_count = 0
        self.budget_head_count = 0
        self.uom_id = False
        self.subtotal = 0.0
        self.dur_payment_term = 0.0
        self.boq_equipment_budget = 0.0
        self.total = 0.0
        if self.eco_mode == 'update':
            boq_labor_ids = []
            for record in rest_of_vals:
                if(record.boq_labor_id):
                    boq_labor_ids.append(record.boq_labor_id.id)
            return {'domain': {'boq_labor_id': [('boq_id', '=', self.eco_id.boq_id.id),
                                                   ('id', 'not in', boq_labor_ids)]}}

    @api.onchange('boq_labor_id')
    def onchange_boq_labor(self):
        if self.eco_mode == 'update':
            if self.boq_labor_id:
                self.update({'job_id': self.boq_labor_id.job_id.id,
                             'description': self.boq_labor_id.description,
                             'boq_head_count': self.boq_labor_id.head_count,
                             'budget_head_count': self.boq_labor_id.budget_head_count,
                             'uom_id': self.boq_labor_id.uom_id.id,
                             'dur_payment_term': self.boq_labor_id.dur_payment_term})

    @api.model
    def create(self, vals):
        boq_labor = self.env['boq.labor'].sudo().search([
            ('id', '=', vals.get('boq_labor_id'))])
        if boq_labor:
            vals['job_id'] = boq_labor.job_id.id
            vals['description'] = boq_labor.description
            vals['boq_head_count'] = boq_labor.head_count
            vals['budget_head_count'] = boq_labor.budget_head_count
            vals['uom_id'] = boq_labor.uom_id.id
            vals['dur_payment_term'] = boq_labor.dur_payment_term
        result = super(SkitECOLabor, self).create(vals)
        for labor in result:
            val = ((labor.boq_head_count) + (labor.head_count))
            subtotal = (val * labor.budget_head_count)
            labor.write({'subtotal': subtotal})
        for labor in result:
            total = (labor.subtotal*labor.dur_payment_term)
            labor.write({'total': total})

        return result


class SkitECOOverhead(models.Model):
    _name = 'eco.overhead'

    eco_mode = fields.Selection([('new', 'New'),
                                 ('update', 'Update')], string='Mode')
    boq_overhead_id = fields.Many2one('boq.overhead', 'BOQ')
    category_id = fields.Many2one('boq.overhead.category', 'Category')
    name = fields.Char(string='Name')
    boq_qty = fields.Float(string="Quantity",
                           digits=dp.get_precision('Product Price'))
    qty = fields.Float(string="Quantity (-+)",
                       digits=dp.get_precision('Product Price'))
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    unit_rate = fields.Float(string="Unit Rate",
                             digits=dp.get_precision('Product Price'))
    boq_equipment_budget = fields.Float("Budget Difference")
    subtotal = fields.Float(string="Subtotal",
                            compute='_compute_overhead_subtotal',
                            digits=dp.get_precision('Product Price'))
    eco_id = fields.Many2one('project.eco', string='ECO', required=True,
                             ondelete='cascade', index=True, copy=False)

    @api.depends('boq_qty', 'qty', 'unit_rate')
    def _compute_overhead_subtotal(self):
        for overhead in self:
            if overhead.eco_mode == 'update':
                budget_diff = (overhead.qty * (overhead.unit_rate))
                sub_total = (overhead.boq_qty * (overhead.unit_rate)) + budget_diff
                overhead.update({'subtotal': sub_total,
                                 'boq_equipment_budget': budget_diff})
            else:
                budget_diff = (overhead.boq_qty * (overhead.unit_rate))
                sub_total = budget_diff
                overhead.update({'subtotal': sub_total,
                                 'boq_equipment_budget': budget_diff})

    @api.onchange('eco_mode')
    def onchange_eco_mode(self):
        rest_of_vals = self.eco_id.eco_overhead_ids - self
        self.boq_overhead_id = False
        self.category_id = False
        self.name = ""
        self.boq_qty = 0.0
        self.qty = 0.0
        self.uom_id = False
        self.unit_rate = False
        self.boq_equipment_budget = 0.0
        self.subtotal = 0.0
        if self.eco_mode == 'update':
            boq_overhead_ids = []
            for record in rest_of_vals:
                if(record.boq_overhead_id):
                    boq_overhead_ids.append(record.boq_overhead_id.id)
            return {'domain': {'boq_overhead_id': [('boq_id', '=', self.eco_id.boq_id.id),
                                                   ('id', 'not in', boq_overhead_ids)]}}

    @api.onchange('boq_overhead_id')
    def onchange_boq_overhead(self):
        if self.eco_mode == 'update':
            if self.boq_overhead_id:
                self.update({'category_id': self.boq_overhead_id.category_id.id,
                             'name': self.boq_overhead_id.name,
                             'boq_qty': self.boq_overhead_id.qty,
                             'uom_id': self.boq_overhead_id.uom_id.id,
                             'unit_rate': self.boq_overhead_id.unit_rate})

    @api.model
    def create(self, vals):
        boq_overhead = self.env['boq.overhead'].sudo().search([
            ('id', '=', vals.get('boq_overhead_id'))])
        if boq_overhead:
            vals['category_id'] = boq_overhead.category_id.id
            vals['name'] = boq_overhead.name
            vals['boq_qty'] = boq_overhead.qty
            vals['uom_id'] = boq_overhead.uom_id.id
            vals['unit_rate'] = boq_overhead.unit_rate
        result = super(SkitECOOverhead, self).create(vals)
        for overhead in result:
            val = ((overhead.unit_rate))
            qty = (overhead.boq_qty + overhead.qty)
            subtotal = (val)*(qty)
            overhead.write({'subtotal': subtotal})

        return result
