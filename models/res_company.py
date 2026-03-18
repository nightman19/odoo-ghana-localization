from odoo import models, fields

class ResCompany(models.Model):
    """Extend company model to add Ghana-specific fields"""
    _inherit = 'res.company'

    ssnit_employer_number = fields.Char(
        'SSNIT Employer Number',
        help='Company SSNIT registration number (e.g., 200502844)'
    )
