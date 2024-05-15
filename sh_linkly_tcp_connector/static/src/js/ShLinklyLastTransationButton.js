odoo.define('sh_linkly_tcp_connector.ShLinklyLastTransationButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class ShLinklyLastTransationButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            
            try{
                const res = await fetch("http://localhost:6352/get_last_transaction")
                const result = await res.json();                
                this.showPopup("ShLinklyLastTransationPopup", result);  
            }catch(e){
                this.showPopup("ErrorPopup", {
                    title: "Error fetching last transction",
                });
                console.error('Error fetching last transacion', e);
            }
            
        }

    }
    ShLinklyLastTransationButton.template = 'ShLinklyLastTransationButton';

    ProductScreen.addControlButton({
        component: ShLinklyLastTransationButton,
        condition: ()=>true,
    });

    Registries.Component.add(ShLinklyLastTransationButton);

    return ShLinklyLastTransationButton;
});
