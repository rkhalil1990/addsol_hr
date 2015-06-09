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
from openerp.tools.translate import _

class hr_addsol_employee(osv.osv):
    _inherit = "hr.employee"
    
    _columns = {
        'asset_ids': fields.one2many('hr.addsol.employee.assets','employee_id',required=True),
        
    }

class hr_addsol_employee_assets(osv.osv):
    _name= "hr.addsol.employee.assets"
    _description="Employee request for assets"
    _rec_name = 'employee_id'    

    _columns = {
        'name':fields.text('Description', states={'draft': [('readonly', False)]} , readonly=True, required=True),
        'employee_id': fields.many2one('hr.employee', 'Employee', states={'draft': [('readonly', False)]} , readonly=True, required=True),
        'product_id': fields.many2one('product.product', 'Request For' ,states={'draft': [('readonly', False)]} ,readonly=True),
        'date_from': fields.datetime('Request Date', states={'draft': [('readonly', False)]}, required=True, readonly=True),
        'date_to': fields.datetime('End Date', states={'draft': [('readonly', False)]}, readonly=True),
        'quantity': fields.float('Quantity', states={'draft': [('readonly', False)]}, readonly=True),
        'state': fields.selection([('draft', 'To Submit'), ('cancel', 'Cancelled'),('confirm', 'To Approve'), ('validate', 'Approved'),('refuse', 'Refused')],
            'Status', readonly=True),
        'allocate_date_from': fields.datetime('Allocation Date', states={'confirm': [('readonly', False)]},readonly=True,),
        'allocate_date_to': fields.datetime('Allocate Date To', states={'confirm': [('readonly', False)]},readonly=True,),
        'type': fields.selection([('asset','Asset Request'),('modify','Modify Information')], 'Request Type' , states={'draft': [('readonly', False)]} , readonly=True, required=True),
        'return_date': fields.datetime('Date Returned'),
        
    }
    
    def _employee_get(self, cr, uid, context=None):
        emp_id = context.get('default_employee_id', False)
        if emp_id:
            return emp_id
        ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)], context=context)
        if ids:
            return ids[0]
        return False
    
    _defaults = {
        'employee_id':_employee_get,
        'state':'draft',
        'type':'asset',
    }
    
    def write(self,cr,uid,ids,vals,context=None):
        res = super(hr_addsol_employee_assets, self).write(cr, uid, ids, vals, context=context)        
        if vals.get('return_date',False):
            
            for prod_id in self.browse(cr, uid, ids):        
                p_id = prod_id.product_id.id               
                qty = prod_id.quantity
                if qty == 0:
                    raise osv.except_osv(_('Error'), _('Quantity Can not be 0'))
                
                source_location = prod_id.product_id.property_stock_inventory.id
                uom = prod_id.product_id.uom_id.id
                prod_name = prod_id.product_id.name
                location_obj = self.pool.get('stock.location')
                destination_location = location_obj.search(cr,uid,[('name','=','Stock')])          
                move_obj = self.pool.get('stock.move')
                move_ids = move_obj.create(cr,uid,{'product_id':p_id,'name':prod_name,'product_uom_qty':qty,'product_uom':uom,'location_id':source_location,'location_dest_id':destination_location[0]})
                
                move_obj.action_done(cr, uid, [move_ids])
        
        return res
           
        
    
    def request_send(self, cr, uid, ids, *args):       
        self.write(cr, uid, ids, {'state': 'confirm'})
        return True
    
    def request_approve(self, cr, uid, ids, *args):    
        for prod_id in self.browse(cr, uid, ids):
            p_id = prod_id.product_id.id
            qty = prod_id.quantity  
            type = prod_id.type
            
            if type=="asset":
                
                    if qty == 0:
                        raise osv.except_osv(_('Error'), _('Quantity Can not be 0'))
                    else:
                        destination_location = prod_id.product_id.property_stock_inventory.id
                        uom = prod_id.product_id.uom_id.id
                        prod_name = prod_id.product_id.name
                        location_obj = self.pool.get('stock.location')
                        source_location_ids = location_obj.search(cr,uid,[('name','=','Stock')])
                    
                        move_obj = self.pool.get('stock.move')
                        move_ids = move_obj.create(cr,uid,{'product_id':p_id,'name':prod_name,'product_uom_qty':qty,'product_uom':uom,'location_dest_id':destination_location,'location_id':source_location_ids[0]})
                        
                        move_obj.action_done(cr, uid, [move_ids])
           
        self.write(cr, uid, ids, {'state': 'validate'})
        return True
    
    def refuse(self, cr, uid, ids, *args):       
        self.write(cr, uid, ids, {'state': 'refuse'})
        return True
    
    def reset(self, cr, uid, ids, *args):       
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True

   
