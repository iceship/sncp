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
    'name': 'Despesa',
    'summary': """ SNCP """,
    'author': 'Aksana/Miguel',
    'website': 'http://www.openerp.com',
    'category': 'Hidden/Dependency',
    'description': 'Módulo despesa',
    'installable': True,
    'auto_install': False,
    'data': ['security/despesa_security.xml',
             'security/ir.model.access.csv',
             'cabimento_view.xml',
             'despesa_view.xml',
             'compromisso_view.xml',
             'dados_gerais_view.xml',
             'faturas_view.xml',
             'proposta_view.xml',
             'ordem_view.xml',
             'descontos_view.xml',
             'requisicoes_view.xml',
             'herancas_view.xml',
             'reposicoes_view.xml',

             'wizard/formulario_diario_cabimento_view.xml',
             'wizard/formulario_diario_compromisso_view.xml',
             'wizard/formulario_diario_pagamentos_ordem_view.xml',
             'wizard/formulario_requisicao_view.xml',
             'wizard/formulario_mensagem_despesa_view.xml',
             'wizard/formulario_ordem_compra_view.xml', ],
    'depends': ['web', 'purchase', 'comum', 'receita', 'stock', 'hr', 'product', 'base', 'account', 'board'],
    'init_xml': ['static_sequence.xml'],
    'update_xml': [],
    'css': [
        'static/src/css/oe_display.css',
    ],
    'js': [
        'static/src/js/aprovador_autorizado.js',
        'static/src/js/requisicoes_pesquisa.js',
        'static/src/js/autorizacoes_pesquisa.js',
    ],
    'qweb': [
        'static/src/xml/requisicoes_pesquisa.xml',
        'static/src/xml/autorizacoes_pesquisa.xml',
    ],
    'images': [
        'images/calendar.png',
    ],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: