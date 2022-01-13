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


class CommissionMoveLine(models.Model):
    _name = 'commission.move.line'

    branch_id = fields.Many2one('res.branch', string='branch id')
    customer_sales_person = fields.Many2one('nassag.salesperson', string='Customer Rep')
    total_commission = fields.Float('Total Commission')
    change_amounts = fields.Float('Exchange Amount')
    rest_amount = fields.Float('Rest Amount')
    hash_amount = fields.Float('Hash Amount')
    paid_date = fields.Date("Paid Date")
    invoice_ids = fields.Many2one('account.move', string='invoice ids')
    product_id_selected = fields.Many2many('product.product', string='Product')
    claim_state = fields.Selection([('Total Paid', 'Total Paid'), ('Part Paid', 'Part Paid'),('Not Paid', 'Not Paid'),
                                    ], 'Commission State', sort=False, readonly=True, default='Not Paid')


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    invoice_id = fields.Many2one('account.move')
    is_commission = fields.Boolean(default=False)
    total_commission = fields.Float(string='Total Commission')
    change_amounts = fields.Float(string='change Amounts')

    @api.model_create_multi
    def create(self, vals):
        res = super(AccountBankStatement, self).create(vals)
        if vals[0]["is_commission"]:
            comm = self.env['commission.move.line'].search([('invoice_ids', '=', vals[0]['invoice_id'])])
            ones = comm.env['commission.move.line'].search([])[-1]

            move = self.env['account.move'].search([('id', '=', vals[0]['invoice_id'])])

            if vals[0]['total_commission'] == vals[0]['change_amounts']:
                for x in ones:
                    x.update({'claim_state': 'Total Paid'})
                for x in move:
                    x.update({'claim_state': 'Total Paid'})
            if vals[0]['total_commission'] > vals[0]['change_amounts']:
                for x in comm:
                    x.update({'claim_state': 'Part Paid'})
                for x in move:
                    x.update({'claim_state': 'Part Paid'})

        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_commission = fields.Boolean(default=False)
    is_claim = fields.Boolean(default=False)
    claim_state = fields.Selection([
        ('Not Claim', 'Not Claim'),
        ('Is Claimed', 'Is Claimed'), ('Total Paid', 'Total Paid'), ('Part Paid', 'Part Paid'),
    ], 'Commission State', sort=False, readonly=True, default='Not Claim')
    branch_id = fields.Many2one('res.branch', string='branch id')
    customer_sales_person = fields.Many2one('nassag.salesperson', string='Customer Rep')
    total_commission = fields.Float('Total Commission')
    hash_amount = fields.Float('Hash Amount')
    product_id_selected = fields.Many2one('product.product', string='Product')
    invoice_amount = fields.Float('Invoice Amount')

    def action_claim(self):
        active_id = self.id
        commission_lines = self.env['invoice.commission.line'].search([('invoice_sale_order_id', '=', active_id)])

        account_debit = self.env['res.config.settings'].search([])[-1] or False

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
            raise UserError(_('add debit and credit account in Sales settings.'))
        self.write({'is_claim': True})
        self.write({'claim_state': 'Is Claimed'})

    def action_paid(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['account.move'].browse(selected_ids)

        for x in selected_records:
            # z = list(filter(lambda a: a != x.customer_sales_person, z))
            if len(selected_ids) == 1:
                total = 0
                hash_amount = 0
                for rec in selected_records:
                    total += rec.total_commission

                if rec.claim_state == 'Part Paid':
                    return {
                        'name': _('Commission Paid'),
                        'res_model': 'paid.commission.wizard',
                        'view_mode': 'form',
                        'context': {
                            'default_customer_sales_person': selected_records.customer_sales_person.id,
                            'default_total_commission': rec.hash_amount,
                            'default_invoice_id':  selected_records.id,
                            'default_product_id_selected': [(6, 0, selected_records.product_id_selected.ids)],

                        },
                        'target': 'new',
                        'type': 'ir.actions.act_window',
                    }
                else:
                    return {
                        'name': _('Commission Paid'),
                        'res_model': 'paid.commission.wizard',
                        'view_mode': 'form',
                        'context': {
                            'default_customer_sales_person': selected_records.customer_sales_person.id,
                            'default_total_commission': total,
                            'default_invoice_id': selected_records.id,
                            'default_product_id_selected': [(6, 0, selected_records.product_id_selected.ids)],

                        },
                        'target': 'new',
                        'type': 'ir.actions.act_window',
                    }
            else:
                raise UserError(_('You Can Not Select More Than One customer sales person In this Action !'))
