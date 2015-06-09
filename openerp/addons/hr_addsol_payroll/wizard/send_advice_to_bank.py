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


import openerp
from openerp.osv import fields, osv

class addsol_send_advice_to_bank(osv.TransientModel):
    _name = 'addsol.send.advice.bank'
    _description = "Send payslip advice to bank"
    
    _columns = {
        'bank_id': fields.many2one('res.bank','Bank',required=True),
        'url': fields.char('URL'),
        'csv_path': fields.binary('CSV File', required=True),
    }
    
    def _bank_get(self, cr, uid, context=None):
        advice_id = context.get('default_advice_id', False)
        if advice_id:
            return advice_id
        browse_obj = self.pool.get('hr.payroll.advice').browse(cr, uid, advice_id , context=context)
        if browse_obj.bank_id.id:
            return browse_obj[0]
        return False
     
    _defaults = {
        'bank_id':_bank_get,
    }
        
    def onchange_bank_id(self, cr, uid, ids, bank_id=False, context=None):
        res = {}
        bank_obj = self.pool.get('res.bank')
        if not bank_id:
            return {'value': res}
        bank = bank_obj.browse(cr, uid, bank_id, context=context)
        res.update({'url': bank.url})
        return {'value': res}
    
    
    def send_advice(self, cr, uid, ids, *args):
        
        return True