odoo.define("sh_pos_cash_in_out.ActionButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const rpc = require("web.rpc");

    const CashMoveButton = require("point_of_sale.CashMoveButton");

    class CashInOutStatementButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-cash-in-out-statement", this.onClickTemplateLoad);
        }
        async onClickTemplateLoad() {
            var self = this;
            let { confirmed, payload } = this.showPopup("CashInOutOptionStatementPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
    }
    CashInOutStatementButton.template = "CashInOutStatementButton";
    ProductScreen.addControlButton({
        component: CashInOutStatementButton,
        condition: function () {
            return this.env.pos.config.sh_cash_in_out_report;
        },
    });
    Registries.Component.add(CashInOutStatementButton);

    class PaymentsButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-cash-in-out-statement", this.onClickTemplateLoad);
        }
        async onClickTemplateLoad() {
            var self = this;
            let { confirmed, payload } = this.showPopup("TransactionPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
    }
    PaymentsButton.template = "PaymentsButton";
    ProductScreen.addControlButton({
        component: PaymentsButton,
        condition: function () {
            return this.env.pos.config.sh_cash_in_out_report;
        },
    });
    Registries.Component.add(PaymentsButton);

    return {
        CashInOutStatementButton,
    };
});
