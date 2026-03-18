from odoo import models, fields, api

class HrEmployeeGhana(models.Model):
    """Extend hr.employee with Ghana-specific payroll calculations"""
    _inherit = 'hr.employee'
    
    # Ghana-specific fields
    basic_salary = fields.Monetary('Basic Salary', currency_field='currency_id')
    transport_allowance = fields.Monetary('Transport Allowance', currency_field='currency_id')
    housing_allowance = fields.Monetary('Housing Allowance', currency_field='currency_id')
    
    # Exemption fields
    exempt_from_ssnit = fields.Boolean(
        string='Exempt from SSNIT',
        default=False,
        help='Check this to exclude employees from SSNIT deductions (e.g., contractors, temporary staff)'
    )
    exempt_from_paye = fields.Boolean(
        string='Exempt from PAYE Tax',
        default=False,
        help='Check this to exclude employees from PAYE tax deductions (e.g., staff below tax threshold)'
    )

    # Computed fields
    gross_salary = fields.Monetary('Gross Salary', compute='_compute_gross_salary', store=True)
    ssnit_employee = fields.Monetary('SSNIT (Employee)', compute='_compute_ssnit', store=True)
    ssnit_employer = fields.Monetary('SSNIT (Employer)', compute='_compute_ssnit', store=True)
    paye_tax = fields.Monetary('PAYE Tax', compute='_compute_paye', store=True)
    net_salary = fields.Monetary('Net Salary', compute='_compute_net_salary', store=True)
    
    company_total_cost = fields.Monetary(
        'Total Company Cost',
        compute='_compute_company_cost',
        store=True,
        help='Gross salary + employer SSNIT contribution'
    )

    # ── 2026 GRA monthly PAYE bands ──────────────────────────────────────────
    # Source: GRA PAYE Schedule 2026 (annual figures ÷ 12, cumulative upper limits)
    #
    #  Band │ Annual band (GH₵)  │ Monthly width │ Monthly cumulative │ Rate
    #  ─────┼────────────────────┼───────────────┼────────────────────┼──────
    #   1   │ First  5,880       │      490.00   │      490.00        │  0%
    #   2   │ Next   1,320       │      110.00   │      600.00        │  5%
    #   3   │ Next   1,560       │      130.00   │      730.00        │ 10%
    #   4   │ Next  38,000       │    3,166.67   │    3,896.67        │ 17.5%
    #   5   │ Next 192,000       │   16,000.00   │   19,896.67        │ 25%
    #   6   │ Next 366,240       │   30,520.00   │   50,416.67        │ 30%
    #   7   │ Above 605,000      │        —      │        —           │ 35%
    #

    _PAYE_MONTHLY_BANDS = [
        (490.00,      0.00),   # 0%   on first GH₵490/month
        (600.00,      0.05),   # 5%   on next  GH₵110/month
        (730.00,      0.10),   # 10%  on next  GH₵130/month
        (3_896.67,    0.175),  # 17.5% on next GH₵3,166.67/month
        (19_896.67,   0.25),   # 25%  on next  GH₵16,000/month
        (50_416.67,   0.30),   # 30%  on next  GH₵30,520/month
        (float('inf'), 0.35),  # 35%  on remainder
    ]

    @api.depends('basic_salary', 'transport_allowance', 'housing_allowance')
    def _compute_gross_salary(self):
        for employee in self:
            employee.gross_salary = (
                employee.basic_salary
                + employee.transport_allowance
                + employee.housing_allowance
            )
    
    @api.depends('basic_salary', 'exempt_from_ssnit')
    def _compute_ssnit(self):
        """Calculate SSNIT contributions (2026 rates)
        
        SSNIT is levied on basic salary only (not allowances).
        The insurable earnings cap is GH₵61,000 per annum → GH₵5,083.33/month.
        Employee rate: 5.5%  |  Employer rate: 13%
        """
        max_monthly_insurable = 61_000 / 12  # GH₵5,083.33
        for employee in self:
            if employee.exempt_from_ssnit:
                employee.ssnit_employee = 0.0
                employee.ssnit_employer = 0.0
                continue
            
            insurable = min(employee.basic_salary, max_monthly_insurable)
            employee.ssnit_employee = round(insurable * 0.055, 2)  # 5.5
            employee.ssnit_employer = round(insurable * 0.130, 2)   # 13%
    
    @api.depends('gross_salary', 'exempt_from_paye')
    def _compute_paye(self):
        """Calculate monthly PAYE using 2026 GRA progressive bands."""
        for employee in self:
            if employee.exempt_from_paye:
                employee.paye_tax = 0.0
                continue
            
            chargeable = employee.gross_salary - employee.ssnit_employee

            if chargeable <= 0:
                employee.paye_tax = 0.0
                continue

            tax = 0.0
            previous_limit = 0.0
            remaining = chargeable

            for cumulative_limit, rate in self._PAYE_MONTHLY_BANDS:
                if remaining <= 0:
                    break
                band_width = (
                    cumulative_limit - previous_limit
                    if cumulative_limit != float('inf')
                    else remaining
                )
                taxable_in_band = min(remaining, band_width)
                tax += taxable_in_band * rate
                remaining -= taxable_in_band
                previous_limit = cumulative_limit
            
            employee.paye_tax = round(tax, 2)
    
    @api.depends('gross_salary', 'paye_tax', 'ssnit_employee')
    def _compute_net_salary(self):
        for employee in self:
            employee.net_salary = (
                employee.gross_salary - 
                employee.paye_tax - 
                employee.ssnit_employee
            )

    @api.depends('gross_salary', 'ssnit_employer')
    def _compute_company_cost(self):
        for employee in self:
            employee.company_total_cost = (
                employee.gross_salary + employee.ssnit_employer
            )


class ResCompany(models.Model):
    """Extend company model to add Ghana-specific fields"""
    _inherit = 'res.company'
    
    ssnit_employer_number = fields.Char(
        'SSNIT Employer Number',
        help='Company SSNIT registration number (e.g., 200502844)'
    )