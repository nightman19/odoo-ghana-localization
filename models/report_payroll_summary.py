from odoo import models, api

class ReportPayrollSummary(models.AbstractModel):
    _name = 'report.gh_localization.report_payroll_summary_pdf'
    _description = 'Ghana Payroll Summary Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Fallback to all employees with salary if wizard didn't pass specific IDs
        if not docids and data and data.get('ids'):
            docids = data.get('ids')
            
        docs = self.env['hr.employee'].browse(docids)
        print(f"DEBUG: docids model is {self.env[self.env.context.get('active_model') or 'hr.employee']._name}")
        # Set custom filename
        if data and data.get('period'):
            period = data.get('period').replace(' ', '_')
            self = self.with_context(payroll_period=period)
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'data': data or {}, # This makes the 'data' variable exist in your XML
        }