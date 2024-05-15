odoo.define("sh_pos_wh_stock_adv.chrome", function (require) {
    "use strict";

    const Chrome = require("point_of_sale.Chrome");
    const RefundButton = require("point_of_sale.RefundButton");
    const Registries = require("point_of_sale.Registries");
    var bus_service = require("bus.BusService");
    const bus = require("bus.Longpolling");
    const session = require("web.session");
    var rpc = require("web.rpc");
    var core = require("web.core");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    var DB = require("point_of_sale.DB");
    var models = require("point_of_sale.models");
    const TicketScreen = require("point_of_sale.TicketScreen");

    var _t = core._t;

    const WHStockAdvTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            _onCloseScreen() {
                this.env.pos.is_refund_button_click = false;
                super._onCloseScreen();
            }
            async _onDoRefund() {
                this.env.pos.is_refund_button_click = false;
                this.env.pos.get_order().is_refund_order = true;
                await super._onDoRefund();
                this.env.pos.get_order().is_refund_order = false;
            }
            async _onBeforeDeleteOrder(order) {
                var res = await super._onBeforeDeleteOrder(order);
                var self = this;
                if (res) {
                    if (self.env.pos.config.sh_update_real_time_qty && self.env.pos.config.sh_show_qty_location && !self.env.pos.config.sh_display_stock_from_other_companies) {
                        if (order && order.get_orderlines()) {
                            _.each(order.get_orderlines(), function (each_orderline) {
                                var quant_by_product_id = self.env.pos.db.quant_by_product_id[each_orderline.product.id];
                                if (quant_by_product_id) {
                                    var list = {
                                        product_id: [each_orderline.product.id, each_orderline.product.display_name],
                                        location_id: self.env.pos.config.sh_pos_location,
                                        quantity: parseInt(quant_by_product_id[self.env.pos.config.sh_pos_location[0]]) + each_orderline.quantity,
                                    };
                                    $.get(
                                        "/update_quanttiy",
                                        {
                                            passed_list: list,
                                        },
                                        function (result) {}
                                    );
                                }
                            });
                        }
                    }
                }
                return res;
            }
        };

    Registries.Component.extend(TicketScreen, WHStockAdvTicketScreen);

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            _super_posmodel.initialize.call(this, session, attributes);
            this.is_pos_order = false;
            this.is_refund_button_click = false;
        },
    });

    const PosWHAdvPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async _finalizeValidation() {
                this.env.pos.is_pos_order = true;
                await super._finalizeValidation();
                this.env.pos.is_pos_order = false;
            }
            async validateOrder(isForceValidate) {
                await super.validateOrder(isForceValidate);
                var self = this;
                if (this.env.pos.config.picking_type_id) {
                    var picking_type = this.env.pos.db.picking_type_by_id[this.env.pos.config.picking_type_id[0]];

                    if (picking_type && picking_type.default_location_src_id) {
                        var location_id = picking_type.default_location_src_id[0];
                        var order = this.env.pos.get_order();
                        if (location_id) {
                            var quant_by_product_id = this.env.pos.db.quant_by_product_id;
                            $.each(quant_by_product_id, function (product, value) {
                                for (var i = 0; i < order.orderlines.models.length; i++) {
                                    if (order.orderlines.models[i].product.id && order.orderlines.models[i].product.id == product) {
                                        $.each(value, function (location, qty) {
                                            if (location == location_id) {
                                                if (self.env.pos.config.sh_update_quantity_cart_change) {
                                                    value[location] = qty + order.orderlines.models[i].quantity;
                                                }
                                                var product_id = order.orderlines.models[i].product.id;
                                                var product_name = order.orderlines.models[i].product.display_name;
                                                var list = { product_id: [product_id, product_name], location_id: self.env.pos.config.sh_pos_location, quantity: value[location], is_valid_order: true };
                                                $.get(
                                                    "/update_quanttiy",
                                                    {
                                                        passed_list: list,
                                                    },
                                                    function (result) {}
                                                );
                                            }
                                        });
                                    }
                                }
                            });
                        }
                    }
                }
            }
        };
    Registries.Component.extend(PaymentScreen, PosWHAdvPaymentScreen);

    const PosResChrome = (Chrome) =>
        class extends Chrome {
            _buildChrome() {
                super._buildChrome();
                var bus_service_obj = bus_service.prototype;
                bus_service_obj["env"] = this.env;
                bus_service_obj.call("bus_service", "updateOption", "stock.update", session.uid);
                bus_service_obj.call("bus_service", "onNotification", this, this._onNotification);
                bus_service_obj.call("bus_service", "startPolling");
            }
            _onNotification(notifications) {
                var self = this;
                if (self && self.env && self.env.pos && self.env.pos.config && self.env.pos.config.sh_display_stock && self.env.pos.config.sh_update_real_time_qty && !self.env.pos.is_pos_order) {
                    if (notifications) {
                        _.each(notifications, function (each_notification) {
                            if (each_notification && each_notification["payload"] && each_notification["payload"][0]) {
                                if (
                                    each_notification["payload"][0]["product_id"] &&
                                    each_notification["payload"][0]["product_id"][0] &&
                                    each_notification["payload"][0]["location_id"] &&
                                    each_notification["payload"][0]["location_id"][0] &&
                                    each_notification["payload"][0]["quantity"] &&
                                    each_notification["payload"][0]["location_id"][0] == self.env.pos.config.sh_pos_location[0]
                                ) {
                                    if (
                                        self &&
                                        self.env &&
                                        self.env.pos &&
                                        self.env.pos.db &&
                                        self.env.pos.db.quant_by_product_id &&
                                        self.env.pos.db.quant_by_product_id[each_notification["payload"][0]["product_id"][0]] &&
                                        self.env.pos.db.quant_by_product_id[each_notification["payload"][0]["product_id"][0]][each_notification["payload"][0]["location_id"][0]]
                                    ) {
                                        self.env.pos.db.quant_by_product_id[each_notification["payload"][0]["product_id"][0]][each_notification["payload"][0]["location_id"][0]] = each_notification["payload"][0]["quantity"];
                                        if (each_notification["payload"][0]["product_id"] && each_notification["payload"][0]["product_id"][0]) {
                                            if (
                                                $(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]')) &&
                                                $(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0]
                                            ) {
                                                if (
                                                    $(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag") &&
                                                    $($(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag"))
                                                ) {
                                                    $($(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("sh_warehouse_display")).text(
                                                        each_notification["payload"][0]["quantity"]
                                                    );
                                                }
                                            }
                                        }
                                    } else {
                                        if (!self.env.pos.db.quant_by_product_id[each_notification["payload"][0]["product_id"][0]]) {
                                            self.env.pos.db.quant_by_product_id[each_notification["payload"][0]["product_id"][0]] = {};
                                            self.env.pos.db.quant_by_product_id[each_notification["payload"][0]["product_id"][0]][each_notification["payload"][0]["location_id"][0]] = each_notification["payload"][0]["quantity"];
                                            if (each_notification["payload"][0]["product_id"] && each_notification["payload"][0]["product_id"][0]) {
                                                if (
                                                    $(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]')) &&
                                                    $(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0]
                                                ) {
                                                    if (
                                                        $(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag") &&
                                                        $($(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag"))
                                                    ) {
                                                        $($(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("sh_warehouse_display")).text(
                                                            each_notification["payload"][0]["quantity"]
                                                        );
                                                    }
                                                }
                                            }
                                        } else if (
                                            self.env.pos.db.quant_by_product_id[each_notification["payload"][0]["product_id"][0]] &&
                                            !self.env.pos.db.quant_by_product_id[each_notification["payload"][0]["product_id"][0]][each_notification["payload"][0]["location_id"][0]]
                                        ) {
                                            self.env.pos.db.quant_by_product_id[each_notification["payload"][0]["product_id"][0]][each_notification["payload"][0]["location_id"][0]] = each_notification["payload"][0]["quantity"];
                                            if (each_notification["payload"][0]["product_id"] && each_notification["payload"][0]["product_id"][0]) {
                                                if (
                                                    $(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]')) &&
                                                    $(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0]
                                                ) {
                                                    if (
                                                        $(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag") &&
                                                        $($(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag"))
                                                    ) {
                                                        $($(document.querySelectorAll('[data-product-id="' + each_notification["payload"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("sh_warehouse_display")).text(
                                                            each_notification["payload"][0]["quantity"]
                                                        );
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        });
                    }
                }
            }
        };

    Registries.Component.extend(Chrome, PosResChrome);

    const PosResRefundButton = (RefundButton) =>
        class extends RefundButton {
            _onClick() {
                this.env.pos.is_refund_button_click = true;
                super._onClick();
            }
        };
    Registries.Component.extend(RefundButton, PosResRefundButton);

    return Chrome;
});
