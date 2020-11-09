# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class ProjectTask(models.Model):
    _inherit = 'project.task'

    qty = fields.Float(string="Quantity")
    material_consumption_progress = fields.Float(string="Material Consumption Progress",
                                                 compute="get_material_consumption")
    material_withdrawal_progress = fields.Float(string="Material Withdrawal Progress",
                                                 compute="get_material_consumption")
    material_consumption = fields.One2many(
        'project.material.consumption', 'task_id', 'Material Consumption',
        copy=True)
    waste_management = fields.One2many(
        'project.waste.management', 'task_id', 'Waste Management',
        copy=True, readonly=True)
    scrap_products = fields.One2many(
        'project.scrap.products', 'task_id', 'Scrap Products',
        copy=True, readonly=True)
    boq_id = fields.Many2one('project.boq', 'BOM/BOQ Reference',
                             readonly=True)
    phase_id = fields.Many2one('project.phase', string="Project Phase",
                               domain="[('project_id', '=', project_id)]")
    stock_location_id = fields.Many2one('stock.location',
                                        string="Task Inventory Location",
                                        domain="[('location_id', '=', project_stock_location_id),('usage', '!=', 'view')]")
    material_budget = fields.Float(string="Material Budget")
    service_budget = fields.Float(string="Service Budget")
    labor_budget = fields.Float(string="Labor Budget")
    equipment_budget = fields.Float(string="Equipment Budget")
    overhead_budget = fields.Float(string="Overhead Budget")
    total_budget = fields.Float(string="Total Budget")

    @api.depends('material_consumption')
    def get_material_consumption(self):
        for ids in self:
            consumption = withdrawal = 0
            if len(ids.material_consumption) > 0:
                for material in ids.material_consumption:
                    consumption += material.consumption_progress
                    withdrawal += material.withdrawal_progress
                ids.update({
                    'material_consumption_progress': consumption > 0 and consumption / len(ids.material_consumption) or 0,
                    'material_withdrawal_progress': withdrawal > 0 and withdrawal / len(ids.material_consumption) or 0,
                })


