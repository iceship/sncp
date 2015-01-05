# -*- encoding: utf-8 -*-
# #############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    vals program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    vals program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with vals program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import decimal
from decimal import *
from datetime import datetime, date

from openerp.osv import fields, osv
from openerp.tools.translate import _


# ------------------------------------------------------VER HISTÓRICO-------------------------------------
class sncp_orcamento_historico_cabecalho(osv.Model):
    _name = 'sncp.orcamento.historico.cabecalho'

    def onchange_name(self, cr, uid, ids, nome, context=None):
        if type(ids) is list:
            if len(ids) != 0:
                cr.execute("""
                DELETE FROM sncp_orcamento_historico_rodape
                WHERE orc_hist_cabecalho_id=%d
                """ % ids[0])

        if not nome:
            return {'value': {'ord_desp_1': None,
                              'ord_desp_2': None,
                              'ord_desp_3': None,
                              'ord_rece_1': None,
                              'ord_rece_2': None,
                              'ord_rece_3': None,
                              'orc_hist_rodape_id': []}}

        if nome == 'rece':
            return {'value': {'ord_desp_1': None,
                              'ord_desp_2': None,
                              'ord_desp_3': None,
                              'orc_hist_rodape_id': []}}
        elif nome == 'desp':
            return {'value': {'ord_rece_1': None,
                              'ord_rece_2': None,
                              'ord_rece_3': None,
                              'orc_hist_rodape_id': []}}

    def pesquisar(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        cr.execute("""DELETE FROM sncp_orcamento_historico_rodape""")

        cr.execute("""DELETE FROM sncp_orcamento_historico_cabecalho WHERE id<%d""" % obj.id)

        where = u''
        order = u''
        x = unicode(obj.ano_ini)
        y = unicode(obj.ano_fim)

        # ANO
        if len(x) > 0 and int(x[0]) in range(0, 10):
            where += u'WHERE HIST.name >= ' + x
            if len(y) > 0 and int(y[0]) in range(0, 10):
                where += u' AND HIST.name <= ' + y
        else:
            if len(y) > 0 and int(y[0]) in range(0, 10):
                where += u'WHERE HIST.name <= ' + y

        # DATA HORA
        if obj.data_ini:
            if len(where) > 0:
                where += u' AND HIST.datahora >= ' + unicode("'" + obj.data_ini + "'")
                if obj.data_fim:
                    where += u' AND HIST.datahora <= ' + unicode("'" + obj.data_fim + "'")
            else:
                where += u'WHERE HIST.datahora >= ' + unicode("'" + obj.data_ini + "'")
                if obj.data_fim:
                    where += u' AND HIST.datahora <= ' + unicode("'" + obj.data_fim + "'")
        else:
            if obj.data_fim:
                if len(where) > 0:
                    where += u' AND HIST.datahora <= ' + unicode("'" + obj.data_fim + "'")
                else:
                    where += u'WHERE HIST.datahora <= ' + unicode("'" + obj.data_fim + "'")

        # DOCUMENTO CONTABILISTICO
        if obj.documento_code_ini:
            if len(where) > 0:
                where += u' AND HIST.doc_contab_id IN (SELECT AM.id FROM account_move AS AM ' \
                         u'WHERE compara_strings(AM.name,' + unicode("'" + obj.documento_code_ini + "'") \
                         + u') >= 0'
                if obj.documento_code_fim:
                    where += u' AND compara_strings(AM.name,' + unicode("'" + obj.documento_code_fim + "'") \
                             + u') <= 0' + u')'
                else:
                    where += u')'
            else:
                where += u'WHERE HIST.doc_contab_id IN (SELECT AM.id FROM account_move AS AM ' \
                         u'WHERE compara_strings(AM.name,' + unicode("'" + obj.documento_code_ini + "'") + \
                         u') >= 0'

                if obj.documento_code_fim:
                    where += u' AND compara_strings(AM.name,' + unicode("'" + obj.documento_code_fim + "'") + \
                             u') <= 0' + u')'
                else:
                    where += u')'
        else:
            if obj.documento_code_fim:
                if len(where) > 0:
                    where += u' AND HIST.doc_contab_id IN (SELECT AM.id FROM account_move AS AM ' \
                             u'WHERE compara_strings(AM.name,' + unicode("'" + obj.documento_code_fim + "'") + \
                             u') <= 0' + u')'
                else:
                    where += u'WHERE HIST.doc_contab_id IN (SELECT AM.id FROM account_move AS AM ' \
                             u'WHERE compara_strings(AM.name,' + unicode("'" + obj.economica_code_fim + "'") + \
                             u') <= 0' + u')'

        # ECONOMICA
        if obj.economica_code_ini:
            if len(where) > 0:
                where += u' AND HIST.economica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                         u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.economica_code_ini + "'") + \
                         u') >= 0'
                if obj.economica_code_fim:
                    where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.economica_code_fim + "'") + \
                             u') <= 0' + u')'
                else:
                    where += u')'
            else:
                where += u'WHERE HIST.economica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                         u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.economica_code_ini + "'") + \
                         u') >= 0'
                if obj.economica_code_fim:
                    where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.economica_code_fim + "'") + \
                             u') <= 0' + u')'
                else:
                    where += u')'
        else:
            if obj.economica_code_fim:
                if len(where) > 0:
                    where += u' AND HIST.economica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.economica_code_fim + "'") + \
                             u') <= 0' + u')'
                else:
                    where += u'WHERE HIST.economica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.economica_code_fim + "'") + \
                             u') <= 0' + u')'

        if obj.name == u'rece':
            # CATEGORIA
            if len(where) > 0:
                where += u' AND HIST.categoria >= ' + unicode("'" + obj.categoria_rece_code_ini + "'")
                if obj.categoria_rece_code_fim:
                    where += u' AND HIST.categoria <= ' + unicode("'" + obj.categoria_rece_code_fim + "'")
            else:
                where += u'WHERE HIST.categoria >= ' + unicode("'" + obj.categoria_rece_code_ini + "'")
                if obj.categoria_rece_code_fim:
                    where += u' AND HIST.categoria <= ' + unicode("'" + obj.categoria_rece_code_fim + "'")

            # ORDENAÇÃO RECEITA
            if obj.ord_rece_1:
                if obj.ord_rece_1 == u'economica_id':
                    order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                             obj.ord_rece_1 + u') COLLATE "C"'

                elif obj.ord_rece_1 == u'doc_contab_id':
                    order += u'ORDER BY (SELECT name FROM account_move WHERE id=HIST.' + \
                             obj.ord_rece_1 + u') COLLATE "C"'

                else:
                    order += u'ORDER BY HIST.' + obj.ord_rece_1

            if obj.ord_rece_2:
                if len(order) > 0:
                    if obj.ord_rece_2 == u'economica_id':
                        order += u',(SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                                 obj.ord_rece_2 + u') COLLATE "C"'

                    elif obj.ord_rece_2 == u'doc_contab_id':
                        order += u',(SELECT name FROM account_move WHERE id=HIST.' + \
                                 obj.ord_rece_2 + u') COLLATE "C"'

                    else:
                        order += u',HIST.' + obj.ord_rece_2

                else:
                    if obj.ord_rece_2 == u'economica_id':
                        order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                                 obj.ord_rece_2 + u') COLLATE "C"'

                    elif obj.ord_rece_2 == u'doc_contab_id':
                        order += u'ORDER BY (SELECT name FROM account_move WHERE id=HIST.' + \
                                 obj.ord_rece_2 + u') COLLATE "C"'

                    else:
                        order += u'ORDER BY HIST.' + obj.ord_rece_2

            if obj.ord_rece_3:
                if len(order) > 0:
                    if obj.ord_rece_3 == u'economica_id':
                        order += u',(SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                                 obj.ord_rece_3 + u') COLLATE "C"'

                    elif obj.ord_rece_3 == u'doc_contab_id':
                        order += u',(SELECT name FROM account_move WHERE id=HIST.' + \
                                 obj.ord_rece_3 + u') COLLATE "C"'

                    else:
                        order += u',HIST.' + obj.ord_rece_3

                else:
                    if obj.ord_rece_3 == u'economica_id':
                        order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                                 obj.ord_rece_3 + u') COLLATE "C"'

                    elif obj.ord_rece_3 == u'doc_contab_id':
                        order += u'ORDER BY (SELECT name FROM account_move WHERE id=HIST.' + \
                                 obj.ord_rece_3 + u') COLLATE "C"'

                    else:
                        order += u'ORDER BY HIST.' + obj.ord_rece_3

        elif obj.name == u'desp':
            # CATEGORIA
            if len(where) > 0:
                if obj.categoria_desp_code_ini:
                    where += u' AND HIST.categoria >= ' + unicode("'" + obj.categoria_desp_code_ini + "'")
                    where += u' AND HIST.categoria <= ' + unicode("'" + obj.categoria_desp_code_fim + "'")
                else:
                    where += u' AND HIST.categoria <= ' + unicode("'" + obj.categoria_desp_code_fim + "'")
            else:
                if obj.categoria_desp_code_ini:
                    where += u'WHERE HIST.categoria >= ' + unicode("'" + obj.categoria_desp_code_ini + "'")
                    where += u' AND HIST.categoria <= ' + unicode("'" + obj.categoria_desp_code_fim + "'")
                else:
                    where += u'WHERE HIST.categoria <= ' + unicode("'" + obj.categoria_desp_code_fim + "'")

            # ORGÂNICA
            if obj.organica_code_ini:
                if len(where) > 0:
                    where += u' AND HIST.organica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.organica_code_ini + "'") + \
                             u') >= 0'
                    if obj.organica_code_fim:
                        where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.organica_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
                else:
                    where += u'WHERE HIST.organica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.organica_code_ini + "'") + \
                             u') >= 0'
                    if obj.organica_code_fim:
                        where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.organica_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
            else:
                if obj.organica_code_fim:
                    if len(where) > 0:
                        where += u' AND HIST.organica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                                 u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.organica_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u'WHERE HIST.organica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                                 u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.organica_code_fim + "'") + \
                                 u') <= 0' + u')'

            # FUNCIONAL
            if obj.funcional_code_ini:
                if len(where) > 0:
                    where += u' AND HIST.funcional_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_ini + "'") + \
                             u') >= 0'
                    if obj.funcional_code_fim:
                        where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
                else:
                    where += u'WHERE HIST.funcional_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_ini + "'") + \
                             u') >= 0'
                    if obj.funcional_code_fim:
                        where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
            else:
                if obj.funcional_code_fim:
                    if len(where) > 0:
                        where += u' AND HIST.funcional_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                                 u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u'WHERE HIST.funcional_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                                 u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_fim + "'") + \
                                 u') <= 0' + u')'

            # CABIMENTO
            if obj.cabimento_code_ini:
                if len(where) > 0:
                    where += u' AND HIST.cabimento_id IN (SELECT CAB.id FROM sncp_despesa_cabimento AS CAB ' \
                             u'WHERE compara_strings(CAB.cabimento,' + unicode("'" + obj.cabimento_code_ini + "'") + \
                             u') >= 0'
                    if obj.cabimento_code_fim:
                        where += u' AND compara_strings(CAB.cabimento,' + unicode("'" + obj.cabimento_code_fim + "'") +\
                                 u') <= 0' + u')'
                    else:
                        where += u')'
                else:
                    where += u'WHERE HIST.cabimento_id IN (SELECT CAB.id FROM sncp_despesa_cabimento AS CAB ' \
                             u'WHERE compara_strings(CAB.cabimento,' + unicode("'" + obj.cabimento_code_ini + "'") + \
                             u') >= 0'
                    if obj.cabimento_code_fim:
                        where += u' AND compara_strings(CAB.cabimento,' + \
                                 unicode("'" + obj.cabimento_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
            else:
                if obj.cabimento_code_fim:
                    if len(where) > 0:
                        where += u' AND HIST.cabimento_id IN (SELECT CAB.id FROM sncp_despesa_cabimento AS CAB ' \
                                 u'WHERE compara_strings(CAB.cabimento,' + \
                                 unicode("'" + obj.cabimento_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u'WHERE HIST.cabimento_id IN (SELECT CAB.id FROM sncp_despesa_cabimento AS CAB ' \
                                 u'WHERE compara_strings(CAB.cabimento,' + \
                                 unicode("'" + obj.cabimento_code_fim + "'") + \
                                 u') <= 0' + u')'

            # COMPROMISSO
            if obj.compromisso_code_ini:
                if len(where) > 0:
                    where += u' AND HIST.compromisso_id IN (SELECT COMP.id FROM sncp_despesa_compromisso AS COMP ' \
                             u'WHERE compara_strings(COMP.compromisso,' + \
                             unicode("'" + obj.compromisso_code_ini + "'") + \
                             u') >= 0'
                    if obj.compromisso_code_fim:
                        where += u' AND compara_strings(COMP.compromisso,' + unicode(
                            "'" + obj.compromisso_code_fim + "'") + u') <= 0' + u')'
                    else:
                        where += u')'
                else:
                    where += u'WHERE HIST.compromisso_id IN (SELECT COMP.id FROM sncp_despesa_compromisso AS COMP ' \
                             u'WHERE compara_strings(COMP.compromisso,' + \
                             unicode("'" + obj.compromisso_code_ini + "'") + u') >= 0'
                    if obj.compromisso_code_fim:
                        where += u' AND compara_strings(COMP.compromisso,' + \
                                 unicode("'" + obj.compromisso_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
            else:
                if obj.compromisso_code_fim:
                    if len(where) > 0:
                        where += u' AND HIST.compromisso_id IN (SELECT COMP.id FROM sncp_despesa_compromisso AS COMP ' \
                                 u'WHERE compara_strings(COMP.compromisso,' + \
                                 unicode("'" + obj.compromisso_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u'WHERE HIST.compromisso_id IN (SELECT COMP.id FROM sncp_despesa_compromisso AS COMP '\
                                 u'WHERE compara_strings(COMP.compromisso,' + \
                                 unicode("'" + obj.compromisso_code_fim + "'") + \
                                 u') <= 0' + u')'

            # ORDENAÇÃO DESPESA
            if obj.ord_desp_1:
                if obj.ord_desp_1 == u'cabimento_id':
                    order += u'ORDER BY (SELECT cabimento FROM sncp_despesa_cabimento WHERE id=HIST.' + \
                             obj.ord_desp_1 + u') COLLATE "C"'

                elif obj.ord_desp_1 == u'compromisso_id':
                    order += u'ORDER BY (SELECT compromisso FROM sncp_despesa_compromisso WHERE id=HIST.' + \
                             obj.ord_desp_1 + u') COLLATE "C"'

                elif obj.ord_desp_1 in [u'economica_id', u'organica_id', u'funcional_id']:
                    order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                             obj.ord_desp_1 + u') COLLATE "C"'

                elif obj.ord_desp_1 == u'doc_contab_id':
                    order += u'ORDER BY (SELECT name FROM account_move WHERE id=HIST.' + \
                             obj.ord_desp_1 + u') COLLATE "C"'

                else:
                    order += u'ORDER BY HIST.' + obj.ord_desp_1

            if obj.ord_desp_2:
                if len(order) > 0:
                    if obj.ord_desp_2 == u'cabimento_id':
                        order += u',(SELECT cabimento FROM sncp_despesa_cabimento WHERE id=HIST.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    elif obj.ord_desp_2 == u'compromisso_id':
                        order += u',(SELECT compromisso FROM sncp_despesa_compromisso WHERE id=HIST.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    elif obj.ord_desp_2 in [u'economica_id', u'organica_id', u'funcional_id']:
                        order += u',(SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    elif obj.ord_desp_2 == u'doc_contab_id':
                        order += u',(SELECT name FROM account_move WHERE id=HIST.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    else:
                        order += u',HIST.' + obj.ord_desp_2

                else:
                    if obj.ord_desp_2 == u'cabimento_id':
                        order += u'ORDER BY (SELECT cabimento FROM sncp_despesa_cabimento WHERE id=HIST.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    elif obj.ord_desp_2 == u'compromisso_id':
                        order += u'ORDER BY (SELECT compromisso FROM sncp_despesa_compromisso WHERE id=HIST.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    elif obj.ord_desp_2 in [u'economica_id', u'organica_id', u'funcional_id']:
                        order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    elif obj.ord_desp_2 == u'doc_contab_id':
                        order += u'ORDER BY (SELECT name FROM account_move WHERE id=HIST.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    else:
                        order += u'ORDER BY HIST.' + obj.ord_desp_2

            if obj.ord_desp_3:
                if len(order) > 0:
                    if obj.ord_desp_3 == u'cabimento_id':
                        order += u',(SELECT cabimento FROM sncp_despesa_cabimento WHERE id=HIST.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    elif obj.ord_desp_3 == u'compromisso_id':
                        order += u',(SELECT compromisso FROM sncp_despesa_compromisso WHERE id=HIST.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    elif obj.ord_desp_3 in [u'economica_id', u'organica_id', u'funcional_id']:
                        order += u',(SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    elif obj.ord_desp_3 == u'doc_contab_id':
                        order += u',(SELECT name FROM account_move WHERE id=HIST.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    else:
                        order += u',HIST.' + obj.ord_desp_3

                else:
                    if obj.ord_desp_3 == u'cabimento_id':
                        order += u'ORDER BY (SELECT cabimento FROM sncp_despesa_cabimento WHERE id=HIST.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    elif obj.ord_desp_3 == u'compromisso_id':
                        order += u'ORDER BY (SELECT compromisso FROM sncp_despesa_compromisso WHERE id=HIST.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    elif obj.ord_desp_3 in [u'economica_id', u'organica_id', u'funcional_id']:
                        order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=HIST.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    elif obj.ord_desp_3 == u'doc_contab_id':
                        order += u'ORDER BY (SELECT name FROM account_move WHERE id=HIST.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    else:
                        order += u'ORDER BY HIST.' + obj.ord_desp_3

        query = unicode('SELECT HIST.id FROM sncp_orcamento_historico AS HIST ')

        if len(where) > 0:
            query += where

        if len(order) > 0:
            query += u' ' + order

        cr.execute(query)

        resultado = cr.fetchall()

        if len(resultado) == 0:
            return True
        else:
            hist_ids = [elem[0] for elem in resultado]
            cr.execute("""SELECT insere_historico_rodape(%s,%d)"""
                       % ('ARRAY' + unicode(hist_ids), obj.id))

        return query

    def imprimir_report(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT id
        FROM sncp_orcamento_historico_rodape
        WHERE orc_hist_cabecalho_id=%d
        """ % obj.id)

        rodapes_ids = cr.fetchall()

        if len(rodapes_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não há linhas para impressão.'))

        datas = {'ids': ids, 'model': 'sncp.orcamento.historico.cabecalho', }

        if obj.name == 'rece':
            return {
                'type': 'ir.actions.report.xml',
                'nodestroy': True,
                'report_name': 'sncp.orcamento.historico.cabecalho.receita.report',
                'datas': datas,
            }

        elif obj.name == 'desp':
            return {
                'type': 'ir.actions.report.xml',
                'nodestroy': True,
                'report_name': 'sncp.orcamento.historico.cabecalho.despesa.report',
                'datas': datas,
            }

        return True

    _columns = {
        'name': fields.selection([('rece', u'Receita'), ('desp', u'Despesa'), ],
                                 u'Histórico da:'),
        'ano_ini': fields.integer(u'Ano', size=4),
        'data_ini': fields.datetime(u'Data e Hora:'),
        'economica_code_ini': fields.char(u'Código da Económica:'),
        'categoria_rece_code_ini': fields.selection([
                                                    ('51rdota', u'Previsão Inicial'), ('52rrefo', u'Reforço (R)'),
                                                    ('53rabat', u'Abate (R)'),
                                                    ('54rinia', u'Receita p/cobrar Início do Ano'),
                                                    ('55rfact', u'Fatura de Vendas'),
                                                    ('56rncrd', u'Nota de Crédito de Vendas'),
                                                    ('57rliqd', u'Liquidação (R)'), ('58cobra', u'Cobrança')],
                                                    u'Categoria:'),
        'categoria_desp_code_ini': fields.selection([
                                                    ('01ddota', u'Dotação Inicial'), ('02drefo', u'Reforço (D)'),
                                                    ('03dabat', u'Abate (D)'), ('04cabim', u'Cabimento'),
                                                    ('05compr', u'Compromisso'), ('06futur', u'Compromisso Futuro'),
                                                    ('07dfact', u'Fatura de Compras'),
                                                    ('08dliqd', u'Liquidação (D)'),
                                                    ('09pagam', u'Pagamento'),
                                                    ('10repos', u'Reposição Abatida a Pagamento'),
                                                    ], u'Categoria:'),
        'organica_code_ini': fields.char(u'Código da Orgânica:'),
        'funcional_code_ini': fields.char(u'Código da Funcional:'),
        'documento_code_ini': fields.char(u'Código do Documento Contabilístico:'),
        'cabimento_code_ini': fields.char(u'Código do Cabimento:'),
        'compromisso_code_ini': fields.char(u'Código do Compromisso:'),
        'ano_fim': fields.integer(u'', size=4),
        'data_fim': fields.datetime(u''),
        'economica_code_fim': fields.char(u''),
        'categoria_rece_code_fim': fields.selection([
                                                    ('51rdota', u'Previsão Inicial'), ('52rrefo', u'Reforço (R)'),
                                                    ('53rabat', u'Abate (R)'),
                                                    ('54rinia', u'Receita p/cobrar Início do Ano'),
                                                    ('55rfact', u'Fatura de Vendas'),
                                                    ('56rncrd', u'Nota de Crédito de Vendas'),
                                                    ('57rliqd', u'Liquidação (R)'), ('58cobra', u'Cobrança')], u''),
        'categoria_desp_code_fim': fields.selection([
                                                    ('01ddota', u'Dotação Inicial'), ('02drefo', u'Reforço (D)'),
                                                    ('03dabat', u'Abate (D)'), ('04cabim', u'Cabimento'),
                                                    ('05compr', u'Compromisso'), ('06futur', u'Compromisso Futuro'),
                                                    ('07dfact', u'Fatura de Compras'),
                                                    ('08dliqd', u'Liquidação (D)'),
                                                    ('09pagam', u'Pagamento'),
                                                    ('10repos', u'Reposição Abatida a Pagamento'),
                                                    ], u''),
        'organica_code_fim': fields.char(u''),
        'funcional_code_fim': fields.char(u''),
        'documento_code_fim': fields.char(u''),
        'cabimento_code_fim': fields.char(u''),
        'compromisso_code_fim': fields.char(u''),
        'ord_rece_1': fields.selection([
                                       ('datahora', u'Data e Hora'), ('doc_contab_id', u'Documento'),
                                       ('economica_id', u'Económica'), ('categoria', u'Categoria'),
                                       ], u'Campo 1'),
        'ord_rece_2': fields.selection([
                                       ('datahora', u'Data e Hora'), ('doc_contab_id', u'Documento'),
                                       ('economica_id', u'Económica'), ('categoria', u'Categoria'),
                                       ], u'Campo 2'),
        'ord_rece_3': fields.selection([
                                       ('datahora', u'Data e Hora'), ('doc_contab_id', u'Documento'),
                                       ('economica_id', u'Económica'), ('categoria', u'Categoria'),
                                       ], u'Campo 3'),

        'ord_desp_1': fields.selection([
                                       ('datahora', u'Data e Hora'), ('doc_contab_id', u'Documento'),
                                       ('organica_id', u'Orgânica'), ('economica_id', u'Económica'),
                                       ('funcional_id', u'Funcional'), ('cabimento_id', u'Cabimento'),
                                       ('compromisso_id', u'Compromisso'), ('categoria', u'Categoria'),
                                       ], u'Campo 1'),
        'ord_desp_2': fields.selection([
                                       ('datahora', u'Data e Hora'), ('doc_contab_id', u'Documento'),
                                       ('organica_id', u'Orgânica'), ('economica_id', u'Económica'),
                                       ('funcional_id', u'Funcional'), ('cabimento_id', u'Cabimento'),
                                       ('compromisso_id', u'Compromisso'), ('categoria', u'Categoria'),
                                       ], u'Campo 2'),
        'ord_desp_3': fields.selection([
                                       ('datahora', u'Data e Hora'), ('doc_contab_id', u'Documento'),
                                       ('organica_id', u'Orgânica'), ('economica_id', u'Económica'),
                                       ('funcional_id', u'Funcional'), ('cabimento_id', u'Cabimento'),
                                       ('compromisso_id', u'Compromisso'), ('categoria', u'Categoria'),
                                       ], u'Campo 3'),

        'orc_hist_rodape_id': fields.one2many('sncp.orcamento.historico.rodape',
                                              'orc_hist_cabecalho_id',
                                              string=u'Rodapé'),
    }

    _defaults = {
        'name': 'rece',
        'ano_fim': date.today().year,
        'data_fim': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                                     datetime.now().minute, datetime.now().second)),
        'categoria_rece_code_ini': u'51rdota',
        'economica_code_fim': u'zzzzzzzzzzzz',
        'documento_code_fim': u'zzzzzzzzzzzz',
        'organica_code_fim': u'zzzzzzzzzzzz',
        'funcional_code_fim': u'zzzzzzzzzzzz',
        'categoria_desp_code_fim': u'10repos',
    }

    def ordenacao_valida_rece(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.ord_rece_1:
            if obj.ord_rece_2:
                if obj.ord_rece_1 == obj.ord_rece_2:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

            if obj.ord_rece_3:
                if obj.ord_rece_1 == obj.ord_rece_3:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

        if obj.ord_rece_2:
            if obj.ord_rece_3:
                if obj.ord_rece_2 == obj.ord_rece_3:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

        return True

    def ordenacao_valida_desp(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.ord_desp_1:
            if obj.ord_desp_2:
                if obj.ord_desp_1 == obj.ord_desp_2:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

            if obj.ord_desp_3:
                if obj.ord_desp_1 == obj.ord_desp_3:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

        if obj.ord_desp_2:
            if obj.ord_desp_3:
                if obj.ord_desp_2 == obj.ord_desp_3:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

        return True

    _constraints = [
        (ordenacao_valida_rece, u'', ['ord_rece_1', 'ord_rece_2', 'ord_rece_3']),
        (ordenacao_valida_desp, u'', ['ord_desp_1', 'ord_desp_2', 'ord_desp_3'])
    ]

sncp_orcamento_historico_cabecalho()


class sncp_orcamento_historico_rodape(osv.Model):
    _name = 'sncp.orcamento.historico.rodape'

    _columns = {
        'orc_hist_cabecalho_id': fields.many2one('sncp.orcamento.historico.cabecalho'),
        'name': fields.integer('Ano'),
        'categoria': fields.selection([
                                      ('01ddota', u'Dotação Inicial'), ('02drefo', u'Reforço (D)'),
                                      ('03dabat', u'Abate (D)'), ('04cabim', u'Cabimento'),
                                      ('05compr', u'Compromisso'), ('06futur', u'Compromisso Futuro'),
                                      ('07dfact', u'Fatura de Compras'), ('08dliqd', u'Liquidação (D)'),
                                      ('09pagam', u'Pagamento'), ('10repos', u'Reposição Abatida a Pagamento'),
                                      ('51rdota', u'Previsão Inicial'), ('52rrefo', u'Reforço (R)'),
                                      ('53rabat', u'Abate (R)'), ('54rinia', u'Receita p/cobrar Início do Ano'),
                                      ('55rfact', u'Fatura de Vendas'), ('56rncrd', u'Nota de Crédito de Vendas'),
                                      ('57rliqd', u'Liquidação (R)'), ('58cobra', u'Cobrança')], u'Categoria'),
        'datahora': fields.datetime("Data e Hora"),
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')]),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')]),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')]),
        'centrocustos_id': fields.many2one('account.analytic.account', u'Centro de Custos',
                                           domain=[('tipo_dim', '=', 'cc'), ('type', '=', 'normal')]),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'cabimento_id': fields.many2one('sncp.despesa.cabimento', u'Cabimento'),
        'compromisso_id': fields.many2one('sncp.despesa.compromisso', u'Compromisso'),
        'doc_contab_id': fields.many2one('account.move', u'ID Documento'),
        'doc_contab_name': fields.char(u'Documento'),
    }

sncp_orcamento_historico_rodape()


# ______________________________________________________ORCAMENTO HISTORICO______________________________
class sncp_orcamento_historico(osv.Model):
    _name = 'sncp.orcamento.historico'
    _description = u"Histórico"

    def insere_valores_historico(self, cr, uid, ids, vals):

        if 'datahora' in vals:
            datahora = unicode(vals['datahora'])
            if datahora.find('.') != -1:
                datahora = datahora[:datahora.find('.')]
        else:
            datahora = unicode(datetime.now())
            if datahora.find('.') != -1:
                datahora = datahora[:datahora.find('.')]

        if vals['categoria'] is '05compr' or vals['categoria'] is '06futur':
            linha_id = self.search(cr, uid, [('name', '=', vals['name']),
                                             ('categoria', '=', vals['categoria']),
                                             ('organica_id', '=', vals['organica_id']),
                                             ('economica_id', '=', vals['economica_id']),
                                             ('funcional_id', '=', vals['funcional_id']),
                                             ('compromisso_id', '=', vals['compromisso_id'])])
            if len(linha_id) == 1:
                self.write(cr, uid, linha_id, {'montante': vals['montante']})
                send = {
                    'name': vals['name'],
                    'categoria': vals['categoria'],
                    'organica_id': vals['organica_id'],
                    'economica_id': vals['economica_id'],
                    'funcional_id': vals['funcional_id'],
                    'montante': vals['montante'],
                    'diferenca': vals['diferenca'],
                }
                db_sncp_orcamento_acumulados = self.pool.get('sncp.orcamento.acumulados')
                db_sncp_orcamento_acumulados.insere_atualiza_valores_acumulados(cr, uid, [], send, 1)
            else:
                send = {
                    'name': vals['name'], 'categoria': vals['categoria'],
                    'datahora': datahora, 'organica_id': vals['organica_id'],
                    'economica_id': vals['economica_id'], 'funcional_id': vals['funcional_id'],
                    'centrocustos_id': vals['centrocustos_id'], 'montante': vals['montante'],
                    'cabimento_id': vals['cabimento_id'], 'cabimento_linha_id': vals['cabimento_linha_id'],
                    'compromisso_id': vals['compromisso_id'], 'compromisso_linha_id': vals['compromisso_linha_id'],
                    'doc_contab_id': vals['doc_contab_id'], 'doc_contab_linha_id': vals['doc_contab_linha_id'],
                }

                self.create(cr, uid, send, )
                send = {
                    'name': vals['name'],
                    'categoria': vals['categoria'],
                    'organica_id': vals['organica_id'],
                    'economica_id': vals['economica_id'],
                    'funcional_id': vals['funcional_id'],
                    'montante': vals['montante'],
                    'diferenca': vals['diferenca'],
                }
                db_sncp_orcamento_acumulados = self.pool.get('sncp.orcamento.acumulados')
                db_sncp_orcamento_acumulados.insere_atualiza_valores_acumulados(cr, uid, [], send, 1)
        else:
            send = {
                'name': vals['name'], 'categoria': vals['categoria'],
                'datahora': datahora, 'organica_id': vals['organica_id'],
                'economica_id': vals['economica_id'], 'funcional_id': vals['funcional_id'],
                'centrocustos_id': vals['centrocustos_id'], 'montante': vals['montante'],
                'cabimento_id': vals['cabimento_id'], 'cabimento_linha_id': vals['cabimento_linha_id'],
                'compromisso_id': vals['compromisso_id'], 'compromisso_linha_id': vals['compromisso_linha_id'],
                'doc_contab_id': vals['doc_contab_id'], 'doc_contab_linha_id': vals['doc_contab_linha_id'],
            }

            self.create(cr, uid, send, )

            send = {
                'name': vals['name'],
                'categoria': vals['categoria'],
                'organica_id': vals['organica_id'],
                'economica_id': vals['economica_id'],
                'funcional_id': vals['funcional_id'],
                'montante': vals['montante'],
            }

            db_sncp_orcamento_acumulados = self.pool.get('sncp.orcamento.acumulados')
            db_sncp_orcamento_acumulados.insere_atualiza_valores_acumulados(cr, uid, [], send, 1)
        return datahora

    def atualiza_valores_historico(self, cr, uid, ids, vals):

        linha_id = self.search(cr, uid, [('name', '=', vals['name']),
                                         ('categoria', '=', vals['categoria']),
                                         ('datahora', '=', vals['datahora']), ])
        if len(linha_id) == 1:
            obj = self.browse(cr, uid, linha_id)
            montante = obj.montante + vals.montante
            aux = decimal.Decimal(unicode(montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante = float(aux)
            self.write(cr, uid, linha_id, {'montante': montante})
        else:
            raise osv.except_osv(_(u'Aviso: Contacte o administrador da base de dados. '
                                   u'Há mais do que uma correspondência para atualização do histórico,'
                                   u' ou a linha não existe :'), _(len(linha_id)))
        send = {
            'name': vals['name'],
            'categoria': vals['categoria'],
            'organica_id': obj.organica_id,
            'economica_id': obj.economica_id,
            'funcional_id': obj.funcional_id,
            'montante': vals['montante'],
        }

        db_sncp_orcamento_acumulados = self.pool.get('sncp.orcamento.acumulados')
        db_sncp_orcamento_acumulados.insere_atualiza_valores_acumulados(cr, uid, send)

    def elimina_valores_historico(self, cr, uid, ids, vals):
        if 'compromisso_id' in vals:
            linhas_ids = self.search(cr, uid, [('name', '=', vals['name']),
                                               ('categoria', '=', vals['categoria']),
                                               ('compromisso_id', '=', vals['compromisso_id']), ])
        else:
            linhas_ids = self.search(cr, uid, [('name', '=', vals['name']),
                                               ('categoria', '=', vals['categoria']),
                                               ('doc_contab_id', '=', vals['doc_contab_id']), ])
        for linha in self.browse(cr, uid, linhas_ids):
            send = {
                'name': vals['name'],
                'categoria': vals['categoria'],
                'organica_id': linha.organica_id.id,
                'economica_id': linha.economica_id.id,
                'funcional_id': linha.funcional_id.id,
                'montante': linha.montante,
            }
            db_sncp_orcamento_acumulados = self.pool.get('sncp.orcamento.acumulados')
            db_sncp_orcamento_acumulados.insere_atualiza_valores_acumulados(cr, uid, [], send, 0)
        self.unlink(cr, uid, linhas_ids)
        return True

    def recalcula_acumulados(self, cr, uid, ids, vals):
        db_sncp_orcamento_acumulados = self.pool.get('sncp.orcamento.acumulados')
        db_sncp_orcamento_acumulados.elimina_linhas_acumulados(cr, uid, [], vals)

        if vals['categoria'] is not None:
            linha_ids = self.search(cr, uid, [('name', '=', vals['name']),
                                              ('categoria', '=', vals['categoria']), ])
        else:
            linha_ids = self.search(cr, uid, [('name', '=', vals['name']), ])

        for linha in self.browse(cr, uid, linha_ids):
            send = {
                'name': vals['name'],
                'categoria': linha.categoria,
                'organica': linha.organica,
                'economica': linha.economica,
                'funcional': linha.funcional,
                'montante': vals['montante'],
            }
            db_sncp_orcamento_acumulados.insere_atualiza_valores_acumulados(cr, uid, [], send, 1)

    def get_ano_pesquisa_list_js(self, cr, uid):
        lista = []
        cr.execute("""SELECT DISTINCT(name) FROM sncp_orcamento_historico""")
        result = cr.fetchall()
        for res in result:
            lista.append(res[0])
        return lista

    def get_dimensao_list_js(self, cr, uid, dim):
        obj_dim = self.pool.get('account.analytic.account')
        lista = []
        if dim == 'organica':
            cr.execute("""SELECT DISTINCT(organica_id) FROM sncp_orcamento_historico""")
            result = cr.fetchall()
        elif dim == 'economica':
            cr.execute("""SELECT DISTINCT(economica_id) FROM sncp_orcamento_historico""")
            result = cr.fetchall()
        else:
            cr.execute("""SELECT DISTINCT(funcional_id) FROM sncp_orcamento_historico""")
            result = cr.fetchall()
        for res in result:
            lista.append(res[0])
        return obj_dim.name_get(cr, uid, lista)

    _columns = {
        'name': fields.integer('Ano'),
        'categoria': fields.selection([
                                      ('01ddota', u'Dotação Inicial'), ('02drefo', u'Reforço (D)'),
                                      ('03dabat', u'Abate (D)'), ('04cabim', u'Cabimento'),
                                      ('05compr', u'Compromisso'), ('06futur', u'Compromisso Futuro'),
                                      ('07dfact', u'Fatura de Compras'), ('08dliqd', u'Liquidação (D)'),
                                      ('09pagam', u'Pagamento'), ('10repos', u'Reposição Abatida a Pagamento'),
                                      ('51rdota', u'Previsão Inicial'), ('52rrefo', u'Reforço (R)'),
                                      ('53rabat', u'Abate (R)'), ('54rinia', u'Receita p/cobrar Início do Ano'),
                                      ('55rfact', u'Fatura de Vendas'), ('56rncrd', u'Nota de Crédito de Vendas'),
                                      ('57rliqd', u'Liquidação (R)'), ('58cobra', u'Cobrança')], u'Categoria'),
        'datahora': fields.datetime("Data e Hora"),
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')]),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')]),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')]),
        'centrocustos_id': fields.many2one('account.analytic.account', u'Centro de Custos',
                                           domain=[('tipo_dim', '=', 'cc'), ('type', '=', 'normal')]),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'cabimento_id': fields.many2one('sncp.despesa.cabimento', u'Cabimento'),
        'cabimento_linha_id': fields.many2one('sncp.despesa.cabimento.linha', u'Cabimento Linha'),
        'compromisso_id': fields.many2one('sncp.despesa.compromisso', u'Compromisso'),
        'compromisso_linha_id': fields.many2one('sncp.despesa.compromisso.linha', u'Linha de compromisso'),
        'doc_contab_id': fields.many2one('account.move', u'Documento'),
        'doc_contab_linha_id': fields.many2one('account.move.line', u'Linha do Documento'),
    }

    _order = 'datahora desc'


sncp_orcamento_historico()
# _______________________________________________________VER ACUMULADOS__________________________________


class sncp_orcamento_acumulados_cabecalho(osv.Model):
    _name = 'sncp.orcamento.acumulados.cabecalho'

    def onchange_name(self, cr, uid, ids, nome, context=None):
        if type(ids) is list:
            if len(ids) != 0:
                cr.execute("""
                DELETE FROM sncp_orcamento_acumulados_rodape
                WHERE orc_acum_cabecalho_id=%d
                """ % ids[0])

        if not nome:
            return {'value': {'ord_desp_1': None,
                              'ord_desp_2': None,
                              'ord_desp_3': None,
                              'ord_rece_1': None,
                              'ord_rece_2': None,
                              'orc_acum_rodape_id': []}}

        if nome == 'rece':
            return {'value': {'ord_desp_1': None,
                              'ord_desp_2': None,
                              'ord_desp_3': None,
                              'orc_acum_rodape_id': []}}
        elif nome == 'desp':
            return {'value': {'ord_rece_1': None,
                              'ord_rece_2': None,
                              'orc_acum_rodape_id': []}}

    def pesquisar(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        cr.execute("""        DELETE FROM sncp_orcamento_acumulados_rodape        """)

        cr.execute("""        DELETE FROM sncp_orcamento_acumulados_cabecalho WHERE id<%d""" % obj.id)

        where = u''
        order = u''
        x = unicode(obj.ano_ini)
        y = unicode(obj.ano_fim)

        # ANO
        if len(x) > 0 and int(x[0]) in range(0, 10):
            where += u'WHERE ACUM.name >= ' + x
            if len(y) > 0 and int(y[0]) in range(0, 10):
                where += u' AND ACUM.name <= ' + y
        else:
            if len(y) > 0 and int(y[0]) in range(0, 10):
                where += u'WHERE ACUM.name <= ' + y

        # ECONOMICA
        if obj.economica_code_ini:
            if len(where) > 0:
                where += u' AND ACUM.economica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                         u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.economica_code_ini + "'") + \
                         u') >= 0'
                if obj.economica_code_fim:
                    where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.economica_code_fim + "'") + \
                             u') <= 0' + u')'
                else:
                    where += u')'
            else:
                where += u'WHERE ACUM.economica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                         u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.economica_code_ini + "'") + \
                         u') >= 0'
                if obj.economica_code_fim:
                    where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.economica_code_fim + "'") + \
                             u') <= 0' + u')'
                else:
                    where += u')'
        else:
            if obj.economica_code_fim:
                if len(where) > 0:
                    where += u' AND ACUM.economica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.economica_code_fim + "'") + \
                             u') <= 0' + u')'
                else:
                    where += u'WHERE ACUM.economica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.economica_code_fim + "'") + \
                             u') <= 0' + u')'

        if obj.name == u'rece':
            # CATEGORIA
            if len(where) > 0:
                where += u' AND ACUM.categoria >= ' + unicode("'" + obj.categoria_rece_code_ini + "'")
                if obj.categoria_rece_code_fim:
                    where += u' AND ACUM.categoria <= ' + unicode("'" + obj.categoria_rece_code_fim + "'")
            else:
                where += u'WHERE ACUM.categoria >= ' + unicode("'" + obj.categoria_rece_code_ini + "'")
                if obj.categoria_rece_code_fim:
                    where += u' AND ACUM.categoria <= ' + unicode("'" + obj.categoria_rece_code_fim + "'")

            # ORDENAÇÃO RECEITA
            if obj.ord_rece_1:
                if obj.ord_rece_1 == u'economica_id':
                    order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=ACUM.' + \
                             obj.ord_rece_1 + u') COLLATE "C"'

                else:
                    order += u'ORDER BY ACUM.' + obj.ord_rece_1

            if obj.ord_rece_2:
                if len(order) > 0:
                    if obj.ord_rece_2 == u'economica_id':
                        order += u',(SELECT code FROM account_analytic_account WHERE id=ACUM.' + \
                                 obj.ord_rece_2 + u') COLLATE "C"'

                    else:
                        order += u',ACUM.' + obj.ord_rece_2

                else:
                    if obj.ord_rece_2 == u'economica_id':
                        order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=ACUM.' + \
                                 obj.ord_rece_2 + u') COLLATE "C"'

                    else:
                        order += u'ORDER BY ACUM.' + obj.ord_rece_2

        elif obj.name == u'desp':
            # CATEGORIA
            if len(where) > 0:
                if obj.categoria_desp_code_ini:
                    where += u' AND ACUM.categoria >= ' + unicode("'" + obj.categoria_desp_code_ini + "'")
                    where += u' AND ACUM.categoria <= ' + unicode("'" + obj.categoria_desp_code_fim + "'")
                else:
                    where += u' AND ACUM.categoria <= ' + unicode("'" + obj.categoria_desp_code_fim + "'")
            else:
                if obj.categoria_desp_code_ini:
                    where += u'WHERE ACUM.categoria >= ' + unicode("'" + obj.categoria_desp_code_ini + "'")
                    where += u' AND ACUM.categoria <= ' + unicode("'" + obj.categoria_desp_code_fim + "'")
                else:
                    where += u'WHERE ACUM.categoria <= ' + unicode("'" + obj.categoria_desp_code_fim + "'")

            # ORGANICA
            if obj.organica_code_ini:
                if len(where) > 0:
                    where += u' AND ACUM.organica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.organica_code_ini + "'") + \
                             u') >= 0'
                    if obj.organica_code_fim:
                        where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.organica_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
                else:
                    where += u'WHERE ACUM.organica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.organica_code_ini + "'") + \
                             u') >= 0'
                    if obj.organica_code_fim:
                        where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.organica_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
            else:
                if obj.organica_code_fim:
                    if len(where) > 0:
                        where += u' AND ACUM.organica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                                 u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.organica_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u'WHERE ACUM.organica_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                                 u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.organica_code_fim + "'") + \
                                 u') <= 0' + u')'

            # FUNCIONAL
            if obj.funcional_code_ini:
                if len(where) > 0:
                    where += u' AND ACUM.funcional_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_ini + "'") + \
                             u') >= 0'
                    if obj.funcional_code_fim:
                        where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
                else:
                    where += u'WHERE ACUM.funcional_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                             u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_ini + "'") + \
                             u') >= 0'
                    if obj.funcional_code_fim:
                        where += u' AND compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u')'
            else:
                if obj.funcional_code_fim:
                    if len(where) > 0:
                        where += u' AND ACUM.funcional_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                                 u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_fim + "'") + \
                                 u') <= 0' + u')'
                    else:
                        where += u'WHERE ACUM.funcional_id IN (SELECT AAA.id FROM account_analytic_account AS AAA ' \
                                 u'WHERE compara_strings(AAA.code,' + unicode("'" + obj.funcional_code_fim + "'") + \
                                 u') <= 0' + u')'

            # ORDENAÇÃO DESPESA
            if obj.ord_desp_1:
                if obj.ord_desp_1 in [u'economica_id', u'organica_id', u'funcional_id']:
                    order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=ACUM.' + \
                             obj.ord_desp_1 + u') COLLATE "C"'

                else:
                    order += u'ORDER BY ACUM.' + obj.ord_desp_1

            if obj.ord_desp_2:
                if len(order) > 0:
                    if obj.ord_desp_2 in [u'economica_id', u'organica_id', u'funcional_id']:
                        order += u',(SELECT code FROM account_analytic_account WHERE id=ACUM.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    else:
                        order += u',ACUM.' + obj.ord_desp_2

                else:
                    if obj.ord_desp_2 in [u'economica_id', u'organica_id', u'funcional_id']:
                        order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=ACUM.' + \
                                 obj.ord_desp_2 + u') COLLATE "C"'

                    else:
                        order += u'ORDER BY ACUM.' + obj.ord_desp_2

            if obj.ord_desp_3:
                if len(order) > 0:
                    if obj.ord_desp_3 in [u'economica_id', u'organica_id', u'funcional_id']:
                        order += u',(SELECT code FROM account_analytic_account WHERE id=ACUM.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    else:
                        order += u',HIST.' + obj.ord_desp_3

                else:
                    if obj.ord_desp_3 in [u'economica_id', u'organica_id', u'funcional_id']:
                        order += u'ORDER BY (SELECT code FROM account_analytic_account WHERE id=ACUM.' + \
                                 obj.ord_desp_3 + u') COLLATE "C"'

                    else:
                        order += u'ORDER BY ACUM.' + obj.ord_desp_3

        query = unicode('SELECT ACUM.id FROM sncp_orcamento_acumulados AS ACUM ')

        if len(where) > 0:
            query += where

        if len(order) > 0:
            query += u' ' + order

        cr.execute(query)

        resultado = cr.fetchall()

        if len(resultado) == 0:
            return True
        else:
            hist_ids = [elem[0] for elem in resultado]
            cr.execute("""SELECT insere_acumulados_rodape(%s,%d)"""
                       % ('ARRAY' + unicode(hist_ids), obj.id))

        return query

    def imprimir_report(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT id
        FROM sncp_orcamento_acumulados_rodape
        WHERE orc_acum_cabecalho_id=%d
        """ % obj.id)

        rodapes_ids = cr.fetchall()

        if len(rodapes_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não há linhas para impressão.'))

        datas = {'ids': ids, 'model': 'sncp.orcamento.acumulados.cabecalho', }

        if obj.name == 'rece':
            return {
                'type': 'ir.actions.report.xml',
                'nodestroy': True,
                'report_name': 'sncp.orcamento.acumulados.cabecalho.receita.report',
                'datas': datas,
            }

        elif obj.name == 'desp':
            return {
                'type': 'ir.actions.report.xml',
                'nodestroy': True,
                'report_name': 'sncp.orcamento.acumulados.cabecalho.despesa.report',
                'datas': datas,
            }

        return True

    _columns = {
        'name': fields.selection([('rece', u'Receita'), ('desp', u'Despesa'), ],
                                 u'Acumulados da:'),
        'ano_ini': fields.integer(u'Ano', size=4),
        'economica_code_ini': fields.char(u'Código da Económica:'),
        'categoria_rece_code_ini': fields.selection([
                                                    ('51rdota', u'Previsão Inicial'), ('52rrefo', u'Reforço (R)'),
                                                    ('53rabat', u'Abate (R)'),
                                                    ('54rinia', u'Receita p/cobrar Início do Ano'),
                                                    ('55rfact', u'Fatura de Vendas'),
                                                    ('56rncrd', u'Nota de Crédito de Vendas'),
                                                    ('57rliqd', u'Liquidação (R)'), ('58cobra', u'Cobrança')],
                                                    u'Categoria:'),
        'categoria_desp_code_ini': fields.selection([
                                                    ('01ddota', u'Dotação Inicial'), ('02drefo', u'Reforço (D)'),
                                                    ('03dabat', u'Abate (D)'), ('04cabim', u'Cabimento'),
                                                    ('05compr', u'Compromisso'), ('06futur', u'Compromisso Futuro'),
                                                    ('07dfact', u'Fatura de Compras'),
                                                    ('08dliqd', u'Liquidação (D)'),
                                                    ('09pagam', u'Pagamento'),
                                                    ('10repos', u'Reposição Abatida a Pagamento'),
                                                    ], u'Categoria:'),
        'organica_code_ini': fields.char(u'Código da Orgânica:'),
        'funcional_code_ini': fields.char(u'Código da Funcional:'),
        'ano_fim': fields.integer(u'', size=4),
        'economica_code_fim': fields.char(u''),
        'categoria_rece_code_fim': fields.selection([
                                                    ('51rdota', u'Previsão Inicial'), ('52rrefo', u'Reforço (R)'),
                                                    ('53rabat', u'Abate (R)'),
                                                    ('54rinia', u'Receita p/cobrar Início do Ano'),
                                                    ('55rfact', u'Fatura de Vendas'),
                                                    ('56rncrd', u'Nota de Crédito de Vendas'),
                                                    ('57rliqd', u'Liquidação (R)'), ('58cobra', u'Cobrança')], u''),
        'categoria_desp_code_fim': fields.selection([
                                                    ('01ddota', u'Dotação Inicial'), ('02drefo', u'Reforço (D)'),
                                                    ('03dabat', u'Abate (D)'), ('04cabim', u'Cabimento'),
                                                    ('05compr', u'Compromisso'), ('06futur', u'Compromisso Futuro'),
                                                    ('07dfact', u'Fatura de Compras'),
                                                    ('08dliqd', u'Liquidação (D)'),
                                                    ('09pagam', u'Pagamento'),
                                                    ('10repos', u'Reposição Abatida a Pagamento'),
                                                    ], u''),

        'organica_code_fim': fields.char(u''),
        'funcional_code_fim': fields.char(u''),
        'ord_rece_1': fields.selection([('economica_id', u'Económica'), ('categoria', u'Categoria')], u'Campo 1'),
        'ord_rece_2': fields.selection([('economica_id', u'Económica'), ('categoria', u'Categoria')], u'Campo 2'),
        'ord_desp_1': fields.selection([
                                       ('organica_id', u'Orgânica'), ('economica_id', u'Económica'),
                                       ('funcional_id', u'Funcional'), ('categoria', u'Categoria'),
                                       ], u'Campo 1'),
        'ord_desp_2': fields.selection([
                                       ('organica_id', u'Orgânica'), ('economica_id', u'Económica'),
                                       ('funcional_id', u'Funcional'), ('categoria', u'Categoria'),
                                       ], u'Campo 2'),
        'ord_desp_3': fields.selection([
                                       ('organica_id', u'Orgânica'), ('economica_id', u'Económica'),
                                       ('funcional_id', u'Funcional'), ('categoria', u'Categoria'),
                                       ], u'Campo 3'),
        'orc_acum_rodape_id': fields.one2many('sncp.orcamento.acumulados.rodape', 'orc_acum_cabecalho_id',
                                              string=u'Rodapé'),
    }

    _defaults = {
        'name': 'rece',
        'ano_fim': date.today().year,
        'categoria_rece_code_ini': u'51rdota',
        'economica_code_fim': u'zzzzzzzzzzzz',
        'organica_code_fim': u'zzzzzzzzzzzz',
        'funcional_code_fim': u'zzzzzzzzzzzz',
        'categoria_desp_code_fim': u'10repos',
    }

    def ordenacao_valida_rece(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.ord_rece_1:
            if obj.ord_rece_2:
                if obj.ord_rece_1 == obj.ord_rece_2:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

        return True

    def ordenacao_valida_desp(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.ord_desp_1:
            if obj.ord_desp_2:
                if obj.ord_desp_1 == obj.ord_desp_2:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

            if obj.ord_desp_3:
                if obj.ord_desp_1 == obj.ord_desp_3:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

        if obj.ord_desp_2:
            if obj.ord_desp_3:
                if obj.ord_desp_2 == obj.ord_desp_3:
                    raise osv.except_osv(_(u'Aviso'), _(u'Campos para ordenar iguais.'))

        return True

    _constraints = [
        (ordenacao_valida_rece, u'', ['ord_rece_1', 'ord_rece_2', 'ord_rece_3']),
        (ordenacao_valida_desp, u'', ['ord_desp_1', 'ord_desp_2', 'ord_desp_3'])
    ]


sncp_orcamento_acumulados_cabecalho()


class sncp_orcamento_acumulados_rodape(osv.Model):
    _name = 'sncp.orcamento.acumulados.rodape'

    _columns = {
        'orc_acum_cabecalho_id': fields.many2one('sncp.orcamento.acumulados.cabecalho'),
        'name': fields.integer('Ano'),
        'categoria': fields.selection([
                                      ('01ddota', u'Dotação Inicial'), ('02drefo', u'Reforço (D)'),
                                      ('03dabat', u'Abate (D)'), ('04cabim', u'Cabimento'),
                                      ('05compr', u'Compromisso'), ('06futur', u'Compromisso Futuro'),
                                      ('07dfact', u'Fatura de Compras'), ('08dliqd', u'Liquidação (D)'),
                                      ('09pagam', u'Pagamento'), ('10repos', u'Reposição Abatida a Pagamento'),
                                      ('51rdota', u'Previsão Inicial'), ('52rrefo', u'Reforço (R)'),
                                      ('53rabat', u'Abate (R)'), ('54rinia', u'Receita p/cobrar Início do Ano'),
                                      ('55rfact', u'Fatura de Vendas'), ('56rncrd', u'Nota de Crédito de Vendas'),
                                      ('57rliqd', u'Liquidação (R)'), ('58cobra', u'Cobrança')], u'Categoria'),
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')]),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')]),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')]),
        'centrocustos_id': fields.many2one('account.analytic.account', u'Centro de Custos',
                                           domain=[('tipo_dim', '=', 'cc'), ('type', '=', 'normal')]),
        'montante': fields.float(u'Montante', digits=(12, 2)),
    }

sncp_orcamento_acumulados_rodape()


# _______________________________________________________ORCAMENTO ACUMULADOS_____________________________
class sncp_orcamento_acumulados(osv.Model):
    _name = 'sncp.orcamento.acumulados'
    _description = u"Acumulados"

    def insere_atualiza_valores_acumulados(self, cr, uid, ids, vals, flag):
        linha_id = self.search(cr, uid, [('name', '=', vals['name']),
                                         ('categoria', '=', vals['categoria']),
                                         ('organica_id', '=', vals['organica_id']),
                                         ('economica_id', '=', vals['economica_id']),
                                         ('funcional_id', '=', vals['funcional_id'])])
        if flag == 1:
            if len(linha_id) == 1:
                if vals['categoria'] is '05compr' or vals['categoria'] is '06futur':
                    obj = self.browse(cr, uid, linha_id[0])
                    montante = 0.0
                    if vals['diferenca'] == 0.0:
                        montante = obj.montante
                    elif vals['diferenca'] != 0.0:
                        montante = obj.montante + vals['diferenca']
                        aux = decimal.Decimal(unicode(montante))
                        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                        montante = float(aux)
                    self.write(cr, uid, linha_id, {'montante': montante})
                else:
                    obj = self.browse(cr, uid, linha_id[0])
                    montante = obj.montante + vals['montante']
                    aux = decimal.Decimal(unicode(montante))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    montante = float(aux)
                    self.write(cr, uid, linha_id, {'montante': montante})
            elif len(linha_id) == 0:
                send = {
                    'name': vals['name'],
                    'categoria': vals['categoria'],
                    'organica_id': vals['organica_id'],
                    'economica_id': vals['economica_id'],
                    'funcional_id': vals['funcional_id'],
                    'montante': vals['montante'], }

                self.create(cr, uid, send)
            else:
                raise osv.except_osv(_(u'Aviso: Contacte o administrador da base de dados. '
                                       u'Há mais de que uma correspondência para atualização dos acumulados :'),
                                     _(len(linha_id)), )
        elif flag == 0:
            if len(linha_id) == 1:
                obj = self.browse(cr, uid, linha_id[0])
                montante = obj.montante - vals['montante']

                aux = decimal.Decimal(unicode(montante))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante = float(aux)

                self.write(cr, uid, linha_id, {'montante': montante})
            elif len(linha_id) == 0:
                send = {
                    'name': vals['name'],
                    'categoria': vals['categoria'],
                    'organica_id': vals['organica_id'],
                    'economica_id': vals['economica_id'],
                    'funcional_id': vals['funcional_id'],
                    'montante': vals['montante'], }

                self.create(cr, uid, send)
            else:
                raise osv.except_osv(_(u'Aviso: Contacte o administrador da base de dados. '
                                       u'Há mais de que uma correspondência para atualização dos acumulados :'),
                                     _(len(linha_id)), )

    def elimina_linhas_acumulados(self, cr, uid, ids, vals):

        if vals['categoria'] is not None:
            linha_ids = self.search(cr, uid, [('name', '=', vals['name']),
                                              ('categoria', '=', vals['categoria']), ])
        else:
            linha_ids = self.search(cr, uid, [('name', '=', vals['name']), ])
        self.unlink(cr, uid, linha_ids)

    def get_ano_pesquisa_list_js(self, cr, uid):
        lista = []
        cr.execute("""SELECT DISTINCT(name) FROM sncp_orcamento_acumulados""")
        result = cr.fetchall()
        for res in result:
            lista.append(res[0])
        return lista

    def get_dimensao_list_js(self, cr, uid, dim):
        obj_dim = self.pool.get('account.analytic.account')
        lista = []
        result = []
        if dim == 'organica':
            cr.execute("""SELECT DISTINCT(organica_id) FROM sncp_orcamento_acumulados""")
            result = cr.fetchall()
        elif dim == 'economica':
            cr.execute("""SELECT DISTINCT(economica_id) FROM sncp_orcamento_acumulados""")
            result = cr.fetchall()
        elif dim == 'funcional':
            cr.execute("""SELECT DISTINCT(funcional_id) FROM sncp_orcamento_acumulados""")
            result = cr.fetchall()
        for res in result:
            lista.append(res[0])
        return obj_dim.name_get(cr, uid, lista)

    def get_name_complete_funcional_js(self, cr, uid):
        cr.execute("""
        SELECT CONCAT(code,' ',name)
        FROM account_analytic_account AS AAA
        WHERE AAA.id IN
        (SELECT DISTINCT SOA.funcional_id FROM sncp_orcamento_acumulados AS SOA
        WHERE SOA.funcional_id IS NOT NULL)
        """)
        name_complete_funcional = cr.fetchall()
        name_complete_funcional = [elem[0] for elem in name_complete_funcional]

        return name_complete_funcional

    _columns = {
        'name': fields.integer('Ano'),
        'categoria': fields.selection([
                                      ('01ddota', u'Dotação Inicial'), ('02drefo', u'Reforço (D)'),
                                      ('03dabat', u'Abate (D)'), ('04cabim', u'Cabimento'),
                                      ('05compr', u'Compromisso'), ('06futur', u'Compromisso Futuro'),
                                      ('07dfact', u'Fatura de Compras'), ('08dliqd', u'Liquidação (D)'),
                                      ('09pagam', u'Pagamento'), ('10repos', u'Reposição Abatida a Pagamento'),
                                      ('51rdota', u'Previsão Inicial'), ('52rrefo', u'Reforço (R)'),
                                      ('53rabat', u'Abate (R)'), ('54rinia', u'Receita p/cobrar Início do Ano'),
                                      ('55rfact', u'Fatura de Vendas'), ('56rncrd', u'Nota de Crédito de Vendas'),
                                      ('57rliqd', u'Liquidação (R)'), ('58cobra', u'Cobrança')], u'Categoria'),
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')]),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')]),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')]),
        'montante': fields.float(u'Montante', digits=(12, 2)),
    }

    _order = 'name, categoria, organica_id, economica_id, funcional_id'


sncp_orcamento_acumulados()