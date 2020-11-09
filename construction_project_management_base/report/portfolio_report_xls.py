# -*- coding: utf-8 -*-
'''
Created on 08 of January 2020
@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError
#import pandas as pd
import io
import base64
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from PIL import Image
import decimal
import logging
_logger = logging.getLogger("_name_")


def workbook_table_label(workbook):
    table_label = workbook.add_format()
    table_label.set_font_color('black')
    table_label.set_font_name('Arial')
    table_label.set_font_size(11)
    return table_label


def workbook_table_label_data(workbook):
    label_data = workbook.add_format()
    label_data.set_bold(True)
    label_data.set_font_color('black')
    label_data.set_font_name('Arial')
    label_data.set_font_size(12)
    label_data.set_center_across()
    label_data.set_align('left')
    return label_data


def workbook_table_label_data_currency(workbook, currency):
    label_data = workbook.add_format()
    label_data.set_bold(True)
    label_data.set_font_color('black')
    label_data.set_font_name('Arial')
    label_data.set_font_size(12)
    label_data.set_center_across()
    label_data.set_align('left')
    label_data.set_num_format('[$'+currency+'-3409]#,##0.00;[RED](-[$'+currency+'-3409]#,##0.00)')
    return label_data


def workbook_table_header(workbook):
    table_header = workbook.add_format()
    table_header.set_bold(True)
    table_header.set_font_color('black')
    table_header.set_font_name('Arial')
    table_header.set_font_size(12)
    table_header.set_bg_color('#b5e9ff')
    table_header.set_center_across()
    table_header.set_align('vcenter')
    return table_header


def workbook_table_row_index(workbook):
    table_row = workbook.add_format()
    table_row.set_bold(True)
    table_row.set_font_color('black')
    table_row.set_font_name('Arial')
    table_row.set_font_size(11)
    table_row.set_bg_color('#cceeff')
    return table_row


def workbook_table_row(workbook):
    table_row = workbook.add_format()
    # table_row.set_bold(True)
    table_row.set_font_color('black')
    table_row.set_font_name('Arial')
    table_row.set_font_size(11)
    table_row.set_bg_color('#cceeff')
    table_row.set_num_format('#,##0.00_);(#,##0.00)')
    return table_row


def workbook_table_row_percent(workbook):
    table_row = workbook.add_format()
    # table_row.set_bold(True)
    table_row.set_font_color('black')
    table_row.set_font_name('Arial')
    table_row.set_font_size(11)
    table_row.set_bg_color('#cceeff')
    table_row.set_num_format('0.00%')
    return table_row


def workbook_table_row_total(workbook, currency):
    table_row = workbook.add_format()
    table_row.set_bold(True)
    table_row.set_font_color('black')
    table_row.set_font_name('Arial')
    table_row.set_font_size(11)
    table_row.set_bg_color('#cceeff')
    table_row.set_num_format('[$'+currency+'-3409]#,##0.00;[RED](-[$'+currency+'-3409]#,##0.00)')
    table_row.set_top(2)
    return table_row


class PortfolioReportXLS(models.AbstractModel):
    _name = 'report.construction_project_management_base.portfolio_report'
    _inherit = 'report.report_xlsx.abstract'

    def get_additional_cost(self, project):
        total = 0
        for i in project.supplement_log_ids:
            if not i.budget_adjustment:
                total += i.supplement_amount
        return total

    def generate_xlsx_report(self, workbook, data, line):
        currency = line.project_id.currency_id.symbol
        user = self.env['res.users'].browse(self._uid)
        worksheet = workbook.add_worksheet("Status")
        # Set Formats
        table_label = workbook_table_label(workbook)
        table_label.set_text_wrap()
        table_label_data = workbook_table_label_data(workbook)
        table_label_data_datetime = table_label_data

        table_label_data_currency = workbook_table_label_data_currency(workbook, currency)
        table_label_data_datetime.set_num_format('dd/mm/yyyy hh:mm AM/PM')
        table_label_data_date = workbook_table_label_data(workbook)
        table_label_data_date.set_num_format('dd/mm/yyyy')
        table_header = workbook_table_header(workbook)
        table_row_index = workbook_table_row_index(workbook)
        table_row = workbook_table_row(workbook)
        table_row_percent = workbook_table_row_percent(workbook)
        table_row_total = workbook_table_row_total(workbook, currency)
        format1 = workbook.add_format({'font_size': 18, 'font_name': 'arial','bg_color':'#CFE2F3','bold': 1})
        format1.set_align('center')

        # DATA header
        worksheet.write('A1', 'Project Name', table_label)
        worksheet.merge_range('B1:D1', line.project_id.name, table_label_data)
        worksheet.set_column(0, 0, 25)
        worksheet.set_column(1, 1, 25)
        worksheet.set_column(1, 3, 15)
        worksheet.set_column(4, 4, 25)
        worksheet.set_column(5, 5, 25)
        worksheet.set_column(6, 9, 15)
        worksheet.set_row(4, 25)
        worksheet.write('A2', 'Run By', table_label)
        worksheet.merge_range('B2:C2', user.name, table_label_data)
        worksheet.write('A3', 'As of', table_label)
        worksheet.merge_range('B3:C3', datetime.now()+timedelta(hours=8), table_label_data_datetime)
        worksheet.write('E1', 'Client Name', table_label)
        worksheet.merge_range('F1:G1', line.project_id.partner_id.name, table_label_data)
        worksheet.merge_range('A5:G5', 'Portfolio Details', format1)
        worksheet.write('A7', 'Awarded Units', table_label)
        worksheet.write('B7', '%s Units' % (line.project_id.project_count), table_label_data)
        worksheet.write('A8', 'Contract Amount', table_label)
        worksheet.write('B8', line.project_id.project_contract_amount, table_label_data_currency)
        worksheet.write('A9', 'Additional Cost Reqested (for Change Orders)', table_label)
        worksheet.write('B9', self.get_additional_cost(line.project_id), table_label_data_currency)
        worksheet.write('E7', 'Mobilization Date', table_label)
        worksheet.write('F7', line.project_id.start_date, table_label_data_date)
        worksheet.write('E8', 'Target Completion Date (Turned Over to CMG with COA)', table_label)
        worksheet.write('F8', line.project_id.projected_end_date, table_label_data_date)
        worksheet.write('E9', 'Requested Extension Date', table_label)
        worksheet.write('F9', line.project_id.extention_date, table_label_data_date)
        buf_image=io.BytesIO(base64.b64decode(line.project_id.image))
        worksheet.insert_image('A11', 'python.png', {'image_data': buf_image, 'x_scale': 1.5, 'y_scale': 1.5, 'x_offset': 15, 'y_offset': 10})

        if line.include_timeline_status:
            worksheet.merge_range('H5:Q5', 'Timeline Status', format1)
            headings = []
            projected_accomplish_temp = {}
            actual_accomplish_temp = {}
            projected_accomplish = []
            actual_accomplish = []
            for rec in line.project_id.projection_accomplishment_ids:
                datee = rec.date
                if not line.project_id.survey_frequent in ['week']:
                    date_format = datee.strftime("%b")+' - '+datee.strftime("%Y")
                else:
                    date_format = 'W%s - %s' % (datee.strftime('%V'), datee.strftime("%Y"))
                if (not date_format in headings):
                    headings.append(date_format)
                projected_accomplish.append(rec.projected / 100)
                actual_accomplish.append(rec.actual / 100)
            worksheet.set_column(8, 8 + len(headings), 15)
            worksheet.set_column(6, 7, 30)
            #  Projected Accomplishment tabular
            if (len(actual_accomplish) >0 or len(projected_accomplish) > 0):
                worksheet.write('H7', "Accomplishment", table_header)
                worksheet.write('H8', "Projected Accomplishment", table_row_index)
                worksheet.write('H9', "Actual Accomplishment", table_row_index)
                worksheet.write_row('I7', headings, table_header)
                worksheet.write_row('I8', projected_accomplish, table_row_percent)
                worksheet.write_row('I9', actual_accomplish, table_row_percent)
            #  Line graph for Projected Accomplishment
            line_graph = workbook.add_chart({'type': 'line'})
            line_graph.add_series({
                'name':       '=Status!$H$8',
                'categories': ['Status', 6, 8, 6, 8+len(headings)],
                'values':     ['Status',7, 8, 7, 8+len(headings)],
            })
            line_graph.add_series({
                'name':       '=Status!$H$9',
                'categories': ['Status', 6, 8, 6, 8+len(headings)],
                'values':     ['Status', 8, 8, 8, 8+len(headings)],
            })
            line_graph.set_title ({'name': 'Projected Accomplishment and Actual Accomplishment','name_font': {'bold':0,'size': 10, 'name': 'arial', 'color':'#808080'}})
            line_graph.set_x_axis({'num_font':  {'rotation': -45}})
            line_graph.set_style(2)
            line_graph.set_legend({'position': 'top'})
            line_graph.set_size({'width':1300,'height' : 500})
            worksheet.insert_chart('H10:Q10', line_graph, {'x_offset': 10, 'y_offset': 10})

        row = 43
        if line.include_budget_status:
        # Tabular data for Project Budget
            worksheet.set_row(row, 25)
            worksheet.merge_range(row, 0, row, 6, 'Budget Status', format1)
            row += 1
            chart_row = row
            chart_category = row
            headings = ('', 'Budget', 'Actual Expense')
            worksheet.write_row(row, 0, headings, table_header)
            row += 1
            worksheet.write(row, 0, 'Material', table_row_index)
            worksheet.write_number(row, 1, line.project_id.material_budget, table_row)
            worksheet.write_number(row, 2, line.project_id.material_expense, table_row)
            row += 1
            worksheet.write(row, 0, 'Subcontract/Outsource Services', table_row_index)
            worksheet.write_number(row, 1, line.project_id.service_budget, table_row)
            worksheet.write_number(row, 2, line.project_id.service_expense, table_row)
            row += 1
            worksheet.write(row, 0, 'Human Resource/Labor',table_row_index)
            worksheet.write_number(row, 1, line.project_id.labor_budget,table_row)
            worksheet.write_number(row, 2, line.project_id.labor_expense,table_row)
            row += 1
            worksheet.write(row, 0, 'Equipment',table_row_index)
            worksheet.write_number(row, 1, line.project_id.equipment_budget,table_row)
            worksheet.write_number(row, 2, line.project_id.equipment_expense,table_row)
            row += 1
            worksheet.write(row, 0, 'Overheads',table_row_index)
            worksheet.write_number(row, 1, line.project_id.overhead_budget,table_row)
            worksheet.write_number(row, 2, line.project_id.overhead_expense,table_row)
            row += 1
            worksheet.write(row, 0, 'Total', table_row_index)
            worksheet.write_number(row, 1, line.project_id.total_budget,table_row_total)
            worksheet.write_number(row, 2, line.project_id.total_expense,table_row_total)
            row += 1

            # Bar graph for Project Budget

            bar_graph = workbook.add_chart({'type': 'column'})
            bar_graph.add_series({
                'name':         ['Status', chart_category, 1, chart_category, 1],
                'categories':   ['Status', chart_category + 1, 0, row - 2, 0],
                'values':       ['Status', chart_category + 1, 1, row - 2, 1],
            })
            bar_graph.add_series({
                'name':         ['Status', chart_category, 2, chart_category, 2],
                'categories':   ['Status', chart_category + 1, 0, row - 2, 0],
                'values':       ['Status', chart_category + 1, 2, row - 2, 2],
            })

            bar_graph.set_title ({'name': 'Budget and Actual Expense','name_font': {'bold':0,'size': 10, 'name': 'arial', 'color':'#808080'}})
            bar_graph.set_x_axis({'name_font': {'rotation': -45}})
            bar_graph.set_y_axis({'num_format': '[$'+currency+']#,##0.00;[RED](-[$'+currency+']#,##0.00)]'})
            bar_graph.set_plotarea({
                                'border': {'color': 'red', 'width': 2, 'dash_type': 'dash'},
                                'fill':   {'color': '#FFFFC2'},
                            })
            bar_graph.set_table({'show_keys': True})
            bar_graph.set_style(2)
            bar_graph.set_legend({'position': 'top'})
            bar_graph.set_size({'width': 590,'height' : 380})
            worksheet.insert_chart(chart_category, 3, bar_graph, {'x_offset': 10, 'y_offset': 10})
            row += 14
        if line.include_project_status:
            worksheet.set_row(row, 25)
            worksheet.merge_range(row, 0, row, 6, 'Project Status', format1)
            row += 1
            headings = ('Project', 'Contract Amount', 'Budget Amount', 'Allocated Amount', 'Reserved Amount', 'Total Expense', 'Completion Status')
            worksheet.write_row(row, 0, headings, table_header)
            row += 1
            for rec in line.project_id.project_ids:
                worksheet.write(row, 0, rec.name, table_row_index)
                worksheet.write_number(row, 1, rec.project_contract_amount, table_row)
                worksheet.write_number(row, 2, rec.project_budget_amount, table_row)
                worksheet.write_number(row, 3, rec.project_budget_allocated, table_row)
                worksheet.write_number(row, 4, rec.project_budget_reserve, table_row)
                worksheet.write_number(row, 5, rec.project_actual_expense, table_row)
                worksheet.write_number(row, 6, rec.actual_accomplishment, table_row_percent)
                row += 1
