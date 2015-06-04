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
    'name': 'HR Services Payroll - Addsol',
    'version': '1.0',
    'author': 'Addition IT Solutions Pvt. Ltd.',
    'category': 'Human Resources',
    'summary': 'Payroll Management with Attendances',
    'website': 'https://www.aitspl.com',
    'description': """
HR Services by Addition IT Solutions
====================================
Contact:
    * website: www.aitspl.com
    * email: info@aitspl.com    

Manage Payroll:
---------------
    * Payroll will be dependent on attendances. If no attendance then no pay.
    
""",
    'images': [],
    'depends': ['hr_attendance','hr_payroll','l10n_in_hr_payroll'],
    'data': [
       'hr_addsol_payroll_data.xml',
       'wizard/send_advice_to_bank_view.xml',
       'hr_addsol_payroll_view.xml',
       
     ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: