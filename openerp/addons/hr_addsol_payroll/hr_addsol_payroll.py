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
import time

from openerp.osv import osv

class addsol_hr_attendance(osv.osv):
    _inherit = 'hr.attendance'
    
    def run_daily_scheduler(self, cr, uid, context=None):
        """ Runs at the end of the day to check attendances of employees.
        And creates leaves if attendance criteria is not satisfied.
        """
        
        employee_obj = self.pool.get('hr.employee')
        leave_obj = self.pool.get('hr.holidays')
        leave_status_obj = self.pool.get('hr.holidays.status')
        user_obj = self.pool.get('res.users')
        calendar_obj = self.pool.get('addsol.hr.calendar')
        resource_calendar_obj = self.pool.get('resource.calendar')
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
            calendar_id = attendance.employee_id.contract_id.working_hours or False
            if not calendar_id:
                continue
            leave_ids = leave_obj.search(cr, uid, domain + [('employee_id','=',attendance.employee_id.id)], context=context)
            hours_count = attendance.worked_hours
            total_daily_hours = calendar_obj.get_working_hours_of_date(cr=cr, uid=uid,
                                                         id=calendar_id.id,
                                                         start_dt=attendance.name,
                                                         resource_id=attendance.employee_id.id, 
                                                         context=context)
            print "==================total_daily_hours===============",total_daily_hours
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
                elif hours_count >= 5 and hours_count <= total_daily_hours:
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

class addsol_hr_payroll(osv.osv):
    _inherit= 'hr.payslip'
    
    def create(self, cr, uid, vals, context=None):
        payslip_id = super(addsol_hr_payroll, self).create(cr, uid, vals, context)
        self.count_attendance(cr, uid, vals, context=context)
        return payslip_id
    
    def count_attendance(self, cr, uid, payslip, context=None):
        attendance_obj = self.pool.get('hr.attendance')
        holiday_obj = self.pool.get('hr.holidays')
        holiday_status_obj = self.pool.get('hr.holidays.status')
        employee_obj = self.pool.get('hr.employee')
        date_from = payslip.get('date_from') or time.strftime('%Y-%m-01')
        date_to = payslip.get('date_to') or time.strftime('%Y-%m-31')
        employee_id = payslip.get('employee_id')
        worked_days = payslip.get('worked_days_line_ids')
#         calendar_id = contract_obj.browse(cr, uid, payslip.get('contract_id'), context=context).working_hours 
        attendance_ids = attendance_obj.search(cr, uid, [('name','>=',date_from),
                                                         ('name','<=',date_to),
                                                         ('employee_id','=',employee_id)])
        present_days = 0.0
        for att in attendance_obj.browse(cr, uid, attendance_ids, context=context):
            if att.action == 'sign_out':
                att_val = employee_obj._get_daily_attendance(cr, uid, att)
                if att.total_worked_hours >= att_val.get('working_hours'):
                    present_days += 1
#         print ">>>>>>>>>>>>>>>>",employee_id, present_days, worked_days
#         for days in worked_days:
#             line = days[2]
#             working_days = unpaid_days = 0
#             if line.get('code') == 'WORK100':
#                 working_days = line.get('number_of_days')
#             if line.get('code') == 'Unpaid':
#                 unpaid_days = line.get('numer_of_days')
#         type_ids = holiday_status_obj.search(cr, uid, [('type','=','paid')], context=context)
#         if present_days < (working_days + unpaid_days):
#             leave_ids = holiday_obj.search(cr, uid, [('date_from','>=',date_from),
#                                          ('date_to','<=',date_to),
#                                          ('employee_id','=',employee_id),
#                                          ('holiday_status_id','in',type_ids),
#                                          ('type','=','remove')])


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: