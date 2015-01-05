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
    'name': 'Receita',
    'summary': """ SNCP """,
    'author': 'Aksana/Miguel',
    'website': 'http://www.openerp.com',
    'category': 'Hidden/Dependency',
    'description': 'Módulo receita',
    'installable': True,
    'auto_install': False,
    'data': [
        'security/receita_security.xml',
        'security/ir.model.access.csv',
        'faturas_view.xml',
        'cobranca_view.xml',
        'guia_view.xml',
        'controlo_view.xml',
        'juros_view.xml',
        'herancas_view.xml',
        'receita_view.xml',
        'teste_view.xml',
        'wizard/formulario_mensagem_receita.xml',
        'wizard/formulario_select_guia_view.xml',
        'views/receita.xml',
    ],
    'depends': ['account', 'sale', 'comum', 'mail', 'base_report_to_printer'],
    'init_xml': [],
    'update_xml': [
    ],
    'qweb': [
        'static/src/xml/pesquisa_departamento.xml',
    ],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: