# Ghana Localization — `gh_localization`

Complete payroll localization module for **Odoo 19 Community Edition**, implementing Ghana's **2026 GRA tax regulations** with automated PAYE, SSNIT, overtime, payslip PDF generation, and multi-client deployment support.

---

## Features

### ✅ 2026 PAYE Tax Calculation
- 7-band progressive tax on **chargeable income** (gross − SSNIT), per GRA 2026 schedule
- Correct band widths including the 30% and 35% top bands
- Automated calculation — no manual spreadsheet entry

### ✅ SSNIT Contributions
- Employee: 5.5% of basic salary
- Employer: 13% of basic salary
- Annual insurable earnings cap: GHS 61,000 (GHS 5,083.33/month)
- SSNIT-exempt flag per employee (contractors, casual staff)

### ✅ Configurable Overtime Engine
- Company-level master switch — businesses that don't pay overtime see nothing
- Per-employee opt-in with override
- Two calculation methods: **monthly fixed amount** or **hourly rate × hours**
- Junior staff (basic ≤ configurable threshold): 5% on first 50% of basic, 10% on excess
- Senior staff: overtime folded into chargeable income, taxed via progressive PIT bands

### ✅ PDF Payslip Generation
- Individual and batch payslip generation via "Select Period" wizard
- Earnings section: Basic Salary, Allowances, Overtime
- Deductions section: PAYE Tax, Overtime Tax (junior staff), SSNIT
- SSNIT breakdown and 2026 tax rate reference on each payslip
- Company logo, address, and Ghana Cedis (GHS) currency

### ✅ Payroll Summary PDF Report
- One-click summary for all employees for a selected period
- Columns: Employee, Department, Basic, Gross, PAYE, SSNIT (Employee), SSNIT (Employer), Net
- Totals row and employer contribution summary
- Correctly named files: `Payroll_Summary_Month_Year.pdf`

### ✅ Automatic Salary Computations
- Gross = Basic + Transport + Housing + Overtime (when enabled)
- PAYE computed on chargeable income (gross − SSNIT), not gross salary
- Net = Gross − PAYE − SSNIT (employee) − Overtime Tax
- Total Company Cost = Gross + SSNIT (employer)
- All fields re-compute automatically when any input changes

### ✅ PAYE & SSNIT Exemptions
- Per-employee boolean flags: `Exempt from PAYE`, `Exempt from SSNIT`
- Useful for casual/part-time staff, contractors, or staff below tax threshold

### ✅ 27-Test Suite
- Full unit test coverage: PAYE bands, SSNIT cap, overtime (junior/senior, monthly/hourly), net salary, exemptions
- Regression guards to prevent reintroduction of known bugs
- Run against a dedicated `odoo_test` Docker database

---

## Tax Rates (2026 GRA Schedule)

### PAYE — Monthly Bands (applied to chargeable income)

| Monthly Band (GHS) | Band Width | Rate |
|---|---|---|
| First 490.00 | 490.00 | 0% |
| Next 110.00 | 110.00 | 5% |
| Next 130.00 | 130.00 | 10% |
| Next 3,166.67 | 3,166.67 | 17.5% |
| Next 16,000.00 | 16,000.00 | 25% |
| Next 30,520.00 | 30,520.00 | 30% |
| Above 50,416.67 | — | 35% |

> **Important:** PAYE is computed on **chargeable income** (gross salary minus SSNIT deduction), not on gross salary directly.

### SSNIT (Social Security)

| | Rate | Cap |
|---|---|---|
| Employee (Tier 1) | 5.5% | GHS 61,000/yr |
| Employer (Tier 1) | 13.0% | GHS 61,000/yr |
| **Total** | **18.5%** | |

### Overtime Tax Rates (GRA)

| Staff Type | Rule |
|---|---|
| Junior (basic ≤ threshold) | 5% on OT up to 50% of basic; 10% on excess |
| Senior (basic > threshold) | Added to chargeable income, taxed progressively |

Default junior threshold: **GHS 1,500/month** (configurable per company)

---

## Example Calculation

**Employee: Senyo Amegah — GHS 2,500 basic salary, no allowances**

| Step | Amount |
|---|---|
| Basic Salary | 2,500.00 |
| SSNIT (Employee 5.5%) | 137.50 |
| Chargeable Income | 2,362.50 |
| PAYE (on chargeable) | 304.19 |
| **Net Salary** | **2,058.31** |
| SSNIT (Employer 13%) | 325.00 |
| **Total Company Cost** | **2,825.00** |

---

## Module Structure

```
gh_localization/
├── __init__.py
├── __manifest__.py
├── data/
│   └── default_user_action.xml      # Sets Payroll Summary as default home page
├── models/
│   ├── __init__.py
│   ├── hr_payroll_ghana.py          # Core PAYE, SSNIT, overtime computed fields
│   ├── payroll_wizard.py            # Period selector + PDF generation logic
│   ├── report_employee_payslip.py   # Individual payslip report model
│   ├── report_payroll_summary.py    # Payroll summary report model
│   └── res_company.py               # Company-level overtime settings
├── reports/
│   └── payroll_summary_pdf.xml      # QWeb template: Payroll Summary PDF
├── security/
│   └── ir.model.access.csv
├── tests/
│   ├── __init__.py
│   └── test_gh_payroll.py           # 27 unit tests
└── views/
    ├── company_views.xml             # Ghana Payroll tab on company form
    ├── employee_views.xml            # Ghana Payroll tab on employee form
    ├── payroll_summary.xml           # Payroll Summary list view + menu
    ├── payroll_wizard_views.xml      # Select Period wizard UI
    ├── payslip_report.xml            # QWeb template: Individual payslip PDF
    └── ssnit_report.xml              # SSNIT Tier 1 & Tier 2 report templates
```

---

## Installation

### Prerequisites
- Odoo 19.0 Community Edition
- PostgreSQL 15
- Docker + docker-compose (recommended)
- Python 3.10+

### Docker Setup (Recommended)

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: your_secure_password
    volumes:
      - odoo-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U odoo"]
      interval: 5s
      timeout: 5s
      retries: 10

  web:
    image: odoo:19
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "127.0.0.1:8069:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons
      - ./config:/etc/odoo
    environment:
      HOST: db
      USER: odoo
      PASSWORD: your_secure_password

volumes:
  odoo-web-data:
  odoo-db-data:
```

```ini
# config/odoo.conf
[options]
proxy_mode = True
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
```

### Install Module

```bash
# Clone into your addons folder
cd /path/to/odoo/addons
git clone https://github.com/nightman19/odoo-ghana-localization.git gh_localization

# Initialize database with module
docker compose exec web odoo \
  --db_host=db --db_port=5432 \
  --db_user=odoo --db_password=your_secure_password \
  --database your_database \
  --init gh_localization \
  --stop-after-init --log-level warn

docker compose restart web
```

### Update Existing Installation

```bash
git pull origin main

docker compose exec web odoo \
  --db_host=db --db_port=5432 \
  --db_user=odoo --db_password=your_secure_password \
  --database your_database \
  --update gh_localization \
  --stop-after-init --log-level warn

docker compose restart web
```

---

## Running Tests

```bash
# Drop any stale test database first
docker compose exec db psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS odoo_test;"

# Run the full 27-test suite
docker compose run --rm test
```

Add a `test` service to your `docker-compose.yml`:

```yaml
test:
  image: odoo:19
  depends_on:
    db:
      condition: service_healthy
  volumes:
    - odoo-web-data:/var/lib/odoo
    - ./addons:/mnt/extra-addons
    - ./config:/etc/odoo
  environment:
    HOST: db
    USER: odoo
    PASSWORD: your_secure_password
  command: >
    odoo
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
    --database odoo_test
    --init gh_localization
    --test-enable
    --test-tags gh_localization
    --stop-after-init
    --log-level test
```

---

## Usage

### 1. Configure Company Settings
Go to **Settings → Companies → [Company] → Ghana Payroll tab**
- Enter SSNIT Employer Number
- Toggle **Enable Overtime** if the business pays overtime
- Set **Junior Staff Threshold** (default GHS 1,500/month)

### 2. Configure Employee Payroll
Go to **Employees → [Employee] → Ghana Payroll tab**
- Enter Basic Salary, Transport Allowance, Housing Allowance
- Set exemption flags if applicable
- Enable overtime per employee (if company has it enabled)
- All deductions and net salary compute automatically

### 3. Generate Payslips
Go to **Employees → Payroll Summary**
- Select employees → **Print → Generate Payslips**
- Choose Month and Year in the wizard
- Downloads `Payslips_Month_Year.pdf` with individual payslip per employee

### 4. Generate Payroll Summary Report
Go to **Employees → Payroll Summary**
- Select employees → **Print → Generate Summary PDF**
- Downloads `Payroll_Summary_Month_Year.pdf` with full payroll table

---

## Production Deployment

For production deployment with nginx reverse proxy and Let's Encrypt SSL, use the included `setup_client.sh` script (available separately). It handles:
- Docker installation and configuration
- nginx reverse proxy setup
- SSL certificate via Let's Encrypt (auto-renewed)
- Database initialization with `gh_localization`
- Automated daily backups (7-day retention)
- Credentials file generation

---

## Changelog

### v1.4.0 — 2026-07
- Fix: Overtime toggle defaulting to off in new databases — added post-setup verification
- Fix: Overtime lines not appearing on payslip PDF — added earnings and deductions rows
- Fix: Total Deductions formula on payslip now includes overtime_tax
- Chore: Update tax rates label from "2025" to "2026" on payslip
- Chore: Fix manifest load order (payroll_wizard_views before payroll_summary)
- Chore: Track data/default_user_action.xml in git

### v1.3.0 — 2026-06
- Feat: Overtime calculations with company-level toggle
- Feat: Junior staff 5%/10% overtime tax, senior staff progressive PIT
- Feat: Monthly and hourly overtime methods, per-employee override
- Test: 27-unit test suite covering all PAYE, SSNIT, and overtime scenarios

### v1.2.0 — 2026-03
- Feat: PAYE and SSNIT exemption flags per employee
- Feat: Payroll Summary PDF report with employer contribution summary
- Fix: Python 2 base64 encoding replaced with Python 3 base64 module
- Fix: Employee IDs correctly passed to payroll summary PDF renderer
- Fix: Restore Select Period button in Payroll Summary view

### v1.1.0 — 2026-03
- Fix: 6 bugs in PAYE calculation
  - Wrong 6-band table → correct 7-band 2026 GRA monthly bands
  - PAYE computed on gross salary → now uses chargeable income (gross − SSNIT)
  - Missing 30% band (GHS 19,897–50,417/month)
  - Missing 35% top band (above GHS 50,417/month)
  - Missing `store=True` on `company_total_cost`
  - Missing `ssnit_employee` in `@api.depends` for `_compute_paye`
- Feat: Payslip PDF with earnings, deductions, SSNIT breakdown, and tax rate reference
- Feat: Batch payslip generation via Select Period wizard
- Test: Initial 16-test suite

### v1.0.0 — 2025-01
- Initial release: PAYE + SSNIT on employee records, Ghana Payroll tab

---

## Compliance & Disclaimer

This module implements tax calculations based on the **2026 Ghana Revenue Authority PAYE schedule** and current SSNIT rates.

- Tax rates and regulations may change — the module is updated when GRA publishes new rates
- Users are responsible for verifying compliance with current GRA regulations
- Always consult a qualified tax professional for compliance matters
- This software is provided "as-is" without warranty

---

## License

**LGPL-3.0** — follows Odoo's standard licensing model.

---

## Author

```
Umaru Nuru Mohammed
Full-Stack & ERP Engineer
nurumohammed.dev@gmail.com
+233 50 348 5540
```
Built for Ghanaian businesses. Contributions welcome.