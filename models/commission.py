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

    def action_claim(self):
        active_id = self.id
        commission_lines = self.env['invoice.commission.line'].search([('invoice_sale_order_id', '=', active_id)])

        account_debit = self.env['res.config.settings'].search([])[-1]
        if account_debit:
            account_invoice_obj = self.env['account.move.line']

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
