from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from datetime import date, datetime


class Paid_Commission_Wizard(models.TransientModel):
    _name = "paid.commission.wizard"
    _inherit = 'mail.thread'

    customer_sales_person = fields.Many2one('nassag.salesperson', string='Customer Rep')

    def create_Paid(self):
        return False

    @api.model
    def default_get(self, fields):
        res = super(Paid_Commission_Wizard, self).default_get(fields)
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['account.move'].browse(selected_ids)
        z = selected_records.customer_sales_person
        for x in selected_records:
            z = list(filter(lambda a: a != x.customer_sales_person, z))
            if len(z) == 0:
                total = 0
                for rec in selected_records:
                    total += rec.total_commission
            else:
                raise Warning('You Can Not Select More Than One customer sales person In this Action !')
        return res