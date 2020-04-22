/**
  -*- coding: utf-8 -*-
  Odoo, Open Source  Material Theme Extend.
  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/
odoo.define('material_theme_extend.material_osbt_script', function (require) {
"use strict";

var core = require('web.core');
var WebClient = require('web.WebClient');
var ControlPanel = require('web.ControlPanel');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var utils = require('web.utils');
var Model = require('web.DataModel');
var session = require('web.session');
var SearchView = require('web.SearchView');
var SystrayMenu = require('web.SystrayMenu');
var data = require('web.data');
var KanbanView = require('web_kanban.KanbanView');
var local_storage = require('web.local_storage');

var qweb = core.qweb;
var FieldRadio = core.form_widget_registry.get('radio');
var ThemeRadio = FieldRadio.extend({
    'template': 'FieldThemeRadio',
    render_value: function () {
        this._super.apply(this, arguments);
        if(this.get('effective_readonly')) {
            this.$el.attr('id', this.get('value')? 'theme_' + this.get('value')[0] : "");
        }
        // var self = this;
        // this.$el.toggleClass("oe_readonly", this.get('effective_readonly'));
        // this.$("input").prop("checked", false).filter(function () {return this.value == self.get_value();}).prop("checked", true);
        // this.$(".oe_radio_readonly").css({'' this.get('value') ? this.get('value')[1] : "");
    } 
});

core.form_widget_registry.add('theme_radio', ThemeRadio);


var ThemeSwicher =  Widget.extend({
        template: "theme-switcher",
        theme_cookie_name: "material_theme",
        events: {
            'click .switch_style': 'switch_style'
        },
        open_themes: function() {
            var self = this;
            // TODO: I am a mess refactor me
            if(this.$('.theme-switcher').hasClass("active")){
                this.$('.theme-switcher').animate({"right":"-350px"}, function(){
                    self.$('.theme-switcher').toggleClass("active");
                });
            }else{
                this.$('.theme-switcher').animate({"right":"0px"}, function(){
                    self.$('.theme-switcher').toggleClass("active");
                });
            }
        },
        switch_style: function(ev){
            ev.preventDefault();
            var theme = $(ev.currentTarget).data('theme');
            this.switch_theme(theme);
        },
        switch_theme: function(theme){
            var links = $('link[rel*=style][theme]');
            if (theme){
                var activate_me = links.filter(function(){ return $(this).attr('theme') === theme;});
                var inactive_others = links.filter(function(){ return $(this).attr('theme') !== theme;});
                // First enable theme
                activate_me.prop('disabled', false);
                // TODO: to stop flickring I think we should use <link rel= preload or alternate instead of
                // settimout may be it works. give it try when you have time
                setTimeout(function(){
                    inactive_others.prop('disabled', true);
                }, 40);
                new Model("res.users").call("write", [session.uid, {'theme':theme}]);
            }
        }
    });

var SystrayThemeSwitcher = Widget.extend({
    template:'ThemeSwicherSysTray',
    events: {
        'click .theme-switcher-toggler': 'toggle_themes',
    },
    init:function(){
        var self = this;
        var theme_switcher = new ThemeSwicher();
        new Model("res.users").call("read", [session.uid, ['theme']]).then(function(res){
            theme_switcher.switch_theme(res.theme);
            theme_switcher.appendTo($('.o_content'));
            self.theme_switcher = theme_switcher;
        });
    },
    toggle_themes: function(ev){
        ev.preventDefault();
        this.theme_switcher.open_themes();
    },
});
SystrayMenu.Items.push(SystrayThemeSwitcher);

});
