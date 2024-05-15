odoo.define("sh_pos_product_qty_pack.ProductQtybag", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");
    var models = require("point_of_sale.models");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const pItem = require("point_of_sale.ProductItem");
    const { useListener } = require("web.custom_hooks");
    
    models.load_fields("product.product", ["sh_qty_in_bag" ]);

    const PosRespitem = (pItem) =>
        class extends pItem {
            constructor() {
                super(...arguments);
                useListener("Add_Product", this.Add_Product);
            }
            Add_Product(e) {
                var qty_val = 0;
                const product = e.detail;
                let { confirmed, payload } = this.showPopup("ProductQtybagPopup", {
                    qty_val: qty_val,
                    title: 'Add Bags',
                    product: product,
                });
                if (confirmed) {
                } else {
                    return;
                }
            }
        };

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            this.bag_qty = "";
            _super_orderline.initialize.call(this, attr, options);
        },
        set_bag_qty: function (bag_qty) {
            this.set("bag_qty", bag_qty);
        },
        get_bag_qty: function () {
            return this.get("bag_qty");
        },
        export_for_printing: function(){
        	
        	var receipt = _super_orderline.export_for_printing.apply(this, arguments);
        	receipt['bags'] = this.get_bag_qty()
        	return receipt
        	
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.bag_qty = this.get("bag_qty") || null;
            return json;
        },
    });

    const PosMercuryProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener("edit_bags", this.EditBags);
            }
            async EditBags(e) {
                var self = this;
                setTimeout(function () {
                    var qty_val1 = self.env.pos.get_order().selected_orderline.sh_bag_qty;
                    let { confirmed, payload } = self.showPopup("ProductQtybagPopup", {
                        qty_val: qty_val1,
                        title: 'Edit Bags',
                        product: self.env.pos.get_order().get_selected_orderline().product,
                    });
                    if (confirmed) {
                    } else {
                        return;
                    }
                }, 100);
            }
        };
    class ProductQtybagPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        mounted() {
            super.mounted();
            $('.add_qty').focus()
        }
        confirm() {
        	var self = this;
            var order = this.env.pos.get_order();
            var bag_qty = $(".add_qty").val();
            if (bag_qty) {
                var bag = this.props.product.sh_qty_in_bag * bag_qty;
                
                var currentOrder = self.env.pos.get_order()
                // currentOrder.add_product(product)
                currentOrder.add_product(this.props.product, {
                    quantity: bag,
                    sh_total_qty: bag,
                    sh_bag_qty: bag_qty,
                });
                self.env.pos.get_order().get_selected_orderline()["sh_bag_qty"] = bag_qty;
                self.env.pos.get_order().get_selected_orderline().set_bag_qty(bag_qty);
            } else {
                alert("please Enter Bag ");
            }
            this.trigger("close-popup");
        }
    }
    ProductQtybagPopup.template = "ProductQtybagPopup";

    Registries.Component.add(ProductQtybagPopup);
    Registries.Component.extend(ProductScreen, PosMercuryProductScreen);
    Registries.Component.extend(pItem, PosRespitem);

    return {
        ProductScreen,
        ProductQtybagPopup,
    };
});
