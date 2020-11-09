from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class DoPurchaseOrder(models.TransientModel):
    _name = 'do.purchase.order'

    action = fields.Selection([
                        ('New', 'Create New'),
                        ('Merge', 'Merge to Existing PO')
                        ], string="Select Action", required=True, default='New')
    project_related = fields.Boolean(string="A Project Related?")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    purchase_id = fields.Many2one('purchase.order', string="RFQ", domain="[('project_related','=', project_related), ('state', '=', ['draft'])]")
    purchase_request_id = fields.Many2one('sprogroup.purchase.request', string="Purchase Request Origin")
    partner_id = fields.Many2one('res.partner', string="Supplier", domain="[('supplier', '=', True)]")
    date_planned = fields.Datetime(string="Required Date")

    @api.model
    def default_get(self, fields):
        res = super(DoPurchaseOrder, self).default_get(fields)
        data = self.env['sprogroup.purchase.request'].browse(self._context.get('active_ids')[0])
        res['analytic_account_id'] = data.analytic_account_id.id
        res['purchase_request_id'] = data.id
        res['project_related'] = data.task_id and True or False
        return res

    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1].id

    def create_purchase(self):
        po_ids = []
        fpos = self.env['account.fiscal.position']
        for i in self:
            po = i.purchase_id
            if not i.action in ['New']:
                for line in i.purchase_request_id.line_ids:
                    domain = [('order_id', '=', po.id), ('product_id', '=', line.product_id.id), ('product_uom', '=', line.product_uom_id.id)]
                    if i.project_related:
                        domain.append(('task_id', '=', i.purchase_request_id.task_id.id))
                    po_line = i.env['purchase.order.line'].search(domain)
                    if po_line[:1]:
                        po_line[:1].write({
                                    'product_qty': po_line[:1].product_qty + line.product_qty
                        })
                    else:
                        if i.env.uid == SUPERUSER_ID:
                            company_id = i.env.user.company_id.id
                            taxes_id = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
                        else:
                            taxes_id = fpos.map_tax(line.product_id.supplier_taxes_id)
                        po.write({
                                    'order_line': [[0, 0, {
                                            'product_id' : line.product_id.id,
                                            'state' : 'draft',
                                            'product_uom' : line.product_uom_id.id,
                                            'price_unit' : 0,
                                            'date_planned' :  datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                            # 'taxes_id' : ((6,0,[taxes_id.id])),
                                            'product_qty' : line.product_qty,
                                            'name' : line.product_id.name,
                                            'account_analytic_id': i.purchase_request_id.task_id and i.analytic_account_id.id or False,
                                            'phase_id': i.purchase_request_id.task_id and i.purchase_request_id.phase_id.id or False,
                                            'task_id': i.purchase_request_id.task_id and i.purchase_request_id.task_id.id or False,
                                            'project_boq_category': i.purchase_request_id.task_id and 'meterial' or '',
                                        }]]
                                })
                i.purchase_request_id.write({'purchase_order_id': po.id})
                i.purchase_request_id.write({
                    'purchase_request_merge_ids': [(4, self.purchase_request_id.id)]
                })
            else:
                order_line = []
                for line in i.purchase_request_id.line_ids:
                    if i.env.uid == SUPERUSER_ID:
                        company_id = i.env.user.company_id.id
                        taxes_id = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
                    else:
                        taxes_id = fpos.map_tax(line.product_id.supplier_taxes_id)
                    order_line.append([0, 0,
                                        {
                                           'name': line.product_id.name,
                                           'product_id': line.product_id.id,
                                           'product_uom': line.product_uom_id.id,
                                           'product_qty': line.product_qty,
                                           'price_unit': 0,
                                           # 'taxes_id': [(6, 0, taxes_id.id)],
                                           'date_planned': i.date_planned or fields.Date.today(),
                                           'account_analytic_id': i.analytic_account_id and i.analytic_account_id.id or False,
                                           'move_dest_ids': [],
                                           'phase_id': i.purchase_request_id.task_id and i.purchase_request_id.phase_id.id or False,
                                           'task_id': i.purchase_request_id.task_id and i.purchase_request_id.task_id.id or False,
                                           'project_boq_category': i.purchase_request_id.task_id and 'meterial' or '',
                                       }])

                po = i.env['purchase.order'].create({
                    'order_line': order_line,
                    'partner_id': i.partner_id.id,
                    'date_order': datetime.now(),
                    'picking_type_id': i._default_picking_type(),
                    'payment_term_id': i.partner_id.property_supplier_payment_term_id.id,
                    'project_related': i.project_related,
                    'date_planned': i.date_planned,
                    'purchase_request_id': i.purchase_request_id.id,
                })
                i.purchase_request_id.write({'purchase_order_id': po.id})
        #     po_ids.append(po.id)
        # # raise ValidationError(_('%s'%(str(po_ids))))
        # '''
        # This function returns an action that display given purchase order ids.
        # When only one found, show the PO immediately.
        # '''
        # action = self.env.ref('purchase.purchase_order_tree')
        # result = action.read()[0]
        # # result['context'] = {}
        # # if not po_ids or len(po_ids) > 1:
        # #     result['domain'] = "[('id','in',po_ids)]"
        # # elif len(po_ids) == 1:
        # res = self.env.ref('purchase.purchase_order_form', False)
        # result['views'] = [(res and res.id or False, 'form')]
        # result['res_id'] = po_ids
        # return result
