odoo.define('custom_oroval.custom', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');
var session = require('web.session');
var MyAttendances = require('hr_attendance.my_attendances');

var QWeb = core.qweb;
var _t = core._t;

MyAttendances.include({
	
	events: {
        "click .o_hr_attendance_sign_in_out_icon": function() {
        	this.$('.o_hr_attendance_sign_in_out_icon').attr("disabled", "disabled");
            this.update_attendance();
            if (this.employee.attendance_state=='checked_out'){
            	document.getElementById("apps_icon").style.display = "block";
            	document.getElementById("app-sidebar").style.display = "block";
            	document.body.className ='drawer drawer--left o_web_client drawer-open'
            }else{
            	document.getElementById("apps_icon").style.display = "none";
            	document.getElementById("app-sidebar").style.display = "none";
            }
        },
        },
        start: function () {
            var self = this;

            var hr_employee = new Model('hr.employee');
            hr_employee.query(['attendance_state', 'name'])
                .filter([['user_id', '=', self.session.uid]])
                .all()
                .then(function (res) {
                    if (_.isEmpty(res) ) {
                        self.$('.o_hr_attendance_employee').append(_t("Error : Could not find employee linked to user"));
                        return;
                    }
                    self.employee = res[0];
                    event.stopPropagation();
                    event.preventDefault();
                    if (self.employee.attendance_state=='checked_in'){
                    	document.getElementById("app-sidebar").style.display = "block";
                    	document.getElementById("apps_icon").style.display = "block";
                    }
                    else{
                    	document.getElementById("app-sidebar").style.display = "none";
                    	document.getElementById("apps_icon").style.display = "none";
        	            return self.do_action({
        	                name: _t("Login Popup"),
        	                type: 'ir.actions.act_window',
        	                res_model: 'login.popup',
        	                view_mode: 'form',
        	                view_type: 'form',
        	                views: [[false, 'form'],],
        	                target: 'new'
        	            })
                }
                    self.$el.html(QWeb.render("HrAttendanceMyMainMenu", {widget: self}));
                });
            
            
         return this._super.apply(this, arguments);
            
        },
   
})


new Model('hr.employee').get_func('search_read')([['user_id', '=', session.uid]])
.then(function(res){
    if (res) {
    	if (session.is_superuser == false ) {
        	if (res[0].attendance_state=='checked_in'){
            	document.getElementById("app-sidebar").style.display = "block";
            	document.getElementById("apps_icon").style.display = "block";
            }
            else{
            	document.getElementById("app-sidebar").style.display = "none";
            	document.getElementById("apps_icon").style.display = "none";
            }
        }else{
            document.getElementById("app-sidebar").style.display = "block";
        	document.getElementById("apps_icon").style.display = "block";
        }
    }
});

});



