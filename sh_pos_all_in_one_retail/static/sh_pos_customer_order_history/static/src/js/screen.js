odoo.define("sh_pos_customer_order_history.screen", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const ClientLine = require("point_of_sale.ClientLine");
    const rpc = require("web.rpc");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    /*var order_list_screen = require("sh_pos_order_list.screen");*/
    var OrderListScreen = require("sh_pos_order_return_exchange.screen");
    var field_utils = require("web.field_utils");
    var models = require("point_of_sale.models");


    const SHPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
                var self = this;
                super.validateOrder(isForceValidate);

                var order = self.env.pos.get_order();
                self.formatted_validation_date = field_utils.format.datetime(moment(self.env.pos.get_order().validation_date), {}, { timezone: false });
                var lines = [];
                var sh_line_id = [];
                if (order && order.export_as_JSON().lines && order.export_as_JSON().lines.length > 0) {
                    _.each(order.export_as_JSON().lines, function (each_orderline) {
                        if (each_orderline[2] && each_orderline[2].sh_line_id) {
                            self.env.pos.db.order_line_by_uid[each_orderline[2].sh_line_id] = each_orderline[2];
                            sh_line_id.push(each_orderline[2].sh_line_id);
                        }

                        lines.push(each_orderline);
                    });
                }
                if (order && order.sh_uid && self.env.pos.db && self.env.pos.db.order_by_uid && !self.env.pos.db.order_by_uid[order.sh_uid]) {
                    if (lines && lines.length > 0) {
                        order["lines"] = lines;
                    }
                    if (sh_line_id && sh_line_id.length > 0) {
                        order["sh_line_id"] = sh_line_id;
                    }
                    if (self.formatted_validation_date) {
                        order["date_order"] = self.formatted_validation_date;
                    }
                    if (order.export_as_JSON() && order.export_as_JSON().amount_total) {
                        order["amount_total"] = order.export_as_JSON().amount_total;
                    }
                    if (order.export_as_JSON()["amount_paid"] >= parseInt(order.export_as_JSON()["amount_total"])) {
                        order["state"] = "paid";
                    } else {
                        order["state"] = "draft";
                    }
                    if (order.export_as_JSON() && order.export_as_JSON().partner_id) {
                        order["partner_id"] = order.export_as_JSON().partner_id;
                    }
                    order["pos_reference"] = order.name;
                    order["total_items"] = order.export_as_JSON().total_item;
                    order["total_qty"] = order.export_as_JSON().total_qty;
                    self.env.pos.db.all_order.push(order);
                    self.env.pos.db.order_by_uid[order.sh_uid] = order;
                }
            }
        };
    Registries.Component.extend(PaymentScreen, SHPaymentScreen);

    const PosClientLine = (ClientLine) =>
        class extends ClientLine {
            constructor() {
                super(...arguments);
            }
            click_order_history_icon(event) {
                var self = this;
                var client_id = event.currentTarget.closest("tr").attributes[1].value;
                if (client_id) {
                    var client_data = self.env.pos.db.get_partner_by_id(parseInt(client_id))
                    if (!client_data) {
                        client_data = self.env.pos.db.get_partner_by_cid(client_id)
                    }
                    if (client_data) {
                        self.env.pos.get_order()['customer_history'] = client_data.name
                        const { confirmed, payload } = self.showTempScreen("OrderListScreen");
                        if (confirmed) {
                        }

                    }
                }
            }
        };
    Registries.Component.extend(ClientLine, PosClientLine);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function () {
            var self = this;
            self.customer_history = false;
            return _super_order.initialize.apply(this, arguments);
        },
    });
});
