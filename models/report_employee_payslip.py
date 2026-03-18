from odoo import models, api

class ReportEmployeePayslipGhana(models.AbstractModel):
    _name = 'report.gh_localization.report_employee_payslip_ghana'
    _description = 'Ghana Employee Payslip Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):

        # ALWAYS trust docids first
        docs = self.env['hr.employee'].browse(docids)

        # Fallback to data only if necessary
        if not docs and data and data.get('ids'):
            docs = self.env['hr.employee'].browse(data.get('ids'))

        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'data': data or {},
        }