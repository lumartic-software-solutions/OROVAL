from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    event_id = fields.Many2one('calendar.event',string="Event")
    deadline = fields.Datetime('Deadline')
    
    
    '''@api.model
    def create(self,vals):
        res = super(ProjectTask, self).create(vals)
        date = fields.Datetime.now()
        user = False
        if vals.get('user_id'):
            user = self.env['res.users'].browse(vals.get('user_id'))
        else:
            user = res.user_id
        if vals.get('deadline'):
            date = vals.get('deadline')
        elif res.deadline:
            date = res.deadline
        event = self.env['calendar.event'].create({
                    'name': vals.get('name',''),
                    'partner_ids' : user and [(6,0,[user.partner_id.id])] or[(6,0,[])] ,
                    'description': vals.get('description',''),
                    'user_id': self._uid,
                    'start_datetime':date, 
                    'start': date,
                    'duration':res.planned_hours,
                    'stop': date,
                  #  'customer':customer,
                    'allday': False,
                    'state': 'open',
                    'privacy': 'confidential',
                    'task_id' : res.id
                    })
        if event:
            res.write({'event_id' : event.id})
        return res'''
    
    @api.model
    def create(self,vals):
        res = super(ProjectTask, self).create(vals)
        date = fields.Datetime.now()
        user = False
        if vals.get('user_id'):
            user = self.env['res.users'].browse(vals.get('user_id'))
        else:
            user = res.user_id
        if vals.get('deadline'):
            date = vals.get('deadline')
#         elif res.deadline:
#             date = res.deadline
            event = self.env['calendar.event'].create({
                        'name': vals.get('name',''),
                        'partner_ids' : user and [(6,0,[user.partner_id.id])] or[(6,0,[])] ,
                        'description': vals.get('description',''),
                        'user_id': self._uid,
                        'start_datetime':date, 
                        'start': date,
                        'duration':res.planned_hours,
                        'stop': date,
                      #  'customer':customer,
                        'allday': False,
                        'state': 'open',
                        'privacy': 'confidential',
                        'task_id' : res.id
                        })
            if event:
                res.write({'event_id' : event.id})
        return res
    
    @api.multi
    def write(self, vals):
        event = self.env['calendar.event'].search([('task_id','=',self.id)])
        if vals.get('deadline') or self.deadline:
            if vals.get('user_id') or  vals.get('deadline') or vals.get('planned_hours') or vals.get('project_id') :
                date = fields.Datetime.now()
                user = False
                duration = 0.0
                                
                if vals.get('deadline'):
                    date = vals.get('deadline')
                elif self.deadline:
                    date = self.deadline
                if vals.get('user_id'):
                    user = self.env['res.users'].browse(vals.get('user_id'))
                elif self.user_id:
                    user = self.user_id
                if vals.get('planned_hours'):
                    duration = vals.get('planned_hours')
                elif self.planned_hours:
                    duration = self.planned_hours
                if event:
                    a = event.write({'customer':self.customer,'partner_ids' : user and [(6,0,[user.partner_id.id])] or [(6,0,[])],
                    'duration':duration,'start_datetime':date,'start':date,'stop':date})
                else:
                    event = self.env['calendar.event'].create({
                            'name': self.name ,
                            'partner_ids' : [(6,0,[user.partner_id.id])],
                            'description': self.description,
                            'start_datetime': date,
                            'user_id': self._uid,
                            'start': date,
                            'stop': date,
                            'duration':self.planned_hours,
                            'allday': False,
                            'state': 'open',
                           # 'customer':customer,
                            'privacy': 'confidential',
                            'task_id' : self.id
                            })
                    vals.update({'event_id' : event.id})
        res = super(ProjectTask, self).write(vals)
        return res


    
class CalendarEvent(models.Model):
    _inherit = 'calendar.event'
    
    task_id = fields.Many2one('project.task',string="Task")
    customer =fields.Char('Customer',related="task_id.partner_id.name")
    partner_shipping_id = fields.Many2one("res.partner",related="task_id.partner_id",string="Delivery Address")
    phone = fields.Char('Phone',related="task_id.partner_id.phone")
    phone = fields.Char('Phone',related="task_id.partner_id.phone")
    mobile = fields.Char('Mobile',related="task_id.partner_id.mobile")
    street = fields.Char('Street',related="task_id.partner_id.street")
    street2 = fields.Char('Street2',related="task_id.partner_id.street2")
    zip = fields.Char('Zip',related="task_id.partner_id.zip")
    city = fields.Char('City',related="task_id.partner_id.city")
    state_id = fields.Many2one("res.country.state",  related="task_id.partner_id.state_id" , string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', related="task_id.partner_id.country_id" ,string='Country', ondelete='restrict')
    
    
    
    # view task button method
    @api.multi
    def view_task(self):
        if self.task_id :
            task_id = self.env['project.task'].search([('id', '=', self.task_id.id)])
            action = self.env.ref('project.action_view_task').read()[0]
            action['views'] = [(self.env.ref('project.view_task_form2').id, 'form')]
            action['res_id'] = task_id.id
            return action
        else :
            raise UserError(_('No hay tarea para este evento!') )
    
    

