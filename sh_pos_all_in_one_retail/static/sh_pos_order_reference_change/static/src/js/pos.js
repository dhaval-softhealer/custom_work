odoo.define("sh_pos_order_reference_change.pos", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var core = require('web.core');
    var _t = core._t;

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function () {
            var self = this;
            self.customer_history = false;
            var json = _super_order.initialize.apply(this, arguments);
            json.name = _.str.sprintf(_t("Sale %s"), json.uid);
            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments);
            this.name = _.str.sprintf(_t("Sale %s"), this.uid);
        }
    });

});
