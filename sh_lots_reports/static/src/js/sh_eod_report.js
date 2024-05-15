odoo.define('sh_lots_reports.report', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var EodReport = AbstractAction.extend({

        init: function (parent, context) {
            this._super(parent, context);
            $.get("/sh_get_eod_report", { context: context }, function (data) {
                $("#js_id_sh_eod_report_content_display").replaceWith(data);
            });

        },
        start: function () {
            var self = this;
            self.render();
            return this._super();
        },
        render: function () {
            var self = this;
            var sale_report = QWeb.render('sh_eod_report.report', {
                widget: self,
            });
            // $(sale_report).prependTo(self.$el);
            $(sale_report).prependTo(self.$el.find('.o_content'));

            return sale_report
        },

    });

    core.action_registry.add('sh_eod_report.report', EodReport);
    return EodReport;

});
