# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015-2016 Addition IT Solutions Pvt. Ltd. (<http://www.aitspl.com>).
#    @author: Ujjvala Gonsalves
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
Addition IT Solutions Pvt. Ltd.
====================================
Contact :
    * website : www.aitspl.com
    * email   : info@aitspl.com    

Manage different requests
===========================

This application allows you to create different requests like:
    * Attendance Requests: when an employee forgets to fill his/her attendance, when an employee is on official tour
    * Allocation Requests: automated process to generate allocation requests after certain period

Other Features:
---------------
    * An employee can cancel his leaves after it is approved.
    * HR person can define a leave rule on leave type for leaves like Sick Leaves and Compensatory Leaves.
    * Automatic process for allocating leaves at the end of every month.
    * Creates automatic leaves for no attendances.
    * Employee is allowed to put expenses with only allowed limits.

Few security rules for an employee like:
------------------------------------------------
    * Should not be able to modify his attendances
    * Should not create allocation request for himself
    
""",
    'images': [],
    'depends': ['hr_holidays', 'hr_expense', 'hr_timesheet_sheet', 'hr_payroll_account'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'hr_addsol_view.xml',
        'hr_addsol_data.xml',
        'hr_addsol_workflow.xml',
     ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: