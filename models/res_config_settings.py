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
        self.env['ir.config_parameter'].set_param('account_commission_debit', self.account_commission_debit.id)
        self.env['ir.config_parameter'].set_param('account_commission_credit', self.account_commission_credit.id)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res['account_commission_debit'] = int(self.env['ir.config_parameter'].sudo().get_param('account_commission_debit', default=0))
        res['account_commission_credit'] = int(self.env['ir.config_parameter'].sudo().get_param('account_commission_credit', default=0))

        return res