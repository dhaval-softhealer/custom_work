odoo.define("sh_pos_order_return_exchange.screen", function (require) {
    "use strict";


    const { debounce } = owl.utils;
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const { useListener } = require("web.custom_hooks");
    const rpc = require("web.rpc");
    var core = require("web.core");
    var framework = require("web.framework");
    var QWeb = core.qweb;
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    var field_utils = require("web.field_utils");

    class OrderListScreen extends PosComponent {
        constructor() {
            super(...arguments);
            this.filter_by_paid_order = false;
            this.filter_by_invoice_order = false;
            this.filter_by_posted_order = false;
            this.state = {
                query: null,
                selectedTemplate: this.props.template,
            };
            this.order_no_return = [];
            this.return_filter = false;
            this.updateTemplateList = debounce(this.updateTemplateList, 70);
        }
        back() {
            this.env.pos.get_order()['customer_history'] = false;
            this.trigger("close-temp-screen");
        }
        change_date() {
            this.state.query = $("#date1")[0].value;
            this.render();
        }
        updateOrderList(event) {
            this.state.query = event.target.value;

            if (event.code === "Enter") {
                const serviceorderlistcontents = this.posorderdetail;
                if (serviceorderlistcontents.length === 1) {
                    this.state.selectedQuotation = serviceorderlistcontents[0];
                }
            } else {
                this.render();
            }
        }
        sh_paid_order_filter() {
            if ($('.sh_paid_order').hasClass('highlight')) {
                this.filter_by_paid_order = false
                $('.sh_paid_order').removeClass('highlight')
            } else {
                this.filter_by_paid_order = true
                this.filter_by_posted_order = false
                this.filter_by_invoice_order = false
                $('.sh_paid_order').addClass('highlight')
                $('.sh_posted_order').removeClass('highlight')
                $('.sh_invoiced_order').removeClass('highlight')
            }
            $(".sh_pagination").pagination("selectPage", 1);
            this.render()
        }
        sh_posted_order_filter() {
            if ($('.sh_posted_order').hasClass('highlight')) {
                this.filter_by_posted_order = false
                $('.sh_posted_order').removeClass('highlight')
            } else {
                this.filter_by_posted_order = true
                this.filter_by_paid_order = false
                this.filter_by_invoice_order = false
                $('.sh_posted_order').addClass('highlight')
                $('.sh_paid_order').removeClass('highlight')
                $('.sh_invoiced_order').removeClass('highlight')
            }
            $(".sh_pagination").pagination("selectPage", 1);
            this.render()
        }
        get_order_by_invoiced_order(name) {
            var self = this;
            return _.filter(this.get_order_by_state('invoiced'), function (template) {
                if (template.name.indexOf(name) > -1) {
                    return true;
                } else if (template['pos_reference'] && template["pos_reference"].indexOf(name) > -1) {
                    return true;
                } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                    return true;
                } else if (template["date_order"] && template["date_order"].indexOf(name) > -1) {

                    return true;
                } else {
                    return false;
                }
            });
        }
        sh_invoiced_order_filter() {
            if ($('.sh_invoiced_order').hasClass('highlight')) {
                this.filter_by_invoice_order = false
                $('.sh_invoiced_order').removeClass('highlight')
            } else {
                this.filter_by_invoice_order = true
                this.filter_by_paid_order = false
                this.filter_by_posted_order = false
                $('.sh_invoiced_order').addClass('highlight')
                $('.sh_posted_order').removeClass('highlight')
                $('.sh_paid_order').removeClass('highlight')
            }
            $(".sh_pagination").pagination("selectPage", 1);
            this.render()
        }
        get_order_by_state(name) {
            var self = this;
            if($('.return_order_button').hasClass('highlight')){
                var templates = _.filter(self.env.pos.db.all_return_order, function (template) {
                    if (template["state"] && template["state"].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
                if(this.env.pos.config.sh_load_order_by && this.env.pos.config.sh_load_order_by == 'all'){                    	
                      return templates;
                }else if (self.env.pos.config.sh_load_order_by == "session_wise") {
                      if (self.env.pos.config.sh_session_wise_option == "current_session") {
                          var display_order = []
                          display_order = templates.filter(function (order) {
                              return order.session_id[0] == self.env.pos.pos_session.id;
                          });                  
                          return display_order;
                      }else if (self.env.pos.config.sh_session_wise_option == "last_no_session") {
                          if (self.env.pos.config.sh_last_no_session != 0) {
                              var filter_order = []
                              filter_order = self.env.pos.get_last_session_order(templates);
                              return filter_order
                          }else{
                              return []
                          }
                      }
                }else if (self.env.pos.config.sh_load_order_by == "day_wise") {
                      if (self.env.pos.config.sh_day_wise_option == "current_day") {                    		
                          return templates.filter(function (order) {
                              var date = new Date();
                              var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                              return order.date_order.split(" ")[0] === today_date;
                          });
                          
                      } else if (self.env.pos.config.sh_day_wise_option == "last_no_day") {
                          if (self.env.pos.config.sh_last_no_days != 0) {
                              return templates.filter(function (order) {
                                  var date = new Date();
                                  var last = new Date(date.getTime() - self.env.pos.config.sh_last_no_days * 24 * 60 * 60 * 1000);
                                  var last = last.getFullYear() + "-" + ("0" + (last.getMonth() + 1)).slice(-2) + "-" + ("0" + last.getDate()).slice(-2);
                                  var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                  
                                  var formated_last_date = field_utils.format.datetime(moment(last), {}, { timezone: false });
                                  var formated_today_date = field_utils.format.datetime(moment(today_date), {}, { timezone: false });
                                  
                                  if(order.date_order.split(" ")[0] > last && order.date_order.split(" ")[0] <= today_date){
                                      return order
                                  }else if(order.date_order.split(" ")[0] > formated_last_date && order.date_order.split(" ")[0] <= formated_today_date){
                                      return order
                                  }
                              });
                          }else{
                              return []
                          }
                      }                       	
                }
                
            }else{
                var templates = _.filter(self.env.pos.db.all_non_return_order, function (template) {
                    if (template["state"] && template["state"].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
                                
                if(this.env.pos.config.sh_load_order_by && this.env.pos.config.sh_load_order_by == 'all'){                    	
                      return templates;
                }else if (self.env.pos.config.sh_load_order_by == "session_wise") {
                      if (self.env.pos.config.sh_session_wise_option == "current_session") {
                          var display_order = []
                          display_order = templates.filter(function (order) {
                              if(order.session_id){
                                  return order.session_id[0] == self.env.pos.pos_session.id;
                              }else{
                                  return true
                              }
                          });                  
                          return display_order;
                      }else if (self.env.pos.config.sh_session_wise_option == "last_no_session") {
                          if (self.env.pos.config.sh_last_no_session != 0) {
                              var filter_order = []
                              filter_order = self.env.pos.get_last_session_order(templates);
                              return filter_order
                          }else{
                              return []
                          }
                      }
                }else if (self.env.pos.config.sh_load_order_by == "day_wise") {
                      if (self.env.pos.config.sh_day_wise_option == "current_day") {                    		
                          return templates.filter(function (order) {
                              var date = new Date();
                              var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                             
                              return order.date_order.split(" ")[0] === today_date;
                          });
                          
                      } else if (self.env.pos.config.sh_day_wise_option == "last_no_day") {
                          if (self.env.pos.config.sh_last_no_days != 0) {
                              return templates.filter(function (order) {
                                  var date = new Date();
                                  var last = new Date(date.getTime() - self.env.pos.config.sh_last_no_days * 24 * 60 * 60 * 1000);
                                  var last = last.getFullYear() + "-" + ("0" + (last.getMonth() + 1)).slice(-2) + "-" + ("0" + last.getDate()).slice(-2);
                                  var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                  
                                  var formated_last_date = field_utils.format.datetime(moment(last), {}, { timezone: false });
                                  var formated_today_date = field_utils.format.datetime(moment(today_date), {}, { timezone: false });
                                  
                                  if(order.date_order.split(" ")[0] > last && order.date_order.split(" ")[0] <= today_date){
                                      return order
                                  }else if(order.date_order.split(" ")[0] > formated_last_date && order.date_order.split(" ")[0] <= formated_today_date){
                                      return order
                                  }
                              });
                          }else{
                              return []
                          }
                      }                       	
                }
            }
        }
       
        get_order_by_posted_order(name) {
            var self = this;
            return _.filter(this.get_order_by_state('done'), function (template) {
                if (template.name.indexOf(name) > -1) {
                    return true;
                } else if (template['pos_reference'] && template["pos_reference"].indexOf(name) > -1) {
                    return true;
                } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                    return true;
                } else if (template["date_order"] && template["date_order"].indexOf(name) > -1) {
                    return true;
                } else {
                    return false;
                }
            });
        }
        get_order_by_paid_order(name) {
            var self = this;
            return _.filter(this.get_order_by_state('paid'), function (template) {
                if (template.name.indexOf(name) > -1) {
                    return true;
                } else if (template['pos_reference'] && template["pos_reference"].indexOf(name) > -1) {
                    return true;
                } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                    return true;
                } else if (template["date_order"] && template["date_order"].indexOf(name) > -1) {
                    return true;
                } else {
                    return false;
                }
            });
        }
        get posorderdetail() {
            var self = this;
            if (this.state.query && this.state.query.trim() !== "") {
                if (this.filter_by_paid_order) {
                    if (this.state.query && this.state.query.trim() !== "") {
                        var templates = this.get_order_by_paid_order(this.state.query.trim());
                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                        var current_page = $(".sh_pagination").find('.active').text();

                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);

                        return templates;
                    } else {
                        var templates = this.get_order_by_state('paid');

                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));

                        var current_page = $(".sh_pagination").find('.active').text();

                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);
                        return templates;
                    }
                } else if (this.filter_by_invoice_order) {
                    if (this.state.query && this.state.query.trim() !== "") {
                        var templates = this.get_order_by_invoiced_order(this.state.query.trim());
                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                        var current_page = $(".sh_pagination").find('.active').text();
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);
                        return templates;
                    } else {
                        var templates = this.get_order_by_state('invoiced');

                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));

                        var current_page = $(".sh_pagination").find('.active').text();
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);

                        return templates;
                    }

                }
                else if (this.filter_by_posted_order) {
                    if (this.state.query && this.state.query.trim() !== "") {
                        var templates = this.get_order_by_posted_order(this.state.query.trim());
                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                        var current_page = $(".sh_pagination").find('.active').text();
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);
                        return templates;
                    } else {
                        var templates = this.get_order_by_state('done');

                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));

                        var current_page = $(".sh_pagination").find('.active').text();
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);

                        return templates;
                    }
                } else {
                    var templates = this.get_order_by_name(this.state.query.trim());

                    $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                    var pageNumber = $(".sh_pagination").pagination("getCurrentPage");
                    var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1);
                    var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                    templates = templates.slice(showFrom, showTo);
                    return templates;
                }
            } else {

                if (this.filter_by_paid_order) {
                    if (this.state.query && this.state.query.trim() !== "") {
                        var templates = this.get_order_by_paid_order(this.state.query.trim());
                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                        var current_page = $(".sh_pagination").find('.active').text();

                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);

                        return templates;
                    } else {
                        var templates = this.get_order_by_state('paid');

                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));

                        var current_page = $(".sh_pagination").find('.active').text();

                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);
                        return templates;
                    }
                } else if (this.filter_by_invoice_order) {
                    if (this.state.query && this.state.query.trim() !== "") {
                        var templates = this.get_order_by_invoiced_order(this.state.query.trim());
                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                        var current_page = $(".sh_pagination").find('.active').text();
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);
                        return templates;
                    } else {
                        var templates = this.get_order_by_state('invoiced');

                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));

                        var current_page = $(".sh_pagination").find('.active').text();
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);

                        return templates;
                    }

                }
                else if (this.filter_by_posted_order) {
                    if (this.state.query && this.state.query.trim() !== "") {
                        var templates = this.get_order_by_posted_order(this.state.query.trim());
                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                        var current_page = $(".sh_pagination").find('.active').text();
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);
                        return templates;
                    } else {
                        var templates = this.get_order_by_state('done');

                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));

                        var current_page = $(".sh_pagination").find('.active').text();
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);

                        return templates;
                    }
                } else {

                    self.order_no_return = [];
                    self.return_order = [];
                    _.each(self.all_order, function (order) {
                        if ((order.is_return_order && order.return_status && order.return_status != "nothing_return") || (!order.is_return_order && !order.is_exchange_order)) {
                            self.order_no_return.push(order);
                        } else {
                            self.return_order.push(order);
                        }
                    });


                    if (!self.return_filter) {

                        if ($(".sh_pagination") && $(".sh_pagination").length) {
                            if (self.env.pos.get_order()['customer_history']) {
                                $(".sh_pagination").pagination("updateItems", Math.ceil(self.order_no_return.length / self.env.pos.config.sh_how_many_order_per_page));
                            } else {
                                $(".sh_pagination").pagination("updateItems", Math.ceil(self.env.pos.db.all_non_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                            }

                        }

                        if (self.env.pos.get_order()['customer_history']) {

                            if ($(".sh_pagination") && $(".sh_pagination").length > 0) {
                                var pageNumber = $(".sh_pagination").pagination("getCurrentPage");
                                var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1);
                                var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                                self.order_no_return = self.order_no_return.slice(showFrom, showTo);
                            }
                            if (self.order_no_return && self.order_no_return.length > 0) {
                                _.each(self.order_no_return, function (each_return_statement) {
                                    if (each_return_statement && each_return_statement.sh_order_line_id && typeof (each_return_statement.sh_order_line_id) && typeof (each_return_statement.sh_order_line_id) == "object") {
                                        each_return_statement['sh_line_id'] = each_return_statement.sh_order_line_id
                                    }
                                });
                            }
                            return self.order_no_return;
                        } else {
                            return self.order_no_return;
                        }

                    } else {

                        if ($(".sh_pagination") && $(".sh_pagination").length) {
                            if (self.env.pos.get_order()['customer_history']) {
                                $(".sh_pagination").pagination("updateItems", Math.ceil(self.return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                            } else {
                                $(".sh_pagination").pagination("updateItems", Math.ceil(self.env.pos.db.all_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                            }
                        }

                        if (self.env.pos.get_order()['customer_history']) {

                            if ($(".sh_pagination") && $(".sh_pagination").length > 0) {
                                var pageNumber = $(".sh_pagination").pagination("getCurrentPage");
                                var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1);
                                var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                                self.return_order = self.return_order.slice(showFrom, showTo);
                            }
                            return self.return_order;
                        } else {
                            return self.return_order;
                        }
                    }

                    //                    return self.return_order;
                }
            }

        }
        get_order_by_name(name) {
            var self = this;
            if (self.return_filter) {
                return _.filter(self.env.pos.db.all_return_order, function (template) {
                    if (template.name.indexOf(name) > -1) {
                        return true;
                    } else if (template["pos_reference"].indexOf(name) > -1) {
                        return true;
                    } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                        return true;
                    } else if (template["date_order"].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
            } else {
                return _.filter(self.env.pos.db.all_non_return_order, function (template) {
                    if (template.name.indexOf(name) > -1) {
                        return true;
                    } else if (template["pos_reference"].indexOf(name) > -1) {
                        return true;
                    } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                        return true;
                    } else if (template["date_order"].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
            }
        }

        clickLine(event) {
            var self = this;
            self.hasclass = true;
            if ($(event.currentTarget).hasClass("highlight")) {
                self.hasclass = false;
            }
            $(".sh_order_list .highlight").removeClass("highlight");
            $(event.currentTarget).closest("table").find(".show_order_detail").removeClass("show_order_detail");
            $(event.currentTarget).closest("table").find(".show_order_detail").removeClass("show_order_detail");
            $(event.currentTarget).closest("table").find(".show_order_detail").removeClass("show_order_detail");
            var order_id = $(event.currentTarget).attr("data-order-id");
            var order_data;
            if (order_id) {

                order_data = self.env.pos.db.order_by_id[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_uid[order_id];
                }
                if (!order_data) {
                    order_id = $(event.currentTarget).attr("data-id");
                    if (order_id) {
                        order_data = self.env.pos.db.order_by_uid[order_id];
                    }
                }
            }
            if (!order_id) {
                order_id = $(event.currentTarget).attr("data-id");
                if (order_id) {
                    order_data = self.env.pos.db.order_by_uid[order_id];
                }
            }
            if (order_data && self.hasclass) {
                self.selected_pos_order = order_id;
                if ((order_data.sh_line_id) || (order_data.sh_order_line_id && typeof (order_data.sh_order_line_id) == 'object')) {
                    if (!order_data['sh_line_id']) {
                        order_data['sh_line_id'] = order_data.sh_order_line_id
                    }
                    _.each(order_data.sh_line_id, function (pos_order_line) {
                        $(event.currentTarget).addClass("highlight");
                        if (order_data.pos_reference) {
                            $(event.currentTarget)
                                .closest("table")
                                .find("tr#" + order_data.pos_reference.split(" ")[1])
                                .addClass("show_order_detail");
                        } else {
                            $(event.currentTarget)
                                .closest("table")
                                .find("tr#" + order_data.name.split(" ")[1])
                                .addClass("show_order_detail");
                        }
                        $(event.currentTarget)
                            .closest("table")
                            .find("#" + pos_order_line)
                            .addClass("show_order_detail");
                    });
                } else {
                    _.each(order_data.lines, function (pos_order_line) {
                        $(event.currentTarget).addClass("highlight");
                        if (order_data.pos_reference && order_data.pos_reference.split(" ") && order_data.pos_reference.split(" ")[1]) {
                            $(event.currentTarget)
                                .closest("table")
                                .find("tr#" + order_data.pos_reference.split(" ")[1])
                                .addClass("show_order_detail");
                        } else if (order_data.name && order_data.name.split(" ") && order_data.name.split(" ")[1]) {
                            $(event.currentTarget)
                                .closest("table")
                                .find("tr#" + order_data.name.split(" ")[1])
                                .addClass("show_order_detail");
                        }
                        if (self.env.pos.db.order_line_by_id[pos_order_line] && self.env.pos.db.order_line_by_id[pos_order_line].id) {
                            $(event.currentTarget)
                                .closest("table")
                                .find("#" + self.env.pos.db.order_line_by_id[pos_order_line].id)
                                .addClass("show_order_detail");
                        }/*else if(pos_order_line[2] && pos_order_line[2].sh_line_id){
                        	if(self.env.pos.db.order_line_by_id[pos_order_line[2].sh_line_id]){
                        		
                        	}
                        }*/
                    });
                }
            }
        }
        return_order_filter() {
            var self = this;
            var previous_order = self.env.pos.db.all_order;
            if (!$(".return_order_button").hasClass("highlight")) {
                self.order_no_return = [];
                $(".return_order_button").addClass("highlight");

                self.return_filter = true;
                $(".sh_pagination").pagination("updateItems", Math.ceil(self.env.pos.db.all_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                $(".sh_pagination").pagination("selectPage", 1);
            } else {
                self.return_order = [];
                $(".return_order_button").removeClass("highlight");
                self.return_filter = false;

                $(".sh_pagination").pagination("updateItems", Math.ceil(self.env.pos.db.all_non_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                $(".sh_pagination").pagination("selectPage", 1);
            }
            self.render();
        }
        reorder_pos_order(event) {
            var self = this;
            var order_id = event.currentTarget.closest("tr").attributes[0].value;

            var order_data = self.env.pos.db.order_by_uid[order_id];
            if (!order_data) {
                order_data = self.env.pos.db.order_by_id[order_id];
            }
            var order_line = [];

            if (self.env.pos.get_order() && self.env.pos.get_order().get_orderlines() && self.env.pos.get_order().get_orderlines().length > 0) {
                var orderlines = self.env.pos.get_order().get_orderlines();
                _.each(orderlines, function (each_orderline) {
                    if (self.env.pos.get_order().get_orderlines()[0]) {
                        self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                    }
                });
            }

            var current_order = self.env.pos.get_order();

            _.each(order_data.lines, function (each_order_line) {
                var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                if (!line_data) {
                    line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                }
                var product = self.env.pos.db.get_product_by_id(line_data.product_id[0]);
                if (!product) {
                    product = self.env.pos.db.get_product_by_id(line_data.product_id);
                }
                current_order.add_product(product, {
                    quantity: line_data.qty,
                    price: line_data.price_unit,
                    discount: line_data.discount,
                });
            });
            if (order_data.sh_partner_id && order_data.sh_partner_id[0] && self.env.pos.db.get_partner_by_cid(order_data['sh_partner_id'][0])) {
                self.env.pos.get_order().set_client(self.env.pos.db.get_partner_by_cid(order_data.sh_partner_id[0]));
            }
            else if (order_data.partner_id[0]) {
                self.env.pos.get_order().set_client(self.env.pos.db.get_partner_by_id(order_data.partner_id[0]));
            }
            current_order.assigned_config = order_data.assigned_config;
            self.trigger("close-temp-screen");
        }
        print_pos_order(event) {
            var self = this;
            var order_id = event.currentTarget.closest("tr").attributes[0].value;
            var order_data = self.env.pos.db.order_by_uid[order_id];
            if (!order_data) {
                order_data = self.env.pos.db.order_by_id[order_id];
            }
            var order_line = [];

            if (self.env.pos.get_order() && self.env.pos.get_order().get_orderlines() && self.env.pos.get_order().get_orderlines().length > 0) {
                var orderlines = self.env.pos.get_order().get_orderlines();
                _.each(orderlines, function (each_orderline) {
                    if (self.env.pos.get_order().get_orderlines()[0]) {
                        self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                    }
                });
            }

            var current_order = self.env.pos.get_order();

            _.each(order_data.lines, function (each_order_line) {
                var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                if (!line_data) {
                    line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                }
                var product = self.env.pos.db.get_product_by_id(line_data.product_id[0]);
                if (!product) {
                    product = self.env.pos.db.get_product_by_id(line_data.product_id);
                }
                current_order.add_product(product, {
                    quantity: line_data.qty,
                    price: line_data.price_unit,
                    discount: line_data.discount,
                });
            });
            current_order.name = order_data.pos_reference;
            current_order.assigned_config = order_data.assigned_config;
            current_order.payment_data = order_data.payment_data;
            current_order.amount_return = order_data.amount_return;
            current_order.is_reprint = true;
            self.trigger("close-temp-screen");
            self.showScreen("ReceiptScreen");
        }
        async return_pos_order(event) {
            var self = this;
            self.env.pos.is_return = true;
            self.env.pos.is_exchange = false;
            var order_line = [];
            var order_id = $(event.target.closest("tr")).attr("data-order-id");
            if (order_id) {
                var order_data = self.env.pos.db.order_by_uid[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_id[order_id];
                    await self.rpc({
                        model: 'pos.order',
                        domain: [['id', '=',order_id]],
                        method: 'search_read',
                    }).then(function (dataorder_id) {
                        if(!self.env.pos.db.order_by_id[order_id]){
                            self.env.pos.db.order_by_id[order_id] = dataorder_id[0]
                        }
                        order_data = dataorder_id[0]
                    })
                }
                if (order_data && order_data.lines) {
                    // _.each(order_data.lines, function (each_order_line) {
                    //     var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                    //     if (!line_data) {
                    //         line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                    //     }
                    //     if (line_data) {
                    //         order_line.push(line_data);
                    //     }
                    // });
                    _.each(order_data.lines,async function (each_order_line) {
                        var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                        if (!line_data) {
                            if(each_order_line[2] && each_order_line[2].sh_line_id){
                                line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                            }
                            await self.rpc({
                                model: 'pos.order.line',
                                domain: [['id', '=',each_order_line]],
                                method: 'search_read',
                            }).then(function (order_line_id) { 
                                line_data = order_line_id[0]
                            })
                        }
                        if (line_data) {
                            order_line.push(line_data);
                        }
                    });
                }
            }
            let { confirmed, payload } = this.showPopup("TemplateReturnOrderPopupWidget", { lines: order_line, order: order_id });
            if (confirmed) {
            } else {
                return;
            }
        }
        async exchange_pos_order(event) {
            var self = this;
            self.env.pos.is_return = false;
            self.env.pos.is_exchange = true;
            var order_line = [];
            var order_id = $(event.target.closest("tr")).attr("data-order-id");
            if (order_id) {
                var order_data = self.env.pos.db.order_by_uid[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_id[order_id];
                    await self.rpc({
                        model: 'pos.order',
                        domain: [['id', '=',order_id]],
                        method: 'search_read',
                    }).then(function (dataorder_id) { 
                        if(!self.env.pos.db.order_by_id[order_id]){
                            self.env.pos.db.order_by_id[order_id] = dataorder_id[0]
                        }
                        order_data = dataorder_id[0]
                    })
                }
                if (order_data && order_data.lines) {
                    _.each(order_data.lines,async function (each_order_line) {
                        var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                        if (!line_data) {
                            if(each_order_line[2] && each_order_line[2].sh_line_id){
                                line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                            }
                            await self.rpc({
                                model: 'pos.order.line',
                                domain: [['id', '=',each_order_line]],
                                method: 'search_read',
                            }).then(function (order_line_id) { 
                                line_data = order_line_id[0]
                            })
                        }
                        if (line_data) {
                            order_line.push(line_data);
                        }
                    });
                }
            }

            let { confirmed, payload } = this.showPopup("TemplateReturnOrderPopupWidget", { lines: order_line, order: order_id });
            if (confirmed) {
            } else {
                return;
            }
        }
        mounted() {
            var self = this;

            $(".sh_pagination").pagination({
                pages: Math.ceil(self.env.pos.order_length / self.env.pos.config.sh_how_many_order_per_page),
                displayedPages: 1,
                edges: 1,
                cssStyle: "light-theme",
                showPageNumbers: false,
                showNavigator: true,
                onPageClick: function (pageNumber) {
                    if (!self.env.pos.get_order()['customer_history']) {
                        try {
                            if (!self.return_filter) {
                                rpc.query({
                                    model: "pos.order",
                                    method: "search_return_order",
                                    args: [self.env.pos.config, pageNumber + 1],
                                })
                                    .then(function (orders) {
                                        if (orders) {
                                            if (orders["order"].length == 0) {
                                                $($(".next").parent()).addClass("disabled");
                                                $(".next").replaceWith(function () {
                                                    $("<span class='current next'>Next</span>");
                                                });
                                            }
                                        }
                                    })
                                    .catch(function (reason) { });

                                rpc.query({
                                    model: "pos.order",
                                    method: "search_return_order",
                                    args: [self.env.pos.config, pageNumber],
                                })
                                    .then(function (orders) {

                                        self.env.pos.db.all_order = [];
                                        self.env.pos.db.order_by_id = {};

                                        if (orders) {
                                            if (orders["order"]) {
                                                self.env.pos.db.all_orders(orders["order"]);
                                            }
                                            if (orders["order_line"]) {
                                                self.env.pos.db.all_orders_line(orders["order_line"]);
                                            }
                                        }
                                        self.all_order = self.env.pos.db.all_order;

                                        self.render();
                                    })
                                    .catch(function (reason) {
                                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1);
                                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                                        self.env.pos.db.all_order = self.env.pos.db.all_non_return_order.slice(showFrom, showTo);
                                        // self.env.pos.db.all_display_order = self.env.pos.db.all_order;
                                        self.all_order = self.env.pos.db.all_order;
                                        self.render();
                                    });
                            } else {
                                rpc.query({
                                    model: "pos.order",
                                    method: "search_return_exchange_order",
                                    args: [self.env.pos.config, pageNumber + 1],
                                })
                                    .then(function (orders) {
                                        if (orders) {
                                            if (orders["order"].length == 0) {
                                                $($(".next").parent()).addClass("disabled");
                                                $(".next").replaceWith(function () {
                                                    $("<span class='current next'>Next</span>");
                                                });
                                            }
                                        }
                                    })
                                    .catch(function (reason) {
                                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber + 1) - 1);
                                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                                        var order = self.env.pos.db.all_return_order.slice(showFrom, showTo);
                                        if (order && order.length == 0) {
                                            $($(".next").parent()).addClass("disabled");
                                            $(".next").replaceWith(function () {
                                                $("<span class='current next'>Next</span>");
                                            });
                                        }
                                    });

                                rpc.query({
                                    model: "pos.order",
                                    method: "search_return_exchange_order",
                                    args: [self.env.pos.config, pageNumber],
                                })
                                    .then(function (orders) {
                                        self.env.pos.db.all_order = [];
                                        self.env.pos.db.order_by_id = {};

                                        if (orders) {
                                            if (orders["order"]) {
                                                self.env.pos.db.all_orders(orders["order"]);
                                            }
                                            if (orders["order_line"]) {
                                                self.env.pos.db.all_orders_line(orders["order_line"]);
                                            }
                                        }
                                        self.all_order = self.env.pos.db.all_order;
                                        // self.env.pos.db.all_display_order = self.env.pos.db.all_order;
                                        self.render();
                                    })
                                    .catch(function (reason) {
                                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1);
                                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                                        self.env.pos.db.all_order = self.env.pos.db.all_return_order.slice(showFrom, showTo);
                                        self.all_order = self.env.pos.db.all_order;
                                        self.render();
                                    });
                            }
                        } catch (error) { }
                    } else {
                        if (self.env.pos.get_order()['customer_history']) {
                            var templates = self.get_order_by_name_history()


                            //                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1);
                            //							var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            //							self.env.pos.db.all_order = templates.slice(showFrom, showTo);
                            //							self.env.pos.db.all_display_order = self.env.pos.db.all_order;
                            //							self.all_order = templates.slice(showFrom, showTo);
                            //							self.render();


                            self.all_order = templates;
                            self.render()
                        }
                    }
                },
            });
            super.mounted();
            if (!self.return_filter) {
                $(".sh_pagination").pagination("updateItems", Math.ceil(self.env.pos.db.all_non_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
            } else {
                $(".sh_pagination").pagination("updateItems", Math.ceil(self.env.pos.db.all_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
            }
            $(".sh_pagination").pagination("selectPage", 1);
        }
        get_order_by_name_history() {
            var self = this;
            var name = self.env.pos.get_order()['customer_history']
            if (self.return_filter) {
                return _.filter(self.env.pos.db.all_return_order, function (template) {
                    if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].indexOf(name) > -1) {
                        return true;
                    } else if (template["sh_partner_id"] && template["sh_partner_id"][1] && template["sh_partner_id"][1].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
            } else {

                return _.filter(self.env.pos.db.all_non_return_order, function (template) {
                    if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].indexOf(name) > -1) {
                        return true;
                    } else if (template["sh_partner_id"] && template["sh_partner_id"][1] && template["sh_partner_id"][1].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
            }
        }
        click_draft(event) {
            var self = this;
            self.env.pos.db.save("removed_notes", []);
            // var order_id = event.currentTarget.closest("tr").attributes[0].value;
            var order_id = $(event.currentTarget.closest("tr")).attr("data-order-id");
            return new Promise(function (resolve, reject) {
                try {
                    rpc.query({
                        model: "pos.order",
                        method: "sh_fronted_cancel_draft",
                        args: [[parseInt(order_id)]],
                    })
                        .then(function (return_order_data) {
                            if (return_order_data) {
                                self.env.pos.db.save("removed_draft_orders", []);
                                self.update_order_list(return_order_data);
                            }
                        })
                        .catch(function (error) {
                            var offline_removed_draft_orders = self.env.pos.db.get_removed_draft_orders();
                            offline_removed_draft_orders.push(parseInt(order_id));

                            self.env.pos.db.save("removed_draft_orders", offline_removed_draft_orders);

                            var return_order_data = { sh_uid: parseInt(order_id) };
                            return_order_data["cancel_draft"] = true;
                            return_order_data["cancel_delete"] = false;

                            self.update_order_list([return_order_data]);
                            self.env.pos.set("synch", { state: "disconnected", pending: "error" });
                        });
                } catch (error) { }
            });
        }
        click_delete(event) {
            var self = this;
            self.env.pos.db.save("removed_notes", []);
            // var order_id = event.currentTarget.closest("tr").attributes[0].value;
            var order_id = $(event.currentTarget.closest("tr")).attr("data-order-id");
            return new Promise(function (resolve, reject) {
                try {
                    rpc.query({
                        model: "pos.order",
                        method: "sh_fronted_cancel_delete",
                        args: [[parseInt(order_id)]],
                    })
                        .then(function (return_order_data) {
                            if (return_order_data) {
                                self.env.pos.db.save("removed_notes", []);
                                self.update_order_list(return_order_data);
                            }
                        })
                        .catch(function (error) {
                            var offline_removed_delete_orders = self.env.pos.db.get_removed_delete_orders();
                            offline_removed_delete_orders.push(parseInt(order_id));

                            self.env.pos.db.save("removed_delete_orders", offline_removed_delete_orders);
                            var return_order_data = { sh_uid: parseInt(order_id) };
                            return_order_data["cancel_draft"] = false;
                            return_order_data["cancel_delete"] = true;

                            self.update_order_list([return_order_data]);
                            self.env.pos.set("synch", { state: "disconnected", pending: "error" });
                        });
                } catch (error) { }
            });
        }
        update_order_list(return_order_data) {
            var self = this;
            var remove_order;
            _.each(self.env.pos.db.all_order, function (each_order) {
                _.each(return_order_data, function (each_return_order) {
                    if (each_return_order.cancel_draft) {
                        if (each_order.id == each_return_order.sh_uid) {
                            each_order.state = "draft";
                        }
                    }
                    if (each_return_order.cancel_delete) {
                        self.env.pos.db.remove_order_by_uid(each_return_order.sh_uid);
                        var currentPage = $('.sh_pagination').pagination('getCurrentPage')
                        $('.sh_pagination').pagination('selectPage', currentPage)
                    }
                });
            });

            self.render();
        }
    }
    OrderListScreen.template = "OrderListScreen";
    Registries.Component.add(OrderListScreen);

    const PosReturnPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }
            cancel_return_order() {
                var self = this;

                if (this.env.pos.get_order() && this.env.pos.get_order().get_orderlines() && this.env.pos.get_order().get_orderlines().length > 0) {
                    var orderlines = this.env.pos.get_order().get_orderlines();
                    _.each(orderlines, function (each_orderline) {
                        if (self.env.pos.get_order().get_orderlines()[0]) {
                            self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                        }
                    });
                }
                self.env.pos.get_order().is_return_order(false);
                self.env.pos.get_order().return_order = false;
                self.env.pos.get_order().is_exchange_order(false);
                self.env.pos.get_order().exchange_order = false;
                self.env.pos.get_order().set_old_pos_reference(false);
                self.showScreen("ProductScreen");
            }
            async _finalizeValidation() {
                super._finalizeValidation();
                var self = this;

                if (this.currentOrder.return_order) {
                    this.currentOrder.is_return_order(true);
                    if (this.currentOrder.old_pos_reference) {
                        this.currentOrder.set_old_pos_reference(this.currentOrder.old_pos_reference);
                        this.currentOrder.set_old_sh_uid(this.currentOrder.old_sh_uid);
                    }
                }
                if (this.currentOrder.exchange_order) {
                    this.currentOrder.is_exchange_order(true);
                    if (this.currentOrder.old_pos_reference) {
                        this.currentOrder.set_old_pos_reference(this.currentOrder.old_pos_reference);
                        this.currentOrder.set_old_sh_uid(this.currentOrder.old_sh_uid);
                    }
                }
            }
        };

    Registries.Component.extend(PaymentScreen, PosReturnPaymentScreen);

    return { OrderListScreen, PosReturnPaymentScreen };
});
