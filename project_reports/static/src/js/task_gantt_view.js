odoo.define('project_reports.TaskGanttView', function (require) {
'use strict';
var GanttView = require('web_gantt_view.GanttView');
var TaskGanttController = require('project_reports.TaskGanttController');
var GanttRenderer = require('web_gantt_view.GanttRenderer');
var TaskGanttModel = require('project_reports.TaskGanttModel');

var view_registry = require('web.view_registry');

var TaskGanttView = GanttView.extend({
    config: _.extend({}, GanttView.prototype.config, {
        Controller: TaskGanttController,
        Renderer: GanttRenderer,
        Model: TaskGanttModel,
    }),
});

view_registry.add('task_gantt', TaskGanttView);
return TaskGanttView;
});