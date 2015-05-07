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
import logging
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import osv

_logger = logging.getLogger(__name__)

class addsol_hr_attendance(osv.osv):
    _inherit = 'hr.attendance'
    
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
                elif hours_count >= 5 and hours_count <= 7.45: # Currently fixed value, can be changed according to company calendar
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

    def run_monthly_scheduler(self, cr, uid, context=None):
        """ Runs at the end of every month to allocate PL, CL & SL to all 
        eligible employees.
        """
        employee_obj = self.pool.get('hr.employee')
        leave_obj = self.pool.get('hr.holidays')
        leave_status_obj = self.pool.get('hr.holidays.status')
        date_from  = datetime.strftime((datetime.now() + relativedelta(months=1) + relativedelta(day=1)),'%Y-%m-%d %H:%M:%S')
        date_to  = datetime.strftime((datetime.now() + relativedelta(months=1) + relativedelta(day=31)),'%Y-%m-%d %H:%M:%S')
        
        employee_ids = employee_obj.search(cr, uid, ['|',('total_days','>=',240),('eligible','=',True)], context=context)
        holiday_status_ids = leave_status_obj.search(cr, uid, [('type','in',('paid','sl','cl'))], context=context)
        for holiday_status in leave_status_obj.browse(cr, uid, holiday_status_ids, context=context):
            for emp in employee_obj.browse(cr, uid, employee_ids, context=context):
                allocate_ids = leave_obj.search(cr, uid, [('date_from','=',date_from), 
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
                leave_id = leave_obj.create(cr, uid, vals, context=context)
                leave_obj.holidays_validate(cr, uid, [leave_id], context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
