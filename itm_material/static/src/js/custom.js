/**
 *  -*- coding: utf-8 -*-
 *  Odoo, Open Source  Itm Material Theme.
 *  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).# 
 * 
 */
odoo.define('web.custom', function(require) {
    "use strict";

    var core = require('web.core');
    var widget = require('web.form_widgets');
    var FormView = require('web.FormView');
    var Model = require('web.DataModel');
    var session = require('web.session');
    var Models = require('web.Model');
    var ajax = require('web.ajax');
    var stylesheetFile = '/itm_material/static/src/less/themes/dynamic_color.less';
	var link  = document.createElement('link');
	link.rel  = "stylesheet";
	link.type = "text/less";
	link.href = stylesheetFile;
	less.sheets.push(link);
    new Model('res.company').get_func('search_read')([['id', '=', session.company_id]])
    .then(function(res){
    		var custom_color = res[0]['color_background']
    		less.modifyVars({
       		    '@dynamic_color_default': custom_color,
       		    '@dynamic_color_hover': 'darken(@dynamic_color_default, 20%)',
       		    '@dynamic_color': 'lighten(@dynamic_color_default, 20%)',
       		    '@dynamic_color_border': 'lighten(@dynamic_color_default, 23%)',
       		    '@dynamic_color_tag_bg': 'lighten(@dynamic_color_default, 30%)',
       		});
    });

     var dynamic_color_code = (function () {
    	 var colors = function dynamic_color_code(color) {
     		var stylesheetFile = '/itm_material/static/src/less/themes/dynamic_color.less';
  			var link  = document.createElement('link');
  			link.rel  = "stylesheet";
  			link.type = "text/less";
  			link.href = stylesheetFile;
  			less.sheets.push(link);
  			less.modifyVars({
  			    '@dynamic_color_default': color,
  			    '@dynamic_color_hover': 'darken(@dynamic_color_default, 22%)',
 			    '@dynamic_color': 'lighten(@dynamic_color_default, 20%)',
 			    '@dynamic_color_border': 'lighten(@dynamic_color_default, 23%)',
 			    '@dynamic_color_tag_bg': 'lighten(@dynamic_color_default, 30%)',
  			});
//  			less.refreshStyles();
     	 };
    	 return colors;
    	 
    	 })();
     
     return {
    	 dynamic_color_code: dynamic_color_code,
    	};
   
});
