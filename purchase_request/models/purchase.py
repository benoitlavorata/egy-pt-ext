from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_request_id = fields.Many2one('sprogroup.purchase.request', string="Purchase Request Origin")

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        if res.purchase_request_id:
            res.purchase_request_id.write({'purchase_order_id': res.id})
        return res


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    purchase_request_id = fields.Many2one('sprogroup.purchase.request', string="Purchase Request Origin")
    purchase_request_merge_ids = fields.Many2many('sprogroup.purchase.request', 'requests_requisition_rel', 'f1', 'f2', string="Purchase Request Merged")

    @api.model
    def create(self, vals):
        res = super(PurchaseRequisition, self).create(vals)
        if res.purchase_request_id:
            res.purchase_request_id.write({'purchase_requisition_id': res.id})
        return res
