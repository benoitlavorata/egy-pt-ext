odoo.define('grid_view.widget_registry', function (require) {
"use strict";

var Registry = require('web.Registry');

return new Registry();
});



odoo.define('grid_view._widget_registry', function(require) {
"use strict";

var grid_widget = require('grid_view.widget');
var registry = require('grid_view.widget_registry');

// Basic fields
registry
    .add('float_factor', grid_widget.FloatFactorWidget)
    .add('float_time', grid_widget.FloatTimeWidget)
    .add('float_toggle', grid_widget.FloatToggleWidget)
});
