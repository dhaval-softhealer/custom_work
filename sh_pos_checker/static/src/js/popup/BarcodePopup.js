odoo.define('sh_pos_checker.BarcodePopup', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useBarcodeReader } = require('point_of_sale.custom_hooks');

    class BarcodePopup extends AbstractAwaitablePopup {
        setup() {
            super.setup()
            useBarcodeReader({
                'product': this.shbarcodeProductAction.bind(this),
            }, true);
        }
        async shbarcodeProductAction(code) {
            if(code.code.startsWith("DBB")){
                const dobMatch = code.code.match(/DBB(\d{8})/);
                if (dobMatch) {
                    const dob = dobMatch[1];
                    const formattedDob = `${dob.substring(0, 2)}-${dob.substring(2, 4)}-${dob.substring(4, 8)}`;
                    const birthDate = new Date(formattedDob);
                    const today = new Date();
                    const ageInMilliseconds = today - birthDate;
                    const ageInYears = Math.floor(ageInMilliseconds / (1000 * 60 * 60 * 24 * 365.25));
                    if(this.props.age <= ageInYears){
                        this.env.pos.get_order().add_product(this.props.product);
                        this.confirm()
                        return true
                    }
                } else {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Age Not Found'),
                        body: this.env._t('DBB pattern not found in the code. '),
                    });
                    console.log("DBB pattern not found in the code.");
                }
            }
            
            
           return false

        }
        confirm(){
            // super.confirm()
        }
    }
    BarcodePopup.template ='BarcodePopup';
    
    Registries.Component.add(BarcodePopup);

    return BarcodePopup
});

