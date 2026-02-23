from odoo import models, api

class ReportEmployeePayslipGhana(models.AbstractModel):
    # This name must match: report + . + module_name + . + template_id
    _name = 'report.gh_localization.report_employee_payslip_ghana'
    _description = 'Ghana Employee Payslip Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Fallback if docids is empty (common when printing from wizards)
        if not docids and data and data.get('ids'):
            docids = data.get('ids')
            
        docs = self.env['hr.employee'].browse(docids)

        # Set custom filename
        if data and data.get('period'):
            period = data.get('period').replace(' ', '_')
            # This will be used by the print_report_name field
            self = self.with_context(payroll_period=period)
            
        return {
            'doc_ids': docids,
            'doc_model': 'hr.employee',
            'docs': docs,  # This populates the 'docs' variable in your XML
            'data': data or {}, # This populates the 'data' variable in your XML
        }
