from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime


class Paid_Commission_Wizard(models.TransientModel):
    _name = "paid.commission.wizard"
    _inherit = 'mail.thread'

    customer_sales_person = fields.Many2one('nassag.salesperson', string='Customer Rep')
    total_commission = fields.Float('Total Commission', readonly=1)
    exchange_amount = fields.Float('Exchange Amount')
    rest_amount = fields.Float('Rest Amount', readonly=1)
    paid_date = fields.Date("Paid Date", required=True, default=fields.Date.today)
    invoice_id = fields.Many2many('account.move', string='invoice ids', readonly=1)

    def create_paid(self):
        for rec in self:
            if rec.exchange_amount <= rec.total_commission:
                invoice_line_vals = {
                    'customer_sales_person': self.customer_sales_person.id,
                    'total_commission': self.total_commission,
                    'exchange_amount': self.exchange_amount,
                    'rest_amount': self.rest_amount,
                    'paid_date': self.paid_date,
                    'invoice_ids': [(6, 0, self.ids)],
                }
                account_invoice_obj = self.env['commission.move.line']
                account_invoice_obj.create(invoice_line_vals)

                selected_ids = self.env.context.get('active_ids', [])
                selected_records = self.env['account.move'].browse(selected_ids)
                for x in selected_records:
                    x.claim_state = 'Total Paid'

                imd = self.env['ir.model.data']
                action = imd.xmlid_to_object('pcp_acc_commission_nassag.action_account_bank_statement_type')
                list_view_id = imd.xmlid_to_res_id('account.view_bank_statement_tree')
                form_view_id = imd.xmlid_to_res_id('account.view_bank_statement_form')
                result = {
                    'name': action.name,
                    'help': action.help,
                    'type': action.type,
                    'views': [ [form_view_id, 'form'],[list_view_id, 'tree']],
                    'target': action.target,
                    'context': action.context,
                    'res_model': action.res_model,
                }
                return result
            else:
                raise Warning('Exchange amount is Greater than Total commission.!')
                return False

    @api.model
    def default_get(self, fields):
        # working
        res = super(Paid_Commission_Wizard, self).default_get(fields)
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['account.move'].browse(selected_ids)
        z = selected_records.customer_sales_person
        for x in selected_records:
            z = list(filter(lambda a: a != x.customer_sales_person, z))
            if len(z) == 0:

                if x.claim_state in 'Not Claim':
                    raise Warning('Commission Not Claimed !')

                if x.claim_state in 'Total Paid':
                    raise Warning('Commission Total Paid !')

                if self.exchange_amount > self.total_commission:
                    raise Warning('Exchange amount is greater than Commission Total ')
            else:
                raise Warning('You Can Not Select More Than One customer sales person In this Action !')
        return res

    @api.onchange('exchange_amount')
    def calculate_rest_amount(self):
        for rec in self:
            if rec.exchange_amount > rec.total_commission:
                raise Warning('Exchange amount is Greater than Total commission.')
            else:
                self.rest_amount = rec.total_commission - rec.exchange_amount