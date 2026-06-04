"""
Tests for gh_localization Ghana PAYE, SSNIT and Overtime calculations.

Run via Docker:
    docker compose run --rm test
"""

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('gh_localization', 'gh_payroll')
class TestGhanaPayroll(TransactionCase):
    """Unit tests for Ghana PAYE, SSNIT and Overtime computed fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee GH',
            'exempt_from_ssnit': False,
            'exempt_from_paye': False,
            'overtime_enabled': False,
        })
        # Ensure company has overtime disabled by default
        cls.env.company.enable_overtime = False
        cls.env.company.overtime_junior_threshold = 1500.0

    def _set_salary(self, basic, transport=0.0, housing=0.0):
        self.employee.write({
            'basic_salary': basic,
            'transport_allowance': transport,
            'housing_allowance': housing,
        })
        self.employee.flush_recordset()

    def _enable_overtime(self, method='monthly', amount=0.0,
                         hours=0.0, rate=0.0):
        self.env.company.enable_overtime = True
        self.employee.write({
            'overtime_enabled': True,
            'overtime_method': method,
            'overtime_amount_manual': amount if method == 'monthly' else 0.0,
            'overtime_hours': hours if method == 'hourly' else 0.0,
            'overtime_hourly_rate': rate if method == 'hourly' else 0.0,
        })
        self.employee.flush_recordset()

    def _disable_overtime(self):
        self.env.company.enable_overtime = False
        self.employee.overtime_enabled = False
        self.employee.flush_recordset()

    # ── Gross salary ──────────────────────────────────────────────────────────

    def test_gross_salary_basic_only(self):
        self._set_salary(basic=2500)
        self.assertAlmostEqual(self.employee.gross_salary, 2500.00, places=2)

    def test_gross_salary_with_allowances(self):
        self._set_salary(basic=2500, transport=300, housing=500)
        self.assertAlmostEqual(self.employee.gross_salary, 3300.00, places=2)

    def test_gross_salary_includes_overtime(self):
        self._set_salary(basic=2500)
        self._enable_overtime(method='monthly', amount=500)
        self.assertAlmostEqual(self.employee.gross_salary, 3000.00, places=2)
        self._disable_overtime()

    # ── SSNIT ─────────────────────────────────────────────────────────────────

    def test_ssnit_standard(self):
        self._set_salary(basic=2500)
        self.assertAlmostEqual(self.employee.ssnit_employee, 137.50, places=2)
        self.assertAlmostEqual(self.employee.ssnit_employer, 325.00, places=2)

    def test_ssnit_capped_at_annual_61000(self):
        self._set_salary(basic=10_000)
        cap = 61_000 / 12
        self.assertAlmostEqual(
            self.employee.ssnit_employee, round(cap * 0.055, 2), places=2)
        self.assertAlmostEqual(
            self.employee.ssnit_employer, round(cap * 0.130, 2), places=2)

    def test_ssnit_exempt(self):
        self._set_salary(basic=2500)
        self.employee.exempt_from_ssnit = True
        self.employee.flush_recordset()
        self.assertEqual(self.employee.ssnit_employee, 0.0)
        self.assertEqual(self.employee.ssnit_employer, 0.0)
        self.employee.exempt_from_ssnit = False

    def test_ssnit_on_basic_not_gross(self):
        self._set_salary(basic=2500, transport=500, housing=500)
        self.assertAlmostEqual(self.employee.ssnit_employee, 137.50, places=2)

    # ── PAYE (no overtime) ────────────────────────────────────────────────────

    def test_paye_2500_basic(self):
        self._set_salary(basic=2500)
        self.assertAlmostEqual(self.employee.paye_tax, 304.19, places=2)

    def test_paye_zero_income(self):
        self._set_salary(basic=0)
        self.assertEqual(self.employee.paye_tax, 0.0)

    def test_paye_within_free_band(self):
        self._set_salary(basic=490)
        self.assertEqual(self.employee.paye_tax, 0.0)

    def test_paye_exempt(self):
        self._set_salary(basic=5000)
        self.employee.write({'exempt_from_paye': True})
        self.employee.invalidate_recordset()
        self.assertEqual(self.employee.paye_tax, 0.0)
        self.employee.write({'exempt_from_paye': False})
        self.employee.invalidate_recordset()

    def test_paye_uses_chargeable_not_gross(self):
        self._set_salary(basic=2500)
        chargeable = 2500.0 - 137.50
        expected = self._calc_paye(chargeable)
        self.assertAlmostEqual(self.employee.paye_tax, expected, places=2)

    def test_paye_high_income_hits_35_band(self):
        self._set_salary(basic=60_000)
        self.assertGreater(self.employee.paye_tax, 0)
        effective = self.employee.paye_tax / self.employee.gross_salary
        self.assertGreater(effective, 0.25)
        self.assertLess(effective, 0.35)
        self.assertAlmostEqual(self.employee.paye_tax, 16_984.98, places=1)

    # ── Overtime: company switch ──────────────────────────────────────────────

    def test_overtime_disabled_at_company_level(self):
        """When company.enable_overtime=False, overtime fields are all zero."""
        self._set_salary(basic=1000)
        self.env.company.enable_overtime = False
        self.employee.write({
            'overtime_enabled': True,
            'overtime_method': 'monthly',
            'overtime_amount_manual': 500,
        })
        self.employee.flush_recordset()
        self.assertEqual(self.employee.overtime_amount, 0.0)
        self.assertEqual(self.employee.overtime_tax, 0.0)
        # gross should not include overtime
        self.assertAlmostEqual(self.employee.gross_salary, 1000.00, places=2)

    def test_overtime_disabled_per_employee(self):
        """When overtime_enabled=False on employee, no overtime computed."""
        self._set_salary(basic=1000)
        self.env.company.enable_overtime = True
        self.employee.write({
            'overtime_enabled': False,
            'overtime_amount_manual': 500,
        })
        self.employee.flush_recordset()
        self.assertEqual(self.employee.overtime_amount, 0.0)
        self.assertEqual(self.employee.overtime_tax, 0.0)
        self.env.company.enable_overtime = False

    # ── Overtime: junior staff ────────────────────────────────────────────────

    def test_overtime_junior_all_within_threshold(self):
        """
        Basic=1,000 (junior ≤ 1,500), overtime=200
        ot_threshold = 1,000 × 50% = 500
        200 < 500 → all at 5%
        overtime_tax = 200 × 5% = 10.00
        """
        self._set_salary(basic=1000)
        self._enable_overtime(method='monthly', amount=200)
        self.assertAlmostEqual(self.employee.overtime_tax, 10.00, places=2)
        self._disable_overtime()

    def test_overtime_junior_exceeds_threshold(self):
        """
        Basic=1,000, overtime=700
        ot_threshold = 1,000 × 50% = 500
        700 > 500 → split
        tax = (500 × 5%) + (200 × 10%) = 25.00 + 20.00 = 45.00
        """
        self._set_salary(basic=1000)
        self._enable_overtime(method='monthly', amount=700)
        self.assertAlmostEqual(self.employee.overtime_tax, 45.00, places=2)
        self._disable_overtime()

    def test_overtime_junior_exactly_at_threshold(self):
        """
        Basic=1,000, overtime=500 (exactly at 50% of basic)
        tax = 500 × 5% = 25.00
        """
        self._set_salary(basic=1000)
        self._enable_overtime(method='monthly', amount=500)
        self.assertAlmostEqual(self.employee.overtime_tax, 25.00, places=2)
        self._disable_overtime()

    def test_overtime_junior_paye_unaffected(self):
        """Junior staff PAYE is computed on base income only, not overtime."""
        self._set_salary(basic=1000)
        paye_no_ot = self.employee.paye_tax
        self._enable_overtime(method='monthly', amount=300)
        self.assertAlmostEqual(self.employee.paye_tax, paye_no_ot, places=2)
        self._disable_overtime()

    # ── Overtime: senior staff ────────────────────────────────────────────────

    def test_overtime_senior_no_separate_tax(self):
        """
        Senior staff (basic > 1,500): overtime_tax = 0,
        PAYE computed on full chargeable including overtime.
        """
        self._set_salary(basic=2500)
        self._enable_overtime(method='monthly', amount=500)
        self.assertEqual(self.employee.overtime_tax, 0.0)
        self._disable_overtime()

    def test_overtime_senior_paye_increases(self):
        """
        Senior staff: PAYE with overtime > PAYE without overtime.
        Basic=2,500, overtime=500
        Without OT: chargeable = 2,500 - 137.50 = 2,362.50 → PAYE = 304.19
        With OT:    chargeable = 3,000 - 137.50 = 2,862.50 → higher PAYE
        """
        self._set_salary(basic=2500)
        paye_no_ot = self.employee.paye_tax
        self._enable_overtime(method='monthly', amount=500)
        self.employee._compute_overtime_amount()
        self.employee._compute_gross_salary()
        self.employee._compute_paye()
        self.employee.flush_recordset()
        self.assertGreater(self.employee.paye_tax, paye_no_ot)
        # Verify exact value: chargeable = 3000 - 137.50 = 2862.50
        expected = self._calc_paye(2862.50)
        self.assertAlmostEqual(self.employee.paye_tax, expected, places=2)
        self._disable_overtime()

    # ── Overtime: hourly method ───────────────────────────────────────────────

    def test_overtime_hourly_amount_computed(self):
        """overtime_amount = hours × rate"""
        self._set_salary(basic=1000)
        self._enable_overtime(method='hourly', hours=10, rate=15.0)
        self.assertAlmostEqual(self.employee.overtime_amount, 150.00, places=2)
        self._disable_overtime()

    def test_overtime_hourly_tax_junior(self):
        """
        Basic=1,000, hours=10, rate=15 → overtime=150
        ot_threshold = 500
        150 < 500 → all at 5%
        overtime_tax = 150 × 5% = 7.50
        """
        self._set_salary(basic=1000)
        self._enable_overtime(method='hourly', hours=10, rate=15.0)
        self.assertAlmostEqual(self.employee.overtime_tax, 7.50, places=2)
        self._disable_overtime()

    # ── Net salary ────────────────────────────────────────────────────────────

    def test_net_salary_2500_no_overtime(self):
        self._set_salary(basic=2500)
        self.assertAlmostEqual(self.employee.net_salary, 2058.31, places=2)

    def test_net_salary_junior_with_overtime(self):
        """
        Basic=1,000, overtime=200
        gross = 1,200, SSNIT = 55, PAYE = 56.12, OT tax = 10.00
        net = 1,200 - 55 - 56.12 - 10.00 = 1,078.88
        """
        self._set_salary(basic=1000)
        self._enable_overtime(method='monthly', amount=200)
        self.assertAlmostEqual(self.employee.gross_salary, 1200.00, places=2)
        self.assertAlmostEqual(self.employee.ssnit_employee, 55.00, places=2)
        self.assertAlmostEqual(self.employee.overtime_tax, 10.00, places=2)
        expected_net = 1200.00 - 55.00 - self.employee.paye_tax - 10.00
        self.assertAlmostEqual(self.employee.net_salary, expected_net, places=2)
        self._disable_overtime()

    def test_net_salary_senior_with_overtime(self):
        """
        Basic=2,500, overtime=500
        gross = 3,000, SSNIT = 137.50, PAYE on 2,862.50, OT tax = 0
        """
        self._set_salary(basic=2500)
        self._enable_overtime(method='monthly', amount=500)
        expected_net = (
            self.employee.gross_salary
            - self.employee.ssnit_employee
            - self.employee.paye_tax
            - self.employee.overtime_tax   # 0 for senior
        )
        self.assertAlmostEqual(self.employee.net_salary, expected_net, places=2)
        self._disable_overtime()

    # ── Company total cost ────────────────────────────────────────────────────

    def test_company_total_cost(self):
        self._set_salary(basic=2500)
        self.assertAlmostEqual(
            self.employee.company_total_cost, 2825.00, places=2)

    # ── Helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def _calc_paye(chargeable):
        BANDS = [
            (490.00,       0.000),
            (600.00,       0.050),
            (730.00,       0.100),
            (3_896.67,     0.175),
            (19_896.67,    0.250),
            (50_416.67,    0.300),
            (float('inf'), 0.350),
        ]
        tax, prev, remaining = 0.0, 0.0, chargeable
        for limit, rate in BANDS:
            if remaining <= 0:
                break
            width = (limit - prev) if limit != float('inf') else remaining
            in_band = min(remaining, width)
            tax += in_band * rate
            remaining -= in_band
            prev = limit
        return round(tax, 2)