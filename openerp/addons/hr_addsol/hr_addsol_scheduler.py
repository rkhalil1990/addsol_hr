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
import logging
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone
import pytz

from openerp.osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

def _get_timezone_employee(employee, date):
    tz = employee.user_id.partner_id.tz
    att_tz = timezone(tz or 'utc')
    attendance_dt = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
    att_tz_dt = pytz.utc.localize(attendance_dt)
    att_tz_dt = att_tz_dt.astimezone(att_tz)
    return att_tz_dt

class addsol_hr_attendance(osv.osv):
    _inherit = 'hr.attendance'
    
    def _total_worked_hours(self, cr, uid, ids, fieldnames, args, context=None):
        total_worked_hours = 0.0
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = 0.0
            if obj.action == 'sign_in':
                res[obj.id] = 0.0
            if obj.action == 'sign_out':
                name = (datetime.strptime(obj.name, '%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%d')
                total_ids = self.search(cr, uid, [
                            ('name','>=',name+' 00:00:00'),
                            ('name','<=',name+' 23:59:59'),
                            ('employee_id', '=', obj.employee_id.id),
                            ('action','=','sign_out')
                        ], order='name DESC')
                total_worked_hours = 0.0
                if total_ids:
                    for rec in self.browse(cr, uid, total_ids, context=context):
                        total_worked_hours += rec.worked_hours
                    res[total_ids[0]] = total_worked_hours
        return res
    
    def _worked_hours_compute(self, cr, uid, ids, fieldnames, args, context=None):
        """For each hr.attendance record of action sign-in: assign 0.
        For each hr.attendance record of action sign-out: assign number of hours since last sign-in.
        """
        res = super(addsol_hr_attendance, self)._worked_hours_compute(cr, uid, ids, fieldnames, args, context)
        return res
    
    _columns = {
        'worked_hours': fields.function(_worked_hours_compute, type='float', string='Worked Hours'),
        'total_worked_hours': fields.function(_total_worked_hours, type='float', string='Total Worked Hours'),
    }

class addsol_hr_holidays(osv.osv):
    _inherit = "hr.holidays"
    
    def check_late_coming_employees(self, cr, uid, attendance_ids, context=None):
        employee_obj = self.pool.get('hr.employee')
        leave_status_obj = self.pool.get('hr.holidays.status')
        attendance_obj = self.pool.get('hr.attendance')
        holiday_status_id = leave_status_obj.search(cr, uid, [('type','=','half')], context=context)
        for attendance in attendance_obj.browse(cr, uid, attendance_ids, context=context):
            attendance_dt = _get_timezone_employee(attendance.employee_id, attendance.name)
            half_leave_ids = self.search(cr, uid, [('date_from','>=',attendance_dt.strftime('%Y-%m-%d 00:00:00')),
                                                   ('date_to','<=',attendance_dt.strftime('%Y-%m-%d 23:59:59')),
                                                   ('employee_id','=',attendance.employee_id.id),
                                                   ('type','=','remove'),
                                                   ('holiday_status_id','=', holiday_status_id and holiday_status_id[0])])
            if half_leave_ids:
                continue
            calendar_id = attendance.employee_id.contract_id.working_hours or False
            if calendar_id:
                sign_in_time = attendance_dt.strftime("%H.%M")
                calendar_val = employee_obj._get_daily_attendance(cr, uid, attendance)
                late_time = calendar_val.get('entry_time') + (calendar_id.late_time * 0.01)
                if attendance.action == 'sign_in' and (float(sign_in_time) > late_time or \
                    calendar_val.get('worked_hours') < calendar_val.get('working_hours')):
                    return True
        return False

    def run_monthly_scheduler(self, cr, uid, context=None):
        """ Runs at the end of every month to allocate PL, CL & SL to all 
        eligible employees.
        """
        employee_obj = self.pool.get('hr.employee')
        leave_status_obj = self.pool.get('hr.holidays.status')
        date_from  = datetime.strftime((datetime.now() + relativedelta(months=1) + relativedelta(day=1)),'%Y-%m-%d')
        date_to  = datetime.strftime((datetime.now() + relativedelta(months=1) + relativedelta(day=31)),'%Y-%m-%d')

        employee_ids = employee_obj.search(cr, uid, [('eligible','=',True)], context=context)
        holiday_status_ids = leave_status_obj.search(cr, uid, [], context=context)
        for holiday_status in leave_status_obj.browse(cr, uid, holiday_status_ids, context=context):
            for emp in employee_obj.browse(cr, uid, employee_ids, context=context):
                if holiday_status.company_id.id == (emp.user_id.company_id and emp.user_id.company_id.id):
                    allocation_range = emp.user_id.company_id and emp.user_id.company_id.allocation_range or 'month'
                    allocate_days = holiday_status.days_to_allocate
                    if allocate_days > 0:
                        if time.strftime('%B') == 'December':
                            days_left = leave_status_obj.get_days(cr, uid, [holiday_status.id], emp.id, context=context)
                            days_left = days_left[holiday_status.id]['remaining_leaves']
                            if days_left <= 12:
                                allocate_days += days_left
                        if allocation_range == 'month':
                            allocate_ids = self.search(cr, uid, [('date_from','>=',date_from), 
                                                                      ('date_to','<=',date_to), 
                                                                      ('type','=','add'), 
                                                                      ('employee_id','=',emp.id),
                                                                      ('holiday_status_id','=',holiday_status.id)], context=context)
                            if allocate_ids:
                                continue
                            vals = {
                                    'name': 'Monthly Allocation of '+ holiday_status.type,
                                    'number_of_days_temp': allocate_days,
                                    'date_from': date_from,
                                    'date_to': date_to,
                                    'employee_id': emp.id,
                                    'holiday_status_id': holiday_status.id,
                                    'type': 'add',
                            }
                        if allocation_range == 'year':
                            allocate_ids = self.search(cr, uid, [('type','=','add'), 
                                                                 ('employee_id','=',emp.id),
                                                                 ('holiday_status_id','=',holiday_status.id)], context=context)
                            if allocate_ids:
                                continue
                            vals = {
                                    'name': 'Yearly Allocation of '+ holiday_status.type,
                                    'number_of_days_temp': allocate_days,
                                    'employee_id': emp.id,
                                    'holiday_status_id': holiday_status.id,
                                    'type': 'add',
                            }
                        leave_id = self.create(cr, uid, vals, context=context)
                        self.holidays_validate(cr, uid, [leave_id], context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
