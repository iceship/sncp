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
    'name': 'Orçamento',
    'summary': """ SNCP """,
    'author': 'Aksana/Miguel',
    'website': 'http://www.openerp.com',
    'category': 'Hidden/Dependency',
    'description': """ Modulo orçamento """,
    'installable': True,
    'auto_install': False,
    'data': ['security/orcamento_security.xml',
             'security/ir.model.access.csv',
             'orcamento_view.xml',
             'orcamento_mapas_view.xml',
             'wizard/formulario_diario_orcamento_view.xml',
             'wizard/formulario_copia_orcamento_view.xml',
             'orcamento_ppi_view.xml',
             'views/orcamento.xml',
             ],
    'depends': ['comum', 'web', 'despesa'],
    'update_xml': [],
    'qweb': [
        'static/src/xml/orcamento_historico_pesquisa.xml',
        'static/src/xml/orcamento_acumulados_pesquisa.xml',
    ],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: