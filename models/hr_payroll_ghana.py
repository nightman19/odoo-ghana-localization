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

    company_total_cost = fields.Monetary(
        'Total Company Cost',
        compute='_compute_company_cost',
        store=True,
        help='Gross salary + employer SSNIT contribution'
    )

    # Overtime fields
    overtime_enabled = fields.Boolean(
        'Overtime Enabled', 
        default=False,
        help='Enable overtime calculations for this employee. '
            'Requires overtime to be enables at company level. ',
            
    )

    overtime_method = fields.Selection(
        selection=[('monthly', 'Monthly Overtime Amount'), ('hourly', 'Hourly Overtime Rate')],
        string='Overtime Calculation Method',
        default='monthly',
        help='Method to calculate overtime pay. Monthly: enter a fixed overtime amount each month. Hourly: enter hours worked and an hourly rate.'
    )

    overtime_hours = fields.Float(
        string='Overtime Hours',
        default=0.0,
        help='Number or overtime hours worked this month (hourly method only).',
    )

    overtime_hourly_rate = fields.Monetary(
        'Hourly Rate',
        currency_field='currency_id',
        help='Overtime pay per hour(hourly method only).'
    )

    overtime_amount_manual = fields.Monetary(
        'Overtime Amount',
        currency_field='currency_id',
        help='Fixed overtime amount for the month (monthly method only).',
    )


    # ── Computed fields ───────────────────────────────────────────────────────
    gross_salary = fields.Monetary(
        'Gross Salary',
        compute='_compute_gross_salary',
        store=True,
    )
    ssnit_employee = fields.Monetary(
        'SSNIT (Employee)',
        compute='_compute_ssnit',
        store=True,
    )
    ssnit_employer = fields.Monetary(
        'SSNIT (Employer)',
        compute='_compute_ssnit',
        store=True,
    )
    overtime_amount = fields.Monetary(
        'Overtime Amount (Computed)',
        compute='_compute_overtime_amount',
        store=True,
        help='Actual overtime amount: hours × rate (hourly) or manual entry (monthly).',
    )
    overtime_tax = fields.Monetary(
        'Overtime Tax',
        compute='_compute_overtime_tax',
        store=True,
        help='Tax on overtime. Junior staff: 5%/10% flat. '
             'Senior staff: included in PAYE (this field shows 0).',
    )
    paye_tax = fields.Monetary(
        'PAYE Tax',
        compute='_compute_paye',
        store=True,
    )
    net_salary = fields.Monetary(
        'Net Salary',
        compute='_compute_net_salary',
        store=True,
    )
    company_total_cost = fields.Monetary(
        'Total Company Cost',
        compute='_compute_company_cost',
        store=True,
        help='Gross salary + employer SSNIT contribution',
    )


    # -- Helper: is this employee junior? ---------
    def _is_junior(self):
        """Return True id basic_salary < company overtime junior threshold."""
        threshold = (
            self.company_id.overtime_junior_threshold
            if self.company_id
            else 1500.00
        )

        return self.basic_salary <= threshold
    

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

    @staticmethod
    def _calculate_paye(chargeable):
        """Apply 2026 GRA monthly progressive bands to a chargeble amount."""
        if chargeable <= 0:
            return 0.0
        tax, prev, remaining = 0.0, 0.0, chargeable
        for limit, rate in HrEmployeeGhana._PAYE_MONTHLY_BANDS:
            if remaining <= 0:
                break
            width = (limit - prev) if limit != float('inf') else remaining
            in_band = min(remaining, width)
            tax += in_band * rate
            remaining -= in_band
            prev = limit
        return round(tax, 2)
    

    # --- Compute: Gross Salary ---
    @api.depends('basic_salary', 'transport_allowance', 'housing_allowance', 'overtime_amount', 'overtime_enabled', 'company_id.enable_overtime')
    def _compute_gross_salary(self):
        for employee in self:
            ot = employee.overtime_amount if (
                employee.overtime_enabled and employee.company_id.enable_overtime
            ) else 0.0
            
            employee.gross_salary = (
                employee.basic_salary
                + employee.transport_allowance
                + employee.housing_allowance
                + ot
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
    
    # --- Compute: Overtime amount ---
    @api.depends('overtime_method', 'overtime_hours', 'overtime_hourly_rate', 'overtime_amount_manual', 'overtime_enabled', 'company_id.enable_overtime')
    def _compute_overtime_amount(self):
        for employee in self:
            if not employee.overtime_enabled or not employee.company_id.enable_overtime:
                employee.overtime_amount = 0.0
                continue

            if employee.overtime_method == 'hourly':
                employee.overtime_amount = round(employee.overtime_hours * employee.overtime_hourly_rate, 2)
            else: 
                employee.overtime_amount = employee.overtime_amount_manual


    # --- Compute: Overtime tax (if applicable) ---
    @api.depends('overtime_amount', 'basic_salary', 'overtime_method',
                 'company_id.enable_overtime', 'company_id.overtime_junior_threshold')
    
    def _compute_overtime_tax(self):
        """Calculate tax on overtime pay for junior staff (if applicable)
        
        For employees with basic salary at or below the company-defined junior threshold, 
        overtime pay is taxed separately at 5%. For senior staff, overtime is included in 
        gross salary and taxed via PAYE.
        """
        for employee in self:
            if not employee.overtime_enabled or not employee.company_id.enable_overtime:
                employee.overtime_tax = 0.0
                continue
            if employee.overtime_amount <= 0:
                employee.overtime_tax = 0.0
                continue

            if employee._is_junior():
                # Junior staff: 5% up to 50% of Basic Monthly Salary(BMS), 10% on excess
                ot_threshold = employee.basic_salary * 0.50
                if employee.overtime_amount <= ot_threshold:
                    employee.overtime_tax = round(employee.overtime_amount * 0.05, 2)
                else:
                    tax = (ot_threshold * 0.05) + ((employee.overtime_amount - ot_threshold) * 0.10)
                    employee.overtime_tax = round(tax, 2)
            else:
                # Senior staff: overtime is added to chargeable income and taxed via PAYE, so no separate overtime_tax line
                employee.overtime_tax = 0.0

        
    # ---Compute: PAYE ---
    @api.depends('gross_salary', 'exempt_from_paye', 'ssnit_employee', 
                 'overtime_tax', 'overtime_amount', 'overtime_enabled', 'basic_salary',
                 'company_id.enable_overtime', 'company_id.overtime_junior_threshold')
    def _compute_paye(self):
        """Calculate monthly PAYE using 2026 GRA progressive bands."""
        for employee in self:
            if employee.exempt_from_paye:
                employee.paye_tax = 0.0
                continue
            
            ot_active = employee.overtime_enabled and employee.company_id.enable_overtime
            is_junior = employee._is_junior()

            if ot_active and employee.overtime_amount > 0 and not is_junior:
                # Implies Senior staff: overtime already in gross_salary,
                # compute PAYE on full chargeable (include. overtime)
                chargeable = employee.gross_salary - employee.ssnit_employee
            else:
                # Implies Junior staff or no overtime: PAYE on base chargeable only
                # (overtime tax handled separately via _compute_overtime_tax)
                base_income = (
                    employee.basic_salary + employee.transport_allowance + employee.housing_allowance
                )
                chargeable = base_income - employee.ssnit_employee
            
            employee.paye_tax = self._calculate_paye(chargeable)
    
    @api.depends('gross_salary', 'paye_tax', 'ssnit_employee', 'overtime_tax')
    def _compute_net_salary(self):
        for employee in self:
            employee.net_salary = (
                employee.gross_salary - 
                employee.paye_tax - 
                employee.ssnit_employee -
                employee.overtime_tax
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

    enable_overtime = fields.Boolean(
        string='Enable Overtime',
        default=False,
        help='Master switch. When off, all overtime fields and calculations '
            'are hidden and zeroed across all employees.',
    )

    overtime_junior_threshold = fields.Monetary(
        string='Overtime Junior Threshold (GH₵/month)',
        currency_field='currency_id',
        default=1500.00,
        help='Employees with basic monthly salary at or below this amount are treates as junior staff for overtime tax purposes (GRA default: GH₵1,500).',
    )