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
    'name': 'SNCP',
    'author': 'Aksana/Miguel',
    'description': 'Sistema de Normalização Contabilística Pública',
    'installable': True,
    'auto_install': False,
    'depends': ['tesouraria', 'orcamento', 'comum', 'despesa', 'receita', 'jasper_reports',
                'print_report',
                'regproc'],
    'category': 'Generic Modules/Others',
    'init_xml': [
    ],
    'update_xml': [
        # INSERIR ISTO MANUALMENTE NO IR_CRON
        # 'data/xml_import/ir_cron_data.xml',

    ],
    'data': [
        'data/xml_import/users_data.xml',
        'data/xml_import/comum_data.xml',
    ],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
