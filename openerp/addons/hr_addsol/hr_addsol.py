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
from datetime import datetime, timedelta
from dateutil import relativedelta as rdelta

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class addsol_hr_employee(osv.osv):
    _inherit = "hr.employee"
    
    def _calc_no_of_years(self, cr, uid, ids, field_name, arg, context=None):
        """ Count total number of years employee has worked in the company
        based on the contracts.
        """
        obj_contract = self.pool.get('hr.contract')
        res = {}
        for emp in self.browse(cr, uid, ids, context=context):
            contract_ids = obj_contract.search(cr, uid, [('employee_id','=',emp.id),], order='date_start', context=context)
            res[emp.id] = 0.0
            for contract in obj_contract.browse(cr, uid, contract_ids, context=context):
                end_date = contract.date_end
                if not end_date:
                    end_date = time.strftime('%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                start_date = datetime.strptime(contract.date_start, '%Y-%m-%d')
                rd = rdelta.relativedelta(end_date, start_date)
                difference_in_years = "{0.years}.{0.months}".format(rd)
                years = float(difference_in_years)
                if float(rd.months) >= 11:
                    years = rd.years + 1.0
                res[emp.id] += years
        return res
    
    def _count_total_days(self, cr, uid, ids, field_name, arg, context=None):
        """ Counts employee's working days based on the attendance. If working
        hours are more than 8 hours/day then 1 day is added.
        """
        obj_attendance = self.pool.get('hr.attendance')
        resource_pool = self.pool.get('resource.calendar')
        res = {}
        for emp in self.browse(cr, uid, ids, context=context):
            attendance_ids = obj_attendance.search(cr, uid, [('employee_id','=',emp.id),], order='name', context=context)
            res[emp.id] = 0
            working_hours = 8
            for att in obj_attendance.browse(cr, uid, attendance_ids, context=context):
                if emp.calendar_id and att.action == 'sign_in':
                    start_dt = datetime.strptime(att.name, '%Y-%m-%d %H:%M:%S')
                    working_hours = resource_pool.get_working_hours_of_date(cr, uid, emp.calendar_id.id, start_dt, None,
                                  None, False, emp.id, None, context)
                if att.action == 'sign_out' and att.worked_hours >= working_hours:
                    res[emp.id] += 1
        return res

    def _eligible_for_pl(self, cr, uid, ids, field_name, arg, context=None):
        """ If employee finishes the trail period mentioned in his contract
        then this flag is marked True. And employee can start availing the
        paid leaves.
        """
        obj_contract = self.pool.get('hr.contract')
        res = {}
        for emp in self.browse(cr, uid, ids, context=context):
            contract_ids = obj_contract.search(cr, uid, [('employee_id','=',emp.id),], order='date_start', context=context)
            res[emp.id] = False
            for contract in obj_contract.browse(cr, uid, contract_ids, context=context):
                if contract.trial_date_start and contract.trial_date_end:
                    if contract.date_start <= time.strftime('%Y-%m-%d'):
                        res[emp.id] = True
        return res

    _columns = {
        'no_of_years': fields.function(_calc_no_of_years, type='float', digits=(16,2), string='Years of Service'),
        'total_days': fields.function(_count_total_days, type='integer', string="Total Present Days"),
        'eligible': fields.function(_eligible_for_pl, type='boolean', string='Eligible for PL?'),
    }

    def create(self, cr, uid, vals, context=None):
        emp_id = super(addsol_hr_employee, self).create(cr, uid, vals, context)
        if vals.get('parent_id'):
            for record in self.browse(cr, uid, [vals.get('parent_id')], context=context):
                if record.user_id:
                    self.message_subscribe_users(cr, uid, [emp_id], user_ids=[record.user_id.id], context=context)
        return emp_id
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('parent_id'):
            for record in self.browse(cr, uid, [vals.get('parent_id')], context=context):
                if record.parent_id.user_id:
                    self.message_subscribe_users(cr, uid, ids, user_ids=[record.user_id.id], context=context)
        return super(addsol_hr_employee, self).write(cr, uid, ids, vals, context)

    def create_user_for_employee(self, cr, uid, ids, context=None):
        """ Allows to create a user for the employee from employee form.
        """
        users_obj = self.pool.get('res.users')
        user_ids = []
        for empl in self.browse(cr, uid, ids, context=context):
            if not empl.work_email:
                raise osv.except_osv(_('Error!'), _("Please enter employee's email address."))
            user_data = {
                'name': empl.name,
                'login': empl.work_email,
                'email': empl.work_email
            }
            user_id = users_obj.create(cr, SUPERUSER_ID, user_data, context=context)
            user_ids.append(user_id)
            self.write(cr, uid, empl.id, {'user_id': user_id}, context=context)
        try:
            users_obj.action_reset_password(cr, SUPERUSER_ID, user_ids, context=context)
        except:
            pass
        return True

class resource_calendar(osv.osv):
    _inherit = 'resource.calendar'
    _columns = {
        'late_days': fields.integer('Days', help="Number of days an employee comes late."),
        'late_time': fields.float('Time (In Minutes)', help="Minutes allowed for late coming.")
    }
    
    _defaults = {
        'late_days': 3,
        'late_time': 15.0,
    }

class addsol_hr_holidays_status(osv.osv):
    _inherit = "hr.holidays.status"
    _columns = {
        'no_of_days': fields.integer('No. of Days'), # Used in case of Sick Leaves
        'type': fields.selection([('paid','Paid Leaves'),
                                  ('unpaid','Unpaid Leaves'),
                                  ('sl','Sick Leaves'),
                                  ('cl','Casual Leaves'),
                                  ('comp','Compensatory Leaves'),
                                  ('request','Request Leaves'),
                                  ('half','Half Day Leave')], 'Basic Types', required=True),
    }
    
class addsol_hr_holidays(osv.osv):
    _inherit = "hr.holidays"
    
    _columns = {
        'no_of_days': fields.related('holiday_status_id', 'no_of_days', type='integer', string='No of Allowed Days'),
        'certificate': fields.binary('Attach Document'),
    }
    
    def onchange_date_from(self, cr, uid, ids, holiday_status_id, date_to, date_from):
        result = super(addsol_hr_holidays, self).onchange_date_from(cr, uid, ids, date_to, date_from)
        leave_type_obj = self.pool.get('hr.holidays.status')
        days = result['value']['number_of_days_temp']
        status = leave_type_obj.browse(cr, uid, holiday_status_id)
        if status.type == 'half' and days > 1:
            result['value'].update({'number_of_days_temp': days/2})
        return result
     
    def onchange_date_to(self, cr, uid, ids, holiday_status_id, date_to, date_from):
        result = super(addsol_hr_holidays, self).onchange_date_from(cr, uid, ids, date_to, date_from)
        leave_type_obj = self.pool.get('hr.holidays.status')
        days = result['value']['number_of_days_temp']
        status = leave_type_obj.browse(cr, uid, holiday_status_id)
        if status.type == 'half' and days > 1:
            result['value'].update({'number_of_days_temp': days/2})
        return result
    
    def onchange_leave_type(self, cr, uid, ids, holiday_status_id, context=None):
        leave_type_obj = self.pool.get('hr.holidays.status')
        res = {'value': {}}
        status = leave_type_obj.browse(cr, uid, holiday_status_id, context=context)
        if status.type == 'half':
            res['value'].update({'number_of_days_temp': 0.50})
        return res

    def _check_sick_leaves_date(self, cr, uid, ids, context=None):
        """ Checks whether the sick leave is for past dates.
        """
        for holiday in self.browse(cr, uid, ids, context=context):
            leave_type = holiday.holiday_status_id.type
            domain = [
                ('date_from', '>=', time.strftime('%Y-%m-%d %H:%M:%S')),
                ('employee_id', '=', holiday.employee_id.id),
                ('no_of_days','>', 0),
                ('type','=','remove'),
            ]
            nholidays = self.search_count(cr, uid, domain, context=context)
            if nholidays and leave_type == 'sl':
                return False
        return True
    
    def _check_sick_leaves_days(self, cr, uid, ids, context=None):
        """ Checks whether the sick leave days are not extended from the 
        specified limit (Mentioned on the leave type).
        """
        for holiday in self.browse(cr, uid, ids, context=context):
            leave_type = holiday.holiday_status_id.type
            domain = [
                ('no_of_days', '<', holiday.number_of_days_temp),('no_of_days','>', 0),
                ('employee_id', '=', holiday.employee_id.id),
                ('type','=','remove'),
            ]
            nholidays = self.search_count(cr, uid, domain, context=context)
            if nholidays and leave_type == 'sl':
                return False
        return True

    _constraints = [
        (_check_sick_leaves_date, 'Sick leaves cannot be taken in advance.', ['date_from']),
        (_check_sick_leaves_days, 'Sick leaves cannot exceed allowed number of days',['number_of_days_temp'])
    ]
    
    def holidays_validate(self, cr, uid, ids, context=None):
        """If leave type has basic type as 'Request', then create attendances
        for period mentioned on leave request."""
        if not context: context={}
        emp_obj = self.pool.get('hr.employee')
        for holiday in self.browse(cr, uid, ids, context=context):
            if holiday.holiday_status_id.type == 'request':
                if holiday.number_of_days_temp <= 1.0:
                    values = {
                         'action': 'sign_in',
                         'action_date': holiday.date_from
                    }
                    context.update(values)
                    emp_obj.attendance_action_change(cr, uid, [holiday.employee_id.id], context=context)
                    values = {
                         'action': 'sign_out',
                         'action_date': holiday.date_to
                    }
                    context.update(values)
                    emp_obj.attendance_action_change(cr, uid, [holiday.employee_id.id], context=context)
                else:
                    from_date = holiday.date_from
                    for days in range(int(holiday.number_of_days_temp)):
                        values = {
                         'action': 'sign_in',
                         'action_date': from_date
                        }
                        context.update(values)
                        emp_obj.attendance_action_change(cr, uid, [holiday.employee_id.id], context=context)
                        from_date = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S')
                        action_date = from_date + timedelta(hours=9)
                        values = {
                             'action': 'sign_out',
                             'action_date': action_date.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        context.update(values)
                        emp_obj.attendance_action_change(cr, uid, [holiday.employee_id.id], context=context)
                        from_date += timedelta(days=1)
                        from_date = from_date.strftime('%Y-%m-%d %H:%M:%S')
        return super(addsol_hr_holidays, self).holidays_validate(cr, uid, ids, context=context)

    def cancel_approved_holidays(self, cr, uid, ids, context=None):
        """Cancel the approved leaves and again goes for approval"""
        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        for holiday in self.browse(cr, uid, ids, context=context):
            if holiday.state == 'validate1':
                self.write(cr, uid, [holiday.id], {'state': 'cancel', 'manager_id': manager})
            else:
                self.write(cr, uid, [holiday.id], {'state': 'cancel', 'manager_id2': manager})
        return True

class addsol_hr_calendar(osv.osv):
    _name = 'addsol.hr.calendar'
    _description = "Calendar for Public Holidays"
    _order = 'date_from'

    _columns = {
        'name': fields.char('Holiday Name', required=True, size=64),
        'date_from': fields.date('On Date', required=True),
        'date_to': fields.date('Till Date'),
        'company_id': fields.many2one('res.company','Company', required=True),
    }
    
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'addsol.hr.calendar', context=c),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: