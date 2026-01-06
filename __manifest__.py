
{
    'name': 'Ghana Localization',
    'version': '1.0.0',
    'category': 'Human Resources',
    'summary': 'Ghana PAYE & SSNIT Calculator for Employees',
    'description': """
        Ghana Payroll Calculator
        ========================
        * 2025 PAYE tax calculation
        * SSNIT contribution calculation
        * Automatic gross/net salary computation
        * Direct integration with employee records
    """,
    'author': 'Umaru Nuru Mohammed',
    'website': 'https://github.com/nightman19',
    'depends': ['hr'],
    'data': [
        'views/employee_views.xml',
        'views/payslip_report.xml',
        'views/payroll_summary.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}