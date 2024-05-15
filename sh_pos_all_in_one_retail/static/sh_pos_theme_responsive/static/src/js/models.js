odoo.define("sh_pos_theme_responsive.models", function (require) {

    var models = require("point_of_sale.models");

    models.load_models({
        model: "sh.pos.theme.settings",
        loaded: function (self, pos_theme_settings) {
            self.pos_theme_settings_data = [];
            self.pos_theme_settings_data = pos_theme_settings;
        },
    });

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        get_header_logo_url: function (theme_id) {
            return window.location.origin + "/web/image?model=sh.pos.theme.settings&field=theme_logo&id=" + theme_id;
        },

    });
});
