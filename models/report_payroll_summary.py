from odoo import models, api

class ReportPayrollSummary(models.AbstractModel):
    _name = 'report.gh_localization.report_payroll_summary_pdf'
    _description = 'Ghana Payroll Summary Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        employee_ids = data.get('ids') if data else []
        docs = self.env['hr.employee'].browse(employee_ids)

        return {
            'doc_ids': employee_ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'data': data or {},
        }

    def _get_report_base_filename(self):
        """THIS controls the final downloaded filename in Odoo 17+"""
        data = self.env.context.get('data') or {}

        month_name = data.get('month_name')
        year = data.get('year')

        if month_name and year:
            return f"Payroll_Summary_{month_name}_{year}"

        return "Payroll_Summary"