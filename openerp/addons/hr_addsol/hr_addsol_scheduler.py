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
from datetime import datetime, timedelta
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
    
    def run_daily_scheduler(self, cr, uid, context=None):
        """ Runs at the end of the day to check attendances of employees.
        And creates leaves if attendance criteria is not satisfied.
        """
        
        _logger.info("Running daily attendance scheduler...")
        employee_obj = self.pool.get('hr.employee')
        leave_obj = self.pool.get('hr.holidays')
        leave_status_obj = self.pool.get('hr.holidays.status')
        user_obj = self.pool.get('res.users')
        calendar_obj = self.pool.get('addsol.hr.calendar')
        users = user_obj.search(cr, uid, [], context=context)
        employees = employee_obj.search(cr, uid, [('user_id','in', users)], context=context)
        current_date = time.strftime('%Y-%m-%d')
        
        # Returns if the current day is a public holiday
        public_holiday = calendar_obj.search(cr, uid, [('date_from','=',current_date)], context=context) and True or False
        if public_holiday:
            return
        
        attendance_ids = self.search(cr, uid, [('name','>=',current_date+' 00:00:00'),('name','<=',current_date+' 23:59:59'),('employee_id','in',employees)], context=context)
        holiday_status_id = leave_status_obj.search(cr, uid, [('type','=','unpaid')], context=context)
        employees_present = []
        domain = [('type','=','remove'),('date_from','>=',current_date+' 00:00:00'),('date_from','<=',current_date+' 23:59:59')]
        for attendance in self.browse(cr, uid, attendance_ids, context=context):
            if attendance.employee_id.id not in employees_present:
                employees_present.append(attendance.employee_id.id)
            values = {}
            leave_ids = leave_obj.search(cr, uid, domain + [('employee_id','=',attendance.employee_id.id)], context=context)
            hours_count = attendance.worked_hours
            if not leave_ids:
                if hours_count < 5 and attendance.action != 'sign_in':
                    values = {
                            'name': 'Full Day - Late Coming',
                            'date_from': current_date,
                            'date_to': current_date,
                            'number_of_days_temp': 1.0,
                            'holiday_status_id': holiday_status_id and holiday_status_id[0] or 1,
                            'employee_id': attendance.employee_id.id,
                            'type': 'remove',
                    }
                elif hours_count >= 5 and hours_count <= 7.45: # Currently fixed value, has to be changed according to company calendar
                    values = {
                            'name': 'Half Day - Late Coming',
                            'date_from': attendance.name,
                            'date_to': attendance.name,
                            'number_of_days_temp': 0.5,
                            'holiday_status_id': holiday_status_id and holiday_status_id[0] or 1,
                            'employee_id': attendance.employee_id.id,
                            'type': 'remove',
                    }
                if values:
                    leave_id = leave_obj.create(cr, uid, values, context=context)
#                     leave_obj.holidays_validate(cr, uid, [leave_id], context=context)

        # For employees who have not marked their attendance
        if len(employees_present) != len(employees):
            absent_employees = [emp for emp in employees if emp not in employees_present]
            for absent_employee in absent_employees:
                emp = employee_obj.browse(cr, uid, absent_employee, context=context)
                leave_ids = leave_obj.search(cr, uid, domain + [('employee_id','=',emp.id)], context=context)
                if not leave_ids:
                    values = {
                            'name': 'No Attendance Marked',
                            'date_from': current_date,
                            'date_to': current_date,
                            'number_of_days_temp': 1.0,
                            'holiday_status_id': holiday_status_id and holiday_status_id[0] or 1,
                            'employee_id': emp.id,
                            'type': 'remove',
                    }
                    leave_id = leave_obj.create(cr, uid, values, context=context)
#                     leave_obj.holidays_validate(cr, uid, [leave_id], context=context)

class addsol_hr_holidays(osv.osv):
    _inherit = "hr.holidays"
    
    def check_late_coming_employees(self, cr, uid, context=None):
        employee_obj = self.pool.get('hr.employee')
        leave_status_obj = self.pool.get('hr.holidays.status')
        attendance_obj = self.pool.get('hr.attendance')
        date_from  = datetime.strftime((datetime.now() + relativedelta(day=1)),'%Y-%m-%d %H:%M:%S')
        date_to  = datetime.strftime((datetime.now() + relativedelta(day=31)),'%Y-%m-%d %H:%M:%S')
        attendance_ids = attendance_obj.search(cr, uid, [('name','>=',date_from),('name','<=',date_to),('action','=','sign_in')], context=context)
        holiday_status_id = leave_status_obj.search(cr, uid, [('type','=','half')], context=context)
        current_date = time.strftime('%Y-%m-%d')
        res = {}
        for attendance in attendance_obj.browse(cr, uid, attendance_ids, context=context):
            half_leave_ids = self.search(cr, uid, [('date_from','=',current_date),
                                                       ('employee_id','=',attendance.employee_id.id),
                                                       ('type','=','remove'),
                                                       ('holiday_status_id','=', holiday_status_id and holiday_status_id[0])])
            if half_leave_ids:
                continue
            attendance_dt = _get_timezone_employee(attendance.employee_id, attendance.name)
            calendar_id = attendance.employee_id.contract_id.working_hours or False
            if not res.has_key(attendance.employee_id.id):
                res[attendance.employee_id.id] = {attendance_dt.strftime('%Y-%m-%d'): 0}
            if attendance_dt.strftime('%Y-%m-%d') in res[attendance.employee_id.id].keys():
                continue
            if calendar_id:
                sign_in_time = attendance_dt.strftime("%H.%M")
                calendar_val = employee_obj._get_daily_attendance(cr, uid, attendance)
                late_time = calendar_val.get('entry_time') + (calendar_id.late_time * 0.01)
#                 print "calendar_val:::::::::::::::::::::::::::",calendar_val
                days = res[attendance.employee_id.id].get(attendance_dt.strftime('%Y-%m-%d'),False)
                if days and float(sign_in_time) > late_time or \
                    calendar_val.get('worked_hours') < calendar_val.get('working_hours'):
                    days += 1
                if res[attendance.employee_id.id].get(attendance_dt.strftime('%Y-%m-%d')) >= calendar_id.late_days:
                    self.create(cr, uid, {
                                    'name': 'Half day - For late coming',
                                    'date_from': current_date,
                                    'date_to': current_date,
                                    'number_of_days_temp': 0.5,
                                    'holiday_status_id': holiday_status_id and holiday_status_id[0],
                                    'employee_id': attendance.employee_id.id,
                                    'type': 'remove',
                                })
        return True

    def run_monthly_scheduler(self, cr, uid, context=None):
        """ Runs at the end of every month to allocate PL, CL & SL to all 
        eligible employees.
        """
        employee_obj = self.pool.get('hr.employee')
        leave_status_obj = self.pool.get('hr.holidays.status')
        date_from  = datetime.strftime((datetime.now() + relativedelta(months=1) + relativedelta(day=1)),'%Y-%m-%d %H:%M:%S')
        date_to  = datetime.strftime((datetime.now() + relativedelta(months=1) + relativedelta(day=31)),'%Y-%m-%d %H:%M:%S')
        
        employee_ids = employee_obj.search(cr, uid, ['|',('total_days','>=',240),('eligible','=',True)], context=context)
        holiday_status_ids = leave_status_obj.search(cr, uid, [('type','in',('paid','sl','cl'))], context=context)
        for holiday_status in leave_status_obj.browse(cr, uid, holiday_status_ids, context=context):
            for emp in employee_obj.browse(cr, uid, employee_ids, context=context):
                allocate_ids = self.search(cr, uid, [('date_from','=',date_from), 
                                                          ('date_to','=',date_to), 
                                                          ('type','=','add'), 
                                                          ('employee_id','=',emp.id),
                                                          ('holiday_status_id','=',holiday_status.id)], context=context)
                if allocate_ids:
                    break
                allocate_days = 1.0
                if time.strftime('%B') == 'December':
                    days_left = leave_status_obj.get_days(cr, uid, [holiday_status.id], emp.id, context=context)
                    days_left = days_left[holiday_status.id]['remaining_leaves']
                    if days_left <= 12:
                        allocate_days += days_left
                vals = {
                        'name': 'Monthly Allocation of '+ holiday_status.type,
                        'number_of_days_temp': allocate_days,
                        'date_from': date_from,
                        'date_to': date_to,
                        'employee_id': emp.id,
                        'holiday_status_id': holiday_status.id,
                        'type': 'add',
                }
                if holiday_status.type in ('cl','sl'):
                    vals.update({'number_of_days_temp': 0.5})
                leave_id = self.create(cr, uid, vals, context=context)
                self.holidays_validate(cr, uid, [leave_id], context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
