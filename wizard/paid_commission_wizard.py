from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime


class Paid_Commission_Wizard(models.TransientModel):
    _name = "paid.commission.wizard"
    _inherit = 'mail.thread'

    customer_sales_person = fields.Many2one('nassag.salesperson', string='Customer Rep')
    total_commission = fields.Float('Total Commission')
    exchange_amount = fields.Float('Exchange Amount')
    rest_amount = fields.Float('Rest Amount', readonly=1)
    paid_date = fields.Date("Paid Date")
    invoice_id = fields.Many2many('account.move', string='invoice ids')

    def create_paid(self):
        if self.exchange_amount <= self.total_commission:
            invoice_line_vals = {
                'customer_sales_person': self.customer_sales_person.id,
                'total_commission': self.total_commission,
                'exchange_amount': self.exchange_amount,
                'rest_amount': self.rest_amount,
                'paid_date': self.paid_date,
                'invoice_id': [(6, 0, self.ids)],
            }
            account_invoice_obj = self.env['commission.move.line']
            account_invoice_obj.create(invoice_line_vals)

            selected_ids = self.env.context.get('active_ids', [])
            selected_records = self.env['account.move'].browse(selected_ids)
            for x in selected_records:
                x.claim_state = 'Total Paid'
        else:
            raise Warning('Exchange amount is Greater than Total commission.!')

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
            else:
                raise Warning('You Can Not Select More Than One customer sales person In this Action !')
        return res

    @api.onchange('total_commission', 'exchange_amount')
    def calculate_rest_amount(self):
        for rec in self:
            if rec.exchange_amount > rec.total_commission:
                rec.exchange_amount = 0
                rec.rest_amount = rec.total_commission - rec.exchange_amount
                raise Warning('Exchange amount is Greater than Total commission.')
            else:
                rec.rest_amount = rec.total_commission - rec.exchange_amount