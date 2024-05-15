odoo.define("corum_interface.pos", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const TicketScreen = require("point_of_sale.TicketScreen");
    const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
    const ProductScreen = require("point_of_sale.ProductScreen");

    console.log("ProductScreen >>> ",ProductScreen)

    const ShProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor(){
                super(...arguments);
                console.log("this >>>*** ",this.controlButtons)
                var data = $.grep(this.controlButtons, function (e) {
                    return e.name != "SetSaleOrderButton";
                });

                console.log("data >>> ",this.controlButtons)
            }
        };
        Registries.Component.extend(ProductScreen, ShProductScreen);

    console.log("ControlButtonsMixin >>> ",ControlButtonsMixin)

    const PosTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            mounted(){
                super.mounted()
                console.log("mounted callled >>>>> ")
                if($('.buttons .highlight') && $('.buttons .highlight').length > 0){
                    $('.buttons .highlight').text('New Sale')
                }
            }
            _getOrderStates(){
                var states = super._getOrderStates()
                if(states.get('ACTIVE_ORDERS') && states.get('ACTIVE_ORDERS').text){
                    states.get('ACTIVE_ORDERS').text = 'All Active Sales'
                }
                return states
            }
        };
        Registries.Component.extend(TicketScreen, PosTicketScreen);

});