from odoo import models, fields, api

class HrEmployeeGhana(models.Model):
    """Extend hr.employee with Ghana-specific payroll calculations"""
    _inherit = 'hr.employee'
    
    # Ghana-specific fields
    basic_salary = fields.Monetary('Basic Salary', currency_field='currency_id')
    transport_allowance = fields.Monetary('Transport Allowance', currency_field='currency_id')
    housing_allowance = fields.Monetary('Housing Allowance', currency_field='currency_id')
    
    # Computed fields
    gross_salary = fields.Monetary('Gross Salary', compute='_compute_gross_salary', store=True)
    paye_tax = fields.Monetary('PAYE Tax', compute='_compute_paye', store=True)
    ssnit_employee = fields.Monetary('SSNIT (Employee)', compute='_compute_ssnit', store=True)
    ssnit_employer = fields.Monetary('SSNIT (Employer)', compute='_compute_ssnit', store=True)
    net_salary = fields.Monetary('Net Salary', compute='_compute_net_salary', store=True)
    
    company_total_cost = fields.Monetary(
        'Total Company Cost',
        compute='_compute_company_cost',
        help='Gross salary + employer SSNIT contribution'
    )

    @api.depends('gross_salary', 'ssnit_employer')
    def _compute_company_cost(self):
        for employee in self:
            employee.company_total_cost = employee.gross_salary + employee.ssnit_employer

    @api.depends('basic_salary', 'transport_allowance', 'housing_allowance')
    def _compute_gross_salary(self):
        for employee in self:
            employee.gross_salary = (
                employee.basic_salary + 
                employee.transport_allowance + 
                employee.housing_allowance
            )
    
    @api.depends('gross_salary')
    def _compute_paye(self):
        """Calculate PAYE using 2025 Ghana tax brackets"""
        for employee in self:
            gross = employee.gross_salary
            tax = 0.0
            
            brackets = [
                (490, 0.00),
                (660, 0.05),
                (3750, 0.10),
                (20000, 0.175),
                (60000, 0.25),
                (float('inf'), 0.30)
            ]
            
            previous_limit = 0
            remaining = gross
            
            for limit, rate in brackets:
                if remaining <= 0:
                    break
                
                taxable = min(remaining, limit - previous_limit)
                tax += taxable * rate
                remaining -= taxable
                previous_limit = limit
            
            employee.paye_tax = round(tax, 2)
    
    @api.depends('basic_salary')
    def _compute_ssnit(self):
        """Calculate SSNIT contributions (2025 rates)"""
        for employee in self:
            max_monthly = 61000 / 12  # GHS 5,083.33
            insurable = min(employee.basic_salary, max_monthly)
            
            employee.ssnit_employee = round(insurable * 0.055, 2)  # 5.5%
            employee.ssnit_employer = round(insurable * 0.13, 2)   # 13%
    
    @api.depends('gross_salary', 'paye_tax', 'ssnit_employee')
    def _compute_net_salary(self):
        for employee in self:
            employee.net_salary = (
                employee.gross_salary - 
                employee.paye_tax - 
                employee.ssnit_employee
            )


class ResCompany(models.Model):
    """Extend company model to add Ghana-specific fields"""
    _inherit = 'res.company'
    
    ssnit_employer_number = fields.Char(
        'SSNIT Employer Number',
        help='Company SSNIT registration number (e.g., 200502844)'
    )