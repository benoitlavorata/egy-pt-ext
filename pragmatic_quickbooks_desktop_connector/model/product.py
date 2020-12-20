from odoo import api, fields, models, _
import requests
import ast
import logging
import json

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    quickbooks_id = fields.Char("Quickbook id ", copy=False)
    is_updated = fields.Boolean("Is Updated")
    qbd_tax_code = fields.Many2one('qbd.tax.code')

    @api.model
    def create(self, vals):
        # print ("-------------------------",vals)
        product_id = super(ProductTemplate, self).create(vals)
        if 'qbd_tax_code' in vals:
            check_tax = self.env['qbd.tax.code'].search([('id', '=', vals['qbd_tax_code'])])
            if not check_tax.is_taxable:
                product_id.taxes_id = [(6, 0, [])]
        return product_id

    def write(self, vals):
        # print ("In write of Product Template  11 -------------------------", vals)

        if not 'is_updated' in vals and not 'quickbooks_id' in vals:
            vals['is_updated'] = True
        if 'qbd_tax_code' in vals:
            check_tax = self.env['qbd.tax.code'].search([('id', '=', vals['qbd_tax_code'])])
            if not check_tax.is_taxable:
                # print ("In write of Product Template 22 -------------------------", check_tax.is_taxable)
                vals['taxes_id'] = [(6, 0, [])]
        # print ("In write of Product Template  33 -------------------------", vals)
        return super(ProductTemplate, self).write(vals)