class ProjectMaterialConsumption(models.Model):
    _name = 'project.material.consumption'
    _description = "Material Consumption"

    product_id = fields.Many2one('product.product', string="Product")
    estimated_qty = fields.Float(string='Estimated Quantity')
    tot_stock_received = fields.Float(string='Total Stock Received',
                                      compute='_update_tot_stock')
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    used_qty = fields.Float(string='Used Quantity', readonly=True)
    available_stock = fields.Float(string='Available Stock',
                                   compute='_compute_tot_stock', readonly=True)
    consumption_progress = fields.Float(string="Consumption",
                                        compute='get_consumption_progress')
    withdrawal_progress = fields.Float(string="Material Withdrawal Progress",
                                                 compute="get_consumption_progress")
    wastage_percent = fields.Float(string="Wastage",
                                   compute='_compute_waste_percent')
    scrap_percent = fields.Float(string="Scrapped",
                                 compute='_compute_scrap_percent')
    task_id = fields.Many2one('project.task', 'Task')

    @api.depends('used_qty', 'tot_stock_received', 'scrap_percent', 'tot_stock_received')
    def get_consumption_progress(self):
        for ids in self:
            if ids.used_qty or ids.scrap_percent or ids.tot_stock_received:
                scrap_product = self.env['project.scrap.products'].search([
                    ('task_id', '=', ids.task_id.id),
                    ('product_id', '=', ids.product_id.id)])
                qty = 0
                for scrap in scrap_product:
                    qty += scrap.qty
                consumption = ((ids.used_qty + qty) / ids.tot_stock_received * 100)
                withdrawal = (ids.tot_stock_received / ids.tot_stock_received * 100)
                ids.update({
                    'consumption_progress': consumption,
                    'withdrawal_progress': withdrawal})

    @api.depends('task_id')
    def _compute_waste_percent(self):
        for material in self:
            waste_mgmt = self.env['project.waste.management'].search([
                ('task_id', '=', material.task_id.id),
                ('product_id', '=', material.product_id.id)])
            waste_percent = 0
            if waste_mgmt:
                qty = received = 0
                for waste in waste_mgmt:
                    qty += waste.qty
                if material.tot_stock_received:
                    received = material.tot_stock_received
                if qty and received != 0:
                    waste_percent = qty / received * 100
            material.update({'wastage_percent': waste_percent})

    @api.depends('task_id')
    def _compute_scrap_percent(self):
        for material in self:
            scrap_product = self.env['project.scrap.products'].search([
                ('task_id', '=', material.task_id.id),
                ('product_id', '=', material.product_id.id)])
            scrap_percent = 0
            if scrap_product:
                qty = received = 0
                for scrap in scrap_product:
                    qty += scrap.qty
                if material.tot_stock_received:
                    received = material.tot_stock_received
                if qty and received != 0:
                    scrap_percent = qty / received * 100
            material.update({'scrap_percent': scrap_percent})

    @api.depends('task_id.stock_location_id')
    def _update_tot_stock(self):
        for material in self:
            product = material.product_id.id
            material_request = self.env['material.requisition.bom'].search([
                ('task_id', '=', material.task_id.id), ('state', '=', 'approved')])
            qty = 0
            for mr_val in material_request:
                location_id = mr_val.picking_id.location_dest_id.id
                move = self.env['stock.move'].search([
                    ('picking_id', '=', mr_val.picking_id.id),
                    ('product_id', '=', product)])
                for vals in move:
                    qty += vals.quantity_done
                material.update({'tot_stock_received': qty})

    @api.depends('tot_stock_received')
    def _compute_tot_stock(self):
        for material in self:
            if not isinstance(material.task_id.id, models.NewId):
                vals = material.search([('id', '=', material.id)])
                waste_management = self.env['project.waste.management'].search([
                        ('task_id', '=', vals.task_id.id),
                        ('product_id', '=', material.product_id.id)])
                scrap_product = self.env['project.scrap.products'].search([
                        ('task_id', '=', vals.task_id.id),
                        ('product_id', '=', material.product_id.id)])
                waste_qty = 0
                scrap = 0
                for waste in waste_management:
                    if waste.is_cutted is False:
                        waste_qty += waste.qty
                for scraps in scrap_product:
                    scrap += scraps.qty
                avail_stock = material.tot_stock_received - (material.used_qty + waste_qty + scrap)
                material.update({'available_stock': avail_stock})
            else:
                if material.tot_stock_received:
                    material.update({'available_stock': material.tot_stock_received})

    def action_used_qty(self):
        return {
                'name': _('Used Quantity'),
                'type': 'ir.actions.act_window',
                'res_model': 'project.used.quantity',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('construction_boq_and_material_management.project_used_quantity_form').ids,
                'target': 'new',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_material_id': self.id,
                    'task_id': self.task_id.id,
                    'received': self.tot_stock_received
                }
            }

    def action_waste_percent(self):
        return {
                'name': _('Waste Process'),
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.waste.process',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('construction_boq_and_material_management.project_waste_process_form').ids,
                'target': 'new',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_material_id': self.id,
                    'default_uom_id': self.uom_id.id,
                    'task_id': self.task_id.id,
                    'uom_id': self.uom_id.id,
                }
            }

    def action_scrap_percent(self):
        return {
                'name': _('Scrap Move'),
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.scrap.move',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('construction_boq_and_material_management.project_scrap_move_form').ids,
                'target': 'new',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_material_id': self.id,
                    'default_uom_id': self.uom_id.id,
                    'task_id': self.task_id.id,
                }
            }


class ProjectWasteManagement(models.Model):
    _name = 'project.waste.management'
    _description = "Waste Management"

    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    qty = fields.Float(string='Quantity')
    wastage_percent = fields.Float(string='Wastage Percentage')
    date_recorded = fields.Date(string='Date Recorded')
    task_id = fields.Many2one('project.task', 'Task')
    is_cutted = fields.Boolean(string="Is Cutted", default=False)
    new_product_id = fields.Many2one('product.product', string="New Product")
    material_waste = fields.Selection([
        ('whole', 'Whole Material Waste'),
        ('cutted', 'Is there a Cutted/Portion Material Waste')],
                                      string='Material Waste',
                                      track_visibility='onchange',
                                      default='whole')
    waste_location_id = fields.Many2one('stock.location',
                                        string="Waste Location",
                                        )
    description = fields.Text(string='Description')
    cutted_portion = fields.Float(string='Cutted Portion')
    cutted_qty = fields.Float(string='')


class ProjectScrapProducts(models.Model):
    _name = 'project.scrap.products'
    _description = "Scrap Products"

    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    qty = fields.Float(string='Quantity')
    scrap_percent = fields.Float(string='Scrap Percentage')
    scrap_reason = fields.Text(string='Scrap Reason')
    date_recorded = fields.Date(string='Date Recorded',
                                default=fields.Date.context_today)
    task_id = fields.Many2one('project.task', 'Task')
    scrap_location_id = fields.Many2one('stock.location',
                                        string="Scrap Location")
