odoo.define('sh_pos_product_variant.ProductScreen', function (require) {
    'use strict';

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");

    const PosProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _clickProduct(event) {
                var self = this;
                const product = event.detail;   
                let age = this.env.pos.db.category_by_id[product.pos_categ_id[0]].sh_age
                if(age && age > 0){
                    this.showPopup('ShValodationTypePopup', {
                        product : product,
                        age : age
                    });
                }else{
                    super._clickProduct(event)
                }
            }
        }

    Registries.Component.extend(ProductScreen, PosProductScreen);
})