class ProductProduct(models.Model):
    _inherit = "product.product"

    # quickbooks_id = fields.Char("Quickbook id ", copy=False)
    # is_updated = fields.Boolean("Is Updated", default=False)

    # @api.multi
    # def create(self, vals):
    #     print ("---------------------- PP---",vals)
    #
    #     product_id = super(ProductProduct, self).create(vals)
    #     # print ("-------------------------", product_id.taxes_id.is_taxable)
    #
    #     if product_id.qbd_tax_code:
    #         if not product_id.qbd_tax_code.is_taxable:
    #             product_id.taxes_id = [(6, 0, [])]
    #     return product_id

    def create_products(self, products):
        # print('\n\n\nProducts :: ', products)
        # print('\n\n Total product Count : ', len(products))
        company = self.env['res.users'].search([('id', '=', 2)]).company_id

        for product in products:
            vals = {}
            if 'quickbooks_id' in product and product.get('quickbooks_id'):
                product_id = self.search([('quickbooks_id', '=', product.get('quickbooks_id'))], limit=1)

                if not product_id:
                    # print('in ifff :')
                    # create new product
                    vals = self._prepare_product_dict(product)
                    if vals:

                        new_product_id = self.create(vals)
                        # print ("---------------------------", vals['quickbooks_id'], new_product_id.quickbooks_id)
                        if new_product_id:
                            self.env.cr.commit()
                            # print('Product Commited !! : ',new_product_id.name)
                            company.write({
                                'last_imported_qbd_id_for_product':product.get("last_time_modified")
                            })

                else:
                    # print('in else : ------------------------------ ')
                    # update existing product
                    vals = self._prepare_product_dict(product)
                    product_id.write(vals)

        return True

    def _prepare_product_dict(self, product):
        # print('\nProduct in prepare dict : \n', product, '\n')
        vals = {}
        if product:
            vals.update({
                'name': product.get('name') if product.get('name') else '',
                'quickbooks_id': product.get('quickbooks_id') if product.get('quickbooks_id') else '',
                'default_code': product.get('default_code') if product.get('default_code') else '',
                'active': product.get('active') if product.get('active') else '',
                'standard_price': float(product.get('standard_price')) if product.get('standard_price') else 0.00,
                'list_price': float(product.get('list_price')) if product.get('list_price') else 0.00,
                'description': product.get('description') if product.get('description') else '',
                'qty_available': float(product.get('qty_available')) if product.get('qty_available') else 0.000,
                'description_purchase': product.get('description_purchase') if product.get('description_purchase') else '',
                'type': product.get('type') if product.get('type') else '',
            })

            if 'tax_code' in product and product.get('tax_code'):

                tax_code = self.env['qbd.tax.code'].search([('name', '=', product.get('tax_code'))])
                if tax_code:
                    vals.update({
                        'qbd_tax_code': tax_code.id
                    })

            if product.get('barcode'):
                vals.update({'barcode':product.get('barcode')})

            company = self.env['res.users'].search([('id', '=', 2)]).company_id
            if 'income_account_id' in product and product.get('income_account_id'):
                account_quickbooks_id = product.get('income_account_id')

                account_id = self.env['account.account'].search([('quickbooks_id', '=', account_quickbooks_id)],
                                                                limit=1)

                if account_id:
                    vals.update({'property_account_income_id': account_id.id})

            else:
                if company.qb_expense_account:
                    vals.update({'property_account_income_id': company.qb_income_account.id})

            if company.qb_expense_account:
                vals.update({'property_account_expense_id': company.qb_expense_account.id})

            # if 'property_account_expense_name' in product and product.get('property_account_expense_name'):
            #     account_quickbooks_id = product.get('property_account_expense_name')
            #
            #     account_id = self.env['account.account'].search([('quickbooks_id', '=', account_quickbooks_id)],
            #                                                     limit=1)
            #     if account_id:
            #         vals.update({'property_account_expense_id': account_id.id})

        if vals:
            return vals

    def export_products(self):

        company = self.env['res.users'].search([('id', '=', 2)]).company_id
        loger_dict={}
        if company.export_pro_limit:
            limit = int(company.export_pro_limit)
        else:
            limit = 0

        if company.export_updated_record:
            products = self.search([('quickbooks_id', '!=', False),('is_updated','=',True)], limit=limit)
        else:
            products = self.search([('quickbooks_id', '=', False)], limit=limit)
        # print('Hereeeeeeeeeeee in product export\n')
        product_data_list = []

        # print('\nProducts : ', products, '\n')

        if products:

            for product in products:
                product_dict = {}
                #only export updated products
                if company.export_updated_record:
                    product_dict = self.get_product_dict(product, company.export_updated_record)

                #only export newly created records
                else:
                    product_dict = self.get_product_dict(product)
                    # print ("---------------",product_dict)

                if product_dict:
                    product_data_list.append(product_dict)

        if product_data_list:
            # print('\n\nProduct Data List :: ', product_data_list, '\n\n')
            # print('Total Count : ', len(product_data_list))

            company = self.env['res.users'].search([('id', '=', 2)]).company_id
            headers = {'content-type': "application/json"}
            data = product_data_list

            data = {'products_list': data}

            response = requests.request('POST', company.url + '/export_products', data=json.dumps(data),
                                        headers=headers,
                                        verify=False)

            # print("\n\nResponse ", type(response.text), response.text)

            resp = ast.literal_eval(response.text)

            # print('\n\nResp : ', resp, '\n')
            if company.export_updated_record == False:
                for res in resp[0].get('Data'):

                    if 'odoo_id' in res and res.get('odoo_id'):
                        product_id = self.browse(int(res.get('odoo_id')))

                        if product_id:
                            if res.get('quickbooks_id'):
                                product_id.write({'quickbooks_id': res.get('quickbooks_id')})
                    loger_dict.update({'operation': 'Export Product',
                                       'odoo_id': res.get('odoo_id'),
                                       'qbd_id': res.get('quickbooks_id'),
                                       'message': res.get('messgae')
                                       })
                    qbd_loger_id = self.env['qbd.loger'].create(loger_dict)
                    # company.write({'qbd_loger_id': [(4, qbd_loger_id.id)]})

            else:
                for res in resp[0].get('Data'):

                    if 'odoo_id' in res and res.get('odoo_id'):
                        product_id = self.browse(int(res.get('odoo_id')))

                        if product_id:
                            product_id.write({'is_updated': False})
                    loger_dict.update({'operation': 'Export Product',
                                       'odoo_id': res.get('odoo_id'),
                                       'qbd_id': res.get('quickbooks_id'),
                                       'message': res.get('messgae')
                                       })
                    qbd_loger_id = self.env['qbd.loger'].create(loger_dict)
                    # company.write({'qbd_loger_id': [(4, qbd_loger_id.id)]})

        return True

    def get_product_dict(self, product, is_updated=False):
        # Name name (31 varchar) --DONE
        # IsActive active (1 bit) --DONE
        # Type type --DONE
        # ManufacturerPartNumber barcode (31 varchar)

        # Description name (4095 varchar)




        # SalesTaxCodeRefFullName tax_code (3 varchar)
        # QuantityOnHand qty_available (18 decimal)
        # SalesAndpurchaseSalesDesc description_sale (4095 varchar)
        # SalesAndpurchasePurchaseDesc description_purchase (4095 varchar)
        # SalesOrPurchasePrice sales_purchase_price_and_purchase_cost (18 decimal)
        # SalesAndPurchaseSalesPrice sales_purchase_price_and_purchase_cost (18 decimal) [IF NOT FOUND IN SalesOrPurchasePrice]
        # PurchaseCost sales_purchase_price_and_purchase_cost (18 decimal)
        # SalesPrice sales_price (18 decimal)
        # SalesOrPurchaseAccountRefListID property_account_income_quickbook_id(36 varchar)
        # IncomeAccountRefListID property_account_income_quickbook_id (36 varchar)

        product_dict = {}
        company = self.env['res.users'].search([('id', '=', 2)]).company_id
        if is_updated == True:
            product_dict.update({'product_qbd_id': product.quickbooks_id,})
        else:
            product_dict.update({'product_qbd_id': '', })

        name = product.default_code if product.default_code else product.name
        if len(name) > 30:
            name = name[:30]

        bad_chars = [';', ':', '!', "*", "$", "'"]
        for i in bad_chars:
            name = name.replace(i,"")

        description = product.name
        for i in bad_chars:
            description = description.replace(i, "")

        product_dict.update({

            'odoo_id': product.id,
            'product_qbd_id': product.quickbooks_id,
            'name': name,
            'description': description,
            'type': product.type if product.type else '',
            'active': product.active if product.active else False,
            'barcode': product.barcode if product.barcode else '',
            'sales_purchase_price_and_purchase_cost': product.standard_price if product.standard_price else 0.0,
            'sales_price': product.list_price if product.list_price else 0.0,
            'description_purchase': product.description_purchase if product.description_purchase else '',
            'qty_available': product.qty_available if product.qty_available else '',
            'tax_code': product.qbd_tax_code.name if product.qbd_tax_code else '',
        })

        if product.property_account_income_id:
            product_dict.update({
                'property_account_income_quickbook_id': product.property_account_income_id.quickbooks_id
            })
        elif product.categ_id.property_account_income_categ_id:
            product_dict.update({
                'property_account_income_quickbook_id': product.categ_id.property_account_income_categ_id.quickbooks_id
            })

        elif company.qb_income_account:
            product_dict.update({
                'property_account_income_quickbook_id': company.qb_income_account.quickbooks_id
            })
        else:
            raise Warning('Please set income account for product - {}'.format(product.name))

        if company.qb_asset_account:
            product_dict.update({
                'asset_account_quickbook_id': company.qb_asset_account.quickbooks_id
            })
        else:
            raise Warning('Set Asset account in Comapny Configuration')

        if company.qb_cogs_account:
            product_dict.update({
                'cogs_account_quickbook_id': company.qb_cogs_account.quickbooks_id
            })
        else:
            raise Warning('Set COGS account in Comapny Configuration')

        # if product.property_account_expense_id:
        #     product_dict.update({
        #         'property_account_expense_quickbook_id': product.property_account_expense_id.quickbooks_id
        #     })
        # elif product.categ_id.property_account_expense_categ_id:
        #     product_dict.update({
        #         'property_account_expense_quickbook_id': product.categ_id.property_account_expense_categ_id.quickbooks_id
        #     })
        # company = self.env['res.users'].search([('id', '=', 2)]).company_id
        # elif company.qb_expense_account:
        #     product_dict.update({
        #         'property_account_expense_quickbook_id': company.qb_expense_account.quickbooks_id
        #     })
        # else:
        #     raise Warning('Please set expense account for product - {}'.format(product.name))

        if product_dict:
            return product_dict

    def export_product_cron(self):
        # print('\n\ncron calledddddddddddd\n\n')
        self.export_products()