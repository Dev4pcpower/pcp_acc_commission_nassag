from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime


class CommissionLine(models.Model):
    _inherit = 'commission.line'

    validity_status = fields.Selection([
        ('invoice', 'Invoice'),
        ('tobe', 'To be Invoiced'),
    ], 'Status', sort=False, readonly=True, default='tobe')
    is_invoiced = fields.Boolean(copy=False, default=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_commission = fields.Boolean(default=False)
    is_claim = fields.Boolean(default=False)
    claim_state = fields.Selection([
        ('Not Claim', 'Not Claim'),
        ('Is Claimed', 'Is Claimed'),
    ], 'Claim State', sort=False, readonly=True, default='Not Claim')
    branch_id = fields.Many2one('res.branch', string='branch id')
    customer_sales_person = fields.Many2one('nassag.salesperson', string='Customer Rep')
    total_commission = fields.Float('Total Commission')

    def action_claim(self):
        active_id = self.id
        commission_lines = self.env['invoice.commission.line'].search([('invoice_sale_order_id', '=', active_id)])

        account_debit = self.env['res.config.settings'].search([])[-1]
        if account_debit.account_commission_debit.id:
            if not self.is_claim:
                total = 0
                for rec in commission_lines:
                    total += rec.total_commission_per_line
                self.env['account.move.line'].create([
                    {
                        'name': 'claim commission',
                        'move_id': active_id,
                        'account_id': account_debit.account_commission_debit.id,
                        'debit': total,
                        'credit': 0,
                    },
                    {
                        'name': 'claim commission',
                        'move_id': active_id,
                        'account_id': account_debit.account_commission_credit.id,
                        'debit': 0,
                        'credit': total,
                    }
                ])
            else:
                raise Warning('All ready Claimed.')
        else:
            raise Warning('add debit and credit account in Sales settings.')
        self.write({'is_claim': True})
        self.write({'claim_state': 'Is Claimed'})

    def action_paid(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['account.move'].browse(selected_ids)
        z = selected_records.customer_sales_person
        for x in selected_records:
            z = list(filter(lambda a: a != x.customer_sales_person, z))
            if len(z) == 0:
                total = 0
                for rec in selected_records:
                    total += rec.total_commission
                return {
                    'name': _('Register Payment'),
                    'res_model': 'paid.commission.wizard',
                    'view_mode': 'form',
                    'context': {
                        'default_customer_sales_person': selected_records.customer_sales_person.id,

                    },
                    'target': 'new',
                    'type': 'ir.actions.act_window',
                }

            else:
                raise Warning('You Can Not Select More Than One customer sales person In this Action !')

