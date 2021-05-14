# -*- coding: utf-8 -*-
# Odoo, Open Source Itm Material Theme.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).# 

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    color_background = fields.Char('Select Theme Color', default="#337AB7")
    dashboard_background = fields.Binary(attachment=True)
    
    
    
    
    @api.multi
    def write(self, data):
        res = super(ResCompany, self).write(data)
        if data.get('color_background'):
            self.env['ir.qweb'].clear_caches()
        return res

    @api.model
    def create(self, data):
        res = super(ResCompany, self).create(data)
        if data.get('color_background'):
            self.env['ir.qweb'].clear_caches()
        return res


    

