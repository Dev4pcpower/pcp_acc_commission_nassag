from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime


class Commission_Invoice_Wizard(models.TransientModel):
    _name = "commission.invoice.wizard"
    _inherit = 'mail.thread'

    def create_invoice(self):

        active_ids = self.env.context.get('active_ids', [])
        commission_lines = self.env['commission.line'].search([('sale_order_id','=',active_ids)])
        list_of_ids = []
        lab_req_obj = self.env['commission.line']
        account_invoice_obj = self.env['account.move']
        account_invoice_line_obj = self.env['invoice.commission.line']
        sale_order = self.env['sale.order'].search([('id','=',active_ids)])

        for active_id in commission_lines:
            lab_req = self.env['commission.line'].search([('sale_order_id','=',active_ids)])
            total = 0
            for rec in lab_req:
                total += rec.qty * rec.commission_value
            for i in lab_req:
                i.validity_status = 'invoice'
                if not i.is_invoiced:
                    invoice_vals = {
                        'name': self.env['ir.sequence'].next_by_code('commission_app_inv_seq'),
                        'invoice_origin': i.sale_order_id or '',
                        'partner_id': sale_order.partner_id.id or '',
                        'branch_id': i.branch_id or '',
                        'currency_id': i.currency_id or '',
                        'customer_sales_person':i.customer_sales_person.id,
                        'move_type': 'out_invoice',
                        'ref': False,
                        'invoice_payment_term_id': False,
                        'team_id': False,
                        'invoice_date': date.today(),
                        'company_id': i.company_id or False,
                        'is_commission': True,
                        'total_commission':total,
                    }
                else:
                    raise UserError(_('All ready Invoiced.'))
            res = account_invoice_obj.create(invoice_vals)
            for i in lab_req:
                invoice_line_vals = {
                    'product_id_selected': i.product_id_selected.id,
                    'qty': i.qty,
                    'commission_value': i.commission_value,
                    'customer_sales_person':sale_order.customer_sales_person.id,
                    'total_commission_per_line': i.total_commission_per_line,
                    'total_commission_order': i.total_commission_order,
                }
                res.write({'invoice_commission_line_id': ([(0, 0, invoice_line_vals)])})
            list_of_ids.append(res.id)
            if list_of_ids:

                lab_req_obj_brw = lab_req_obj.browse(self._context.get('active_id'))
                lab_req_obj_brw.write({'is_invoiced': True})

                imd = self.env['ir.model.data']
                action = imd.xmlid_to_object('account.action_move_out_invoice_type')
                list_view_id = imd.xmlid_to_res_id('account.view_invoice_tree')
                form_view_id = imd.xmlid_to_res_id('account.view_move_form')
                result = {
                    'name': action.name,
                    'help': action.help,
                    'type': action.type,
                    'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
                    'target': action.target,
                    'context': action.context,
                    'res_model': action.res_model,

                }
                if list_of_ids:
                    result['domain'] = "[('id','in',%s)]" % list_of_ids
                else:
                    raise UserError(_('All ready Invoiced.'))
            msg_body = 'Commission Claim created'
            for msg in self:
                msg.message_post(body=msg_body)
                lab_req.is_invoiced = 'True'
            return result
