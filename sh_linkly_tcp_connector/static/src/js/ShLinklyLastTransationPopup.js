odoo.define('sh_linkly_tcp_connector.ShLinklyLastTransationPopup', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class ShLinklyLastTransationPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            Object.assign(this, this.props);
            console.log('11', this);
        }
        get lastTransactionSuccessUpdated() {
            return this.lastTransactionSuccess ? 'Success' : 'Failed';
        }
        get momentDateTime() {
            const formatString = "ddd MMM DD HH:mm:ss [IST] YYYY";
            let momentObj = moment(this.bankDate, formatString)
            return momentObj
        }
        get dateTime(){
            return this.momentDateTime.format("h:mma D/MM/YYYY");
        }
        get txnTypeUpdated() {
            if (this.txnType === 'PurchaseCash') {
                return 'Purchase';
            } else {
                return this.txnType;
            }
        }
        get amtPurchaseUpdated(){
            return '$' + this.amtPurchase;
        }
        
    }

    ShLinklyLastTransationPopup.template = 'ShLinklyLastTransationPopup';

    Registries.Component.add(ShLinklyLastTransationPopup);

    return ShLinklyLastTransationPopup;
});
