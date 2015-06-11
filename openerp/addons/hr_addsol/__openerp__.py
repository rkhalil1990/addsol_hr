# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015-2016 Addition IT Solutions Pvt. Ltd. (<http://www.aitspl.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'HR Services - Addsol',
    'version': '1.0',
    'author': 'Addition IT Solutions Pvt. Ltd.',
    'category': 'Human Resources',
    'summary': 'Attendance Requests & Leaves Management',
    'website': 'https://www.aitspl.com',
    'description': """
HR Services by Addition IT Solutions
====================================
Contact:
    * website: www.aitspl.com
    * email: info@aitspl.com    

Manage different requests:
---------------------------
    * Attendance Requests: generates attendances for employees for e.g. employee forgets to fill his/her attendance or is on official tour
    * Allocation Requests: automated process to generate allocation requests after certain period

Other features:
---------------
    * An employee can cancel his leaves after it is approved.
    * HR person can define a leave rule on leave type for leaves like Sick Leaves and Compensatory Leaves.
    * Automatic process for allocating leaves at the end of every month.
    * Checks employee's late comings of whole month at the end of every month.
    * Leave Type: (Half Day): counts number of days 0.5 in case half day leave type is selected

Few security rules for an employee:
-----------------------------------
    * Not allowed to modify his attendances
    * Can't create allocation request for himself
    * Can see his payslip, salary structure and working schedule
    
""",
    'images': [],
    'depends': ['hr_holidays', 'hr_timesheet_sheet', 'l10n_in_hr_payroll', 
                'base_import_module', 'hr_expense', 'document_ftp'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'hr_addsol_view.xml',
        'hr_addsol_data.xml',
        'hr_addsol_workflow.xml',
        'res_config_view.xml',
        'hr_addsol_report.xml',
        'views/report_employee.xml',
        'wizard/import_install_data_view.xml',
     ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: