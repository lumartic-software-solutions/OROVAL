from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import time


# create new wizard object for manage task(start,end,stop)  
class CustomWizard(models.TransientModel):
    _name = 'new.wizard'
    
    name = fields.Char(string="Name")
    description = fields.Text("Description")
    
    @api.model
    def default_get(self, vals):
        result = super(CustomWizard, self).default_get(vals)
        context = self.env.context
        project_task = self.env['project.task'].search([('id', '=', context.get('active_id'))])
        if context.get('start_task'):
            result.update({'name' : "Are you going to start the task " + project_task.name + '?'})
        if context.get('continue_task'):
            result.update({'name' : "Are you going to continue the task " + project_task.name + '?'})
        if context.get('restart_task'):
            result.update({'name' : "Are you going to restart the task " + project_task.name + '?'})
        return result
    
# button method of manage task and calculate duration
    @api.multi
    def accept_task(self):
        context = self._context
        stage_obj = self.env['project.stage']
        project_task = self.env['project.task'].sudo().search([('id', '=', context.get('active_id'))])
        data_list = []
        start_date = datetime.today()
        p_time = fields.Datetime.now()
        if project_task:
            if not project_task.project_id:
                raise UserError(_("Por favor asigne Proyecto primero"))
        if context.get('ok') and context.get('start_task'):
            if project_task:
                project_task.write({'state' : 'start', 'start_time' : p_time,'start_date' : start_date})
            if project_task.project_id.stage_id.name == 'Nuevo' :
                stage_id = stage_obj.search([('name','=','En Progreso')])
                if stage_id :
                    project_task.project_id.write({'stage_id' : stage_id.id})
        if context.get('ok') and context.get('restart_task'):
            if project_task:
                project_task.write({'state' : 'start', 'restart_time' : p_time,'start_date' : start_date})
#         if context.get('ok') and context.get('pause_task'):
#             if project_task.start_time != False and project_task.con_time == False and project_task.restart_time == False:
#                 pausetime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.start_time), '%Y-%m-%d %H:%M:%S')
#             if project_task.restart_time != False and project_task.con_time == False:
#                 pausetime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.restart_time), '%Y-%m-%d %H:%M:%S')
#             if project_task.con_time != False and project_task.restart_time== False:
#                 pausetime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.con_time), '%Y-%m-%d %H:%M:%S')
#             if project_task.restart_time != False and project_task.con_time != False:
#                 pausetime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.restart_time), '%Y-%m-%d %H:%M:%S')
#             m , s = divmod(pausetime_diff.total_seconds(), 60)
#             h, m = divmod(m, 60)
#             dur_h = (_('%0*d') % (2, h))
#             dur_m = (_('%0*d') % (2, m * 1.677966102))
#             duration = dur_h + '.' + dur_m
#             data = {'name': self.description,
#                     'start_date' : project_task.start_date if project_task else '',
#                     'date': datetime.today(),
#                     'project_id': project_task.project_id.id,
#                     'task_id': project_task.id,
#                     'unit_amount': float(duration),
#                     'user_id': self._uid}
#             data_list.append((0, 0, data))
#             project_task.write({'state' : 'pause', 'timesheet_ids' : data_list,'pause_time' : p_time})
        if context.get('ok') and context.get('continue_task'):
            if project_task:
                project_task.write({'state' : 'continue', 'con_time' : p_time,'start_date' : start_date})
        if context.get('ok') and context.get('end_task'):
            for p in project_task.task_line:
                p.states = 'to_invoice'
            if project_task.start_time != False and project_task.con_time == False and project_task.restart_time == False:
                start_time = project_task.start_time
                endtime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.start_time), '%Y-%m-%d %H:%M:%S')
            if project_task.restart_time != False and project_task.con_time == False:
                start_time = project_task.restart_time
                endtime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.restart_time), '%Y-%m-%d %H:%M:%S')
            if project_task.con_time != False and project_task.restart_time== False:
                start_time = project_task.con_time
                endtime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.con_time), '%Y-%m-%d %H:%M:%S')
            if project_task.restart_time != False and project_task.con_time != False:
                start_time = project_task.restart_time
                endtime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.restart_time), '%Y-%m-%d %H:%M:%S')
            m , s = divmod(endtime_diff.total_seconds(), 60)
            h, m = divmod(m, 60)
            dur_h = (_('%0*d') % (2, h))
            dur_m = (_('%0*d') % (2, m * 1.677966102))
            duration = dur_h + '.' + dur_m
            data = {'name': self.description,
                    'date': datetime.now(),
                    'start_date' : start_time if project_task else '',
                    'project_id': project_task.project_id.id,
                    'task_id': project_task.id,
                    'unit_amount': float(duration),
                    'user_id': self._uid}
            data_list.append((0, 0, data))
            marivi_user_id = self.env['res.users'].search([('login','=', 'oroval.servicios.adm@gmail.com')])
            project_task.write({'state' : 'end', 'timesheet_ids' : data_list, 'user_id':marivi_user_id.id})
            get_task = [task.id for task in project_task.project_id.task_ids if task.state ==  'end' ]
            if set(project_task.project_id.task_ids.ids) == set(get_task):
                stage_id = stage_obj.search([('name','=','Finalizados')])
                if stage_id :
                    project_task.project_id.write({'stage_id' : stage_id.id})
        if context.get('ok') and context.get('stop_task'):
            if project_task.start_time != False and project_task.con_time == False and project_task.restart_time == False:
                start_time = project_task.start_time
                stoptime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.start_time), '%Y-%m-%d %H:%M:%S')
            if project_task.restart_time != False and project_task.con_time == False:
                start_time = project_task.restart_time
                stoptime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.restart_time), '%Y-%m-%d %H:%M:%S')
            if project_task.con_time != False and project_task.restart_time== False:
                start_time = project_task.con_time
                stoptime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.con_time), '%Y-%m-%d %H:%M:%S')
            if project_task.restart_time != False and project_task.con_time != False:
                start_time = project_task.restart_time
                stoptime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.restart_time), '%Y-%m-%d %H:%M:%S')
            if project_task.start_time == False and project_task.con_time == False and project_task.restart_time == False:
                start_time = p_time
                stoptime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S')
