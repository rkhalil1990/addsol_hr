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
from dateutil import rrule, parser


from openerp.osv import fields, osv

class addsol_hr_payroll(osv.osv):
    _inherit= 'hr.payslip'
    
    def create(self, cr, uid, vals, context=None):
        payslip_id = super(addsol_hr_payroll, self).create(cr, uid, vals, context)
        self.count_attendance(cr, uid, [payslip_id], vals, context=context)
        return payslip_id
    
    def write(self, cr, uid, ids, vals, context=None):
        payslip_id = super(addsol_hr_payroll, self).write(cr, uid, ids, vals, context)
        self.count_attendance(cr, uid, ids, vals, context=context)
        return payslip_id
    
    def count_attendance(self, cr, uid, ids, payslip, context=None):
        attendance_obj = self.pool.get('hr.attendance')
        employee_obj = self.pool.get('hr.employee')
        calendar_obj = self.pool.get('resource.calendar')
        leave_obj = self.pool.get('hr.holidays')
        leave_status_obj = self.pool.get('hr.holidays.status')
        payslip_rec = self.browse(cr, uid, ids[0], context)
        date_from = payslip.get('date_from') or payslip_rec.date_from
        date_to = payslip.get('date_to') or payslip_rec.date_to
        employee_id = payslip.get('employee_id') or payslip_rec.employee_id.id
        emp_rec = employee_obj.browse(cr, uid, employee_id, context)
        calendar = False
        if emp_rec.contract_id and emp_rec.contract_id.working_hours:
            calendar = emp_rec.contract_id.working_hours
        if calendar:
            dates = list(rrule.rrule(rrule.DAILY,
                                         dtstart=parser.parse(date_from),
                                         until=parser.parse(date_to)))
            days = 0
            leave_dates = []
            domain = [('type','=','remove'),('date_from','>=',date_from),('date_to','<=',date_to)]
            leave_ids = leave_obj.search(cr, uid, domain + [('employee_id','=',employee_id)], context=context)
            for leave in leave_obj.browse(cr, uid, leave_ids, context):
                for leave_date in list(rrule.rrule(rrule.DAILY,
                                         dtstart=parser.parse(leave.date_from),
                                         until=parser.parse(leave.date_to))):
                    leave_dates.append(leave_date.strftime('%Y-%m-%d 00:00:00'))
            for dt in dates:
                dh = calendar_obj.get_working_hours_of_date(cr=cr, uid=uid,
                                                             id=calendar.id,
                                                             start_dt=dt,
                                                             resource_id=employee_id,
                                                             context=context)
                if dh != 0.0:
                    date_from = dt.strftime('%Y-%m-%d 00:00:00')
                    date_to = dt.strftime('%Y-%m-%d 23:59:59')
                    print date_from, date_to
                    attendance_ids = attendance_obj.search(cr, uid, [('name','>=',date_from),
                                                            ('name','<=',date_to),
                                                            ('employee_id','=',employee_id)])
                    if not attendance_ids:
                        if date_from not in leave_dates:
                            holiday_status_id = leave_status_obj.search(cr, uid, [('type','=','unpaid')], context=context)
                            values = {
                                    'name': 'No Attendance Marked',
                                    'date_from': dt,
                                    'date_to': dt,
                                    'number_of_days_temp': 1.0,
                                    'holiday_status_id': holiday_status_id and holiday_status_id[0] or 1,
                                    'employee_id': employee_id,
                                    'type': 'remove',
                            }
                            leave_obj.create(cr, uid, values, context=context)
                    else:
                        late = leave_obj.check_late_coming_employees(cr, uid, attendance_ids, context)
                        if late:
                            days += 1
                            late_coming_date = dt
                    if days > calendar.late_days:
                        holiday_status_id = leave_status_obj.search(cr, uid, [('type','=','half')], context=context)
                        days = 0 # Re-initialize the counter
                        if late_coming_date.strftime('%Y-%m-%d 00:00:00') not in leave_dates:
                            leave_obj.create(cr, uid, {
                                                'name': 'Half day - For late coming',
                                                'date_from': late_coming_date,
                                                'date_to': late_coming_date,
                                                'number_of_days_temp': 0.5,
                                                'holiday_status_id': holiday_status_id and holiday_status_id[0],
                                                'employee_id': employee_id,
                                                'type': 'remove',
                                            })
                            
                            
class addsol_bank(osv.osv):
    _inherit= 'res.bank'
    
    _columns = {
        'url': fields.char('URL'),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: