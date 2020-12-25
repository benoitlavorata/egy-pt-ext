# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from dateutil import relativedelta


_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def _action_start(self):
        for inventory in self:
            if inventory.state != 'draft':
                continue
            if inventory.date:
                vals = {
                    'state': 'confirm',
                    'inv_type': 'adj'
                }
            else:
                vals = {
                    'state': 'confirm',
                    'date': fields.Datetime.now(),
                    'inv_type': ''
                }
            if not inventory.line_ids and not inventory.start_empty:
                self.env['stock.inventory.line'].create(inventory._get_inventory_lines_values())
            inventory.write(vals)

    inv_type = fields.Selection([('move', 'Move'), ('adj', 'Adjustment')], default='move')


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

    analytic_account_id = fields.Many2one('account.analytic.account', _('Analytic Account'))
    date = fields.Datetime(
        'Date', default=fields.Datetime.now, index=True, required=True,
        states={'done': [('readonly', True)]})

    def _action_done(self, cancel_backorder=False):
        act_id = self.env['stock.inventory'].search([('id', '=', self.inventory_id.id)], limit=1)
        self.filtered(lambda move: move.state == 'draft')._action_confirm()
        moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_todo = self.env['stock.move']

        # Cancel moves where necessary ; we should do it before creating the extra moves because
        # this operation could trigger a merge of moves.
        for move in moves:
            if move.quantity_done <= 0:
                if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
                    move._action_cancel()

        # Create extra moves where necessary
        for move in moves:
            if move.state == 'cancel' or move.quantity_done <= 0:
                continue

            moves_todo |= move._create_extra_move()

        moves_todo._check_company()
        # Split moves where necessary and move quants
        for move in moves_todo:
            # To know whether we need to create a backorder or not, round to the general product's
            # decimal precision and not the product's UOM.
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
                # Need to do some kind of conversion here
                qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
                new_move = move._split(qty_split)
                move._unreserve_initial_demand(new_move)
                if cancel_backorder:
                    self.env['stock.move'].browse(new_move).with_context(moves_todo=moves_todo)._action_cancel()
        moves_todo.mapped('move_line_ids').sorted()._action_done()
        # Check the consistency of the result packages; there should be an unique location across
        # the contained quants.
        for result_package in moves_todo\
                .mapped('move_line_ids.result_package_id')\
                .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
            if len(result_package.quant_ids.filtered(lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity), precision_rounding=q.product_uom_id.rounding)).mapped('location_id')) > 1:
                raise UserError(_('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
        picking = moves_todo.mapped('picking_id')
        dt = fields.Datetime.now()
        if act_id.inv_type == 'adj':
            dt = act_id.date
        print(dt)
        moves_todo.write({'state': 'done', 'date': dt})
        move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
        for move_dest in moves_todo.move_dest_ids:
            move_dests_per_company[move_dest.company_id.id] |= move_dest
        for company_id, move_dests in move_dests_per_company.items():
            move_dests.sudo().with_context(force_company=company_id)._action_assign()

        # We don't want to create back order for scrap moves
        # Replace by a kwarg in master
        if self.env.context.get('is_scrap'):
            return moves_todo

        if picking and not cancel_backorder:
            picking._create_backorder()
        return moves_todo


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


class StockPicking(models.Model):
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


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    user_ids = fields.Many2many('res.users', 'company_user_rel', 'company_id', 'user_id', 'Owner user')
