odoo.define("pos_product_suggestion.pos_product_suggestion", function (require) {
    "use strict";

    const { useState } = owl.hooks;
    const ProductsWidgetControlPanel = require("point_of_sale.ProductsWidgetControlPanel");
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const ProductsWidget = require("point_of_sale.ProductsWidget");
    const { useListener } = require("web.custom_hooks");
    const { useRef } = owl.hooks;

    var module = require("point_of_sale.models");

    var models = module.PosModel.prototype.models;

    for (var i = 0; i < models.length; i++) {
        var model = models[i];

        if (model.model === "product.product") {
            model.fields.push("suggestion_line");
        }
    }

    var models = require("point_of_sale.models");

    models.load_models({
        model: "product.suggestion",
        fields: [],
        loaded: function (self, suggestions) {
            self.suggestions = suggestions;
            self.suggestion = [];
            _.each(suggestions, function (suggestion) {
                self.suggestion[suggestion.id] = suggestion;
            });
        },
    });

    const PosProductsWidget = (ProductsWidget) =>
        class extends ProductsWidget {
            constructor() {
                super(...arguments);
                this.final_suggest_products = [];
            }
            get_final_suggested_product_ids(products) {
                var self = this;
                var temp_suggest_ids = [];
                var final_suggest_products = [];
                _.each(products, function (product) {
                    if (product.suggestion_line.length > 0) {
                        _.each(product.suggestion_line, function (sug_line) {
                            temp_suggest_ids.push(sug_line);
                        });
                    }
                });

                if (temp_suggest_ids.length > 0) {
                    _.each(temp_suggest_ids, function (id) {
                        var pro = self.env.pos.db.get_product_by_id(self.env.pos.suggestion[id].product_suggestion_id[0]);
                        if (pro) {
                            final_suggest_products.push(pro);
                        }
                    });
                }

                return final_suggest_products.length > 0 ? _.uniq(final_suggest_products) : [];
            }
            get suggestedproduct() {
                if (this.final_suggest_prodcuts && this.final_suggest_prodcuts.length > 0 && $('.sh_product_list_main')) {
                    $('.sh_product_list_main').addClass("sh_list_with_sugggestion")
                }
                return this.final_suggest_prodcuts;
            }
        };
    Registries.Component.extend(ProductsWidget, PosProductsWidget);

    class SuggestedProductList extends PosComponent {
        mounted() {
            super.mounted()
            if ($('.suggestion-list') && $('.suggestion-list').length > 0) {
                $('.sh_product_list_main').addClass("sh_list_with_sugggestion")
            }
        }
    }
    SuggestedProductList.template = "SuggestedProductList";

    Registries.Component.add(SuggestedProductList);
});