#             if project_task.pause_time != False and project_task.con_time == False and project_task.restart_time == False:
#                 stoptime_diff = datetime.strptime(str(p_time), '%Y-%m-%d %H:%M:%S') - datetime.strptime(str(project_task.pause_time), '%Y-%m-%d %H:%M:%S')
            m , s = divmod(stoptime_diff.total_seconds(), 60)
            h, m = divmod(m, 60)
            dur_h = (_('%0*d') % (2, h))
            dur_m = (_('%0*d') % (2, m * 1.677966102))
            duration = dur_h + '.' + dur_m
            data = {'name': self.description,
                    'date': datetime.now(),
                    'start_date' : start_time if project_task else '',
                    'project_id': project_task.project_id.id,
                    'task_id': project_task.id,
                    'unit_amount': float(duration),
                    'user_id': self._uid}
            data_list.append((0, 0, data))
            project_task.write({'state' : 'stop', 'timesheet_ids' : data_list})
        return True

# made new wizard for generate invoice of measurement lines           
class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    @api.model
    def _get_advance_payment_method(self):
        if self._count() == 1:
            sale_obj = self.env['sale.order']
            order = sale_obj.browse(self._context.get('active_ids'))[0]
            if all([line.product_id.invoice_policy == 'order' for line in order.order_line]) or order.invoice_count:
                return 'all'
        return 'delivered'
    
    advance_payment_method = fields.Selection([
        ('delivered', 'Invoiceable lines'),
        ('all', 'Invoiceable lines (deduct down payments)'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)'),
        ('measurement' , 'Down Payment (By Lines Of Finished Measurement)')
        ], string='What do you want to invoice?', default=_get_advance_payment_method, required=True)
    check_measurement_lines = fields.One2many('check.measurement.lines', 'wizard_line', string="Check Measurement Lines")
    sale_order_line = fields.One2many('sales.order.lines', 'wizard_sales_lines', string="Sale order Lines")
    
    @api.model
    def default_get(self, vals):
        res = super(SaleAdvancePaymentInv, self).default_get(vals)
        context = self._context
        sale_orders = self.env['sale.order'].browse(context.get('active_ids', []))
        line_vals = []
        sale_line_vals = []
        for i in sale_orders.order_line:
            if i.check_measurement_line:
                for j in i.check_measurement_line:
                    if j.states == 'to_invoice':
                        values = {  
                                'des_unit_measurement' :j.des_unit_measurement,
                                'length' :j.length,
                                'width' :j.width,
                                'height' :j.height,
                                'ud' :j.ud,
                                'measurement_result' :j.measurement_result,
                                'select_task' : False,
                                'line_id' : j.id
                                }
                        line_vals.append((0, 0, values))
                res.update({'check_measurement_lines' : line_vals})
            if not i.check_measurement_line:
                if i.invoice_status == 'to invoice':
                    project_lines = self.env['project.task'].search([('sale_line_id', '=', i.id)])
                    if project_lines:
                        if project_lines.state == 'end':
                                values = {  
                                        'product_id' :i.product_id.id,
                                        'layout_category_id' :i.layout_category_id.id,
                                        'name' :i.name,
                                        'product_uom_qty' :i.product_uom_qty,
                                        'product_uom' :i.product_uom.id,
                                        'price_unit' :i.price_unit,
                                        'purchase_price' : i.purchase_price,
                                        'tax_id' : i.tax_id.ids,
                                        'discount' : i.discount,
                                        'subtotoal' : i.price_subtotal,
                                        'select_line' : False,
                                        'sale_id' : i.id
                                        }
                                sale_line_vals.append((0, 0, values))
                                res.update({'sale_order_line' : sale_line_vals})
        return res
            
