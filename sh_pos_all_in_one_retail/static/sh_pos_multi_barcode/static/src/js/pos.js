odoo.define("sh_pos_multi_barcode.pos", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var DB = require("point_of_sale.DB");
    const rpc = require("web.rpc");

    models.load_models({
        label: "Loading Product Template Baarcode",
        loaded: function (self) {
            if (self && self.config && self.config.sh_enable_multi_barcode) {
                rpc.query({
                    model: "product.template.barcode",
                    method: "search_read",
                }).then(function (all_barcode) {
                    if (all_barcode) {
                        _.each(all_barcode, function (each_barcode) {
                            self.env.pos.db.product_by_barcode[each_barcode.name] = self.env.pos.db.product_by_id[each_barcode.product_id[0]];
                        });
                    }
                });
            }
        },
    });
});
