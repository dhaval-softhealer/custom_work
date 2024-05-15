odoo.define("sh_pos_cash_in_out.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var exports = {};
    const { Gui } = require("point_of_sale.Gui");

    models.load_models({
        model: "pos.payment.method",
        label: "load_payment",
        loaded: function (self, all_payment_method) {
            self.db.all_payment_method = all_payment_method;
            if (all_payment_method && all_payment_method.length > 0) {
                _.each(all_payment_method, function (each_payment_method) {
                    self.db.payment_method_by_id[each_payment_method.id] = each_payment_method;
                });
            }
        },
    });

    models.load_models({
        model: "sh.cash.in.out",
        label: "load_cash_in_out_statement",
        loaded: function (self, all_cash_in_out_statement) {
            if (all_cash_in_out_statement && all_cash_in_out_statement.length > 0) {
                self.db.all_cash_in_out_statement = all_cash_in_out_statement;
            }
        },
    });

    models.load_models({
        model: "pos.session",
        label: "load_session",
        domain: function (self) {
            return ['|', ["user_id", "=", self.user.id], ["state", "=", "opened"]];
        },
        // domain: [["state", "=", "opened"], '|', ["user_id", "=", self.user.id]],
        loaded: function (self, all_session) {
            if (all_session && all_session.length > 0) {
                self.db.all_sessions(all_session);
                _.each(all_session, function (each_session) {
                    if (self.pos_session.id == each_session.id && each_session.state == 'opened') {
                        self.cash_register_total_entry_encoding = each_session.cash_register_total_entry_encoding;
                        self.cash_register_balance_end = each_session.cash_register_balance_end;
                        self.cash_register_balance_end_real = each_session.cash_register_balance_end_real;
                        self.cash_register_balance_start = each_session.cash_register_balance_start;
                    }
                });
            }
        },
    });

    models.load_models({
        model: "pos.payment",
        label: "load_pos_payment",
        domain: function (self) {
            return [['id', '=', self.pos_session.id]]
        },
        loaded: function (self, all_payment) {
            if (all_payment && all_payment.length > 0) {
                self.db.all_payment = all_payment;
                _.each(all_payment, function (each_payment) {
                    // if (each_payment.session_id[0] == self.pos_session.id) {
                        self.db.payment_line_by_id[each_payment.id] = each_payment;
                    // }
                });
            }
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (attributes) {
            this.cash_in_out_statement_receipt = false;
            this.is_session_close = false;
            this.cash_register_total_entry_encoding = 0.0;
            this.cash_register_balance_end = 0.0;
            this.cash_register_balance_end_real = 0.0;
            this.cash_register_balance_start = 0.0;
            var posmodel = _super_posmodel.initialize.call(this, attributes);
        },
    });
});
