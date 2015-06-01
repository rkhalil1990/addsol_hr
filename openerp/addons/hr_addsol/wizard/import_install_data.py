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
import os
import csv
import base64
from io import BytesIO
import zipfile
from os.path import join as opj

import openerp
from openerp.osv import fields, osv

class import_install_data(osv.TransientModel):
    _name = 'import.install.data'
    _description = "Import and Installs Data"
    
    _columns = {
        'folder_path': fields.binary('Data .ZIP file', required=True),
    }
    
    def install_data(self, cr, uid, ids, context=None):
        module_obj = self.pool.get('ir.module.module')
        record = self.browse(cr, uid, ids, context=context)[0]
        zip_data = base64.decodestring(record.folder_path)
        fp = BytesIO()
        fp.write(zip_data)
        with zipfile.ZipFile(fp, "r") as z:
            with openerp.tools.osutil.tempdir() as module_dir:
                z.extractall(module_dir)
                dirs = [d for d in os.listdir(module_dir) if os.path.isdir(opj(module_dir, d))]
                for mod_name in dirs:
                    try:
                        path = opj(module_dir, mod_name)
                        update_path = self.convert_csv_to_xml(cr, uid, path, context)
                        module_obj.import_module(cr, uid, mod_name, update_path, force=False, context=context)
                    except Exception, e:
                        raise osv.except_osv(('Error!'),('%s'%e.message))
        return True

    def convert_csv_to_xml(self, cr, uid, folder_name, context=None):
        os.chdir(folder_name)
        csvFiles = [f for f in os.listdir('.') if f.endswith('.csv') or f.endswith('.CSV')]
        newList = []
        missing_files = []
        for csvfile in csvFiles:
            if csvfile == 'hr.department.csv':
                newList.insert(0, csvfile)
            else:
                missing_files.append('hr.department.csv')
            if csvfile == 'hr.job.csv':
                newList.insert(1, csvfile)
            else:
                missing_files.append('hr.job.csv')
            if csvfile == 'hr.employee.csv':
                csvData = csv.reader(open(csvfile))
                rowNum = 0
                partner_data = []
                data = []
                for row in csvData:
                    d = {}
                    if rowNum == 0:
                        fieldnames = row
                    else:
                        with open('res.partner.csv', 'wb') as partner_file:
                            partner_fields = ['name', 'email']
                            writer = csv.DictWriter(partner_file, fieldnames=partner_fields)
                            writer.writeheader()
                            for i in range(len(fieldnames)):
                                if fieldnames[i] == 'name':
                                    d = {'name': row[i]}
                                if fieldnames[i] == 'work_email':
                                    d.update({'email': row[i]})
                            partner_data.append(d)
                            for v in partner_data:
                                writer.writerow(v)
                        with open('res.users.csv', 'wb') as user_file:
                            fields = ['name', 'email','login','partner_id']
                            writer = csv.DictWriter(user_file, fieldnames=fields)
                            writer.writeheader()
                            for i in range(len(fieldnames)):
                                if fieldnames[i] == 'name':
                                    d = {'name': row[i],'partner_id': row[i]}
                                if fieldnames[i] == 'work_email':
                                    d.update({'email': row[i],'login': row[i]})
                            data.append(d)
                            for v in data:
                                writer.writerow(v)
                    rowNum += 1
                newList.insert(2, 'res.partner.csv')
                newList.insert(3, 'res.users.csv')
                newList.insert(4, csvfile)
            else:
                missing_files.append('hr.employee.csv')
            if csvfile == 'hr.payroll.structure.csv':
                newList.insert(5, csvfile)
            else:
                missing_files.append('hr.payroll.structure.csv')
            if csvfile == 'hr.contract.csv':
                newList.insert(6, csvfile)
            else:
                missing_files.append('hr.contract.csv')
        terp = {
            'name': "Data",
            'version': '1.0',
            'author': 'Addition IT Solutions Pvt. Ltd.',
            'category': 'Human Resources',
            'sequence': 100,
            'website': 'https://www.aitspl.com',
            'summary': 'Jobs, Departments, Employees Details',
            'description': """
        Human Resources Management
        ==========================
        Imports HR data
            """,
            'images': [],
            'depends': ['hr_addsol'],
            'data': [],
            'installable': True,
            'auto_install': False,
        }
        fo = open("__init__.py", "wb")
        fo.write("import %s" %folder_name)
        fo.close()
        terp.update(data=newList)
        fo = open("__openerp__.py", "wb")
        fo.write(str(terp))
        fo.close()
        return folder_name

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: