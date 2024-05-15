odoo.define("sh_pos_customer_display_logo.pos", function (require) {
    "use strict";
    
    var models = require("point_of_sale.models");
    
    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
    	get_screen_logo_url: function () {
            return window.location.origin + "/web/image?model=pos.config&field=sh_customer_display_logo&id=" + this.config.id;
        },
    }); 
});