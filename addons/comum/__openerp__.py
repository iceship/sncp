# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

{
    'name': 'Comum',
    'summary': """ SNCP """,
    'version': '1.1',
    'author': 'Aksana/Miguel',
    'website': 'http://www.openerp.com',
    'category': 'Hidden/Dependency',
    'description': """ Módulo que introduz analítica multidimensão """,
    'installable': True,
    'auto_install': False,
    'data': [
            'security/comum_security.xml',
            'security/ir.model.access.csv',
            'geral_view.xml',
            'herancas_view.xml',
            'param_view.xml',
            'views/comum.xml',
    ],
    'depends': ['account', 'web', 'sale', 'account_accountant', 'base', 'hr', 'base_report_to_printer'],
    'images': [
        'images/calendar_year_icon.jpg',
        'static/src/img/icons/icon.png',

    ],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
