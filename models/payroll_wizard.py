from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class PayrollPeriodWizard(models.TransientModel):
    _name = 'payroll.period.wizard'
    _description = 'Select Payroll Period'

    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'),
        ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True, default=lambda self: datetime.now().strftime('%m'))
    
    year = fields.Selection(
        selection='_get_years',
        string='Year',
        required=True,
        default=lambda self: str(datetime.now().year)
    )

    @api.model
    def _get_years(self):
        """Generate years from 2024 to current year + 2"""
        current_year = datetime.now().year
        years = [(str(year), str(year)) for year in range(2024, current_year + 3)]
        return years

    def action_generate_payslips(self):
        """Generate payslips for selected employees and period"""
        self.ensure_one()

        active_ids = self.env.context.get('active_ids', [])

        if active_ids:
            employees = self.env['hr.employee'].browse(active_ids)
            employees = employees.filtered(lambda e: e.basic_salary > 0)
        else:
            employees = self.env['hr.employee'].search([('basic_salary', '>', 0)])

        if not employees:
            raise UserError("No employees with salary information found.")

        month_name = dict(self._fields['month'].selection).get(self.month)
        filename = f"Payslips_{month_name}_{self.year}.pdf"

        # Render PDF manually
        report = self.env['ir.actions.report']
        pdf_content, _ = report._render_qweb_pdf(
            'gh_localization.report_employee_payslip_ghana',
            employees.ids,
            data={
                'ids': employees.ids,
                'month': self.month,
                'year': self.year,
                'month_name': month_name,
            }
        )

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': pdf_content.encode('base64') if isinstance(pdf_content, str) else pdf_content,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
        
    
    def action_generate_summary_pdf(self):
        """Generate payroll summary for selected employees and period"""
        self.ensure_one()

        active_ids = self.env.context.get('active_ids', [])

        if active_ids:
            employees = self.env['hr.employee'].browse(active_ids)
            employees = employees.filtered(lambda e: e.basic_salary > 0)
        else:
            employees = self.env['hr.employee'].search([('basic_salary', '>', 0)])

        if not employees:
            raise UserError("No employees with salary information found.")

        month_name = dict(self._fields['month'].selection).get(self.month)
        filename = f"Payroll_Summary_{month_name}_{self.year}.pdf"

        # Render PDF manually
        report = self.env['ir.actions.report']
        pdf_content, _ = report._render_qweb_pdf(
            'gh_localization.report_payroll_summary_pdf',
            employees.ids,
            data={
                'month': self.month,
                'year': self.year,
                'month_name': month_name,
            }
        )

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': pdf_content.encode('base64') if isinstance(pdf_content, str) else pdf_content,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }