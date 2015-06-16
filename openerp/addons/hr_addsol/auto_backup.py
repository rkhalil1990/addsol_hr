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
from cStringIO import StringIO
from ftplib import FTP
import logging

from openerp.osv import osv
import openerp.service.db as DB
import openerp.tools.config as CONFIG
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

# from openerp.addons.document_ftp import test_easyftp as te

# CONFIG['db_user'] = 'ujjvalag'
# CONFIG['db_host'] = 'localhost'
# CONFIG['db_port'] = 5432
# CONFIG['db_password'] = 'ujjvalag'

# Setup Configuration
fp = open('/etc/odoo-server.conf','r')
for line in fp.readlines():
    if line.find('=') > 0:
        key, val = line.split('=')
        if key.startswith('db_'):
            CONFIG[key.rstrip()] = val.strip(' \n')

class addsol_res_users(osv.osv):
    _inherit = 'res.users'

    def run_autobackup_database(self, cr, uid, context=None):
        user = self.browse(cr, SUPERUSER_ID, uid, context)
        host = 'localhost'
        port = '8021'
        foldername = '/'
        ftp_url = (user.company_id.document_ftp_url).replace('ftp://','')
        ftp_user = user.company_id.document_ftp_user
        ftp_passwd = user.company_id.document_ftp_passwd
        for url in ftp_url.split('/'):
            if url.find(':') > 0:
                host, port = url.split(':')[0], url.split(':')[1]
            else:
                foldername += '/'+ url
        db_list = DB.exp_list()
        for db in db_list:
            backup_db = StringIO(DB.exp_dump(db))
            values = {
                      'host': str(host),
                      'port': str(port),
                      'timeout': 10.0,
                      'foldername': foldername,
                      'backup_db': backup_db,
                      'ftp_user': ftp_user,
                      'ftp_passwd': ftp_passwd,
                      'db_name': db,
            }
            self.get_ftp(cr, uid, values, context)

    def get_ftp(self, cr, uid, values, context=None):
        ftp = FTP()
        host = values.get('host','localhost')
        port = values.get('port','8021')
        timeout = values.get('timeout',10.0)
        try:
            ftp.connect(host, port, timeout)
        except:
            _logger.info('FTP %s:%s Connection Refused!'%host,port)
        user = values.get('ftp_user')
        passwd = values.get('ftp_passwd')
        foldername = values.get('foldername')
        backup_db = values.get('backup_db')
        try:
            ftp.login(user, passwd)
        except:
            _logger.info('Authentication Failed! User: %s'%user)
        db = values.get('db_name')
        ftp.cwd(foldername)
        ftp.storbinary('STOR ' + db +'_'+time.strftime('%Y-%m-%d')+'.sql', backup_db)
        ftp.close()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: