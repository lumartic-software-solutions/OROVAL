from odoo import api, fields, models, _, registry, SUPERUSER_ID
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
import threading
import datetime


class MailMessage(models.Model):
    _inherit = "mail.message"
    
#     Create task log in project
    @api.model
    def create(self, vals):
        res = super(MailMessage, self).create(vals)
        if 'model' in vals :
            if vals['model'] == 'project.task':
                if 'res_id' in vals:
                    task_id = self.env['project.task'].browse(vals.get('res_id'))
                    if task_id:
                        if task_id.project_id :
                            line_vals = []
                            if res.sudo().tracking_value_ids :
                                for   j in res.sudo().tracking_value_ids:
                                    values = {  
                                        'field' :j.field,
                                        'field_desc' :j.field_desc,
                                        'field_type' :j.field_type,
                                        'new_value_char' :j.new_value_char,
                                        #'mail_message_id' :res.id,
                                        }
                                    line_vals.append((0, 0, values))
                            task_id.project_id.message_post( body=vals.get('body', ''), tracking_value_ids=line_vals)
#                             self.env['mail.message'].create(
#                             {'res_id': task_id.project_id.id,
#                              'model': 'project.project',
#                              'subtype_id': vals.get('subtype_id'),
#                              'attachment_ids': [(6,0,res.attachment_ids.ids)] ,
#                               'message_id':res.id,
#                             'body': vals.get('body') or '',
#                              'tracking_value_ids': line_vals
#                              }
#                             )
        return res


class ResParner(models.Model):
    _inherit = "res.partner"
    
    @api.multi
    def custom_action_view_project_project(self):
        self.ensure_one()
        action = self.env.ref('project.open_view_project_all').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action.pop('target', None)
        return action
    
    @api.multi
    def _notify_by_email(self, message, force_send=False, send_after_commit=True, user_signature=True):
        """ Method to send email linked to notified messages. The recipients are
        the recordset on which this method is called.

        :param boolean force_send: send notification emails now instead of letting the scheduler handle the email queue
        :param boolean send_after_commit: send notification emails after the transaction end instead of durign the
                                          transaction; this option is used only if force_send is True
        :param user_signature: add current user signature to notification emails """
        if not self.ids:
            return True

        # existing custom notification email
        base_template = None
        if message.model and self._context.get('custom_layout', False):
            base_template = self.env.ref(self._context['custom_layout'], raise_if_not_found=False)
        if not base_template:
            base_template = self.env.ref('mail.mail_template_data_notification_email_default')

        base_template_ctx = self._notify_prepare_template_context(message)
        if not user_signature:
            base_template_ctx['signature'] = False
        base_mail_values = self._notify_prepare_email_values(message)

        # classify recipients: actions / no action
        if message.model and message.res_id and hasattr(self.env[message.model], '_message_notification_recipients'):
            recipients = self.env[message.model].browse(message.res_id)._message_notification_recipients(message, self)
        else:
            recipients = self.env['mail.thread']._message_notification_recipients(message, self)

        emails = self.env['mail.mail']
        recipients_nbr, recipients_max = 0, 50
        for email_type, recipient_template_values in recipients.iteritems():
            if recipient_template_values['followers']:
                # generate notification email content
                template_fol_values = dict(base_template_ctx, **recipient_template_values)  # fixme: set button_unfollow to none
                template_fol_values['has_button_follow'] = False
                template_fol = base_template.with_context(**template_fol_values)
                # generate templates for followers and not followers
                fol_values = template_fol.generate_email(message.id, fields=['body_html', 'subject'])
                # send email
                new_emails, new_recipients_nbr = self._notify_send(fol_values['body'], fol_values['subject'], recipient_template_values['followers'], **base_mail_values)
                # update notifications
                self._notify_udpate_notifications(new_emails)

                emails |= new_emails
                recipients_nbr += new_recipients_nbr
            if recipient_template_values['not_followers']:
                # generate notification email content
                template_not_values = dict(base_template_ctx, **recipient_template_values)  # fixme: set button_follow to none
                template_not_values['has_button_unfollow'] = False
                template_not = base_template.with_context(**template_not_values)
                # generate templates for followers and not followers
                not_values = template_not.generate_email(message.id, fields=['body_html', 'subject'])
                # send email
                new_emails, new_recipients_nbr = self._notify_send(not_values['body'], not_values['subject'], recipient_template_values['not_followers'], **base_mail_values)
                # update notifications
                self._notify_udpate_notifications(new_emails)

                emails |= new_emails
                recipients_nbr += new_recipients_nbr

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        test_mode = getattr(threading.currentThread(), 'testing', False)
        if force_send and recipients_nbr < recipients_max and \
                (not self.pool._init or test_mode):
            email_ids = emails.ids
            dbname = self.env.cr.dbname
            _context = self._context
            if _context.get('default_model') != 'project.task':

		        def send_notifications():
		            db_registry = registry(dbname)
		            with api.Environment.manage(), db_registry.cursor() as cr:
		                env = api.Environment(cr, SUPERUSER_ID, _context)
		                env['mail.mail'].browse(email_ids).send()

		        # unless asked specifically, send emails after the transaction to
		        # avoid side effects due to emails being sent while the transaction fails
		        if not test_mode and send_after_commit:
		            self._cr.after('commit', send_notifications)
		        else:
		            emails.send()

        return True

    
#  Project Stage 
class ProjectStage(models.Model):
    _name = "project.stage"  
    
    name = fields.Char(string='Name')
    fold = fields.Boolean(string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')
    
    
#  Project Method
class Project(models.Model):
    _name = "project.project"
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'project.project']
    
    #  Compute Invoice Status Method
    @api.multi
    def _compute_invoice_status (self):
        for inv in self:
            invoice_id = self.env['account.invoice'].search([('project_id', '=', inv.id)])
            if len(invoice_id) >= 1:
                inv.invoice_status = 'invoiced'
            else:
                inv.invoice_status = 'no'
                
    # compute total no of sales order in re
    @api.one
    def _compute_count_sales(self):
        if self.analytic_account_id :
            order_id = self.env['sale.order'].search([('project_id', '=', self.analytic_account_id.id)])
            if order_id :
                total = 0
                for rec in order_id : 
                    total += 1
                self.count_sales = total
            else:
                self.count_sales = 0
    
    count_sales = fields.Integer(
        string='Number of sales',
        readonly=True, compute='_compute_count_sales')
    invoice_status = fields.Selection([
        ('invoiced', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Invoice Status', compute="_compute_invoice_status" , readonly=True)
    stage_id = fields.Many2one('project.stage', string='Stage', track_visibility='onchange', index=True,
        group_expand='_read_group_stage_ids')
    partner_shipping_id = fields.Many2one("res.partner", string="Work Address")
    phone = fields.Char('Phone', related="partner_shipping_id.phone")
    mobile = fields.Char('Mobile', related="partner_shipping_id.mobile")
    street = fields.Char('Street', related="partner_shipping_id.street")
    street2 = fields.Char('Street2', related="partner_shipping_id.street2")
    zip = fields.Char('Zip', related="partner_shipping_id.zip")
    city = fields.Char('City', related="partner_shipping_id.city")
    state_id = fields.Many2one("res.country.state", related="partner_shipping_id.state_id" , string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', related="partner_shipping_id.country_id" , string='Country', ondelete='restrict')
    job_position = fields.Char(related="partner_shipping_id.function", string="Job Position")
    
    @api.onchange('partner_shipping_id')
    def onchange_partner_shipping_id(self):
        if self.partner_shipping_id:
            if self.partner_shipping_id.parent_id:
                self.partner_id = self.partner_shipping_id.parent_id.id
            else:
                self.partner_id = self.partner_shipping_id.id
       
    # details of order using smart button in project
    @api.multi      
    def sale_order_details(self):
        action = self.env.ref('sale.action_orders').read()[0]
        if self.analytic_account_id :
            order_id = self.env['sale.order'].search([('project_id', '=', self.analytic_account_id.id)])
            if len(order_id.ids) == 1 :
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "sale.order",
                    "views": [[False, "form"]],
                    "res_id": order_id.id,
                }
            elif len(order_id.ids) >= 1 :
                action['domain'] = [('id', 'in', [order.id for order in  order_id])]
                return action
            else:
                action['domain'] = [('id', '=', False)]
                return action
    
    #  fold kanban method
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('fold', '=', False)]
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
    
    #  View Invoice Method
    @api.multi
    def view_project_invoice(self):
        invoice_id = self.env['account.invoice'].search([('project_id', '=', self.id)])
        action = self.env.ref('account.action_invoice_tree').read()[0]
        if len(invoice_id) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoice_id.id
        elif len(invoice_id) > 1:
            action['domain'] = [('id', 'in', invoice_id.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    #   For open Project form view from kanban
    @api.multi
    def view_project_project(self):
        project_id = self.env['project.project'].search([('id', '=', self.id)])
        action = self.env.ref('custom_oroval.custom_oroval_view_project_all').read()[0]
        if project_id:
            action['views'] = [(self.env.ref('project.edit_project').id, 'form')]
            action['res_id'] = project_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    #  Add Followers when project created and set stage id Method
    @api.model
    def create(self, vals):
        stage_id = self.env['project.stage'].search([('name', '=', 'Nuevo')], limit=1)
        if stage_id :
            vals.update({'stage_id' : stage_id.id})
        res = super(Project, self).create(vals)
        user_login_list = ['Tony', 'Marivi', 'Marcos']
        user_list = []
        for rec in user_login_list : 
            user_id = self.env['res.users'].search([('name', '=', rec)])
            if user_id:
                user_list.append(user_id.partner_id.id)
        mail_invite = self.env['mail.wizard.invite'].with_context({
            'default_res_model': 'project.project',
            'default_res_id': res.id
        }).create({
            'partner_ids': [(6, 0, user_list)],
            'send_mail': True})
        mail_invite.add_followers()
        return res

        
class ProductTemplate(models.Model):
    _inherit = "product.template"
    _order = "default_code"
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True): 
        if 'categ_id' in groupby:
            orderby = 'default_code ASC' + (orderby and (',' + orderby) or '')
        return super(ProductTemplate, self).read_group(domain, fields, groupby, offset=0, limit=limit, orderby=orderby, lazy=lazy)
    
    work_hours = fields.Float(string='Work Hours')


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    internal_note = fields.Text('Internal Note', related="opportunity_id.description")
    
#     Set Customer Reference In Sale Order 
    @api.model
    def default_get(self, vals):
        default_get_res = super(SaleOrder, self).default_get(vals)
        context = self._context
        if context.get('default_opportunity_id', ""):
            crm_id = self.env['crm.lead'].search([('id', '=', context['default_opportunity_id'])])
            default_get_res.update({'client_order_ref': crm_id.name})
        if context.get('active_model', False) == "project.project":
            project_obj = self.env['project.project'].search([('id', '=', context['active_id'])])
            if project_obj:
                default_get_res.update({'partner_id':project_obj.partner_id.id, 'project_id':project_obj.analytic_account_id.id})
        return default_get_res
    
    # set new template in mail
    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('custom_oroval', 'sale_send_email_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "sale.mail_template_data_notification_email_sale_order"
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
    
    @api.multi
    @api.onchange('pricelist_id', 'order_line')
    def onchange_pricelist_id(self):
        if self.pricelist_id:
            if self.order_line:
                for line in self.order_line:
                    if line.order_id.pricelist_id and line.order_id.partner_id:
                        product = line.product_id.with_context(
                            lang=line.order_id.partner_id.lang,
                            partner=line.order_id.partner_id.id,
                            quantity=line.product_uom_qty,
                            date=line.order_id.date_order,
                            pricelist=line.order_id.pricelist_id.id,
                            uom=line.product_uom.id,
                            fiscal_position=self.env.context.get('fiscal_position')
                        )
                        line.price_unit = self.env['account.tax']._fix_tax_included_price(line._get_display_price(product), product.taxes_id, line.tax_id)
    
    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        count = 0
        for i in res.order_line:
            count += 1
            i.sequence = count
            values = {} 
            line_vals = []
            for j in i.check_measurement_line:
                values = {  
                    'des_unit_measurement' :j.des_unit_measurement,
                    'length' :j.length,
                    'width' :j.width,
                    'height' :j.height,
                    'ud' :j.ud,
                    'measurement_result' :j.measurement_result,
                    }
                line_vals.append((0, 0, values))
            line_obj = self.env['sale.order.line']
            if i.related_product:
                for p in i.related_product: 
                    count += 1
                    group_id = False     
                    data = {
                        'name': p.name,
                        'order_id':res.id,
                        'product_id': p.id,
                        'product_uom_qty': i.product_uom_qty,
                        'product_uom': i.product_uom.id,
                        'company_id': i.order_id.company_id.id,
                        'group_id': group_id,
                        'check_product_uom': i.check_product_uom,
                        'check_measurement_line': line_vals,
                        'sequence' : count,
			'price_unit' : p.lst_price,
                        'pricelist_id' : self.pricelist_id.id
                        }
                    line_obj.create(data)
        return res
    
    @api.multi
    def write(self, values):
        if values.get('order_line'):
            reserved = []
            related = []
            for rec in self.order_line:
                reserved.append(rec.id)
                if rec.related_product:
                    for p in rec.related_product:
                        related.append(p.id)
            res = super(SaleOrder, self).write(values)
            if values.get('order_line'):
                count = 0
                for i in self.order_line:
                    count += 1
                    i.sequence = count
                    
                    if i.id in reserved or i.id not in related:
                        values = {} 
                        line_vals = []
                        for j in i.check_measurement_line:
                            values = {  
                                'des_unit_measurement' :j.des_unit_measurement,
                                'length' :j.length,
                                'width' :j.width,
                                'height' :j.height,
                                'ud' :j.ud,
                                'measurement_result' :j.measurement_result,
                                }
                            line_vals.append((0, 0, values))
                        line_obj = self.env['sale.order.line']
                        if i.related_product:
                            
                            for p in i.related_product:
                                if p.id not in related:
                                    count += 1
                                    group_id = False     
                                    data = {
                                        'name': p.name,
                                        'order_id':self.id,
                                        'product_id': p.id,
                                        'product_uom_qty': i.product_uom_qty,
                                        'product_uom': i.product_uom.id,
                                        'company_id': i.order_id.company_id.id,
                                        'group_id': group_id,
                                        'check_product_uom': i.check_product_uom,
                                        'check_measurement_line': line_vals,
                                        'sequence' : count,
                                        'price_unit' : p.lst_price,
                                        'pricelist_id' : self.pricelist_id.id
                                        }
                                    line_obj.create(data)
            return res
        else:
            res = super(SaleOrder, self).write(values)
            return res

    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        if self.env['report'].get_action(self, 'custom_oroval.custom_sale_template'):
            return self.env['report'].get_action(self, 'custom_oroval.custom_sale_template')
        else:
            return self.env['report'].get_action(self, 'sale.report_saleorder')

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        ctx = self._context
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return
        if ctx.get('default_partner_shipping_id'):
            addr = self.partner_id.address_get(['delivery', 'invoice'])
            values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': ctx.get('default_partner_shipping_id'),
            }
        else:
            addr = self.partner_id.address_get(['delivery', 'invoice'])
            values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            }
        if self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.user_id:
            values['user_id'] = self.partner_id.user_id.id
        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)

        
#                      
# Set Measurement  In Sale Order Line           
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"  

    # Compute Total Result 
    @api.depends('check_measurement_line.measurement_result')
    @api.multi
    def _total_result(self):
        for order in self:
            order.result = 0.0
            for line in order.check_measurement_line:
                order.result += line.measurement_result
                
    @api.depends('check_measurement_line.measurement_result')
    @api.multi
    def _compute_total_ud(self):
        for order in self:
            order.total_ud = 0.0
            for line in order.check_measurement_line:
                order.total_ud += line.ud
     
    check_product_uom = fields.Boolean('Check Product Uom', default=False, implied_group='custom_oroval.check_measurement_line')  
    check_measurement_line = fields.One2many('check.measurement.line', 'line_id', string="Measurement", copy=True)
    result = fields.Float('Result', compute="_total_result")  
    work_hours = fields.Float(string='Work Hours')
    total_ud = fields.Float("Total UD", compute="_compute_total_ud")
    related_product = fields.Many2many('product.product', string="Related Product")
    check_measurement = fields.Char("Check Measurement")
    product_type = fields.Selection(related='product_id.type', string="Product Type")

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.result:
            res.update({'product_uom_qty': res.result})
        return res
    
    @api.multi
    def write(self, vals):
        if self.result:
            vals.update({'product_uom_qty' : self.result})
        res = super(SaleOrderLine, self).write(vals)
        return res
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return 
        else:
            if self.product_id.type == 'service':
                self.work_hours = self.product_id.work_hours
            else:
                self.work_hours = 0.00
        if not self.order_id:
            return
        part = self.order_id.partner_id
        if not part:
            warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a partner!'),
                }
            return {'warning': warning}
    
# Set Order Quantity
    @api.multi
    @api.onchange('result')
    def onchange_result(self):
        self.product_uom_qty = self.result 
    
# Set Product Uom  for Measurement  
    @api.multi
    @api.onchange('product_uom')
    def onchange_product_uom(self):
        if self.product_uom:
            self.check_measurement = self.product_uom.name
            if  self.product_uom.name == 'ud' or self.product_uom.name == 'Unidad' or self.product_uom.name == 'Unidad(s)' or  self.product_uom.name == 'Hours' or self.product_uom.name == 'Units' or self.product_uom.name == 'Hour(s)' or self.product_uom.name == 'Unit(s)' or self.product_uom.name == 'm' or self.product_uom.name == 'ml'  or self.product_uom.name == 'm3' or self.product_uom.name == 'm2' or self.product_uom.name == 'm2l' or self.product_uom.name == 'm2L'or  self.product_uom.name == 'Horas' or self.product_uom.name == 'Hora(s)':
                self.check_product_uom = True
            else:
                self.check_product_uom = False
                
# Set Check Measurement Line  In Invoice Line     
    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % 
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)
        line_vals = []
        for lines in self.check_measurement_line:
            values = {  'des_unit_measurement' :lines.des_unit_measurement,
                        'length' :lines.length,
                        'width' :lines.width,
                        'height' :lines.height,
                        'ud' :lines.ud,
                        'measurement_result' :lines.measurement_result,
                                    }
            line_vals.append(values)
        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.project_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'check_product_uom': self.check_product_uom,
            'check_measurement_line': [(0, 0, data) for data in line_vals],
        }
        return res

    
# Check Measurement Line  To Set Multiple  Measurement 
class CheckMeasurementLine(models.Model):
    _name = 'check.measurement.line'  
         
    line_id = fields.Many2one('sale.order.line', string='Order lines')
    invoice_line_id = fields.Many2one('account.invoice.line', string='Invoice lines')
    des_unit_measurement = fields.Text('Description')  
    length = fields.Float('Long', default=1.0)  
    width = fields.Float('Width', default=1.0)   
    height = fields.Float('Height', default=1.0) 
    ud = fields.Float('UD' , required=True, default=1.0) 
    measurement_result = fields.Float('Measurement result partial 1')
    custom = fields.Char('custom', default=lambda self: self._context.get('check_uom'))
    states = fields.Selection([('draft', 'Draft'), ('to_invoice', 'To be Invoice'), ('done', 'Done')], string='Status')
    
# Calculate Measurement  
    @api.multi
    @api.onchange('length', 'height', 'width', 'ud')
    def onchange_measurement(self):
        if not self.length or not self.height or not self.width:
            self.measurement_result = 0.0 
        else:
            values = {
                'measurement_result': self.length * self.height * self.width * self.ud or 0.0,
            }
            self.update(values)
        return {}

    
class AccountInvoiceLines(models.Model):
    _inherit = 'account.invoice.line'
    
    @api.depends('check_measurement_line.measurement_result')
    @api.multi
    def _total_resultinvoice(self):
        for i in self:
            i.results = 0.0
            for l in i.check_measurement_line:
                i.results += l.measurement_result
                
    @api.depends('check_measurement_line.measurement_result')
    @api.multi
    def _compute_total_ud(self):
        for order in self:
            order.total_ud = 0.0
            for line in order.check_measurement_line:
                order.total_ud += line.ud
        
    check_product_uom = fields.Boolean('Check Product Uom', default=False)  
    check_measurement_line = fields.One2many('check.measurement.line', 'invoice_line_id', string="Measurement", copy=True)
    total_ud = fields.Float("Total UD", compute="_compute_total_ud")
    results = fields.Float('Result', compute="_total_resultinvoice")
    check_measurement = fields.Char("Check Mesurement")
    product_type = fields.Selection(related='product_id.type', string="Product Type")

    # Set Product Uom  for Measurement In Invoice Line
    @api.multi
    @api.onchange('uom_id')
    def onchange_product_uom(self):
        if  self.uom_id :
            self.check_measurement = self.uom_id.name
            if self.uom_id.name == 'ud' or self.uom_id.name == 'Unidad' or self.uom_id.name == 'Unidad(s)' or self.uom_id.name == 'Hours' or self.uom_id.name == 'Units' or self.uom_id.name == 'Hour(s)' or self.uom_id.name == 'Unit(s)' or self.uom_id.name == 'm' or self.uom_id.name == 'ml'  or self.uom_id.name == 'm3' or self.uom_id.name == 'm2' or self.uom_id.name == 'm2l' or self.uom_id.name == 'm2L' or self.uom_id.name == 'Horas' or self.uom_id.name == 'Hora(s)':
                self.check_product_uom = True
            else:
                self.check_product_uom = False

    @api.multi
    @api.onchange('results')
    def onchange_results(self):
        self.quantity = self.results 

 
# add start date field
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    start_date = fields.Datetime(string="Start Date")
    date = fields.Datetime('End Date', required=True, index=True, default=datetime.datetime.now())
    
       
# set customer reference in project
class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    @api.multi
    def project_create(self, vals):
        '''
        This function is called at the time of analytic account creation and is used to create a project automatically linked to it if the conditions are meet.
        '''
        self.ensure_one()
        Project = self.env['project.project']
        sale_id = self.env['sale.order'].search([('name', '=', vals.get('name'))])
        project = Project.with_context(active_test=False).search([('analytic_account_id', '=', self.id)])
        if not project and self._trigger_project_creation(vals):
            project_values = {
                'name': sale_id.client_order_ref or " ",
                'analytic_account_id': self.id,
                'use_tasks': True,
		'partner_shipping_id': sale_id.partner_shipping_id.id,
			
            }
            return Project.create(project_values).id
        return False


# set planned hours  in project task and create task of measurement lines
class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'
    
    def _create_service_task(self):
        project = self._get_project()
        planned_hours = self._convert_qty_company_hours()
        for j in self.sale_line_id:
            if j.check_measurement_line:
                for i in j.check_measurement_line:
                    task = self.env['project.task'].create({
                        'name': i.des_unit_measurement + "  -  " + j.product_id.name if i.des_unit_measurement else 'Measurement Line  -  ' + j.product_id.name,
                        'date_deadline': self.date_planned,
                        'planned_hours': (j.product_uom_qty * j.work_hours) or planned_hours,
                        'remaining_hours': planned_hours,
                        'partner_id': j.order_id.partner_id.id or self.partner_dest_id.id,
                        'user_id': j.order_id.user_id.id,
                        'procurement_id': self.id,
                        'description': self.name + '<br/>',
                        'project_id': project.id,
                        'company_id': self.company_id.id,
                        'task_line' : i.id,
                        'ud' : i.ud,
                        'length' : i.length,
			'partner_shipping_id':j.order_id.partner_shipping_id.id,
                        'width' : i.width,
                        'height' : i.height,
                        'measurement_result' : i.measurement_result,
                        'description_pad' : j.name,
                        'state':'draft'
                    })
                self.write({'task_id' : task.id})
                msg_body = _("Task Created (%s): <a href=# data-oe-model=project.task data-oe-id=%d>%s</a>") % (self.product_id.name, task.id, task.name)
                self.message_post(body=msg_body)
                if self.sale_line_id.order_id:
                    self.sale_line_id.order_id.message_post(body=msg_body)
                    task_msg = _("This task has been created from: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a> (%s)") % (self.sale_line_id.order_id.id, self.sale_line_id.order_id.name, self.product_id.name)
                    task.message_post(body=task_msg)
                return task
            else:
                res = super(ProcurementOrder, self)._create_service_task()
                return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    project_id = fields.Many2one('project.project', string='Project')
    tasks_ids = fields.Many2many('project.task', compute='_compute_tasks_ids', string='Tasks associated to this sale')
    tasks_count = fields.Integer(string='Tasks', compute='_compute_tasks_ids')
    
    timesheet_ids = fields.Many2many('account.analytic.line', compute='_compute_timesheet_ids', string='Timesheet activities associated to this sale')
    timesheet_count = fields.Float(string='Timesheet activities', compute='_compute_timesheet_ids')
    
    @api.multi
    @api.depends('project_id')
    def _compute_timesheet_ids(self):
        for order in self:
            if order.project_id:
                order.timesheet_ids = self.env['account.analytic.line'].search(
                    [('project_id', '=', order.project_id.id)])
            else:
                order.timesheet_ids = []
            order.timesheet_count = len(order.timesheet_ids)
    
    @api.multi
    @api.depends('project_id')
    def _compute_tasks_ids(self):
        for order in self:
            if order.project_id:
                order.tasks_ids = self.env['project.task'].search([('project_id', '=', order.project_id.id), ('active', '=', False)])
                order.tasks_count = len(order.tasks_ids)
    
    @api.multi
    def custom_action_view_task(self):
        self.ensure_one()
        action = self.env.ref('project.action_view_task')
        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[False, 'kanban'], [list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'calendar'], [False, 'pivot'], [False, 'graph']],
            'target': action.target,
            'context': "{'group_by':'stage_id'}",
            'res_model': action.res_model,
        }
        if len(self.tasks_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % self.tasks_ids.ids
        elif len(self.tasks_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = self.tasks_ids.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
        
    @api.multi
    def custom_action_view_project_project(self):
        self.ensure_one()
        action = self.env.ref('project.open_view_project_all').read()[0]
        form_view_id = self.env.ref('project.edit_project').id
        action['views'] = [(form_view_id, 'form')]
        if self.project_id:
            action['res_id'] = self.project_id.id
        action.pop('target', None)
        return action
    
    @api.multi
    def custom_action_view_timesheet(self):
        self.ensure_one()
        action = self.env.ref('hr_timesheet.act_hr_timesheet_line')
        list_view_id = self.env.ref('hr_timesheet.hr_timesheet_line_tree').id
        form_view_id = self.env.ref('hr_timesheet.hr_timesheet_line_form').id

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if self.timesheet_count > 0:
            result['domain'] = "[('id','in',%s)]" % self.timesheet_ids.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    @api.multi
    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('custom_oroval.account_email_template_invoice', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="account.mail_template_data_notification_email_account_invoice",
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        context = self._context
        res.compute_taxes()
        count = 0
        line_obj = self.env['account.invoice.line']
        for i in res.invoice_line_ids:
            count += 1
            i.sequence = count
            values = {} 
            line_vals = []
            if i.check_measurement_line :
                account = i.product_id.property_account_income_id or i.product_id.categ_id.property_account_income_categ_id
                if not account:
                    raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % 
                                    (i.product_id.name, i.product_id.id, i.product_id.categ_id.name))
                for j in i.check_measurement_line:
                    values = {  
                        'des_unit_measurement' :j.des_unit_measurement,
                        'length' :j.length,
                        'width' :j.width,
                        'height' :j.height,
                        'ud' :j.ud,
                        'measurement_result' :j.measurement_result,
                        }
                    line_vals.append((0, 0, values))
                if line_vals :
                    data = {
                        'name': i.name,
                        'sequence': count,
                        'origin': i.invoice_id.id,
                        'account_id': account.id,
                        'price_unit': i.price_unit,
                        'quantity': i.quantity,
                        'discount': i.discount,
                        'uom_id': i.uom_id.id,
                        'product_id': i.product_id.id or False,
                        'check_product_uom': i.check_product_uom,
                        'check_measurement_line': line_vals,
                        }
                    line_obj.create(data)
        return res

    @api.multi
    def write(self, values):
        if values.get('invoice_line_ids'):
            reserved = []
            for rec in self.invoice_line_ids:
                reserved.append(rec.id)
        res = super(AccountInvoice, self).write(values)
        count = 0
        line_obj = self.env['account.invoice.line']
        if values.get('invoice_line_ids'):
            for i in self.invoice_line_ids:
                count += 1
                i.sequence = count
                values = {} 
                line_vals = []
                if i.check_measurement_line :
                    account = i.product_id.property_account_income_id or i.product_id.categ_id.property_account_income_categ_id
                    if not account:
                        raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % 
                                (i.product_id.name, i.product_id.id, i.product_id.categ_id.name))
                    for j in i.check_measurement_line:
                        values = {  
                            'des_unit_measurement' :j.des_unit_measurement,
                            'length' :j.length,
                            'width' :j.width,
                            'height' :j.height,
                            'ud' :j.ud,
                            'measurement_result' :j.measurement_result,
                            }
                        line_vals.append((0, 0, values))
                    if line_vals :
                        data = {
                            'name': i.name,
                            'sequence': count,
                            'origin': i.invoice_id.id,
                            'account_id': account.id,
                            'price_unit': i.price_unit,
                            'quantity': i.quantity,
                            'discount': i.discount,
                            'uom_id': i.uom_id.id,
                            'product_id': i.product_id.id or False,
                            'check_product_uom': i.check_product_uom,
                            'check_measurement_line': line_vals,
                            }
                        line_obj.create(data)
        return res

    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        if self.env['report'].get_action(self, 'custom_oroval.custom_invoice_template'):
            return self.env['report'].get_action(self, 'custom_oroval.custom_invoice_template')
        else:
            return self.env['report'].get_action(self, 'account.report_invoice')


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    related_id = fields.Many2one('sale.order.line')

    
class CrmPhonecall(models.Model):
    _inherit = "crm.phonecall"
    
    task_id = fields.Many2one(
        'project.task',
        string='Task',
    )
    event_id = fields.Many2one(
        'calendar.event',
        string='Event',
    )
    alarm_ids = fields.Many2many(
        'calendar.alarm',
        string='Reminders',
    )
    
    #  Set Contract 
    @api.model
    def default_get(self, vals):
        res = super(CrmPhonecall, self).default_get(vals)
        context = self._context
        if 'default_task_id' in  context:
            task_id = self.env['project.task'].browse(context['default_task_id'])
            if task_id:
                res.update({'partner_id': task_id.partner_id.id or False})
        return res
    
    @api.model
    def create(self, vals):
        res = super(CrmPhonecall, self).create(vals)
        if res.task_id :
            date = vals.get('date', '')
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
                    'phonecall_id':res.id,
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
        return res

    
#  manage timing fields with task
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    @api.one
    def _compute_partner_access(self):
        if self.user_has_groups('project.group_project_manager'):
            self.partner_access = False
        else :
            self.partner_access = True
    
    job_position = fields.Char(related="partner_shipping_id.function", string="Job Position")
    start_date = fields.Date(string="Start Date")
    partner_access = fields.Boolean('Partner Access', compute='_compute_partner_access') 
    customer = fields.Char('Customer Name', related="partner_id.name")   
    address = fields.Char('Street', related="partner_shipping_id.street")
    street2 = fields.Char('Street2', related="partner_shipping_id.street2")
    zip = fields.Char('Zip', related="partner_shipping_id.zip")
    city = fields.Char('City', related="partner_shipping_id.city")
    state_id = fields.Many2one("res.country.state", related="partner_shipping_id.state_id" , string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', related="partner_shipping_id.country_id" , string='Country', ondelete='restrict')
    phone = fields.Char('Phone', related="partner_shipping_id.phone")  
    mobile = fields.Char('Mobile', related="partner_shipping_id.mobile")          
    email = fields.Char('Email', related="partner_shipping_id.email") 
    partner_shipping_id = fields.Many2one("res.partner", string="Work Address")         
    task_line = fields.Many2one('check.measurement.line', string="Task Line")
    start_time = fields.Datetime("Start Time")
#     pause_time = fields.Datetime("Pause Time")
    con_time = fields.Datetime("Continue Time")
    end_time = fields.Datetime("End Time")
    restart_time = fields.Datetime("Restart Time")
    state = fields.Selection([('draft', 'New'), ('start', 'Start'), ('continue', 'Continue'), ('end', 'End'), ('stop', 'Stop')], string='Status', default='draft')
    length = fields.Float('Long')  
    width = fields.Float('Width')   
    height = fields.Float('Height') 
    ud = fields.Float('UD') 
    internal_note = fields.Text('Internal Notes', related="sale_line_id.order_id.internal_note")
    measurement_result = fields.Float('Measurement result partial 1')
    invoice_status = fields.Selection([
        ('invoiced', 'Invoiced'),
        ('no', 'Nothing To Invoice')
        ], string='Invoice Status', default='no', readonly=True)
    task_phonecall_count = fields.Integer(
        compute='_compute_task_phonecall_count',
        string="Phone calls",
    )


    @api.model
    def default_get(self, field_list):
        """ Set 'date_assign' if user_id is set. """
        ctx =self._context
        result = super(ProjectTask, self).default_get(field_list)
        if 'user_id' in result:
            result['date_assign'] = fields.Datetime.now()
        if ctx.get('active_id'):
            project_search = self.env['project.project'].browse(ctx.get('active_id'))
            if project_search:
                result['partner_shipping_id'] = project_search[0].partner_shipping_id.id
        return result
    
    @api.onchange('partner_shipping_id')
    def onchange_partner_shipping_id(self):
        if self.partner_shipping_id:
            if self.partner_shipping_id.parent_id:
                self.partner_id = self.partner_shipping_id.parent_id.id
            else:
                self.partner_id = self.partner_shipping_id.id

    @api.multi
    def _compute_task_phonecall_count(self):
        for task in self:
            task.task_phonecall_count = self.env[
                'crm.phonecall'].search_count(
                [('task_id', '=', task.id)])
    
    @api.multi
    def stop_task(self):
        context = self._context
        if context.get('stop_task'):
            for i in self:
                i.write({'state' : 'stop'})
               

class Layoutsale(models.Model):
    _inherit = "sale.layout_category"
    
    active_categ = fields.Boolean(string='Active')


class CrmLead(models.Model):
    _inherit = "crm.lead"
    
    new_date_action = fields.Datetime(string='Next Activity Date')
    partner_shipping_id = fields.Many2one('res.partner', string='Work Address')
    job_position = fields.Char(related="partner_shipping_id.function", string="Job Position")
    
    @api.onchange('partner_shipping_id')
    def onchange_partner_id(self):
        if self.partner_shipping_id.parent_id:
            self.partner_id = self.partner_shipping_id.parent_id.id
        else:
            self.partner_id = self.partner_shipping_id.id


class ActivityLog(models.TransientModel):
    _inherit = "crm.activity.log"
    
    new_date_action = fields.Datetime(string='Next Activity Date')
    
    @api.multi
    def action_schedule(self):
        for log in self:
            log.lead_id.write({
                'title_action': log.title_action,
                'date_action': log.new_date_action,
                'next_activity_id': log.next_activity_id.id,
                'new_date_action' : log.new_date_action,
                'disable' :False
            })
        return True
    
    @api.multi
    def action_log(self):
        for log in self:
            body_html = "<div><b>%(title)s</b>: %(next_activity)s</div>%(description)s%(note)s" % {
                'title': _('Activity Done'),
                'next_activity': log.next_activity_id.name,
                'description': log.title_action and '<p><em>%s</em></p>' % log.title_action or '',
                'note': log.note or '',
            }
            log.lead_id.message_post(body_html, subject=log.title_action, subtype_id=log.next_activity_id.subtype_id.id)
            log.lead_id.write({
                'date_deadline': log.date_deadline,
                'planned_revenue': log.planned_revenue,
                'title_action': False,
                'date_action': False,
                'next_activity_id': False,
                'new_date_action' : False,
            })
        return True
    
    @api.onchange('lead_id')
    def onchange_lead_id(self):
        self.next_activity_id = self.lead_id.next_activity_id
        self.date_deadline = self.lead_id.date_deadline
        self.team_id = self.lead_id.team_id
        self.planned_revenue = self.lead_id.planned_revenue
        self.title_action = self.lead_id.title_action
        self.new_date_action = self.lead_id.new_date_action
                
