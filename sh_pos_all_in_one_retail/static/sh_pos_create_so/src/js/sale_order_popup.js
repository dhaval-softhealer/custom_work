odoo.define("sh_pos_create_so.saleorderbuttonpopup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class saleOrderPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            //   useSubEnv({ attribute_components: [] })
        }
        ClickOk(){
            var self = this;
            this.trigger("close-popup");
            if (this.env.pos.get_order() && this.env.pos.get_order().get_orderlines() && this.env.pos.get_order().get_orderlines().length > 0) {
                var orderlines = this.env.pos.get_order().get_orderlines();
                _.each(orderlines, function (each_orderline) {
                    if (self.env.pos.get_order().get_orderlines()[0]) {
                        self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                    }
                });
            }
        }
    }
    saleOrderPopup.template = 'saleOrderPopup'

    Registries.Component.add(saleOrderPopup)

    return saleOrderPopup
});
