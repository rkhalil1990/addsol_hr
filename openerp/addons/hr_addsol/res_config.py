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
from openerp.osv import fields, osv

class addsol_hr_attendance_payroll_config_settings(osv.osv_memory):
    _inherit = 'hr.config.settings'

    _columns = {
        'module_hr_addsol_payroll': fields.boolean('Generate Payroll Based on Attendance',
            help="This installs the module hr_addsol_payroll."),
        'allocation_range': fields.selection([('month','Month'),('year','Year')],
            'Allocate automatic leaves every', required=True,
            help="Periodicity on which you want automatic allocation of leaves to eligible employees."),
    }
    
    def get_default_allocation(self, cr, uid, fields, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return {
            'allocation_range': user.company_id.allocation_range,
        }

    def set_default_allocation(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({
            'allocation_range': config.allocation_range,
        })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: