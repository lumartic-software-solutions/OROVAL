from odoo import api, models


#  sale order reports 
class ReportSaleReport(models.AbstractModel):
    _name = 'report.custom_oroval.custom_sale_template'
    
 
    @api.model
    def render_html(self, docids, data=None):
        sale_obj = self.env['sale.order'].browse(docids[0])
        self.model = self.env.context.get('active_model')
        user = self.env["res.users"].browse(self._uid)
        company_data = user.company_id
        data = {'custom_header':user.company_id.custom_header ,
                'header_text': company_data.header_text ,
                'custom_footer':  company_data.custom_footer,
                'footer_text': company_data.footer_text}
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': sale_obj,
            'data': data,
            'doc' :user,
        }
        return self.env['report'].render('custom_oroval.custom_sale_template', values=docargs)



