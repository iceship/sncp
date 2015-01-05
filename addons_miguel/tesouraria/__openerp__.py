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
    'name': 'Tesouraria',
    'summary': """ SNCP """,
    'author': 'Aksana/Miguel',
    'website': 'http://www.openerp.com',
    'category': 'Hidden/Dependency',
    'description': 'Módulo Tesouraria',
    'installable': True,
    'auto_install': False,
    'data': [
            'security/tesouraria_security.xml',
            'security/ir.model.access.csv',
            'herancas_view.xml',

            'tesouraria_view.xml',
            'movimentos_view.xml',
            'mapas_view.xml',
            'oper_tesouraria_view.xml',
            'wizard/formulario_diario_reposicao_view.xml',
            'wizard/formulario_guia_cobrar_view.xml',
            'wizard/formulario_select_op_view.xml',
            'wizard/formulario_tesouraria_cheques_view.xml',
            'wizard/formulario_tesouraria_series_view.xml',
            'wizard/formulario_tesouraria_view.xml',
    ],
    'depends': ['account', 'base', 'web', 'hr', 'comum', 'despesa'],
    'init_xml': [],
    'update_xml': [
    ],
    'css': [
        'static/src/css/oe_display.css',
    ],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
