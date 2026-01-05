# Odoo Ghana Localization

Complete payroll localization module for Odoo 19 Community Edition, implementing Ghana's 2025 tax regulations.

## Features

✅ **2025 PAYE Tax Calculation**
- 6-tier progressive tax brackets (0% - 30%)
- Automatic tax computation based on gross income
- Compliant with Ghana Revenue Authority regulations

✅ **SSNIT Contributions**
- Employee contribution: 5.5%
- Employer contribution: 13%
- Automatic ceiling enforcement (GHS 61,000 annual maximum)
- Tier 1 and Tier 2 breakdown

✅ **Automatic Salary Computations**
- Gross salary calculation
- Net salary calculation
- Real-time updates as salary components change

✅ **Custom Employee Fields**
- Basic Salary
- Transport Allowance
- Housing Allowance
- Monthly deductions breakdown

## Installation

### Prerequisites
- Odoo 19.0 Community Edition
- PostgreSQL
- Python 3.8+

### Install Module

1. **Clone the repository:**
```bash
cd /path/to/odoo/addons
git clone https://github.com/nightman19/odoo-ghana-localization.git gh_localization
```

2. **Restart Odoo:**
```bash
# If using Docker
docker-compose restart

# If running natively
sudo systemctl restart odoo
```

3. **Update Apps List:**
   - Go to Apps menu in Odoo
   - Click "Update Apps List"
   - Wait for update to complete

4. **Install the module:**
   - Search for "Ghana Localization"
   - Click "Activate"

## Usage

### Configure Employee Payroll

1. **Navigate to Employees:**
   - Go to Employees menu
   - Select an employee or create new

2. **Add salary information:**
   - Click the "Ghana Payroll" tab
   - Enter Basic Salary
   - Add allowances (Transport, Housing)
   - All calculations update automatically

3. **View payroll breakdown:**
   - Gross Salary (auto-calculated)
   - PAYE Tax (auto-calculated)
   - SSNIT Employee contribution (auto-calculated)
   - SSNIT Employer contribution (auto-calculated)
   - Net Salary (auto-calculated)

## Tax Rates (2025)

### PAYE (Pay As You Earn)

| Monthly Income (GHS) | Tax Rate |
|---------------------|----------|
| 0 - 490 | 0% |
| 491 - 660 | 5% |
| 661 - 3,750 | 10% |
| 3,751 - 20,000 | 17.5% |
| 20,001 - 60,000 | 25% |
| Above 60,000 | 30% |

### SSNIT (Social Security)

- **Total Rate:** 18.5% of basic salary
- **Employee:** 5.5%
- **Employer:** 13%
- **Maximum Insurable Income:** GHS 61,000 per year (GHS 5,083.33 per month)
- **Distribution:**
  - Tier 1 (Basic SSNIT): 13.5%
  - Tier 2 (Occupational Pension): 5%

## Example Calculation

**Employee Salary:**
- Basic Salary: GHS 5,000.00
- Transport Allowance: GHS 1,000.00
- Housing Allowance: GHS 500.00

**Results:**
- Gross Salary: GHS 6,500.00
- PAYE Tax: GHS 798.75
- SSNIT (Employee): GHS 275.00
- SSNIT (Employer): GHS 650.00
- **Net Salary: GHS 5,426.25**

## Module Structure
```
gh_localization/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── hr_payroll_ghana.py
└── views/
    └── employee_views.xml
```

## Technical Details

### Models

**`hr.employee` (inherited)**
- Extends the standard Odoo employee model
- Adds Ghana-specific payroll fields
- Implements automatic tax calculations

### Computed Fields

All calculations are performed using Odoo's `@api.depends` decorators:
- `_compute_gross_salary()` - Sums all salary components
- `_compute_paye()` - Applies progressive tax brackets
- `_compute_ssnit()` - Calculates social security contributions
- `_compute_net_salary()` - Deducts taxes from gross

## Development

### Local Development Setup
```bash
# Clone Odoo 19
git clone https://github.com/odoo/odoo.git --depth 1 --branch 19.0

# Install dependencies
pip3 install -r odoo/requirements.txt

# Clone this module
cd odoo/addons
git clone https://github.com/nightman19/odoo-ghana-localization.git gh_localization

# Run Odoo
./odoo-bin --addons-path=addons --dev=all
```

### Running Tests
```bash
# Run module tests
./odoo-bin --test-enable --stop-after-init -i gh_localization -d test_db
```

## Roadmap

- [ ] PDF Payslip generation with Ghana format
- [ ] Bank payment file export (Ghana banks)
- [ ] GRA E-VAT integration
- [ ] Mobile Money payment integration
- [ ] Multi-currency support
- [ ] Historical tax rate support (2023, 2024)
- [ ] Bonus and overtime calculations
- [ ] Twi language translation

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Commit your changes:** `git commit -m 'Add amazing feature'`
4. **Push to the branch:** `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Areas Needing Contribution

- [ ] Unit tests for tax calculations
- [ ] Additional allowance types
- [ ] Integration with Odoo Accounting module
- [ ] PDF report templates
- [ ] Documentation improvements

## Compliance & Disclaimer

This module implements tax calculations based on the **2025 Ghana Revenue Authority tax rates** as published. 

**Important:**
- Tax rates and regulations may change
- Users are responsible for verifying compliance with current GRA regulations
- This software is provided "as-is" without warranty
- Always consult with a qualified tax professional for compliance matters

## License

**LGPL-3.0** - This module follows Odoo's licensing model.

See [LICENSE](LICENSE) file for details.

## Credits

**Author:** Umaru Nuru Mohammed

**Built with:**
- [Odoo](https://www.odoo.com) - Open Source ERP
- Python 3
- PostgreSQL

## Support

- **Issues:** [GitHub Issues](https://github.com/nightman19/odoo-ghana-localization/issues)
- **Documentation:** [Odoo Documentation](https://www.odoo.com/documentation/19.0/)
- **GRA Guidelines:** [Ghana Revenue Authority](https://gra.gov.gh)

## Changelog

### Version 1.0.0 (2025-01-04)
- Initial release
- PAYE calculation with 2025 rates
- SSNIT contribution calculation
- Custom employee payroll tab
- Automatic gross/net salary computation

---

**Star ⭐ this repo if you find it useful!**

**Made with ❤️ for Ghanaian businesses**