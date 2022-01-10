from odoo import _, api, fields, models
from odoo.exceptions import Warning, UserError
from datetime import date, datetime


class Paid_Commission_Wizard(models.TransientModel):
    _name = "paid.commission.wizard"

    customer_sales_person = fields.Many2one('nassag.salesperson', string='Customer Rep', readonly=1)
    total_commission = fields.Float(string='Total Commission', readonly=1)
    rest_amount = fields.Float(string='Rest Amount', readonly=1)
    change_amount = fields.Float(string='change Amount',readonly=0)
    change_amounts = fields.Float(string='change Amounts', readonly=0)
    paid_date = fields.Date(string="Paid Date", required=True, default=fields.Date.today)
    invoice_id = fields.Many2many('account.move', string='invoice ids', readonly=1)
    product_id_selected = fields.Many2many('product.product', string='Product')

    def create_paid(self):
        for rec in self:
            if rec.change_amounts == 0:
                raise UserError(_("change amount can't be zero"))
            if rec.rest_amount > 0:
                for x in self:
                        x.claim_state = 'Part Paid'
            if self.change_amounts < rec.total_commission:
                invoice_line_vals = {
                    'customer_sales_person': self.customer_sales_person.id,
                    'total_commission': self.total_commission,
                    'change_amounts': self.change_amounts,
                    'rest_amount': self.rest_amount,
                    'paid_date': self.paid_date,
                    'invoice_ids': [(6, 0, self.ids)],
                    'product_id_selected': [(6, 0, self.product_id_selected.ids)],
                }
                account_invoice_obj = self.env['commission.move.line']
                account_invoice_obj.create(invoice_line_vals)

                selected_ids = self.env.context.get('active_ids', [])
                selected_records = self.env['account.move'].browse(selected_ids)
                for x in selected_records:
                    x.claim_state = 'Part Paid'

                imd = self.env['ir.model.data']
                action = imd.xmlid_to_object('pcp_acc_commission_nassag.action_account_bank_statement_type')
                list_view_id = imd.xmlid_to_res_id('account.view_bank_statement_tree')
                form_view_id = imd.xmlid_to_res_id('account.view_bank_statement_form')
                result = {
                    'name': action.name,
                    'help': action.help,
                    'type': action.type,
                    'views': [[form_view_id, 'form'], [list_view_id, 'tree']],
                    'target': action.target,
                    'context': action.context,
                    'res_model': action.res_model,
                }
                return result

            if self.change_amounts == rec.total_commission:
                invoice_line_vals = {
                    'customer_sales_person': self.customer_sales_person.id,
                    'total_commission': self.total_commission,
                    'change_amounts': self.change_amounts,
                    'rest_amount': self.rest_amount,
                    'paid_date': self.paid_date,
                    'invoice_ids': [(6, 0, self.ids)],
                    'product_id_selected': [(6, 0, self.product_id_selected.ids)],

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
                    'views': [[form_view_id, 'form'], [list_view_id, 'tree']],
                    'target': action.target,
                    'context': action.context,
                    'res_model': action.res_model,
                }
                return result
            else:
                raise UserError(_("Exchange amount is Greater than Total commission.!"))

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # res['']

        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['account.move'].browse(selected_ids)
        z = selected_records.customer_sales_person
        for x in selected_records:
            z = list(filter(lambda a: a != x.customer_sales_person, z))
            if len(z) == 0:
                if x.customer_sales_person.id == '':
                    raise UserError(_('none customer sale person !'))

                if x.claim_state in 'Not Claim':
                    raise UserError(_('Commission Not Claimed !'))

                if x.claim_state in 'Total Paid':
                    raise UserError(_('Commission Total Paid !'))

                if self.change_amounts > self.total_commission:
                    raise UserError(_('Exchange amount is greater than Commission Total '))
            else:
                raise UserError(_('You Can Not Select More Than One customer sales person In this Action !'))
        return res

    @api.onchange('change_amounts')
    def calculate_rest_amount(self):
        for rec in self:
            if rec.change_amounts > rec.total_commission:
                raise UserError(_('Exchange amount is Greater than Total commission.'))
            else:
                self.rest_amount = rec.total_commission - rec.change_amounts
