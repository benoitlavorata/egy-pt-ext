# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProjectUsedQuantity(models.Model):
    _name = 'project.used.quantity'
    _description = "Project Used Quantity"

    product_id = fields.Many2one('product.product', string="Product",
                                 readonly=True)
    quantity = fields.Float(string='Quantity')
    material_id = fields.Many2one('project.material.consumption',
                                  string="Material")

    @api.constrains('quantity')
    def _onchange_used_qty(self):
        qty = self.quantity
        available_stock = self.material_id.available_stock
        if(qty > available_stock):
            raise UserError(_('Used Quantity​ can not be greater than the ​Available Stock .'))


    def update_used_qty(self):
        task = self.env.context['task_id']
        received_qty = self.env.context['received']
        product = self.product_id.id
        waste_management = self.env['project.waste.management'].search([
            ('task_id', '=', task), ('product_id', '=', product)])
        scrap_product = self.env['project.scrap.products'].search([
            ('task_id', '=', task), ('product_id', '=', product)])
        waste_qty = 0
        scrap = 0
        for waste in waste_management:
            waste_qty += waste.qty
        for scraps in scrap_product:
            scrap += scraps.qty
        available_qty = received_qty - (self.quantity + waste_qty + scrap)
        self.material_id.write({'used_qty': self.material_id.used_qty + self.quantity,
                                'available_stock': available_qty,
                                'consumption_progress': self.quantity})
        from_loc = self.material_id.task_id.stock_location_id.id

        stock_picking = self.env['stock.picking']
        stock_warehouse = self.env['stock.warehouse'].sudo().search([
            ('company_id', '=', self.material_id.task_id.company_id.id)], limit=1)
        stock_move = self.env['stock.move']
        picking = stock_picking.create({
                'picking_type_id': self.material_id.task_id.project_id.picking_type_id.id,
                'location_id': from_loc,
                'location_dest_id': stock_warehouse.lot_stock_id.id,
                'material_id': self.material_id.id
                                            })
        stock_move.create({
                'name': _('New Move:') + self.material_id.product_id.display_name,
                'product_id': self.material_id.product_id.id,
                'product_uom_qty': self.quantity,
                'product_uom': self.material_id.product_id.uom_id.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
            })
        picking.action_confirm()
        picking.action_assign()
        for pack_operation in picking.move_lines:
            pack_operation.quantity_done = pack_operation.product_uom_qty
        picking.button_validate()


class ProjectWasteProcess(models.Model):
    _name = 'wizard.waste.process'
    _description = "Waste Process Wizard"

    product_id = fields.Many2one('product.product', string="Product",
                                 readonly=True)
    new_product_id = fields.Many2one('product.product',
                                     string="New Product Name",
                                     required=True)
    material_waste = fields.Selection([
        ('whole', 'Whole Material Waste'),
        ('cutted', 'Is there a Cutted/Portion Material Waste')],
                                      string='Material Waste',
                                      required=True, copy=False,
                                      index=True,
                                      track_visibility='onchange',
                                      default='whole')
    quantity = fields.Float(string='Quantity')
    waste_location_id = fields.Many2one('stock.location',
                                        string="Waste Location",
                                        domain="[('usage', '=', 'internal'),('scrap_location', '=', False)]",
                                        required=True)
    description = fields.Text(string='Description',
                              required=True)
    material_id = fields.Many2one('project.material.consumption',
                                  string="Material")
    cutted_portion = fields.Float(string='Cutted Portion')
    cutted_qty = fields.Float(string='')
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure",
                             readonly=True)
    waste_percent = fields.Float(string="Waste Percentage",
                                 compute='_update_waste_percent')

    @api.depends('quantity')
    def _update_waste_percent(self):
        for val in self:
            val.update({'waste_percent': val.quantity})

    @api.constrains('quantity')
    def _onchange_wastage_qty(self):
        qty = self.quantity
        available_stock = self.material_id.available_stock
        if(qty > available_stock):
            if (self.material_waste == 'whole'):
                raise UserError(_('Wastage Quantity​ can not be greater than the ​Available Stock .'))

    def update_waste_process(self):
        uom = self.env.context['uom_id']
        waste_management = self.env['project.waste.management']
        cutted = False
        if self.material_waste == 'cutted':
            cutted = True
        waste_management.create({'product_id': self.product_id.id,
                                 'new_product_id': self.new_product_id.id,
                                 'qty': self.quantity,
                                 'task_id': self.material_id.task_id.id,
                                 'date_recorded': fields.Date.today(),
                                 'uom_id': uom,
                                 'is_cutted': cutted,
                                 'material_waste': self.material_waste,
                                 'waste_location_id': self.waste_location_id.id,
                                 'description': self.description,
                                 'cutted_portion': self.cutted_portion,
                                 'cutted_qty': self.cutted_qty,
                                 'wastage_percent': self.waste_percent})
        if self.material_waste == 'whole':
            stock_picking = self.env['stock.picking']
            stock_move = self.env['stock.move']
            picking = stock_picking.create({'picking_type_id': self.material_id.task_id.picking_type_id.id,
                                            'location_id': self.material_id.task_id.stock_location_id.id,
                                            'location_dest_id': self.waste_location_id.id,
                                            })
            stock_move.create({
                    'name': _('New Move:') + self.new_product_id.display_name,
                    'product_id': self.new_product_id.id,
                    'product_uom_qty': self.quantity,
                    'product_uom': self.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                })
            picking.action_confirm()
            picking.action_assign()
            for pack_operation in picking.move_lines:
                pack_operation.quantity_done = pack_operation.product_uom_qty
            picking.button_validate()


class ProjectScrapMove(models.Model):
    _name = 'wizard.scrap.move'
    _description = "Scrap Move Wizard"

    product_id = fields.Many2one('product.product', string="Product",
                                 readonly=True)
    quantity = fields.Float(string='Quantity of Scrap Material')
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure",
                             readonly=True)
    scrap_percent = fields.Float(string='Scrap Percentage',
                                 compute='_update_scrap_percent',
                                 readonly=True)
    scrap_location_id = fields.Many2one('stock.location',
                                        string="Scrap Location", required=True,
                                        domain="[('usage', '=', 'inventory'),('scrap_location', '=', True)]")
    description = fields.Text(string='Description',
                              required=True)
    material_id = fields.Many2one('project.material.consumption',
                                  string="Material")

    @api.depends('quantity')
    def _update_scrap_percent(self):
        for val in self:
            val.update({'scrap_percent': val.quantity})

    @api.constrains('quantity')
    def _onchange_scrap_qty(self):
        qty = self.quantity
        available_stock = self.material_id.available_stock
        if(qty > available_stock):
            raise UserError(_('Scrap Quantity​ can not be greater than the ​Available Stock .'))

    def update_scrap_move(self):
        scrap_move = self.env['project.scrap.products']
        scrap_move.create({'product_id': self.product_id.id,
                           'uom_id': self.uom_id.id,
                           'qty': self.quantity,
                           'date_recorded': fields.Date.today(),
                           'scrap_reason': self.description,
                           'task_id': self.material_id.task_id.id,
                           'scrap_location_id': self.scrap_location_id.id,
                           'scrap_percent': self.scrap_percent,
                           })
        qty = self.material_id.available_stock - self.quantity
        self.material_id.write({'available_stock': qty
                                })
        stock_picking = self.env['stock.picking']
        stock_move = self.env['stock.move']
        picking = stock_picking.create({'picking_type_id': self.material_id.task_id.picking_type_id.id,
                                        'location_id': self.material_id.task_id.stock_location_id.id,
                                        'location_dest_id': self.scrap_location_id.id,
                                        })
        stock_move.create({
                'name': _('New Move:') + self.material_id.product_id.display_name,
                'product_id': self.material_id.product_id.id,
                'product_uom_qty': self.quantity,
                'product_uom': self.uom_id.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
            })
        picking.action_confirm()
        picking.action_assign()
        for pack_operation in picking.move_lines:
            pack_operation.quantity_done = pack_operation.product_uom_qty
        picking.button_validate()


class SkitStockPicking(models.Model):
    _inherit = 'stock.picking'

    material_id = fields.Many2one('project.material.consumption',
                                  "Material Requisition")
