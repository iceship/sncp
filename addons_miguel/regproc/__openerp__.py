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
    'name': 'Registo de Processos',
    'summary': """ SNCP """,
    'author': 'Aksana/Miguel',
    'decription': 'Módulo regproc',
    'installable': True,
    'auto_install': False,
    'depends': ['web', 'base', 'base_setup', 'hr', 'comum', 'receita', 'mail',
                'base_report_to_printer', 'document'],
    'category': 'Generic Modules/Others',
    'init_xml': [],
    'update_xml': [],
    'data': [
        'security/regproc_security.xml',
        'security/ir.model.access.csv',
        'wizard/document_list_view.xml',

        'regproc_view.xml',
    ],
    'js': [
        'static/src/js/regproc_pesquisa.js',
        'static/src/js/filter_manager.js',
    ],
    'qweb': [
        'static/src/xml/regproc_pesquisa.xml',
        'static/src/xml/filter_manager.xml',
    ],
    'css': [
        'static/src/css/oe_display.css',
    ],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
