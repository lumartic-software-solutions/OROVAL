# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

# ==================================== start ==========================================
class TaskInvoiceLines(models.TransientModel):
    _name = "task.invoice.lines"


    wizard_create_invoice = fields.Many2one('create.project.invoice.wizard',  string="Project Invoice")
    sequence = fields.Integer(string="Sequence")
    name = fields.Text(string="Description")
    quantity = fields.Float(string="Quantity")
    account_id = fields.Many2one('account.account', string="Account")
    
    

class CreateProjectInvoiceWizard(models.TransientModel):
    _name = "create.project.invoice.wizard"
    _description = "Create Project Invoice Wizard"


    project_invoice_line = fields.One2many('task.invoice.lines', 'wizard_create_invoice', string="Invoice Lines")
    
    @api.model
    def default_get(self, vals):
        res = super(CreateProjectInvoiceWizard, self).default_get(vals)
        context = self.env.context
        ir_property_obj = self.env['ir.property']
        if 'active_id' in context:
            project_id = self.env['project.project'].browse(context.get('active_id'))
            user_id = self.env['res.users'].browse(context.get('uid'))
            line_vals =[]
            sequence = 0
            if project_id.user_id.id != user_id.id :
                raise UserError(_('¡La tarea no se asigna a este usuario!') )
            for task in project_id.task_ids :
                if task.user_id.id == user_id.id and task.state == 'end' and task.invoice_status == 'no':
                    sequence +=1
                    account = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                    if account :
                        values = {  
                            'name': task.name,
                            'sequence' : sequence,
                            'account_id': account.id,
                            'quantity': 1.0,
                             }
                        line_vals.append((0, 0, values))
                    else :
                        raise UserError(_('¡No hay una cuenta de ingresos definida!') ) 
            if len(line_vals) >= 1 :
                res.update({'project_invoice_line' : line_vals})
        return res
    
    
    # Create Project Invoice Method
    @api.multi
    def create_project_invoice(self):
        context = self.env.context
        ir_property_obj = self.env['ir.property']
        if 'active_id' in context:
            project_id = self.env['project.project'].browse(context.get('active_id'))
            list_value = []
            remain_task = []
            user_id = self.env['res.users'].browse(context.get('uid'))
            sequence = 0
            if project_id.user_id.id != user_id.id :
                    raise UserError(_('¡La tarea no se asigna a este usuario!') )
            for task in project_id.task_ids :
                if task.state != 'end' :
                    remain_task.append(task.id)
                if task.user_id.id == user_id.id and task.state == 'end' and task.invoice_status == 'no':
                    task.invoice_status = 'invoiced'
                    sequence +=1
                    vals = {}
                    account = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                    if account :
                        vals = {
                            'name': task.name,
                            'sequence' : sequence,
                            'account_id': account.id,
                            'price_unit':0.0,
                            'quantity': 1.0,
                        }
                        list_value.append(vals)
                    else :
                        raise UserError(_('¡No hay una cuenta de ingresos definida!') )  
            if list_value :
                if project_id.partner_id :
                    partner_account = project_id.partner_id.property_account_receivable_id
                else :
                    raise UserError(_('por favor asigne al cliente para este proyecto!') ) 
                    partner_account = ir_property_obj.get('property_account_receivable_id', 'res.partner')
                invoice_id = self.env['account.invoice'].create({
                            'project_id' : project_id.id or False,
                            'name': project_id.name or  '',
                            'origin': project_id.name or  '',
                            'type': 'out_invoice',
                            'reference': False,
                            'account_id': partner_account.id,
                            'partner_id': project_id.partner_id.id or False,
                            'invoice_line_ids': [(0, 0, data) for data in list_value],
                            'user_id': user_id.id or False,
                        })
                if len(remain_task) == 0:
                    project_id.write({'invoice_status' : 'full invoiced'})
                else:
                    if len(invoice_id) >= 1:
                        project_id.write({'invoice_status' : 'invoiced'})
                    else :
                        project_id.write({'invoice_status' : 'no'})
                if self._context.get('open_project_invoices', False):
                    return project_id.view_project_invoice()
                return {'type': 'ir.actions.act_window_close'}
            else:
                raise UserError(_('No se encontró tarea !') ) 
            
            
# ==================================== stop ==========================================

              