# create invoice method for measurement lines
    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        list_value = []
        line_values = {}
        order_line_dict = {}
        order_line_list = []
        line_vals = []
        for inv in self:
            if inv.advance_payment_method == 'measurement':  
                if inv.check_measurement_lines:
                    for k in inv.check_measurement_lines:
                        if k.select_task == True:
                            check_line_id = self.env['check.measurement.line'].search([('states', '=', 'to_invoice'), ('id', '=', k.line_id.id)])
                            for j in check_line_id:
                                if j.line_id.invoice_status == 'to invoice':
                                    j.states = 'done'
                                    order_line_list.append(j.line_id.id)
                                    if not j.line_id.id in order_line_dict:
                                        order_line_dict[j.line_id.id] = j.measurement_result
                                    else:
                                        order_line_dict[j.line_id.id] = order_line_dict[j.line_id.id] + j.measurement_result
                           
                    if len(order_line_list) > 0 :
                        line_id = self.env['sale.order.line'].search([('id', 'in', order_line_list)])
                        for i in line_id :
                            project_task = self.env['project.task'].search([('sale_line_id', '=', i.id)])
                            if project_task:
                                for p in project_task:
                                    if p.state == 'end':
                                        for j in inv.check_measurement_lines: 
                                            if j.select_task == True:
                                                if i.id == j.line_id.line_id.id:
                                                    p.active = False
                            line_vals = []
                            for lines in i.check_measurement_line:
                                values = {  
                                    'des_unit_measurement' :lines.des_unit_measurement,
                                    'length' :lines.length,
                                    'width' :lines.width,
                                    'height' :lines.height,
                                    'ud' :lines.ud,
                                    'measurement_result' :lines.measurement_result,
                                    }
                                if lines.states == 'done' :
                                    values.update({'states' : 'to_invoice'})
                                line_vals.append(values)
                            if i.id in order_line_dict:
                                i.invoice_status = 'invoiced'
                                name = i.product_id.name,
                                sale_name = i.product_id.description_sale 
                                if sale_name:
                                    name = sale_name.encode('utf8')
                                line_values = {'name': i.name.encode('utf8') or name ,
                                'origin': order.name,
                                'account_id': order.partner_id.property_account_receivable_id.id,
                                'price_unit': i.price_unit,
                                'quantity': order_line_dict[i.id],
                                'discount': 0.0,
                                'uom_id': i.product_uom.id,
                                'product_id': i.product_id.id,
                                'sale_line_ids': [(6, 0, [i.id])],
                                'invoice_line_tax_ids': [(6, 0, i.tax_id.ids)],
                                'account_analytic_id': order.project_id.id or False,
                                'check_product_uom': i.check_product_uom,
                                'check_measurement_line': [(0, 0, data) for data in line_vals],
                                    }
                                list_value.append(line_values)
                
                if inv.sale_order_line:
                    for j in inv.sale_order_line:
                        for i in order.order_line:
                            name = i.product_id.name,
                            sale_name = i.product_id.description_sale 
                            if sale_name:
                                name = sale_name.encode('utf8')
                            if i.invoice_status == 'to invoice':
                                if not i.check_measurement_line:
                                    project_lines = self.env['project.task'].search([('sale_line_id', '=', i.id)])
                                    if project_lines:
                                        for p in project_lines:
                                            if p.state == 'end': 
                                                if j.select_line == True:
                                                    if i.id == j.sale_id.id:
                                                        line_values = {'name':i.name.encode('utf8') or name ,
                                                                        'origin': order.name,
                                                                        'account_id': order.partner_id.property_account_receivable_id.id,
                                                                        'price_unit': i.price_unit,
                                                                        'quantity': i.product_uom_qty,
                                                                        'discount': 0.0,
                                                                        'uom_id': i.product_uom.id,
                                                                        'product_id': i.product_id.id,
                                                                        'sale_line_ids': [(6, 0, [i.id])],
                                                                        'invoice_line_tax_ids': [(6, 0, i.tax_id.ids)],
                                                                        'account_analytic_id': order.project_id.id or False,
                                                            }
                                                        list_value.append(line_values)
                if line_values:
                    if inv.check_measurement_lines:
                        invoice = inv_obj.create({
                                    'name': order.client_order_ref or order.name,
                                    'origin': order.name,
                                    'type': 'out_invoice',
                                    'reference': False,
                                    'account_id': order.partner_id.property_account_receivable_id.id,
                                    'partner_id': order.partner_invoice_id.id,
                                    'partner_shipping_id': order.partner_shipping_id.id,
                                    'invoice_line_ids': [(0, 0, data) for data in list_value],
                                    'currency_id': order.pricelist_id.currency_id.id,
                                    'payment_term_id': order.payment_term_id.id,
                                    'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
                                    'team_id': order.team_id.id,
                                    'user_id': order.user_id.id,
                                    'comment': order.note,
                                    'project_id' : order.project_project_id.id
                                })
                    else:
                        raise UserError(_("Please select atleast one line for Invoice."))
                    invoice.compute_taxes()
                    invoice.message_post_with_view('mail.message_origin_link',
                                values={'self': invoice, 'origin': order},
                                subtype_id=self.env.ref('mail.mt_note').id)
                    return invoice
            else:
                return super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)

