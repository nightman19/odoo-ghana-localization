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
        active_ids = self.env.context.get('active_ids', [])
        
        if not active_ids:
            raise UserError("Please select employees from the list first by checking the boxes next to their names.")
            
        employees = self.env['hr.employee'].browse(active_ids)
        
        if not employees.exists():
            raise UserError("Selected employees not found. Please try again.")
        
        month_names = {
            '01': 'January', '02': 'February', '03': 'March',
            '04': 'April', '05': 'May', '06': 'June',
            '07': 'July', '08': 'August', '09': 'September',
            '10': 'October', '11': 'November', '12': 'December'
        }
        month_name = month_names[self.month]
        period_str = f"{month_name}_{self.year}"
        
        # Generate PDF - use report_action instead
        return self.env.ref('gh_localization.action_report_employee_payslip_ghana').with_context(
            download_filename=f"Payslip_{period_str}.pdf"
        ).report_action(
            employees.ids,
            data={
                'ids':employees.ids,
                'month': self.month,
                'year': self.year,
                'month_name': month_name,
                'period': f"{month_name} {self.year}"
            }
        )

    def action_generate_summary_pdf(self):
        """Generate payroll summary PDF for selected period"""
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        
        if active_ids:
            employees = self.env['hr.employee'].browse(active_ids)
            employees = employees.filtered(lambda e: e.basic_salary > 0)
        else:
            employees = self.env['hr.employee'].search([('basic_salary', '>', 0)])
        
        if not employees:
            raise UserError("No employees with salary information found.")

        # Get values for filename
        month_name = dict(self._fields['month'].selection).get(self.month)
        # Create a clean filename string (e.g., Payroll_Summary_January_2024)
        filename = f"Payroll_Summary_{month_name}_{self.year}"
        
        # Trigger report with .with_context() so the XML 'print_report_name' can see it
        action = self.env.ref('gh_localization.action_report_payroll_summary_pdf').report_action(
            employees.ids,
            data={
                'ids': employees.ids,
                'month': self.month,
                'year': self.year,
                'month_name': month_name,
                'period': f"{month_name} {self.year}"
            }
        )

        action.update({
            'name': filename,
            'display_name': filename,
        })

        return action