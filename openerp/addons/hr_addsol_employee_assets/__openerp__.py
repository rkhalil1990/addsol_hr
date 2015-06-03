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
    'name': 'HR Employee Assets - Addsol',
    'version': '1.0',
    'author': 'Addition IT Solutions Pvt. Ltd.',
    'category': 'Human Resources',
    'summary': 'Employee Assets',
    'website': 'https://www.aitspl.com',
    'description': """
HR Employee Assets by Addition IT Solutions
====================================
Contact:
    * website: www.aitspl.com
    * email: info@aitspl.com    

Functionality:
* Employee will mention date & quantity of the asset he wants, in the request.
* When admin approves the request, quantity will be deducted from the inventory & end date will be stored.
* When employee returns the asset, return date will be stored & again inventory will be updated

    
""",
    'images': [],
    'depends': ['hr_addsol'],
    'data': [
        'security/ir.model.access.csv',
        'hr_addsol_employee_assets_view.xml',
     ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: