# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    picking_id = fields.Many2one('stock.picking', string='Stock Picking')

    def button_confirm_unused(self):
        result = super(PurchaseOrder, self).button_confirm()
        cost_line_obj = self.env['job.cost.line']
        for order in self:
            for line in order.order_line:
                cost_id = line.job_cost_id
                if not line.job_cost_line_id:
                    if cost_id:
                        hours = 0.0
                        qty = 0.0
                        date = line.date_planned
                        product_id = line.product_id.id
                        description = line.name
                        if line.product_id.type == 'service':
                            job_type = 'labour'
                            hours = line.product_qty
                        else:
                            job_type = 'material'
                            qty = line.product_qty

                        price = line.price_unit
                        vals = {
                            'date': date,
                            'product_id': product_id,
                            'description': description,
                            'job_type': job_type,
                            'product_qty': qty,
                            'cost_price': price,
                            'hours': hours,
                        }
                        job_cost_line_id = cost_line_obj.create(vals)
                        line.job_cost_line_id = job_cost_line_id.id
                        job_cost_line_ids = cost_id.job_cost_line_ids.ids
                        job_cost_line_ids.append(job_cost_line_id.id)
                        if job_cost_line_id.job_type == 'labour':
                            cost_vals = {
                                'job_labour_line_ids': [(6, 0, job_cost_line_ids)],
                            }
                        else:
                            cost_vals = {
                                'job_cost_line_ids': [(6, 0, job_cost_line_ids)],
                            }
                        cost_id.update(cost_vals)
        return result


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    job_cost_id = fields.Many2one('job.costing', string='Job Cost Center')
    job_cost_line_id = fields.Many2one('job.cost.line', string='Job Cost Line')

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)
        res.update({
            'job_cost_id': self.job_cost_id.id,
            'job_cost_line_id': self.job_cost_line_id.id,
        })
        return res


class PurchaseRequisition(models.Model):
    _inherit = 'material.purchase.requisition'

    @api.onchange('task_id')
    def onchange_project_task(self):
        for rec in self:
            rec.project_id = rec.task_id.project_id.id
            rec.analytic_account_id = rec.task_id.project_id.analytic_account_id.id

    @api.depends('requisition_line_ids',
                 'requisition_line_ids.product_id',
                 'requisition_line_ids.product_id.boq_type')
    def compute_equipment_machine(self):
        eqp_machine_total = 0.0
        work_resource_total = 0.0
        work_cost_package_total = 0.0
        subcontract_total = 0.0
        for rec in self:
            for line in rec.requisition_line_ids:
                if line.product_id.boq_type == 'eqp_machine':
                    eqp_machine_total += line.product_id.standard_price * line.qty
                if line.product_id.boq_type == 'worker_resource':
                    work_resource_total += line.product_id.standard_price * line.qty
                if line.product_id.boq_type == 'work_cost_package':
                    work_cost_package_total += line.product_id.standard_price * line.qty
                if line.product_id.boq_type == 'subcontract':
                    subcontract_total += line.product_id.standard_price * line.qty
            print("::::::::::::::::::::::::eqp_machine_total", eqp_machine_total)
            rec.equipment_machine_total = eqp_machine_total
            rec.worker_resource_total = work_resource_total
            rec.work_cost_package_total = work_cost_package_total
            rec.subcontract_total = subcontract_total

#     #@api.multi
#     @api.depends('purchase_order_ids')
#     def _purchase_order_count(self):
#         for rec in self:
#             rec.purchase_order_count = len(rec.purchase_order_ids)

    task_id = fields.Many2one(
        'project.task',
        string='Task / Job Order',
    )
    task_user_id = fields.Many2one(
        'res.users',
        related='task_id.user_id',
        string='Task / Job Order User'
    )
    project_id = fields.Many2one(
        'project.project',
        string='Construction Project',
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
    )
#     analytic_account_id = fields.Many2one(
#         'account.analytic.account',
#         string='Analytic Account',
#     )
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='Purchase Orders',
    )
#     purchase_order_count = fields.Integer(
#         compute='_purchase_order_count',
#         string="Purchase Orders",
#         store=True,
#     )
    equipment_machine_total = fields.Float(
        compute='compute_equipment_machine',
        string='Equipment / Machinery Cost',
        store=True,
    )
    worker_resource_total = fields.Float(
        compute='compute_equipment_machine',
        string='Worker / Resource Cost',
        store=True,
    )
    work_cost_package_total = fields.Float(
        compute='compute_equipment_machine',
        string='Work Cost Package',
        store=True,
    )
    subcontract_total = fields.Float(
        compute='compute_equipment_machine',
        string='Subcontract Cost',
        store=True,
    )