# add new invoice method in accounting
    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if self.advance_payment_method == 'delivered':
            sale_orders.action_invoice_create()
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        elif self.advance_payment_method == 'measurement':
            for order in sale_orders:
                so_line = {}
                amount = order.amount_total
                self._create_invoice(order, so_line, amount)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.values'].sudo().set_default('sale.config.settings', 'deposit_product_id_setting', self.product_id.id)
 
            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                else:
                    tax_ids = taxes.ids
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, tax_ids)],
                })
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

class CheckMeasurementLines(models.TransientModel):
    _name = "check.measurement.lines"
    
    name = fields.Char("Name")
    wizard_line = fields.Many2one('sale.advance.payment.inv', string="Task Lines")
    des_unit_measurement = fields.Text('Description')  
    length = fields.Float('Long', default=1.0)  
    width = fields.Float('Width', default=1.0)   
    height = fields.Float('Height', default=1.0) 
    ud = fields.Float('UD' , default=1.0) 
    measurement_result = fields.Float('Measurement result partial 1')
    select_task = fields.Boolean("Select Task", default=False)
    line_id = fields.Many2one('check.measurement.line', string="line id")
    
class SalesOrderLines(models.TransientModel):
    _name = 'sales.order.lines'
    
    wizard_sales_lines = fields.Many2one('sale.advance.payment.inv', string="Wizard Lines")
    product_id = fields.Many2one('product.product', string="Product")
    layout_category_id = fields.Many2one('sale.layout_category')
    name = fields.Text(string="Description")
    product_uom_qty = fields.Float(string="Ordered Quantity")
    product_uom = fields.Many2one("product.uom", string="Unit Of Measure")
    price_unit = fields.Float(string="Unit Price")
    purchase_price = fields.Float(string="Cost")
    tax_id = fields.Many2many('account.tax', string="Taxes")
    discount = fields.Float(string="Discount")
    subtotoal = fields.Float(string="Subtotal")
    select_line = fields.Boolean(string="Select Line", default=False)
    sale_id = fields.Many2one('sale.order.line', string="Sale id")
    
