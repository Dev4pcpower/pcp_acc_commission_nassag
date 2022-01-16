from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime


class Commission_Invoice_Wizard(models.TransientModel):
    _name = "commission.invoice.wizard"
    _inherit = 'mail.thread'

    def create_invoice(self):
        active_ids = self.env.context.get('active_ids', [])
        sale_order = self.env['sale.order'].search([('name', '=', active_ids.invoice_origin)])
        commission_lines = self.env['commission.line'].search([('sale_order_id','=',sale_order.id)])
        account_invoice_line_obj = self.env['invoice.commission.line']
        for i in commission_lines:
                invoice_line_vals = {
                    'product_id_selected': i.product_id_selected.id,
                    'qty': i.qty,
                    'commission_value': i.commission_value,
                    'customer_sales_person':sale_order.customer_sales_person.id,
                    'total_commission_per_line': i.total_commission_per_line,
                    'total_commission_order': i.total_commission_order,
                }
        active_ids.write({'invoice_commission_line_id': ([(0, 0, invoice_line_vals)])})
