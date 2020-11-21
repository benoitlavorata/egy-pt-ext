# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date, timedelta
from io import BytesIO,StringIO
from odoo.tools.float_utils import float_compare, float_is_zero, float_round




class WizardInventoryAdjustment(models.TransientModel):
	_name = 'wizard.inventory.adjustment'

	inventory_date = fields.Date('Inventory BackDate',required=True)
	inventory_remark = fields.Char('Remark',required=True)



	def custom_backdateorder_button_inventoryadjust(self):

		custom_stock_inventory_ids = self.env['stock.inventory'].browse(self._context.get('active_id'))

		custom_stock_inventory_ids.action_validate()


		for custom_stock_inventory_ids1 in custom_stock_inventory_ids:
			custom_stock_inventory_ids1.write({'accounting_date':self.inventory_date})

			for custom_stock_inventory_ids3 in custom_stock_inventory_ids1.line_ids:
				custom_stock_inventory_ids3.write({'invline_remark':self.inventory_remark})

			for custom_stock_inventory_ids2 in custom_stock_inventory_ids1.move_ids:
				custom_stock_inventory_ids2.write({'date':custom_stock_inventory_ids1.accounting_date,
					'move_remark':self.inventory_remark})

				for custom_stock_inventory_ids4 in custom_stock_inventory_ids2.move_line_ids:
					custom_stock_inventory_ids4.write({'date':custom_stock_inventory_ids2.date,
						'moveline_remark':self.inventory_remark})

					custom_accountmove = self.env['account.move'].create({'date':self.inventory_date,
						'journal_id':3,'stock_move_id':custom_stock_inventory_ids2.id})

					self.env['account.move.line'].create({'partner_id':3,'account_id':1,
						'name':'Transfer','move_id':custom_accountmove.id})

					custom_accountmove.post()



class LineInventoryUpdate(models.Model):
	_inherit = 'stock.inventory.line'

	invline_remark = fields.Char('Remark')



class StockMoveLineUpdate(models.Model):
	_inherit = 'stock.move.line'

	moveline_remark = fields.Char('Remark')


class StockMoveUpdate(models.Model):
	_inherit = 'stock.move'

	move_date = fields.Date(string="Date")
	move_remark = fields.Char(string="Remarks")

	def _action_done(self,cancel_backorder=False):
		res = super(custom_StockMove_Update, self)._action_done()
		
		for move in res:
			move.write({'date': move.move_date or fields.Datetime.now()})
			for line in move.mapped('move_line_ids'):
				line.write({'date': move.move_date or fields.Datetime.now()})
		return res

		


class StockInventoryUpdate(models.Model):
	_inherit = 'stock.inventory'


	def action_validate_custom(self):

		return {
					'view_type': 'form',
					'view_mode': 'form',
					'res_model': 'wizard.inventory.adjustment',
					'type': 'ir.actions.act_window',
					'target': 'new',
					'res_id': False,
					'context': self.env.context,
				}

