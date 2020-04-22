from odoo import api, fields, models, _, registry, SUPERUSER_ID
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
import threading
from datetime import datetime

class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    crm_id = fields.Many2one(
        comodel_name='crm.lead',
        string='CRM',
    )   
    
class CrmLead(models.Model):
    _inherit = "crm.lead"
    
    event_id = fields.Many2one(
        'calendar.event',
        string='Event',
    )
    alarm_ids = fields.Many2many(
        'calendar.alarm',
        string='Reminders',
    )
    
    
    '''@api.model
    def create(self, vals):
        res = super(CrmLead, self).create(vals)
        date = vals.get('new_date_action', '')
        if not date:
            date = unicode(datetime.now())
        event = self.env['calendar.event'].create({
                    'name': vals.get('name', ''),
                    'partner_ids' : [(6, 0, [res.user_id.partner_id.id])] or[(6, 0, [])] ,
                    'user_id': res.user_id.id,
                    'start_datetime':date,
                    'start': date,
                    'stop': date,
                    'allday': False,
                    'state': 'open',
                    'privacy': 'confidential',
                    'crm_id':res.id,
                    'alarm_ids':[(6, 0, res.alarm_ids.ids)] if res.alarm_ids else [],
            })
        if event:
            res.write({'event_id' : event.id})
        return res
    
    @api.multi
    def write(self, vals):
        res = super(CrmPhonecall, self).write(vals)
        event = self.env['calendar.event'].search([('phonecall_id', '=', self.id)])
        if event and 'event_id' not in vals :
            date = fields.Datetime.now()
            if 'date' in vals :
                date = vals.get('date') or self.date
            event.write({
                    'name': self.name or '',
                    'partner_ids' :  [(6, 0, [self.user_id.partner_id.id]) if self.user_id.partner_id.id else []] ,
                    'user_id': self.user_id.id,
#                     'start_datetime':date, 
                    'start': date,
                    'stop': date,
                })
        return res'''



             
