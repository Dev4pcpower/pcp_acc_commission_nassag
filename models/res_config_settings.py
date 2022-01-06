from odoo import fields, models ,api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    account_id = fields.Many2one('account.account')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_commission_debit = fields.Many2one('account.account',config_parameter='account_commission_debit', index=True, check_company=True)
    account_commission_credit = fields.Many2one('account.account',config_parameter='account_commission_debit',index=True, check_company=True)

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('account_commission_debit', self.account_commission_debit)
        self.env['ir.config_parameter'].set_param('account_commission_credit', self.account_commission_credit)
        return res

