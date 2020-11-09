odoo.define('stock_reports.ReportGridView', function (require) {
'use strict';

var GridView = require('grid_view.GridView');
var ReportGridController = require('stock_reports.ReportGridController');
var viewRegistry = require('web.view_registry');

var ReportGridView = GridView.extend({
    config: _.extend({}, GridView.prototype.config, {
        Controller: ReportGridController,
    }),
});

viewRegistry.add('stock_reports_report_grid', ReportGridView);

return ReportGridView;

});
