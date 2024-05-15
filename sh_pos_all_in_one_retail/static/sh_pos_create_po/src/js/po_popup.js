odoo.define("sh_pos_create_po.create_po_popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class PoPopup extends AbstractAwaitablePopup{
        constructor(){
            super(...arguments);
        }
        click_ok(){
            var self = this;
            this.env.pos.db.remove_all_purchase_orders();
            
            if (this.env.pos.get_order() && this.env.pos.get_order().get_orderlines() && this.env.pos.get_order().get_orderlines().length > 0) {
                var orderlines = this.env.pos.get_order().get_orderlines();
                _.each(orderlines, function (each_orderline) {
                    if (self.env.pos.get_order().get_orderlines()[0]) {
                        self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                    }
                });
            }
            this.trigger("close-popup");
        }
    }
    PoPopup.template = 'PoPopup'

    Registries.Component.add(PoPopup)

    return PoPopup
});
