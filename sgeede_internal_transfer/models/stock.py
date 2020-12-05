# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero

_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def _action_start(self):
        for inventory in self:
            if inventory.state != 'draft':
                continue
            if inventory.date:
                vals = {
                    'state': 'confirm'
                }
            else:
                vals = {
                    'state': 'confirm',
                    'date': fields.Datetime.now()
                }
            if not inventory.line_ids and not inventory.start_empty:
                self.env['stock.inventory.line'].create(inventory._get_inventory_lines_values())
            inventory.write(vals)


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    def _get_default_inventory_date(self):
        date = fields.Datetime.now()
        act_id = self.env['stock.inventory'].search([('id', '=', self._context.get('default_inventory_id'))]).date
        if act_id:
            return act_id
        else:
            return date

    inventory_date = fields.Datetime('Inventory Date', readonly=False,
                                     default=_get_default_inventory_date,
                                     help="Last date at which the On Hand Quantity has been computed.")


class StockMove(models.Model):
    _inherit = "stock.move"

    date = fields.Datetime(
        'Date', default=fields.Datetime.now, index=True, required=True,
        states={'done': [('readonly', True)]},
        help="Move date: scheduled date until move is done, then date of actual move processing")

    @api.model_create_multi
    def create(self, vals_list):
        tracking = []
        for vals in vals_list:
            if vals.get('date'):
                self.date = vals.get('date')
                print(self.date)
            if not self.env.context.get('mail_notrack') and vals.get('picking_id'):
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                initial_values = {picking.id: {'state': picking.state}}
                tracking.append((picking, initial_values))
        res = super(StockMove, self).create(vals_list)
        for picking, initial_values in tracking:
            picking.message_track(picking.fields_get(['state']), initial_values)
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    date = fields.Datetime('Date', default=fields.Datetime.now, required=True)

    def _action_done(self):
        Quant = self.env['stock.quant']

        ml_to_delete = self.env['stock.move.line']
        for ml in self:
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                  rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))

            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            if ml.lot_name and not ml.lot_id:
                                lot = self.env['stock.production.lot'].create(
                                    {'name': ml.lot_name, 'product_id': ml.product_id.id, 'company_id': ml.move_id.company_id.id}
                                )
                                ml.write({'lot_id': lot.id})
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            continue
                    elif ml.move_id.inventory_id:
                        continue

                    if not ml.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % ml.product_id.display_name)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_to_delete |= ml
        ml_to_delete.unlink()

        (self - ml_to_delete)._check_company()

        done_ml = self.env['stock.move.line']
        for ml in self - ml_to_delete:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding

                if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) > 0:
                    qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id, rounding_method='HALF-UP')
                    extra_qty = qty_done_product_uom - ml.product_qty
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
                if not ml._should_bypass_reservation(ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
                    try:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    except UserError:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            done_ml |= ml

        if self.move_id.date:
            (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
                'product_uom_qty': 0.00,
                'date': self.move_id.date,
            })
        else:
            (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
                'product_uom_qty': 0.00,
                'date': fields.Datetime.now(),
            })


class AccountMove(models.Model):
    _inherit = 'account.move'

    vendor_ref = fields.Char()


class stock_picking(models.Model):
    _inherit = "stock.picking"

    def do_internal_transfer_details(self):
        context = dict(self._context or {})
        picking = [picking]
        context.update({
            'active_model': self._name,
            'active_ids': picking,
            'active_id': len(picking) and picking[0] or False
            })

        return True

    transfer_id = fields.Many2one('stock.internal.transfer', _('Transfer'))


class stock_move(models.Model):
    _inherit = "stock.move"

    analytic_account_id = fields.Many2one('account.analytic.account', _('Analytic Account'))


class stock_warehouse(models.Model):
    _inherit = "stock.warehouse"

    user_ids = fields.Many2many('res.users', 'company_user_rel', 'company_id', 'user_id', 'Owner user')
