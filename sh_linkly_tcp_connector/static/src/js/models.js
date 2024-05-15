odoo.define('sh_linkly_tcp_connector.models', function (require) {
    "use strict";

    var POSModel = require('point_of_sale.models');
    var PaymentInterface = require('point_of_sale.PaymentInterface');

    var PaymentLinkly = PaymentInterface.extend({

        init: function () {
            this._super.apply(this, arguments);
        },

        send_payment_request: function () {
            this._super.apply(this, arguments);
            this.pos.get_order().selected_paymentline.set_payment_status('waitingCard');
            return this.sendPayment();
        },

        send_payment_cancel: function () {
            this._super.apply(this, arguments);
            const line = this.pos.get_order().selected_paymentline
            console.log('File: models.js Line : 22',);
            line.set_payment_status('waitingCancel');
            return this._cancelTransaction(line);
        },

        async _cancelTransaction(line) {
            try {
                await fetch('http://localhost:6352/cancel')                
            } catch (err) {
                console.log(err)
            }
            var self = this;
            clearInterval(self.responseInterval);
            setTimeout(() => {
                clearInterval(self.responseInterval);
                line.set_payment_status('retry');

            }, 4000);
            return Promise.resolve();
        },

        sendPayment: async function(type = "purchase") {
            try {
                var amount = this.pos.get_order().selected_paymentline.amount;
                if (amount == 0) {
                    return Promise.reject("Transaction amount is zero.");
                }
                if (amount < 0) {
                    amount = Math.abs(amount);
                    type = "refund";
                }

                var ref = this.pos.get_order().uid;
                return await new Promise((resolve) => {
                    this.transactionResolve = resolve;
                    this._payment_request(ref, amount, type);
                });

            } catch (error) {
                console.error('Error occurred during transaction:', error);
                this.pos.get_order().selected_paymentline.set_payment_status('retry');
                return Promise.reject(error);
            }
        },

        _payment_request(order_id, amount, type) {
            const url = 'http://localhost:6352';
            const body = `?amount=${encodeURIComponent(amount)}&txnRef=${encodeURIComponent(order_id)}&type=${encodeURIComponent(type)}`;
        
            const fetchAndStoreResponse = async () => {
                try {
                    const response = await fetch(url + '/response');
                    const data = await response.json();
                    console.log('response', response);
                    console.log('data', data);
                    if (data.onTransactionEvent && data.onTransactionEvent.txnRef.trim() == order_id) {
                        console.log('data.onTransactionEvent', data.onTransactionEvent);
                        if (data.onTransactionEvent.success) {
                            this.transactionResolve(true);
                            clearInterval(this.responseInterval);
                        } else if (data.onTransactionEvent.success == false) {
                            this.transactionResolve();
                            console.log('data.onTransactionEvent', data.onTransactionEvent);
                            clearInterval(this.responseInterval);
                        }
                    }
                } catch (error) {
                    console.error('Error fetching response:', error);
                    clearInterval(this.responseInterval);
                    this.transactionResolve()
                }
            };
        
            clearInterval(this.responseInterval);
            this.responseInterval = setInterval(fetchAndStoreResponse, 4000);
            fetch(url + body);

        },
    });

    POSModel.register_payment_method('linkly', PaymentLinkly);

    return PaymentLinkly;
});
