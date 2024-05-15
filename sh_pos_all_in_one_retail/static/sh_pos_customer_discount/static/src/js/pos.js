odoo.define('sh_pos_customer_discount.pos', function (require) {
    'use strict';

    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit')
    const ClientListScreen = require('point_of_sale.ClientListScreen')
    const Registries = require("point_of_sale.Registries");
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var _t = core._t;
    const { Gui } = require("point_of_sale.Gui");

    models.load_fields('res.partner', ['sh_customer_discount'])

    const ShClientDetailsEdit = (ClientDetailsEdit) =>
        class extends ClientDetailsEdit {
            constructor() {
                super(...arguments);
            }
            mounted() {
                super.mounted()
                var self = this
                var detail_div = document.createElement('div')
                $(detail_div).addClass('client-detail sh_discount')
                var lable_span = document.createElement('span')
                $(lable_span).addClass('label')
                $(lable_span).text('Max Discount')
                $(detail_div).append(lable_span)
                var detail_input = document.createElement('input')
                $(detail_input).attr({ 'name': 'Discount', 'id': 'customer_discount', 'class': 'detail', 'value': 0.00 })
                var detail_div1 = document.createElement('div')
                $(detail_div1).addClass('client-detail sh_discount')
                var lable_span1 = document.createElement('span')
                $(lable_span1).addClass('label')
                $(detail_div1).append(lable_span1)
                $(lable_span1).text('Discount Type')
                var type_selection = document.createElement('select')
                $(type_selection).attr({ 'id': 'sh_discount_type' })
                var option = document.createElement('option')
                $(option).val('percentage')
                $(option).text('Percentage')
                var option1 = document.createElement('option')
                $(option1).val('fixed')
                $(option1).text('Fixed')
                if ($("#Set_customer_discount").is(":checked")) {
                    var value = this.props.partner.sh_maximum_discount
                    $(detail_input).attr({ 'name': 'Max Discount', 'id': 'customer_discount', 'class': 'detail', 'value': value })
                    $(detail_div).append(detail_input)
                    var type_val = this.props.partner.sh_discount_type
                    $(type_selection).append(option, option1)
                    $(type_selection).val(type_val).change()
                    $(detail_div1).append(type_selection)
                    $('.client-details-left').append(detail_div, detail_div1)
                }
                $("#Set_customer_discount").change(function () {
                    if ($("#Set_customer_discount").is(":checked")) {
                        var value = self.props.partner.sh_maximum_discount
                        $(detail_input).attr({ 'name': 'Discount', 'id': 'customer_discount', 'class': 'detail', 'value': value })
                        var type_val = self.props.partner.sh_discount_type
                        $(type_selection).val(type_val).change()

                        $(detail_div).append(detail_input)
                        $(type_selection).append(option, option1)
                        $(detail_div1).append(type_selection)

                        $('.client-details-left').append(detail_div, detail_div1)

                        $('.client-details-left').append()
                    } else {
                        $('.client-details-left').find('.sh_discount').remove()
                    }
                })
            }
            saveChanges(event) {
                var discount = 0;
                if ($('#sh_customer_discount')) {
                    discount = $('#sh_customer_discount').val();
                    if (discount && event && event.detail && event.detail.processedChanges) {
                        event.detail.processedChanges['sh_customer_discount'] = discount || 0
                    }
                }
                if (this.env.pos.config.sh_enable_customer_discount) {
                    let processedChanges = {};
                    for (let [key, value] of Object.entries(this.changes)) {
                        if (this.intFields.includes(key)) {
                            processedChanges[key] = parseInt(value) || false;
                        } else {
                            processedChanges[key] = value;
                        }
                    }
                    if (discount) {
                        processedChanges['sh_customer_discount'] = discount || 0
                    }
                    if ((!this.props.partner.name && !processedChanges.name) ||
                        processedChanges.name === '') {
                        return this.showPopup('ErrorPopup', {
                            title: _t('A Customer Name Is Required'),
                        });
                    }
                    processedChanges.id = this.props.partner.id || false;
                    this.trigger('save-changes', { processedChanges });
                }
                else {
                    super.saveChanges()
                }
            }

        }
    Registries.Component.extend(ClientDetailsEdit, ShClientDetailsEdit)

    const ShClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            constructor() {
                super(...arguments);
            }
            confirm() {

                var self = this
                var Order = self.env.pos.get_order()
                var Client = this.state.selectedClient

                if (Client && Client.sh_enable_max_dic) {
                    var sh_total_after_dic = Order.get_total_with_tax()
                    var sh_product_total = Order.get_total_without_tax() + Order.get_total_discount()
                    var sh_customer_max_dis = Client.sh_maximum_discount
                    if (Client.sh_discount_type == "percentage") {
                        var sh_customer_discount_per = ((sh_product_total - sh_total_after_dic) * 100) / sh_product_total

                        if (sh_customer_discount_per > sh_customer_max_dis) {

                            var body = "Sorry, " + sh_customer_discount_per.toFixed(2) + "% discount is not allowed. Maximum discount for this customer is " + sh_customer_max_dis + "%";
                            Gui.showPopup('ErrorPopup', {
                                title: 'Exceed Discount Limit !',
                                body: body,
                            })
                        } else {
                            super.confirm()
                        }

                    }
                    else {
                        var sh_customer_discount_fixed = Order.get_total_discount()

                        if (sh_customer_discount_fixed > sh_customer_max_dis) {

                            var body = "Sorry, " + sh_customer_discount_fixed.toFixed(2) + " discount is not allowed. Maximum discount for this customer is " + sh_customer_max_dis;
                            Gui.showPopup('ErrorPopup', {
                                title: 'Exceed Discount Limit !',
                                body: body,
                            })
                        } else {
                            super.confirm()
                        }
                    }
                } else {
                    super.confirm()
                }

                if (this.env.pos.config.sh_enable_customer_discount) {
                    var self = this
                    var old_client = this.env.pos.get_order().get_client()
                    _.each(this.env.pos.get_order().get_orderlines(), function (orderline) {
                        if (!orderline.discount) {
                            if (orderline && self.state.selectedClient) {
                                orderline.set_discount(self.state.selectedClient.sh_customer_discount)
                            }
                        } else {
                            if (old_client && old_client.sh_customer_discount == orderline.discount) {
                                if (self.state.selectedClient) {
                                    orderline.set_discount(self.state.selectedClient.sh_customer_discount)
                                } else {
                                    orderline.discount = 0
                                    orderline.discountStr = '' + 0
                                }
                            }
                        }
                    })
                }
            }

        }
    Registries.Component.extend(ClientListScreen, ShClientListScreen)
});
