odoo.define('sh_pos_checker.sh_checking_popup', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const codeReader = new ZXing.BrowserMultiFormatReader();

    class ShValodationTypePopup extends AbstractAwaitablePopup {
        setup(){
            super.setup()
            this.sh_show_date_field = false
        }
        // async open_barcode_scaner() {
        //     var self = this;
        //     let selectedDeviceId;
        //     self.cancel()
        //     await codeReader
            
        //     if (codeReader.canEnumerateDevices ){
        //         codeReader.getVideoInputDevices().then(function (result) {
        //             //THEN METHOD START HERE
        //             console.log('result 123 ',result)
        //             if ( result ){
        //                 const sourceSelect = document.getElementById("js_id_sh_sale_barcode_mobile_cam_select");
        //                 console.log("sourceSelect",sourceSelect);
        //                 $("#js_id_sh_sale_barcode_mobile_cam_select option").remove();
                        
        //                 _.each(result, function (item) {
        //                     const sourceOption = document.createElement("option");
        //                     sourceOption.text = item.label;
        //                     sourceOption.value = item.deviceId;
        //                     sourceSelect.appendChild(sourceOption);
        //                 });
        //                 $("#js_id_sh_sale_barcode_mobile_cam_select").change(function (e) {
        //                 });
                        
        //                 selectedDeviceId = sourceSelect.value;
        //                 //SHOW VIDEO
                        
        //     $("#js_id_sh_sale_barcode_mobile_vid_div").show();

        //     //SHOW STOP/ HIDE START BUTTON
        //     $("#js_id_sh_sale_barcode_mobile_reset_btn").show();
        //     $("#js_id_sh_sale_barcode_mobile_start_btn").hide();

        //     //CALL METHOD
        //     //CONTINUOUS SCAN OR NOT.SystrayMenu
        //     if (self.env.pos.config.sh_pos_bm_is_cont_scan) {
        //         self.decodeOnce(codeReader, selectedDeviceId);
        //     } else {
        //         console.log("selectedDeviceId", selectedDeviceId);
        //         self.decodeContinuously(codeReader, selectedDeviceId);
        //     }

        //     $(".camera-list").show();
        //     $(".camera-list").addClass('sh_video_container');
        //     $(".product-list-container").hide();
        //     $("#js_id_sh_sale_barcode_mobile_reset_btn").css("display", "block");
        //     $("#js_id_sh_sale_barcode_mobile_start_btn").css("display", "none");
        //             }
        //         })
        //     }else{
        //         Gui.showPopup('ErrorPopup', {
        //             title: 'Camera Error',
        //             body: 'Camera Not Found !',
        //         });
        //     }
        // }
        // async decodeContinuously(codeReader, selectedDeviceId) {
        //     var self = this;
        //     console.log("11111111111111111111111 --====>", await codeReader.decodeFromInputVideoDevice(selectedDeviceId, "video"));
        //     codeReader.decodeFromInputVideoDeviceContinuously(selectedDeviceId, "video", (result, err) => {
        //         //RESULT
        //         console.log("result ===>", result);
        //         if (result) {
        //             var product = "";
        //             if (self.env.pos.config.sh_pos_barcode_mobile_type == "barcode") {
        //                 product = self.env.pos.db.get_product_by_barcode(result.text);
        //             } else if (self.env.pos.config.sh_pos_barcode_mobile_type == "int_ref") {
        //                 product = self.env.pos.db.get_product_by_default_code(result.text);
        //             } else if (self.env.pos.config.sh_pos_barcode_mobile_type == "sh_qr_code") {
        //                 product = self.env.pos.db.get_product_by_qr(result.text);
        //             } else if (self.env.pos.config.sh_pos_barcode_mobile_type == "all") {
        //                 if (self.env.pos.db.get_product_by_barcode(result.text)) {
        //                     product = self.env.pos.db.get_product_by_barcode(result.text);
        //                 } else if (self.env.pos.db.get_product_by_default_code(result.text)) {
        //                     product = self.env.pos.db.get_product_by_default_code(result.text);
        //                 } else if (self.env.pos.db.get_product_by_qr(result.text)) {
        //                     product = self.env.pos.db.get_product_by_qr(result.text);
        //                 }
        //             }
        //             if (product) {
        //                 self.env.pos.get_order().add_product(product);
        //                 if (self.env.pos.config.sh_pos_bm_is_notify_on_success) {
        //                     $.iaoAlert({ msg: "Product: " + product.display_name + " Added to cart successfully.", type: "notification", mode: "dark", autoHide: true, alertTime: "3000", closeButton: true });
        //                 }
        //                 if (self.env.pos.config.sh_pos_bm_is_sound_on_success) {
        //                     Gui.playSound('bell');
        //                 }
        //             } else {
        //                 if (self.env.pos.config.sh_pos_bm_is_notify_on_fail) {
        //                     $.iaoAlert({ msg: "Warning: Scanned Internal Reference/Barcode not exist in any product!", type: "error", autoHide: true, alertTime: "3000", closeButton: true, mode: "dark" });
        //                 }
        //                 if (self.env.pos.config.sh_pos_bm_is_sound_on_fail) {
        //                     Gui.playSound('error');
        //                 }
        //             }

        //             $("#js_id_sh_sale_barcode_mobile_vid_div").hide();
        //             $("#js_id_sh_sale_barcode_mobile_vid_div").show();
        //         }

        //         if (err) {
        //             console.log("ERROR", err);
        //             if (err instanceof ZXing.NotFoundException) {
        //                 console.log("No QR code found.");
        //             }
        //             if (err instanceof ZXing.ChecksumException) {
        //                 console.log("A code was found, but it's read value was not valid.");
        //             }

        //             if (err instanceof ZXing.FormatException) {
        //                 console.log("A code was found, but it was in a invalid format.");
        //             }
        //         }
        //     });
        // }
        // async decodeOnce(codeReader, selectedDeviceId) {
        //     var self = this;
        //     console.log("called ==>", selectedDeviceId , codeReader);
        //     console.log("ytrsttt --====>", await codeReader.decodeFromInputVideoDevice(selectedDeviceId, "video"));
        //     codeReader.decodeFromInputVideoDevice(selectedDeviceId, "video").then((result) => {
        //         //RESULT
           
        //         var product = "";
        //         if (self.env.pos.config.sh_pos_barcode_mobile_type == "barcode") {
        //             product = self.env.pos.db.get_product_by_barcode(result.text);
        //         } else if (self.env.pos.config.sh_pos_barcode_mobile_type == "int_ref") {
        //             product = self.env.pos.db.get_product_by_default_code(result.text);
        //         } else if (self.env.pos.config.sh_pos_barcode_mobile_type == "sh_qr_code") {
        //             product = self.env.pos.db.get_product_by_qr(result.text);
        //         } else if (self.env.pos.config.sh_pos_barcode_mobile_type == "all") {
        //             if (self.env.pos.db.get_product_by_barcode(result.text)) {
        //                 product = self.env.pos.db.get_product_by_barcode(result.text);
        //             } else if (self.env.pos.db.get_product_by_default_code(result.text)) {
        //                 product = self.env.pos.db.get_product_by_default_code(result.text);
        //             } else if (self.env.pos.db.get_product_by_qr(result.text)) {
        //                 product = self.env.pos.db.get_product_by_qr(result.text);
        //             }
        //         }
        //         if (product) {
        //             self.env.pos.get_order().add_product(product);
        //             if (self.env.pos.config.sh_pos_bm_is_notify_on_success) {
        //                 $.iaoAlert({ msg: "Product: " + product.display_name + " Added to cart successfully.", type: "notification", mode: "dark", autoHide: true, alertTime: "3000", closeButton: true });
        //             }
        //             if (self.env.pos.config.sh_pos_bm_is_sound_on_success) {
        //                 Gui.playSound('bell');
        //             }
        //         } else {
        //             if (self.env.pos.config.sh_pos_bm_is_notify_on_fail) {
        //                 $.iaoAlert({ msg: "Warning: Scanned Internal Reference/Barcode not exist in any product!", type: "error", autoHide: true, alertTime: "3000", closeButton: true, mode: "dark" });
        //             }
        //             if (self.env.pos.config.sh_pos_bm_is_sound_on_fail) {
        //                 Gui.playSound('error');
        //             }
        //         }
        //         //RESET READER
        //         codeReader.reset();

        //         //HIDE VIDEO
        //         $("#js_id_sh_sale_barcode_mobile_vid_div").hide();

        //         //HIDE STOP/ SHOW START BUTTON
        //         $("#js_id_sh_sale_barcode_mobile_reset_btn").hide();
        //         $("#js_id_sh_sale_barcode_mobile_start_btn").show();

        //         // HIDE CAMERA AND OPEN PRODUCTS
        //         $(".camera-list").hide();
        //         $(".camera-list").removeClass('sh_video_container');
        //         $(".product-list-container").show();
        //         $(".category-list").show();
        //     });
        // }
        // onClickStop() {
        //     //RESET READER
        //     codeReader.reset();
        //     //HIDE VIDEO
        //     $("#js_id_sh_sale_barcode_mobile_vid_div").hide();

        //     $(".camera-list").hide();
        //     $(".camera-list").removeClass('sh_video_container');
        //     $(".product-list-container").show();
        //     $("#js_id_sh_sale_barcode_mobile_reset_btn").css("display", "none");
        //     $("#js_id_sh_sale_barcode_mobile_start_btn").css("display", "block");
        // }
        async open_barcodePopup(){
            const { confirmed, payload } =  await this.showPopup('BarcodePopup',{'age':this.props.age, product : this.props.product,})
            if(confirmed){
                console.log("confirrm ==>", confirmed);
            }
            else{
                this.cancel()
            }
        }

        get currentOrder() {
            return this.env.pos.get_order();
        }
        async open_customer_screen(){
            this.confirm()
            const currentPartner = this.currentOrder.get_partner();
            const { confirmed, payload: newPartner } = await this.showTempScreen(
                'PartnerListScreen',
                { partner: currentPartner }
            );
            if (confirmed) {
                this.currentOrder.set_partner(newPartner);
                this.currentOrder.updatePricelist(newPartner);
                if(newPartner && newPartner.Sh_birthdate){
                    const birthDate = new Date(newPartner.Sh_birthdate);
                    const today = new Date();
                    const ageInMilliseconds = today - birthDate;
                    const ageInYears = Math.floor(ageInMilliseconds / (1000 * 60 * 60 * 24 * 365.25));
                    if(this.props.age >= ageInYears){
                        this.currentOrder.add_product(this.props.product);
                    }else{
                        await this.showPopup('ErrorPopup', {
                            title: this.env._t('Under Age Limit'),
                            body: this.env._t('This product has an age restriction. '),
                        });

                    }

                }
            }
        }        
        async show_date_field(){
            let self = this;
            
            // Toggle the Highlight class based on its current presence
            if ($(".sh_birthdate").hasClass('Highlight')) {
                self.sh_show_date_field = false;
                $(".sh_birthdate").removeClass('Highlight');
            } else {
                $(".sh_birthdate").addClass('Highlight');
                self.sh_show_date_field = true;
            }
        
            self.render();
        }
        
        cancel(){
            super.cancel()
            this.env.pos.get_order().number_buffer_reset = false
        }
        sh_confirm(){
            super.confirm()
            let date =  $("#date_input").val()
            if(date){
                console.log("daye ==", date);
                const birthDate = new Date(date);
                const today = new Date();
                const ageInMilliseconds = today - birthDate;
                const ageInYears = Math.floor(ageInMilliseconds / (1000 * 60 * 60 * 24 * 365.25));
                if(this.props.age <= ageInYears){
                    this.currentOrder.add_product(this.props.product);
                }else{
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Under Age Limit'),
                        body: this.env._t('This product has an age restriction. '),
                    });
    
                }
            }else{
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Invalid Date'),
                    body: this.env._t('Please add the birthdate properly.'),
                });
            }
        }
    }

    ShValodationTypePopup.template ='ShValodationTypePopup';
    
    Registries.Component.add(ShValodationTypePopup);

    return ShValodationTypePopup
});

