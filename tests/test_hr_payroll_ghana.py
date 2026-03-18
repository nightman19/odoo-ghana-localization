"""
Tests for gh_localization Ghana PAYE & SSNIT calculations.

Run via Docker:
    docker compose run --rm test

Run directly (requires Odoo environment):
    odoo --test-enable --test-tags gh_localization --stop-after-init
"""

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('gh_localization', 'gh_payroll')
class TestGhanaPayroll(TransactionCase):
    """Unit tests for Ghana PAYE and SSNIT computed fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Minimal employee — we override salary fields per test
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee GH',
            'exempt_from_ssnit': False,
            'exempt_from_paye': False,
        })

    def _set_salary(self, basic, transport=0.0, housing=0.0):
        """Helper: update salary fields and flush computed fields."""
        self.employee.write({
            'basic_salary': basic,
            'transport_allowance': transport,
            'housing_allowance': housing,
        })
        self.employee.flush_recordset()

    # ── Gross salary ──────────────────────────────────────────────────────────

    def test_gross_salary_basic_only(self):
        self._set_salary(basic=2500)
        self.assertAlmostEqual(self.employee.gross_salary, 2500.00, places=2)

    def test_gross_salary_with_allowances(self):
        self._set_salary(basic=2500, transport=300, housing=500)
        self.assertAlmostEqual(self.employee.gross_salary, 3300.00, places=2)

    # ── SSNIT ─────────────────────────────────────────────────────────────────

    def test_ssnit_standard(self):
        """5.5% employee / 13% employer on basic salary."""
        self._set_salary(basic=2500)
        self.assertAlmostEqual(self.employee.ssnit_employee, 137.50, places=2)
        self.assertAlmostEqual(self.employee.ssnit_employer, 325.00, places=2)

    def test_ssnit_capped_at_annual_61000(self):
        """SSNIT insurable earnings cap: GH₵61,000/yr → GH₵5,083.33/month."""
        self._set_salary(basic=10_000)  # above cap
        cap = 61_000 / 12
        self.assertAlmostEqual(self.employee.ssnit_employee, round(cap * 0.055, 2), places=2)
        self.assertAlmostEqual(self.employee.ssnit_employer, round(cap * 0.130, 2), places=2)

    def test_ssnit_exempt(self):
        self._set_salary(basic=2500)
        self.employee.exempt_from_ssnit = True
        self.employee.flush_recordset()
        self.assertEqual(self.employee.ssnit_employee, 0.0)
        self.assertEqual(self.employee.ssnit_employer, 0.0)

    def test_ssnit_on_basic_not_gross(self):
        """SSNIT is calculated on basic salary only, not allowances."""
        self._set_salary(basic=2500, transport=500, housing=500)
        # gross = 3500, but SSNIT must still use 2500
        self.assertAlmostEqual(self.employee.ssnit_employee, 137.50, places=2)

    # ── PAYE ──────────────────────────────────────────────────────────────────

    def test_paye_2500_basic(self):
        """
        GH₵2,500 basic, no allowances.
        Chargeable = 2500 - 137.50 = 2362.50/month
        Band 1: 490    × 0%    =    0.00
        Band 2: 110    × 5%    =    5.50
        Band 3: 130    × 10%   =   13.00
        Band 4: 1632.50 × 17.5% = 285.69  (rounds to 285.69)
        → monthly PAYE = 304.19
        """
        self._set_salary(basic=2500)
        self.assertAlmostEqual(self.employee.paye_tax, 304.19, places=2)

    def test_paye_zero_income(self):
        self._set_salary(basic=0)
        self.assertEqual(self.employee.paye_tax, 0.0)

    def test_paye_within_free_band(self):
        """Income fully within the 0% band → zero tax."""
        self._set_salary(basic=490)
        ssnit = round(490 * 0.055, 2)
        chargeable = 490 - ssnit
        # chargeable = 462.55, still within GH₵490 free band
        self.assertEqual(self.employee.paye_tax, 0.0)

    def test_paye_exempt(self):
        self._set_salary(basic=5000)
        self.employee.exempt_from_paye = True
        self.employee.flush_recordset()
        self.assertEqual(self.employee.paye_tax, 0.0)

    def test_paye_uses_chargeable_not_gross(self):
        """
        Regression: PAYE must be on chargeable income (gross - SSNIT),
        NOT on gross salary directly.
        """
        self._set_salary(basic=2500)
        gross_based_paye = self._compute_paye_on_value(2500.00)
        chargeable_based_paye = self._compute_paye_on_value(2500.00 - 137.50)
        # The stored value must match the chargeable-based calculation
        self.assertAlmostEqual(self.employee.paye_tax, chargeable_based_paye, places=2)
        self.assertNotAlmostEqual(self.employee.paye_tax, gross_based_paye, places=2)

    def test_paye_high_income_hits_35_band(self):
        """Income of GH₵60,000/month reaches the 35% band.
        Chargeable = 60,000 - SSNIT cap (279.58) = 59,720.42
        This exceeds the 30% band ceiling of 50,416.67, so 35% applies
        on the remainder. Effective rate is ~28.3% (not 30%+ — lower
        bands drag the effective rate below the marginal rate).
        """
        self._set_salary(basic=60_000)
        self.assertGreater(self.employee.paye_tax, 0)
        effective_rate = self.employee.paye_tax / self.employee.gross_salary
        self.assertGreater(effective_rate, 0.25)
        self.assertLess(effective_rate, 0.35)
        self.assertAlmostEqual(self.employee.paye_tax, 16_984.98, places=1)

    def test_paye_allowances_are_taxable(self):
        """Cash allowances increase assessable income and therefore PAYE."""
        self._set_salary(basic=2500)
        paye_no_allowances = self.employee.paye_tax

        self._set_salary(basic=2500, transport=500)
        paye_with_allowances = self.employee.paye_tax

        self.assertGreater(paye_with_allowances, paye_no_allowances)

    # ── Net salary ────────────────────────────────────────────────────────────

    def test_net_salary_2500(self):
        """Net = gross - PAYE - SSNIT(employee). Expected GH₵2,058.31."""
        self._set_salary(basic=2500)
        self.assertAlmostEqual(self.employee.net_salary, 2058.31, places=2)

    def test_net_salary_never_negative_on_exemptions(self):
        self._set_salary(basic=2500)
        self.employee.write({'exempt_from_paye': True, 'exempt_from_ssnit': True})
        self.employee.flush_recordset()
        self.assertAlmostEqual(self.employee.net_salary, 2500.00, places=2)

    # ── Company cost ──────────────────────────────────────────────────────────

    def test_company_total_cost(self):
        """Total cost = gross + employer SSNIT (13%)."""
        self._set_salary(basic=2500)
        # gross=2500, employer SSNIT = 2500 * 13% = 325
        self.assertAlmostEqual(self.employee.company_total_cost, 2825.00, places=2)

    # ── Helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_paye_on_value(chargeable):
        """Standalone band calculation for regression comparisons."""
        BANDS = [
            (490.00,     0.000),
            (600.00,     0.050),
            (730.00,     0.100),
            (3_896.67,   0.175),
            (19_896.67,  0.250),
            (50_416.67,  0.300),
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