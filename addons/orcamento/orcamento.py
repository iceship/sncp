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

import pytz
from datetime import datetime, date
from openerp.osv import fields, osv
from openerp.tools.translate import _


# ____________________________________________________________FUNÇÕES COMUNS AO MODULO________________________
def get_sequence(self, cr, uid, context, text, value):
    seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_' + text + '_code_' + unicode(value))
    if seq is False:
        sequence_type = self.pool.get('ir.sequence.type')
        values_type = {
            'name': 'type_' + text + '_name_' + unicode(value),
            'code': 'seq_' + text + '_code_' + unicode(value)}
        sequence_type.create(cr, uid, values_type, context=context)
        sequence = self.pool.get('ir.sequence')
        values = {
            'name': 'seq_' + text + '_name_' + unicode(value),
            'code': 'seq_' + text + '_code_' + unicode(value),
            'number_next': 1,
            'number_increment': 1}
        sequence.create(cr, uid, values, context=context)
        seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_' + text + '_code_' + unicode(value))
    return seq


# ______________________________________________________ORCAMENTO______________________________
class sncp_orcamento(osv.Model):
    _name = 'sncp.orcamento'
    _description = u'Orçamento'

    def call_formulario(self, cr, uid, ids, context=None):
        return self.pool.get('formulario.sncp.orcamento.diario').wizard(cr, uid, ids)

    def copiar_linhas_orcamento(self, cr, uid, ids, context=None):
        return self.pool.get('formulario.sncp.orcamento.copia').wizard(cr, uid, ids)

    def copia(self, cr, uid, ids, vals, context=None):
        if vals['ad_val'] is True:
            cr.execute("""
            SELECT copia_linhas_orc_mod(%d,%d,'%s',%f,false,true)
            """ % (vals['orc_origem_id'], vals['orc_destino_id'], vals['titulo'], vals['fator']))
        elif vals['sub_val'] is True:
            cr.execute("""
            SELECT copia_linhas_orc_mod(%d,%d,'%s',%f,true,false)
            """ % (vals['orc_origem_id'], vals['orc_destino_id'], vals['titulo'], vals['fator']))

        return True

    def _ano_restrict(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.ano < date.today().year:
            raise osv.except_osv(_(u'Aviso'), _(u'Ano não pode ser inferior ao ano atual.'))
        return True

    def _mesmo_id_organica_economica_funcional(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        cr.execute("""
        SELECT linhas_orcamento_mm_dimensoes(%d,'%s')
        """ % (obj.id, obj.titulo))

        mensagem = cr.fetchone()[0]
        if len(mensagem) != 0:
            raise osv.except_osv(_(mensagem), _(u''))

        return True

    def _get_tipo(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return context.get('tipo_orc', 'orc')

    def _verifica_datas(self, cr, uid, ids, context=None):

        data = self.browse(cr, uid, ids[0])

        if data.tipo_orc in ['alt', 'rev']:
            if data.tipo_mod == 'alt':
                if data.aprova1 <= data.aprova2 != 0 and not data.aprova3:
                    return True
            else:
                if data.aprova1 <= data.aprova2 <= data.aprova3 != 0:
                    return True
        else:
            if data.aprova1 <= data.aprova2 <= data.aprova3 != 0:
                return True
        raise osv.except_osv(_(u'No caso de ser uma modificação e o tipo de modificação ser alteração'
                               u' a data do deliberativo não deve estar preenchida.'),
                             _(u'Além de que a data de aprovação do presidente deve ser inferior ou igual'
                               u' à data de aprovação do executivo e esta deve ser inferior ou igual'
                               u' à data de aprovação do deliberativo, caso a data do deliberativo exista.'
                               u' Caso contrário a data de aprovação do presidente deve ser inferior ou igual'
                               u' à data de aprovação do executivo.'))

    def verifica_contabilizado(self, cr, uid, ids, vals, context=None):
        orc = self.browse(cr, uid, ids[0])
        parametros = vals
        datahora = datetime.strptime(parametros['data'], "%Y-%m-%d")
        datahora = datahora.replace(second=1)

        datahora = datahora.replace(tzinfo=pytz.utc)

        cr.execute(""" SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=%d""" % orc.id)
        ha_linhas = cr.fetchall()
        if len(ha_linhas) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não há linhas para processar.'))

        if orc.tipo_mod in ['rev', 'alt']:
            cr.execute("""
            SELECT contabiliza_modificacao(%d,%d,%d,'%s','%s')
            """ % (orc.id, uid, parametros['diario_id'], unicode(datahora), parametros['ref']))
            mensagem = (cr.fetchone())[0]
            if len(mensagem) > 0:
                raise osv.except_osv(_(mensagem), _(u''))
        else:
            cr.execute("""
            SELECT contabiliza(%d,%d,%d,'%s','%s')
            """ % (orc.id, uid, parametros['diario_id'], unicode(datahora), parametros['ref']))

        return True

    def orcamento_proposed(self, cr, uid, ids, context=None):
        orcamento = self.browse(cr, uid, ids[0])
        linhas = []
        if orcamento.titulo == 'rece':
            cr.execute("""
            SELECT id
            FROM sncp_orcamento_linha
            WHERE orcamento_id = %d AND economica_id IS NULL
            """ % orcamento.id)

            linhas = cr.fetchall()

        elif orcamento.titulo == 'desp':
            cr.execute("""
            SELECT id
            FROM sncp_orcamento_linha
            WHERE orcamento_id = %d AND (economica_id IS NULL OR organica_id IS NULL)
            """ % orcamento.id)

            linhas = cr.fetchall()

        if len(linhas) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Linhas do orçamento mal configuradas.'))

        self.write(cr, uid, ids, {'state': 'proposed'})
        return True

    def orcamento_approved(self, cr, uid, ids, context=None):
        self._verifica_datas(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state': 'approved'})
        return True

    def orcamento_accounted(self, cr, uid, ids, vals):

        cr.execute("""
        SELECT type FROM account_account
        WHERE code='011'
        """)

        code011 = cr.fetchone()

        if code011 is not None:
            tipo = code011[0]
            if tipo == 'view':
                raise osv.except_osv(_(u'Aviso'), _(u'A conta com o código 011 '
                                                    u' deve ter tipo interno diferente de vista.'))

        cr.execute("""
        SELECT type FROM account_account
        WHERE code='031'
        """)

        code031 = cr.fetchone()

        if code031 is not None:
            tipo = code031[0]
            if tipo == 'view':
                raise osv.except_osv(_(u'Aviso'), _(u'A conta com o código 031 '
                                                    u' deve ter tipo interno diferente de vista.'))

        cr.execute("""
        SELECT type FROM account_account
        WHERE code='034'
        """)

        code034 = cr.fetchone()

        if code034 is not None:
            tipo = code034[0]
            if tipo == 'view':
                raise osv.except_osv(_(u'Aviso'), _(u'A conta com o código 034 '
                                                    u' deve ter tipo interno diferente de vista.'))

        cr.execute("""
        SELECT type FROM account_account
        WHERE code='021'
        """)

        code021 = cr.fetchone()

        if code021 is not None:
            tipo = code021[0]
            if tipo == 'view':
                raise osv.except_osv(_(u'Aviso'), _(u'A conta com o código 021 '
                                                    u' deve ter tipo interno diferente de vista.'))

        cr.execute("""
        SELECT type FROM account_account
        WHERE code='023'
        """)

        code023 = cr.fetchone()

        if code023 is not None:
            tipo = code023[0]
            if tipo == 'view':
                raise osv.except_osv(_(u'Aviso'), _(u'A conta com o código 023 '
                                                    u' deve ter tipo interno diferente de vista.'))
        cr.execute("""
        SELECT type FROM account_account
        WHERE code='03211'
        """)

        code03211 = cr.fetchone()

        if code03211 is not None:
            tipo = code03211[0]
            if tipo == 'view':
                raise osv.except_osv(_(u'Aviso'), _(u'A conta com o código 03211 '
                                                    u' deve ter tipo interno diferente de vista.'))

        cr.execute("""
        SELECT type FROM account_account
        WHERE code='0322'
        """)

        code0322 = cr.fetchone()

        if code0322 is not None:
            tipo = code0322[0]
            if tipo == 'view':
                raise osv.except_osv(_(u'Aviso'), _(u'A conta com o código 0322 '
                                                    u' deve ter tipo interno diferente de vista.'))
        cr.execute("""
        SELECT type FROM account_account
        WHERE code='02211'
        """)

        code02211 = cr.fetchone()

        if code02211 is not None:
            tipo = code02211[0]
            if tipo == 'view':
                raise osv.except_osv(_(u'Aviso'), _(u'A conta com o código 02211 '
                                                    u' deve ter tipo interno diferente de vista.'))

        cr.execute("""
        SELECT type FROM account_account
        WHERE code='02212'
        """)

        code02212 = cr.fetchone()

        if code02212 is not None:
            tipo = code02212[0]
            if tipo == 'view':
                raise osv.except_osv(_(u'Aviso'), _(u'A conta com o código 02212 '
                                                    u' deve ter tipo interno diferente de vista.'))

        if code011 is None or code031 is None or code034 is None or code021 is None or code023 is None \
                or code03211 is None or code0322 is None or code02211 is None or code02212 is None:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina as contas com os seguintes códigos:\n'
                                                u'1. 011 com tipo interno diferente de vista.\n'
                                                u'2. 031 com tipo interno diferente de vista.\n'
                                                u'3. 034 com tipo interno diferente de vista.\n'
                                                u'4. 021 com tipo interno diferente de vista.\n'
                                                u'5. 023 com tipo interno diferente de vista.\n'
                                                u'6. 03211 com tipo intereno diferente de vista.\n'
                                                u'7. 0322 com tipo interno diferente de vista.\n'
                                                u'8. 02211 com tipo interno diferente de vista.\n'
                                                u'9. 02212 com tipo interno diferente de vista.\n'))

        return self.verifica_contabilizado(cr, uid, vals['orcamento_id'], vals)

    def accounted_cancel(self, cr, uid, ids, context=None):
        return self.anula_contabilizado(cr, uid, ids)

    def anula_contabilizado(self, cr, uid, ids):
        orc = self.browse(cr, uid, ids[0])
        if orc.tipo_mod in ['rev', 'alt']:
            cr.execute("""SELECT anula_modificacao(%d)
                       """ % orc.id)
            mensagem = (cr.fetchone())[0]
            if len(mensagem) > 0:
                raise osv.except_osv(_(mensagem), _(u''))
        else:
            cr.execute("""
        SELECT anula_orcamento(%d)
        """ % orc.id)
            mensagem = (cr.fetchone())[0]
            if len(mensagem) > 0:
                raise osv.except_osv(_(mensagem), _(u''))

    def approved_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'proposed'})
        return True

    def orcamento_closed(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'closed'})
        return True

    def descricao(self, cr, uid, ids, ano, titulo):
        word = u''
        if titulo == 'rece':
            word = u'Receita'
        elif titulo == 'desp':
            word = u'Despesa'

        if ano is False and titulo is False:
            return {}
        elif ano is False and titulo:
            vals = {'name': u'Orçamento da ' + word}
        elif ano and titulo is False:
            vals = {'name': u'Orçamento para o ano ' + unicode(ano)}
        else:
            vals = {'name': u'Orçamento da ' + word + u' para o ano ' + unicode(ano)}

        if len(ids) != 0:
            self.write(cr, uid, ids, vals)

        return {'value': vals}

    def descricao_mod(self, cr, uid, ids, ano, titulo, tipo_mod, numero, alt_principal):
        word = u''
        word2 = u''
        if tipo_mod == 'rev':
            word = u'Revisão do orçamento'
        elif tipo_mod == 'alt':
            word = u'Alteração do orçamento'

        if titulo == 'rece':
            word2 = u'receita'
        elif titulo == 'desp':
            word2 = u'despesa'

        vals = {}

        if ano is False and titulo is False and tipo_mod:
            vals = {'name': word}
        elif ano is False and titulo and tipo_mod is False:
            vals = {'name': word2}
        elif ano is False and titulo and tipo_mod:
            vals = {'name': word + u' da ' + word2}
        elif ano and titulo is False and tipo_mod:
            vals = {'name': word + u' ' + u'para o ano ' + unicode(ano)}
        elif ano and titulo and tipo_mod is False:
            vals = {'name': word2 + u' ' + u'para o ano ' + unicode(ano)}
        elif ano and titulo and tipo_mod:
            vals = {'name': word + u' da ' + word2 + u' ' + u'para o ano ' + unicode(ano)}

        if tipo_mod == 'rev':
            vals = {'name': unicode(numero) + u'.ª ' + word + u' da ' + word2 + u' ' + u'para o ano ' + unicode(ano)}
        elif tipo_mod == 'alt':
            vals = {
                'name': unicode(alt_principal) + u'.ª ' + word + u' da ' + word2 + u' ' + u'para o ano ' + unicode(ano)}

        self.write(cr, uid, ids, vals)

        return {'value': vals}

    def prosseguir(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'preenche_linhas': 1})
        return True

    def cria_linha(self, cr, uid, ids, context=None):
        cr.execute("""SELECT titulo FROM sncp_orcamento WHERE id=%d""" % ids[0])
        titulo = cr.fetchone()[0]
        cr.execute("""INSERT INTO sncp_orcamento_linha(orcamento_id,titulo,reforco)
                      VALUES (%d,'%s',%f)""" % (ids[0], titulo, 0.01))
        self.write(cr, uid, ids, {'cab_readonly': 1})
        return True

    def imprimir_report_receita(self, cr, uid, ids, context=None):
        orc = self.browse(cr, uid, ids[0])
        cr.execute("""DELETE FROM sncp_orcamento_imprimir_receita """)
        cr.execute("""SELECT insere_orcamento_imprimir_receita(%d);""" % orc.id)
        cr.execute("""SELECT get_parents(AAA.code,%d)
                        FROM sncp_orcamento_linha AS OL
                        LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                        WHERE OL.orcamento_id = %d""" % (orc.id, orc.id))
        cr.execute("""SELECT atualiza_print_orcamento();""")
        cr.execute("""UPDATE sncp_orcamento_imprimir_receita SET linha='artigo' WHERE linha='';""")
        cr.execute("""SELECT insere_titulos(false,%d);""" % orc.id)

        datas = {'ids': ids, 'model': 'sncp.orcamento', }

        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.orcamento.receita.report',
            'datas': datas,
        }

    def imprimir_report_despesa(self, cr, uid, ids, context=None):
        orc = self.browse(cr, uid, ids[0])
        cr.execute("""DELETE FROM sncp_orcamento_imprimir_despesa""")
        cr.execute("""SELECT insere_orcamento_imprimir_despesa(%d);""" % orc.id)
        cr.execute("""
        SELECT get_parents_economica(AAA2.code,AAA.code,%d)
        FROM sncp_orcamento_linha AS OL
        LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
        LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
        WHERE OL.orcamento_id = %d
        """ % (orc.id, orc.id))

        cr.execute("""
        SELECT get_parents_organica(AAA2.code,%d)
        FROM sncp_orcamento_linha AS OL
        LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
        WHERE OL.orcamento_id=%d
        """ % (orc.id, orc.id))
        cr.execute("""        SELECT atualiza_print_orcamento_despesa();        """)
        cr.execute("""        SELECT check_cab_organica();        """)
        cr.execute("""UPDATE sncp_orcamento_imprimir_despesa SET linha='artigo' WHERE linha='';""")

        datas = {'ids': ids, 'model': 'sncp.orcamento', }

        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.orcamento.despesa.report',
            'datas': datas,
        }

    def teste_existencia_orcamento(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_linha_historico'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_linha_historico(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_linha_acumulados'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_linha_acumulados(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_companhia'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_companhia(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_periodo'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_periodo(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_movimento_contabilistico'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_movimento_contabilistico(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_dados_orcamento'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_dados_orcamento(cr)

        cr.execute(
            """SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_linha_movimento_contabilistico'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_linha_movimento_contabilistico(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'contabiliza'""")
        result = cr.fetchone()
        if result is None:
            self.sql_contabiliza(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'abate_possivel'""")
        result = cr.fetchone()
        if result is None:
            self.sql_abate_possivel(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'da_valor_acumulado'""")
        result = cr.fetchone()
        if result is None:
            self.sql_da_valor_acumulado(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'da_disponibilidade_orcamental'""")
        result = cr.fetchone()
        if result is None:
            self.sql_da_disponibilidade_orcamental(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'verifica_abate'""")
        result = cr.fetchone()
        if result is None:
            self.sql_verifica_abate(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_dados_alteracao_revisao'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_dados_alteracao_revisao(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'contabiliza_modificacao'""")
        result = cr.fetchone()
        if result is None:
            self.sql_contabiliza_modificacao(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'elimina_acumulados'""")
        result = cr.fetchone()
        if result is None:
            self.sql_elimina_acumulados(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'elimina_historico_orc_mod_cab'""")
        result = cr.fetchone()
        if result is None:
            self.sql_elimina_historico_orc_mod_cab(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_dados_orcamento_anular'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_dados_orcamento_anular(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'anula_orcamento'""")
        result = cr.fetchone()
        if result is None:
            self.sql_anula_orcamento(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'anula_modificacao'""")
        result = cr.fetchone()
        if result is None:
            self.sql_anula_modificacao(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fu_extenso_euro'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fu_extenso_euro(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fu_extenso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fu_extenso(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fu_extenso_blk'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fu_extenso_blk(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_dados_alteracao_revisao_anular'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_dados_alteracao_revisao_anular(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname='linhas_orcamento_mm_dimensoes'""")
        result = cr.fetchone()
        if result is None:
            self.sql_linhas_orcamento_mm_dimensoes(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname='da_previsao_atual'""")
        result = cr.fetchone()
        if result is None:
            self.sql_da_previsao_atual(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname='previsao_atual_possivel'""")
        result = cr.fetchone()
        if result is None:
            self.sql_previsao_atual_possivel(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname='copia_linhas_orc_mod'""")
        result = cr.fetchone()
        if result is None:
            self.sql_copia_linhas_orc_mod(cr)

        return True

    def teste_existencia_orcamento_receita(self, cr):
        # Bloco de teste de existencia das funções
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_orcamento_imprimir_receita'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_orcamento_imprimir_receita(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_parents'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_parents(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'atualiza_print_orcamento'""")
        result = cr.fetchone()
        if result is None:
            self.sql_atualiza_print_orcamento(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'calcula_montante_titulo'""")
        result = cr.fetchone()
        if result is None:
            self.sql_calcula_montante_titulo(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_titulos'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_titulos(cr)
        return True

    def teste_existencia_orcamento_despesa(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_orcamento_imprimir_despesa'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_orcamento_imprimir_despesa(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_parents_economica'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_parents_economica(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_parents_organica'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_parents_organica(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'atualiza_print_orcamento_despesa'""")
        result = cr.fetchone()
        if result is None:
            self.sql_atualiza_print_orcamento_despesa(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'check_cab_organica'""")
        result = cr.fetchone()
        if result is None:
            self.sql_check_cab_organica(cr)
        return True

    def teste_existencia_modificacao_receita(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_modificacao_imprimir_receita'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_modificacao_imprimir_receita(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'obtem_previsao_atual'""")
        result = cr.fetchone()
        if result is None:
            self.sql_obtem_previsao_atual(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'mod_get_parents'""")
        result = cr.fetchone()
        if result is None:
            self.sql_mod_get_parents(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'atualiza_print_modificacao'""")
        result = cr.fetchone()
        if result is None:
            self.sql_atualiza_print_modificacao(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'calcula_montante_titulo_mod'""")
        result = cr.fetchone()
        if result is None:
            self.sql_calcula_montante_titulo_mod(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_titulos_mod'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_titulos_mod(cr)

        return True

    def teste_existencia_modificacao_despesa(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_modificacao_imprimir_despesa'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_modificacao_imprimir_despesa(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'obtem_mod_desp_previsao_atual'""")
        result = cr.fetchone()
        if result is None:
            self.sql_obtem_mod_desp_previsao_atual(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_mod_desp_parents_economica'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_mod_desp_parents_economica(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_mod_desp_parents_organica'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_mod_desp_parents_organica(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'atualiza_print_modificacao_despesa'""")
        result = cr.fetchone()
        if result is None:
            self.sql_atualiza_print_modificacao_despesa(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'mod_desp_check_cab_organica'""")
        result = cr.fetchone()
        if result is None:
            self.sql_mod_desp_check_cab_organica(cr)

        return True

    def teste_existencia_historico_acumulados(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname='insere_historico_rodape'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_historico_rodape(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname='insere_acumulados_rodape'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_acumulados_rodape(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname='compara_strings'""")
        result = cr.fetchone()
        if result is None:
            self.sql_compara_strings(cr)

        return True

    _columns = {
        'name': fields.char(u'Descrição', size=64),
        'titulo': fields.selection([('rece', u'Receita'), ('desp', u'Despesa')], u'Título', ),
        'orc_linhas_id': fields.one2many('sncp.orcamento.linha', 'orcamento_id', string='Linhas'),
        'ano': fields.integer('Ano', size=4),
        'tipo_orc': fields.selection([
                                     ('orc', u'Orçamento'),
                                     ('rev', u'Revisão'),
                                     ('alt', u'Alteração')
                                     ], u'Tipo Orçamento'),
        'tipo_mod': fields.selection([('rev', u'Revisão'),
                                      ('alt', u'Alteração')], u'Tipo de Modificação'),
        'numero': fields.integer(u'Número'),
        'alt_principal': fields.integer(u'Alteração principal'),
        'contab': fields.boolean(u'Contabilizado'),
        'aprova1': fields.date('Pelo Presidente'),
        'aprova2': fields.date('Pelo Executivo'),
        'aprova3': fields.date('Pelo Deliberativo'),
        'doc_contab_id': fields.many2one('account.move', u'Documento de Contabilização'),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('proposed', u'Proposta'),
                                   ('approved', u'Aprovação'),
                                   ('accounted', u'Contabilizado'),
                                   ('closed', u'Fechado')], 'Status'),
        'preenche_linhas': fields.integer(u'linhas'),
        'cab_readonly': fields.integer(u''),
    }

    # ORÇAMENTO/MODIFICAÇÕES

    def sql_insere_linha_historico(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_linha_historico(ano integer,categoria varchar,datahora timestamp,
                                                        organica_id integer,economica_id integer,funcional_id integer,
        montante numeric,move_id integer,linha_move_id integer,centrocustos_id integer,cabimento_id integer,
        cabimento_linha_id integer,compromisso_id integer,compromisso_linha_id integer) RETURNS TIMESTAMP AS
        $$
        BEGIN
        INSERT INTO sncp_orcamento_historico(name,categoria,datahora,organica_id,economica_id,funcional_id,montante,
        doc_contab_id,doc_contab_linha_id,centrocustos_id,cabimento_id,cabimento_linha_id,compromisso_id,
        compromisso_linha_id)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14);
        RETURN $3;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_linha_acumulados(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_linha_acumulados(ano integer,categoria varchar,organica_id integer,
        economica_id integer,funcional_id integer,montante numeric) RETURNS boolean AS
        $$
        DECLARE
            linha_acumulados sncp_orcamento_acumulados%ROWTYPE;
            encontrado boolean=FALSE;
        BEGIN
        FOR linha_acumulados IN SELECT * FROM sncp_orcamento_acumulados AS SOA
            WHERE SOA.name = $1 AND SOA.categoria = $2 AND SOA.economica_id = $4 AND
        (
         (($3 IS NULL AND $5 IS NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id IS NULL)) OR
         (($3 IS NULL AND $5 IS NOT NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id = $5)) OR
         (($3 IS NOT NULL AND $5 IS NULL) AND (SOA.organica_id =$3 AND SOA.funcional_id IS NULL)) OR
         (($3 IS NOT NULL AND $5 IS NOT NULL) AND (SOA.organica_id = $3 and SOA.funcional_id = $5))
        ) LOOP
        encontrado=TRUE;
        UPDATE sncp_orcamento_acumulados SET montante = linha_acumulados.montante+$6 WHERE id = linha_acumulados.id;
        END LOOP;

        IF encontrado=FALSE THEN
           INSERT INTO sncp_orcamento_acumulados(name,categoria,organica_id,economica_id,funcional_id,montante)
        VALUES ($1,$2,$3,$4,$5,$6);
        END IF;
        RETURN TRUE;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_get_companhia(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION get_companhia(user_id integer) RETURNS integer AS
        $$
        BEGIN
        RETURN (SELECT company_id FROM res_users WHERE id=$1);
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_get_periodo(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION get_periodo(date) RETURNS integer AS
        $$
        BEGIN
        RETURN (SELECT id FROM account_period WHERE $1 BETWEEN date_start AND date_stop);
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_movimento_contabilistico(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_movimento_contabilistico(user_id integer,journal_id integer,date,
                                    ref varchar,ano integer) RETURNS integer AS $$
        DECLARE
         periodo_id integer;
         companhia_id integer;
         nome varchar;
        BEGIN
        periodo_id=get_periodo($3);
        companhia_id=get_companhia($1);
        nome=$4 || ' ' || $5;
        INSERT INTO account_move(name,ref,period_id,journal_id,state,date,company_id)
        VALUES (nome,ref,periodo_id,$2,'draft',$3,companhia_id);
        RETURN (SELECT currval('account_move_id_seq'));
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_get_dados_orcamento(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION get_dados_orcamento(orc_id integer,out ano integer,out categoria varchar,
        out deb1 integer,out cred1 integer,out deb2 integer,out cred2 integer) AS $$
        DECLARE
         orcamento sncp_orcamento%ROWTYPE;
        BEGIN
        SELECT * INTO orcamento FROM sncp_orcamento WHERE id=$1;
        ano=orcamento.ano;
        IF orcamento.titulo='rece' THEN
                categoria='51rdota';
                deb1=(SELECT id FROM account_account WHERE code='011');
                cred1=(SELECT id FROM account_account WHERE code='031');
                deb2=cred1;
                cred2=(SELECT id FROM account_account WHERE code='034');
        ELSIF orcamento.titulo='desp' THEN
                categoria='01ddota';
                deb1=(SELECT id FROM account_account WHERE code='011');
                cred1=(SELECT id FROM account_account WHERE code='021');
                deb2=cred1;
                cred2=(SELECT id FROM account_account WHERE code='023');
        ELSE
                categoria='';
                deb1=0;
                cred1=0;
                deb2=0;
                cred2=0;
        END IF;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_linha_movimento_contabilistico(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_linha_movimento_contabilistico(conta_id integer,journal_id integer,date,
        ref varchar,move_id integer,valor numeric,organica_id integer,economica_id integer,funcional_id integer,
        deb_creb varchar) RETURNS integer AS $$
        DECLARE
            periodo_id integer;
        BEGIN
        periodo_id = get_periodo($3);
        IF $10='credit' THEN
            INSERT INTO account_move_line(account_id,date,journal_id,period_id,name,move_id,credit,organica_id,
            economica_id,funcional_id) VALUES($1,$3,$2,periodo_id,$4,$5,$6,$7,$8,$9);
            RETURN (SELECT currval('account_move_line_id_seq'));
        ELSE
            INSERT INTO account_move_line(account_id,date,journal_id,period_id,name,move_id,debit,organica_id,
            economica_id,funcional_id) VALUES($1,$3,$2,periodo_id,$4,$5,$6,$7,$8,$9);
            RETURN (SELECT currval('account_move_line_id_seq'));
        END IF;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_contabiliza(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION contabiliza(orc_id integer,user_id integer,journal_id integer,varchar,ref varchar)
        RETURNS boolean AS
        $$
        DECLARE
            ok boolean;
            datahora timestamp;
            move_line_id integer;
            move_id integer;
            dados RECORD;
            linha_orcamento sncp_orcamento_linha%ROWTYPE;
            novadatahora timestamp;
        BEGIN
             dados=get_dados_orcamento($1);
             move_id=insere_movimento_contabilistico($2,$3,$4::date,$5,dados.ano);
             UPDATE sncp_orcamento SET doc_contab_id = move_id WHERE id = $1;
             FOR linha_orcamento in SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=$1 LOOP

             move_line_id=insere_linha_movimento_contabilistico(dados.deb1,$3,$4::date,$5,move_id,
             linha_orcamento.reforco,linha_orcamento.organica_id,linha_orcamento.economica_id,
             linha_orcamento.funcional_id,'debit');

                 move_line_id=insere_linha_movimento_contabilistico(dados.cred1,$3,$4::date,$5,
                 move_id,linha_orcamento.reforco,linha_orcamento.organica_id,linha_orcamento.economica_id,
                 linha_orcamento.funcional_id,'credit');

                 move_line_id=insere_linha_movimento_contabilistico(dados.deb2,$3,$4::date,$5,move_id,
                 linha_orcamento.reforco,linha_orcamento.organica_id,linha_orcamento.economica_id,
                 linha_orcamento.funcional_id,'debit');

                 move_line_id=insere_linha_movimento_contabilistico(dados.cred2,$3,$4::date,$5,move_id,
                 linha_orcamento.reforco,linha_orcamento.organica_id,linha_orcamento.economica_id,
                 linha_orcamento.funcional_id,'credit');

                 novadatahora=insere_linha_historico(dados.ano,dados.categoria,$4::timestamp,
                 linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,
                 linha_orcamento.reforco,move_id,move_line_id,NULL,NULL,NULL,NULL,NULL);

                 ok=insere_linha_acumulados(dados.ano,dados.categoria,linha_orcamento.organica_id,
                 linha_orcamento.economica_id,linha_orcamento.funcional_id,linha_orcamento.reforco);
             END LOOP;
             UPDATE sncp_orcamento SET state = 'accounted',contab=TRUE WHERE id = $1;
        RETURN ok;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_abate_possivel(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION abate_possivel(integer) RETURNS varchar AS $$
        DECLARE
            lin sncp_orcamento_linha%ROWTYPE;
            mensagem varchar='';
            ano integer;
        BEGIN
            ano=(SELECT SO.ano FROM sncp_orcamento AS SO WHERE id=$1);
            FOR lin in SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=$1 LOOP
                  IF lin.anulacao>0 THEN
                IF verifica_abate(ano,lin.organica_id,lin.economica_id,lin.funcional_id,lin.anulacao)=FALSE THEN
                   mensagem='Para a combinação ' || '[' || COALESCE((SELECT CONCAT(code,' ',name)
                   FROM account_analytic_account WHERE id=lin.organica_id),'') || '/ '
                   || COALESCE((SELECT CONCAT(code,' ',name) FROM account_analytic_account
                    WHERE id=lin.economica_id),'') || '/ '
                   || COALESCE((SELECT CONCAT(code,' ',name) FROM account_analytic_account
                    WHERE id=lin.funcional_id),'') || ']'
                   || ' o abate de ' || lin.anulacao ||' não é possível';
                   RETURN mensagem;
                        END IF;
                      END IF;
           END LOOP;
           RETURN mensagem;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_da_previsao_atual(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION da_previsao_atual(economica_id integer,ano integer) RETURNS numeric AS
        $$
        DECLARE
         temp_val numeric;
         abate_val numeric;
         liq_val numeric;
       BEGIN
         temp_val=COALESCE((SELECT SUM(SOA.montante) FROM sncp_orcamento_acumulados AS SOA
         WHERE SOA.economica_id=$1 AND SOA.name=$2 AND SOA.categoria IN ('51rdota','52rrefo')),0.0);
         abate_val=COALESCE((SELECT SUM(SOA.montante) FROM sncp_orcamento_acumulados AS SOA
         WHERE SOA.economica_id=$1 AND SOA.name=$2 AND SOA.categoria='53rabat'),0.0);
         liq_val=COALESCE((SELECT SUM(SOA.montante) FROM sncp_orcamento_acumulados AS SOA
         WHERE SOA.name=$2 AND SOA.categoria='57rliq'),0.0);
         RETURN temp_val-abate_val-liq_val;
       END
       $$LANGUAGE plpgsql;
        """)
        return True

    def sql_previsao_atual_possivel(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION previsao_atual_possivel(orcamento_id integer,ano integer) RETURNS varchar AS $$
        DECLARE
            linha RECORD;
            mensagem varchar='';
            valor numeric;
        BEGIN
        FOR linha IN (SELECT * FROM sncp_orcamento_linha AS OL WHERE OL.orcamento_id=$1) LOOP
            valor=da_previsao_atual(linha.economica_id,$2);
            IF linha.anulacao>0 AND linha.anulacao>valor THEN
                mensagem='O abate não pode ser superior a '|| to_char(linha.anulacao,'999G999G999G9990D00');
                RETURN mensagem;
            END IF;
        END LOOP;
        RETURN mensagem;
        END
        $$LANGUAGE plpgsql;
        """)
        return True

    def sql_da_valor_acumulado(self, cr):
        cr.execute("""
        CREATE or REPLACE FUNCTION da_valor_acumulado(ano integer,categoria varchar,organica_id integer,
        economica_id integer,funcional_id integer) RETURNS NUMERIC AS $$
        BEGIN

        RETURN (SELECT COALESCE(SUM(montante), 0.0)
        FROM sncp_orcamento_acumulados AS SOA
        WHERE SOA.name = $1 AND
         SOA.categoria = $2 AND
         SOA.economica_id = $4 AND
        (
         (($3 IS NULL AND $5 IS NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id IS NULL)) OR
         (($3 IS NULL AND $5 IS NOT NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id = $5)) OR
         (($3 IS NOT NULL AND $5 IS NULL) AND (SOA.organica_id =$3 AND SOA.funcional_id IS NULL)) OR
         (($3 IS NOT NULL AND $5 IS NOT NULL) AND (SOA.organica_id = $3 and SOA.funcional_id = $5))
        ));
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_da_disponibilidade_orcamental(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION da_disponibilidade_orcamental(ano integer,organica_id integer,economica_id integer,
        funcional_id integer) RETURNS NUMERIC AS $$
        DECLARE
            somadotacao numeric;
                somareforcos numeric;
                somaabates numeric;
                somacabimentos numeric;
        BEGIN
            somadotacao=da_valor_acumulado($1,'01ddota',$2,$3,$4);
            somareforcos=da_valor_acumulado($1,'02drefo',$2,$3,$4);
            somaabates=da_valor_acumulado($1,'03dabat',$2,$3,$4);
            somacabimentos=da_valor_acumulado($1,'04cabim',$2,$3,$4);
            RETURN somadotacao+somareforcos-somaabates-somacabimentos;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_verifica_abate(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION verifica_abate(ano integer,organica_id integer,economica_id integer,
        funcional_id integer,anulacao numeric) RETURNS BOOLEAN AS
        $$
        DECLARE
         disporc numeric;
        BEGIN
            disporc=da_disponibilidade_orcamental($1,$2,$3,$4);
            IF disporc < $5 THEN
            RETURN FALSE;
            ELSE
            RETURN TRUE;
            END IF;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_get_dados_alteracao_revisao(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION get_dados_alteracao_revisao(orc_id integer,out ano integer,out tipo_mod varchar,
        out titulo varchar) AS $$
        DECLARE
         modificacao sncp_orcamento%ROWTYPE;
        BEGIN
        SELECT * INTO modificacao FROM sncp_orcamento WHERE id=$1;
        ano=modificacao.ano;
        tipo_mod=modificacao.tipo_mod;
        titulo=modificacao.titulo;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_contabiliza_modificacao(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION contabiliza_modificacao(orc_id integer,user_id integer,journal_id integer,varchar,
        ref varchar) RETURNS varchar AS
        $$
        DECLARE
            ok boolean;
            datahora timestamp;
            move_line_id integer;
            move_id integer;
            dados RECORD;
            deb1 integer;
            cred1 integer;
            deb2 integer;
            cred2 integer;
            categoria varchar;
            mensagem varchar;
            linha_orcamento sncp_orcamento_linha%ROWTYPE;
                novadatahora timestamp;
        BEGIN
             dados=get_dados_alteracao_revisao($1);
             IF dados.titulo='desp' THEN
                mensagem=abate_possivel($1);
                IF LENGTH(mensagem)>0 THEN
                    RETURN mensagem;
                END IF;
             END IF;
             IF dados.titulo='rece' THEN
                mensagem=previsao_atual_possivel($1,dados.ano);
                IF LENGTH(mensagem)>0 THEN
                    RETURN mensagem;
                END IF;
             END IF;
             move_id=insere_movimento_contabilistico($2,$3,$4::date,$5,dados.ano);
             UPDATE sncp_orcamento SET doc_contab_id = move_id WHERE id = $1;
             FOR linha_orcamento in SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=$1 LOOP
             IF linha_orcamento.reforco>0.0 THEN
                IF dados.titulo='rece' THEN
                    deb1=(SELECT id FROM account_account WHERE code='03211');
                    cred1=(SELECT id FROM account_account WHERE code='031');
                    deb2=(SELECT id FROM account_account WHERE code='034');
                    cred2=deb1;
                    categoria='52rrefo';
                    ELSE
                    deb1=(SELECT id FROM account_account WHERE code='011');
                    cred1=(SELECT id FROM account_account WHERE code='02211');
                    deb2=cred1;
                    cred2=(SELECT id FROM account_account WHERE code='023');
                    categoria='02drefo';
                END IF;
            ELSE
                IF dados.titulo='rece' THEN
                    deb1=(SELECT id FROM account_account WHERE code='031');
                    cred1=(SELECT id FROM account_account WHERE code='0322');
                    deb2=cred1;
                    cred2=(SELECT id FROM account_account WHERE code='034');
                    categoria='53rabat';
                    ELSE
                    deb1=(SELECT id FROM account_account WHERE code='02212');
                    cred1=(SELECT id FROM account_account WHERE code='011');
                    deb2=(SELECT id FROM account_account WHERE code='023');
                    cred2=deb1;
                    categoria='03dabat';
                END IF;
            END IF;

             move_line_id=insere_linha_movimento_contabilistico(deb1,$3,$4::date,$5,move_id,
             COALESCE(linha_orcamento.reforco,0.0)
                 +COALESCE(linha_orcamento.anulacao,0.0),
             linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,'debit');

                 move_line_id=insere_linha_movimento_contabilistico(cred1,$3,$4::date,$5,
                 move_id,COALESCE(linha_orcamento.reforco,0.0)
                 +COALESCE(linha_orcamento.anulacao,0.0),linha_orcamento.organica_id,linha_orcamento.economica_id,
                 linha_orcamento.funcional_id,'credit');

                 move_line_id=insere_linha_movimento_contabilistico(deb2,$3,$4::date,$5,move_id,
                 COALESCE(linha_orcamento.reforco,0.0)
                 +COALESCE(linha_orcamento.anulacao,0.0),
                 linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,'debit');

                 move_line_id=insere_linha_movimento_contabilistico(cred2,$3,$4::date,$5,move_id,
                 COALESCE(linha_orcamento.reforco,0.0)
                 +COALESCE(linha_orcamento.anulacao,0.0),
                 linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,'credit');

                 novadatahora=insere_linha_historico(dados.ano,categoria,$4::timestamp,
                 linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,
                 COALESCE(linha_orcamento.reforco,0.0)
                 +COALESCE(linha_orcamento.anulacao,0.0),move_id,move_line_id,NULL,NULL,NULL,NULL,NULL);

                 ok=insere_linha_acumulados(dados.ano,categoria,linha_orcamento.organica_id,
                 linha_orcamento.economica_id,linha_orcamento.funcional_id,COALESCE(linha_orcamento.reforco,0.0)
                 +COALESCE(linha_orcamento.anulacao,0.0));
             END LOOP;
             UPDATE sncp_orcamento SET state = 'accounted',contab=TRUE WHERE id = $1;
        RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_elimina_acumulados(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION elimina_acumulados(name integer,categoria varchar,organica_id integer,
        economica_id integer,funcional_id integer,montante numeric) RETURNS boolean AS $$
        DECLARE
            lin sncp_orcamento_acumulados%ROWTYPE;
        BEGIN
             FOR lin in SELECT * FROM sncp_orcamento_acumulados AS SOA
             WHERE SOA.name = $1 AND SOA.categoria = $2 AND SOA.economica_id = $4
             AND
        (
         (($3 IS NULL AND $5 IS NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id IS NULL)) OR
         (($3 IS NULL AND $5 IS NOT NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id = $5)) OR
         (($3 IS NOT NULL AND $5 IS NULL) AND (SOA.organica_id =$3 AND SOA.funcional_id IS NULL)) OR
         (($3 IS NOT NULL AND $5 IS NOT NULL) AND (SOA.organica_id = $3 and SOA.funcional_id = $5))
        ) LOOP
            UPDATE sncp_orcamento_acumulados SET montante=lin.montante-$6 WHERE id=lin.id;
        END LOOP;
        RETURN TRUE;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_elimina_historico_orc_mod_cab(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION elimina_historico_orc_mod_cab(name integer,categoria varchar,move_id integer)
        RETURNS boolean AS $$
        DECLARE
            lin sncp_orcamento_historico%ROWTYPE;
            ok boolean;
        BEGIN
             FOR lin in SELECT * FROM sncp_orcamento_historico AS SOH
             WHERE SOH.name = $1 AND SOH.categoria = $2 AND SOH.doc_contab_id=$3
             LOOP
             ok=elimina_acumulados(lin.name,lin.categoria,lin.organica_id,lin.economica_id,lin.funcional_id,
                lin.montante);
             DELETE FROM sncp_orcamento_historico WHERE id=lin.id;
             END LOOP;
        RETURN TRUE;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_get_dados_orcamento_anular(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION get_dados_orcamento_anular(orc_id integer,out ano integer,out categoria varchar,
            out move_id integer) AS $$
        DECLARE
         orcamento sncp_orcamento%ROWTYPE;
        BEGIN
        SELECT * INTO orcamento FROM sncp_orcamento WHERE id=$1;
        ano=orcamento.ano;
        move_id=orcamento.doc_contab_id;
        IF orcamento.titulo='rece' THEN
                categoria='51rdota';
        ELSIF orcamento.titulo='desp' THEN
                categoria='01ddota';
        ELSE
                categoria='';
        END IF;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_anula_orcamento(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION anula_orcamento(orc_id integer) RETURNS varchar AS
        $$
        DECLARE
            mensagem varchar='';
            lin_historico sncp_orcamento_historico%ROWTYPE;
            dados RECORD;
            ok boolean;
        BEGIN
             dados=get_dados_orcamento_anular($1);
             FOR lin_historico IN SELECT * FROM sncp_orcamento_historico AS SOH
             WHERE SOH.categoria='04cabim' AND SOH.name=dados.ano
             LOOP
            mensagem='Não é possível anular pois existe cabimento para o ano ' || dados.ano;
             END LOOP;
             IF LENGTH(mensagem)<>0 THEN
            RETURN mensagem;
             END IF;
             ok=elimina_historico_orc_mod_cab(dados.ano,dados.categoria,dados.move_id);
             DELETE FROM account_move_line WHERE move_id=dados.move_id;
             DELETE FROM account_move WHERE id=dados.move_id;
             UPDATE sncp_orcamento SET state = 'approved',contab=FALSE,doc_contab_id=NULL WHERE id = $1;
        RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_anula_modificacao(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION anula_modificacao(orc_id integer) RETURNS varchar AS
        $$
        DECLARE
            mensagem varchar='';
            lin_orcamento sncp_orcamento_linha%ROWTYPE;
            dados RECORD;
            ano integer;
            ok boolean;
            categoria varchar;
        BEGIN
             dados=get_dados_alteracao_revisao_anular($1);
             FOR lin_orcamento IN SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=$1
             LOOP
            IF lin_orcamento.reforco>0.0 THEN
                IF dados.titulo='rece' THEN
                   categoria='52rrefo';
                ELSE
                categoria='02drefo';
                END IF;
            IF dados.titulo='desp' THEN
                IF lin_orcamento.reforco>da_disponibilidade_orcamental(dados.ano,lin_orcamento.organica_id,
                lin_orcamento.economica_id,lin_orcamento.funcional_id) THEN
                mensagem='Não existe valor suficiente para cobrir os cabimentos';
                END IF;
                IF LENGTH(mensagem)<>0 THEN
                   RETURN mensagem;
                END IF;
            END IF;
            ELSE
                IF dados.titulo='rece' THEN
                  categoria='53rabat';
                ELSE
                  categoria='03dabat';
                END IF;
            END IF;
             ok=elimina_historico_orc_mod_cab(dados.ano,categoria,dados.move_id);
             END LOOP;
             DELETE FROM account_move_line WHERE move_id=dados.move_id;
             DELETE FROM account_move WHERE id=dados.move_id;
             UPDATE sncp_orcamento SET state = 'approved',contab=FALSE,doc_contab_id=NULL WHERE id = $1;
        RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_fu_extenso_euro(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION fu_extenso_euro(num numeric(20,2)) returns text as $$
        DECLARE
           val_extenso text;
           resultado text;
        BEGIN
          val_extenso=fu_extenso($1,'euro','euros');
          resultado=upper(substring( val_extenso from 1 for 1)) || lower(substring( val_extenso from 2 ));
          return resultado;
        END;
        $$ LANGUAGE plpgsql
           IMMUTABLE
           RETURNS NULL ON NULL INPUT ;
        """)
        return True

    def sql_fu_extenso(self, cr):
        cr.execute("""
        CREATE or replace FUNCTION fu_extenso(num numeric(20,2) , moeda text , moedas text) returns text as $$
        declare
        w_int char(21) ;
        x integer ;
        v integer ;
        w_ret text ;
        w_ext text ;
        w_apoio text ;
        m_cen text[] := array['quatrilião','quatriliões','trilião','triliões','bilião','biliões','milhão','milhões',
        'mil','mil'] ;
        begin
          w_ret := '' ;
          w_int := to_char(num * 100 , 'fm000000000000000000 00') ;
          for x in 1..5 loop
              v := cast(substr(w_int,(x-1)*3 + 1,3) as integer) ;
              if v > 0 then
                 if v > 1 then
                    w_ext := m_cen[(x-1)*2+2] ;
                   else
                    w_ext := m_cen[(x-1)*2+1] ;
                 end if ;
                 w_ret := w_ret || fu_extenso_blk(substr(w_int,(x-1)*3 + 1,3)) || ' ' || w_ext ||' ' ;
              end if ;
          end loop ;
          v := cast(substr(w_int,16,3) as integer) ;
          if v > 0 then
             if v > 1 then
                w_ext := moedas ;
               else
                if w_ret = '' then
                   w_ext := moeda ;
                  else
                   w_ext := moedas ;
                end if ;
             end if ;
             w_apoio := fu_extenso_blk(substr(w_int,16,3)) || ' ' || w_ext ;
             if w_ret = '' then
                w_ret := w_apoio ;
               else
                if v > 100 then
                   if w_ret = '' then
                      w_ret := w_apoio ;
                     else
                      w_ret := w_ret || w_apoio ;
                   end if ;
                  else
                   w_ret := btrim(w_ret,', ') || ' e ' || w_apoio ;
                end if ;
             end if ;
            else
             if w_ret <> '' then
                if substr(w_int,13,6) = '000000' then
                   w_ret := btrim(w_ret,', ') || ' de ' || moedas ;
                  else
                   w_ret := btrim(w_ret,', ') || ' ' || moedas ;
                end if ;
             end if ;
          end if ;
          v := cast(substr(w_int,20,2) as integer) ;
          if v > 0 then
             if v > 1 then
                w_ext := 'cêntimos' ;
               else
                w_ext := 'cêntimo' ;
             end if ;
             w_apoio := fu_extenso_blk('0'||substr(w_int,20,2)) || ' ' || w_ext ;
             if w_ret = '' then
                w_ret := w_apoio  || ' de ' || moeda;
               else
                w_ret := w_ret || ' e ' || w_apoio ;
             end if ;
          end if ;
          return w_ret ;
        end ;
        $$ LANGUAGE plpgsql
           IMMUTABLE
           RETURNS NULL ON NULL INPUT ;
        """)
        return True

    def sql_fu_extenso_blk(self, cr):
        cr.execute("""
        CREATE or replace FUNCTION fu_extenso_blk(num char(3)) returns text as $$
        declare
        w_cen integer ;
        w_dez integer ;
        w_dez2 integer ;
        w_uni integer ;
        w_tcen text ;
        w_tdez text ;
        w_tuni text ;
        w_ext text ;
        m_cen text[] := array['','cento','duzentos','trezentos','quatrocentos','quinhentos','seiscentos','setecentos',
        'oitocentos','novecentos'];
        m_dez text[] :=array['','dez','vinte','trinta','quarenta','cinquenta','sessenta','setenta','oitenta','noventa'];
        m_uni text[] := array['','um','dois','três','quatro','cinco','seis','sete','oito','nove','dez','onze','doze',
        'treze','catorze','quinze','dezasseis','dezassete','dezoito','dezanove'] ;
        begin
          w_cen := cast(substr(num,1,1) as integer) ;
          w_dez := cast(substr(num,2,1) as integer) ;
          w_dez2 := cast(substr(num,2,2) as integer) ;
          w_uni := cast(substr(num,3,1) as integer) ;
          if w_cen = 1 and w_dez2 = 0 then
             w_tcen := 'Cem' ;
             w_tdez := '' ;
             w_tuni := '' ;
            else
             if w_dez2 < 20 then
                w_tcen := m_cen[w_cen + 1] ;
                w_tdez := m_uni[w_dez2 + 1] ;
                w_tuni := '' ;
               else
                w_tcen := m_cen[w_cen + 1] ;
                w_tdez := m_dez[w_dez + 1] ;
                w_tuni := m_uni[w_uni + 1] ;
             end if ;
          end if ;
          w_ext := w_tcen ;
          if w_tdez <> '' then
             if w_ext = '' then
                w_ext := w_tdez ;
               else
                w_ext := w_ext || ' e ' || w_tdez ;
             end if ;
          end if ;
          if w_tuni <> '' then
             if w_ext = '' then
                w_ext := w_tuni ;
               else
                w_ext := w_ext || ' e ' || w_tuni ;
             end if ;
          end if ;
          return w_ext ;
        end ;
        $$ LANGUAGE plpgsql
           IMMUTABLE
           RETURNS NULL ON NULL INPUT ;
        """)
        return True

    def sql_get_dados_alteracao_revisao_anular(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION get_dados_alteracao_revisao_anular(orc_id integer,out titulo varchar,out ano integer,
        out move_id integer) AS $$
        DECLARE
         orcamento sncp_orcamento%ROWTYPE;
        BEGIN
        SELECT * INTO orcamento FROM sncp_orcamento WHERE id=$1;
        ano=orcamento.ano;
        titulo=orcamento.titulo;
        move_id=orcamento.doc_contab_id;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_linhas_orcamento_mm_dimensoes(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION linhas_orcamento_mm_dimensoes(orcamento_id integer,tipo varchar)
        RETURNS varchar AS $$
        DECLARE
          linha_orc RECORD;
          mensagem varchar='';
          num_linhas integer;
        BEGIN
            FOR linha_orc IN (SELECT * FROM sncp_orcamento_linha AS SOL WHERE SOL.orcamento_id=$1) LOOP
            IF $2='rece' THEN
                num_linhas=(SELECT COUNT(id)
                    FROM sncp_orcamento_linha AS OL
                    WHERE OL.orcamento_id=$1 AND OL.economica_id=linha_orc.economica_id
                    );
            ELSIF $2='desp' THEN
                  num_linhas=(SELECT COUNT(id)
                      FROM sncp_orcamento_linha AS OL
                      WHERE OL.orcamento_id=$1 AND OL.economica_id=linha_orc.economica_id AND
                        OL.organica_id=linha_orc.organica_id
                      AND ( (OL.funcional_id IS NULL AND linha_orc.funcional_id IS NULL) OR
                                (OL.funcional_id IS NOT NULL AND OL.funcional_id=linha_orc.funcional_id))
                        );
            END IF;

            IF num_linhas > 1 THEN
               IF $2='rece' THEN
                mensagem='A combinação  Orgânica()/Económica(' ||
                     (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_orc.economica_id)
                     || ')/Funcional() encontra-se repetida';
               ELSIF $2='desp' THEN
                mensagem='A combinação  Orgânica('
                         || (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_orc.organica_id) ||
                         ')/Económica(' ||
                     (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_orc.economica_id);
                IF linha_orc.funcional_id IS NULL THEN
                   mensagem= mensagem || ')/Funcional() encontra-se repetida';
                ELSE
                   mensagem=mensagem || ')/Funcional(' ||
                   (SELECT AAA.code FROM account_analytic_account AS AAA
                   WHERE id= linha_orc.funcional_id) ||') encontra-se repetida';
                END IF;

              END IF;
            RETURN mensagem;
            END IF;
            END LOOP;
        RETURN mensagem;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_copia_linhas_orc_mod(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION copia_linhas_orc_mod(origem_id integer,destino_id integer,titulo varchar,
        fator numeric,sub boolean,adi boolean)
        RETURNS BOOLEAN AS $$
        DECLARE
            dados RECORD;
            valor numeric;
        BEGIN
        FOR dados IN (SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=$1) LOOP
            IF COALESCE((SELECT id
                     FROM sncp_orcamento_linha AS SOL
                         WHERE SOL.orcamento_id=$2 AND SOL.economica_id=dados.economica_id
             AND ((SOL.funcional_id IS NULL AND dados.funcional_id IS NULL)
                  OR
                     (SOL.funcional_id IS NOT NULL AND SOL.funcional_id=dados.funcional_id))
                 AND ((SOL.organica_id IS NULL AND dados.organica_id IS NULL) OR
                  (SOL.organica_id IS NOT NULL AND SOL.organica_id=dados.organica_id))
            ),0)=0 THEN
                IF dados.reforco>0.0 THEN
                   IF $5=TRUE THEN
                      valor=ROUND($4*dados.reforco,2);
                   ELSIF $6=TRUE THEN
                      valor=ROUND(($4*dados.reforco)+dados.reforco,2);
                   END IF;

                   INSERT INTO sncp_orcamento_linha(orcamento_id,organica_id,economica_id,funcional_id,reforco,titulo)
                   VALUES($2,dados.organica_id,dados.economica_id,dados.funcional_id,valor,$3);

                ELSIF dados.anulacao>0.0 THEN
                    IF $5=TRUE THEN
                          valor=ROUND($4*dados.anulacao,2);
                    ELSIF $6=TRUE THEN
                          valor=ROUND(($4*dados.anulacao)+dados.anulacao,2);
                    END IF;

                   INSERT INTO sncp_orcamento_linha(orcamento_id,organica_id,economica_id,funcional_id,anulacao,titulo)
                   VALUES($2,dados.organica_id,dados.economica_id,dados.funcional_id,valor,$3);

                END IF;
            END IF;
        END LOOP;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    # ____AQUI RECEITA

    def sql_insere_orcamento_imprimir_receita(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_orcamento_imprimir_receita(orcamento_id integer) RETURNS BOOLEAN AS $$
        DECLARE
            dados RECORD;
        BEGIN
        FOR dados in (SELECT COALESCE(AAA.code,'') AS cd,COALESCE(AAA.name,'') AS nm,
            COALESCE(OL.reforco,0.0) AS montante,CAST('artigo' AS varchar) AS linha
                  FROM sncp_orcamento_linha AS OL
                      LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                  WHERE OL.orcamento_id=$1) LOOP
                        INSERT INTO sncp_orcamento_imprimir_receita(codigo,name,linha,montante,orcamento_id)
                        VALUES (dados.cd,dados.nm,dados.linha,dados.montante,$1);
        END LOOP;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_get_parents(self, cr):
        cr.execute("""
        CREATE OR REPLACE function get_parents(codigo varchar,orcamento_id integer) RETURNS boolean AS $$
        DECLARE
        ok boolean=TRUE;
        codigo_atual varchar;
        parent_atual integer;
        linha varchar;
        dados RECORD;
        BEGIN
        FOR dados IN (SELECT AAA.code,AAA.name,AAA.parent_id FROM account_analytic_account AS AAA WHERE code=$1
            LIMIT 1) LOOP

        parent_atual=dados.parent_id;
        IF parent_atual IS NULL
        THEN ok=false;
        END IF;
        END LOOP;
        WHILE (ok=true) LOOP
        FOR dados IN (SELECT code,name,parent_id FROM account_analytic_account WHERE id=parent_atual) LOOP

           codigo_atual=TRIM(dados.code);
           IF LOWER(SUBSTRING(codigo_atual from 1 for 1)) NOT BETWEEN '0' AND '9' THEN
           codigo_atual=SUBSTRING(codigo_atual from 2 for LENGTH(codigo_atual));
           END IF;

           IF LENGTH(codigo_atual) = 2 THEN
              linha='capitulo';
           ELSIF LENGTH(codigo_atual) = 4 THEN
              linha='grupo';
           ELSE
              linha='';
           END IF;

           IF dados.code NOT IN (SELECT PO.codigo FROM sncp_orcamento_imprimir_receita AS PO
           WHERE PO.codigo=dados.code) THEN
            INSERT INTO sncp_orcamento_imprimir_receita(codigo,name,linha,orcamento_id)
            VALUES (dados.code,dados.name,linha,$2);
            parent_atual=dados.parent_id;
            IF parent_atual IS NULL THEN
                ok=false;
            END IF;
           ELSE
              ok=false;
           END IF;
        END LOOP;
        END LOOP;

        RETURN ok;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_atualiza_print_orcamento(self, cr):
        cr.execute("""
        CREATE OR REPLACE function atualiza_print_orcamento() RETURNS boolean AS $$
        DECLARE
            dados RECORD;
            codigo_atual varchar;
            novo_montante numeric;
        BEGIN
            FOR dados IN (SELECT codigo FROM sncp_orcamento_imprimir_receita WHERE linha IN ('grupo','capitulo')) LOOP
            codigo_atual=trim(dados.codigo) || '%';
            novo_montante=( SELECT SUM(montante) FROM sncp_orcamento_imprimir_receita
            WHERE linha='artigo' AND codigo LIKE codigo_atual);
            UPDATE sncp_orcamento_imprimir_receita SET montante=novo_montante WHERE codigo=dados.codigo;
            END LOOP;
            RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_calcula_montante_titulo(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION calcula_montante_titulo(codigo_from varchar,codigo_to varchar)
        RETURNS numeric AS $$
        BEGIN
             RETURN (SELECT SUM(montante)
                    FROM sncp_orcamento_imprimir_receita
                    WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2);
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_titulos(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_titulos(despesa boolean,orcamento_id integer)
        RETURNS boolean AS
        $$
        DECLARE
          dados varchar;
          prefixo varchar(1);
          montante numeric;
        BEGIN
             dados=(SELECT codigo FROM sncp_orcamento_imprimir_receita WHERE linha='artigo' LIMIT 1);
             IF SUBSTRING(dados FROM 1 FOR 1) NOT BETWEEN '0' AND '9' THEN
                prefixo=SUBSTRING(dados FROM 1 FOR 1);
             ELSE
                prefixo='';

             END IF;

             IF $1=FALSE THEN
                montante=(SELECT calcula_montante_titulo('',prefixo||'08'));
                INSERT INTO sncp_orcamento_imprimir_receita(codigo,name,montante,linha,orcamento_id)
                VALUES('','RECEITAS CORRENTES',montante,'titulo',$2);
                montante=(SELECT calcula_montante_titulo(prefixo||'09',prefixo||'zz'));
                INSERT INTO sncp_orcamento_imprimir_receita(codigo,name,montante,linha,orcamento_id)
                VALUES(prefixo||'08zzzzzzzzzzzz','RECEITAS DE CAPITAL',montante,'titulo',$2);
             ELSE
                INSERT INTO sncp_orcamento_imprimir_receita(codigo,name,linha) VALUES('','DESPESAS CORRENTES','titulo');
                INSERT INTO sncp_orcamento_imprimir_receita(codigo,name,linha)
                    VALUES(prefixo||'06zzzzzzzzzzzz','RECEITAS DE CAPITAL','titulo');
             END IF;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    # ___AQUI DESPESA

    def sql_insere_orcamento_imprimir_despesa(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_orcamento_imprimir_despesa(orcamento_id integer) RETURNS BOOLEAN AS $$
            DECLARE
                dados RECORD;
            BEGIN
            FOR dados IN (SELECT SUM(OL.reforco) AS montante,COALESCE(AAA.name,'') AS nm,COALESCE(AAA2.code,'')
            AS cod_organica,
            COALESCE(AAA.code,'') AS cod_economica,
                          CAST('artigo' AS varchar) AS linha
                      FROM sncp_orcamento_linha AS OL
                      LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                          LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
                          WHERE OL.orcamento_id = $1
                          GROUP BY AAA2.code,AAA.code,AAA.name) LOOP
                    INSERT INTO sncp_orcamento_imprimir_despesa(codigo_eco,codigo_org,name,linha,montante,orcamento_id)
                    VALUES (dados.cod_economica,dados.cod_organica,dados.nm,dados.linha,dados.montante,$1);
            END LOOP;

            FOR dados IN (SELECT SUM(OL.reforco) AS montante,COALESCE(AAA2.name,'') AS nm,
            COALESCE(AAA2.code,'') AS cod_organica,
                          CAST('cabecalho2' AS varchar) AS linha
                      FROM sncp_orcamento_linha AS OL
                      LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
                          WHERE OL.orcamento_id = $1
                          GROUP BY AAA2.code,AAA2.name)
             LOOP
              INSERT INTO sncp_orcamento_imprimir_despesa(codigo_eco,codigo_org,name,linha,montante,orcamento_id)
              VALUES ('',dados.cod_organica,dados.nm,dados.linha,dados.montante,$1);
            END LOOP;

            RETURN TRUE;
            END
            $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_get_parents_economica(self, cr):
        cr.execute("""
        CREATE OR REPLACE function get_parents_economica(codigo_org varchar,codigo_eco varchar,orcamento_id integer)
        RETURNS boolean AS $$
            DECLARE
                ok boolean=TRUE;
                codigo_atual varchar;
                parent_atual integer;
                linha varchar;
                dados RECORD;
            BEGIN
             FOR dados IN (SELECT AAA.code,AAA.name,AAA.parent_id FROM account_analytic_account AS AAA WHERE code=$2
                    LIMIT 1) LOOP

             parent_atual=dados.parent_id;
             IF parent_atual IS NULL
                THEN ok=false;
             END IF;
            END LOOP;
             WHILE (ok=true) LOOP
               FOR dados IN (SELECT code,name,parent_id FROM account_analytic_account WHERE id=parent_atual) LOOP

                   codigo_atual=TRIM(dados.code);
                   IF LOWER(SUBSTRING(codigo_atual from 1 for 1)) NOT BETWEEN '0' AND '9' THEN
                   codigo_atual=SUBSTRING(codigo_atual from 2 for LENGTH(codigo_atual));
                   END IF;

                   IF LENGTH(codigo_atual) = 2 THEN
                      linha='capitulo';
                   ELSIF LENGTH(codigo_atual) = 4 THEN
                      linha='grupo';
                   ELSE
                      linha='';
                   END IF;

                   IF dados.code NOT IN (SELECT PO.codigo_eco FROM sncp_orcamento_imprimir_despesa AS PO
                   WHERE PO.codigo_eco=dados.code
                   AND PO.codigo_org=$1) THEN
                    INSERT INTO sncp_orcamento_imprimir_despesa(codigo_eco,codigo_org,name,linha,orcamento_id)
                    VALUES (dados.code,$1,dados.name,linha,$3);
                    parent_atual=dados.parent_id;
                    IF parent_atual IS NULL THEN
                        ok=false;
                    END IF;
                   ELSE
                      ok=false;
                   END IF;
              END LOOP;
            END LOOP;
            RETURN TRUE;
            END
            $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_get_parents_organica(self, cr):
        cr.execute("""
        CREATE OR REPLACE function get_parents_organica(codigo_org varchar,orcamento_id integer) RETURNS boolean AS $$
        DECLARE
            ok boolean=TRUE;
            codigo_atual varchar;
            parent_atual integer;
            linha varchar;
            dados RECORD;
        BEGIN
         FOR dados IN (SELECT AAA.code,AAA.name,AAA.parent_id FROM account_analytic_account AS AAA WHERE code=$1
                LIMIT 1) LOOP

         parent_atual=dados.parent_id;
         IF parent_atual IS NULL
            THEN ok=false;
         END IF;
        END LOOP;
         WHILE (ok=true) LOOP
           FOR dados IN (SELECT code,name,parent_id FROM account_analytic_account WHERE id=parent_atual) LOOP

               codigo_atual=TRIM(dados.code);
               IF LOWER(SUBSTRING(codigo_atual from 1 for 1)) NOT BETWEEN '0' AND '9' THEN
               codigo_atual=SUBSTRING(codigo_atual from 2 for LENGTH(codigo_atual));
               END IF;

               IF LENGTH(codigo_atual) = 2 THEN
                  linha='cabecalho1';
               ELSE
                  linha='cabecalho2';
               END IF;

               IF dados.code NOT IN (SELECT PO.codigo_org FROM sncp_orcamento_imprimir_despesa AS PO
               WHERE PO.codigo_org = dados.code
               AND PO.codigo_eco='') THEN
                INSERT INTO sncp_orcamento_imprimir_despesa(codigo_eco,codigo_org,name,linha,orcamento_id)
                VALUES ('',dados.code,dados.name,linha,$2);
                parent_atual=dados.parent_id;
                IF parent_atual IS NULL THEN
                    ok=false;
                END IF;
               ELSE
                  ok=false;
               END IF;
          END LOOP;
        END LOOP;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_atualiza_print_orcamento_despesa(self, cr):
        cr.execute("""
        CREATE OR REPLACE function atualiza_print_orcamento_despesa() RETURNS boolean AS $$
            DECLARE
                dados RECORD;
                codigo_atual varchar;
                novo_montante numeric;
            BEGIN
                FOR dados IN (SELECT codigo_org,codigo_eco FROM sncp_orcamento_imprimir_despesa
                WHERE linha IN ('grupo','capitulo')) LOOP
                codigo_atual=trim(dados.codigo_eco) || '%';
                novo_montante=( SELECT SUM(montante) FROM sncp_orcamento_imprimir_despesa
                WHERE linha='artigo' AND codigo_org=dados.codigo_org
                AND codigo_eco LIKE codigo_atual);
                UPDATE sncp_orcamento_imprimir_despesa SET montante=novo_montante
                WHERE codigo_org=dados.codigo_org AND codigo_eco=dados.codigo_eco;
                END LOOP;
                RETURN TRUE;
            END
            $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_check_cab_organica(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION check_cab_organica() RETURNS BOOLEAN AS $$
        DECLARE
          dados RECORD;
        BEGIN
          IF (SELECT COALESCE((SELECT id FROM sncp_orcamento_imprimir_despesa
          WHERE linha='cabecalho1'),0))=0 THEN
             UPDATE sncp_orcamento_imprimir_despesa SET linha='cabecalho1'
             WHERE linha='cabecalho2';
          END IF;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    # AQUI MODIFICAÇÃO RECEITA
    def sql_insere_modificacao_imprimir_receita(self, cr):

        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_modificacao_imprimir_receita(tipo varchar,ano integer,id integer)
        RETURNS BOOLEAN AS $$
        DECLARE
          dados RECORD;
          BEGIN
            IF $1='alt' THEN
            FOR dados in (SELECT COALESCE(AAA.code,'') AS cd,COALESCE(AAA.name,'') AS nm,
            COALESCE(SUM(OL.reforco),0.0) AS reforco,
                CAST('artigo' AS varchar) AS linha,COALESCE(SUM(OL.anulacao),0.0) AS anulacao,OL.economica_id AS eco_id
                    FROM sncp_orcamento_linha AS OL
                    LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                    WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO
                        WHERE SO.ano=$2 AND SO.tipo_orc='alt' and SO.alt_principal=$3 AND SO.titulo='rece')
                    GROUP BY AAA.code,AAA.name,linha,OL.economica_id)
                    LOOP
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,linha,reforco,abate,economica_id)
                VALUES (dados.cd,dados.nm,dados.linha,dados.reforco,dados.anulacao,dados.eco_id);
                    END LOOP;
                ELSIF $1='rev' THEN
                   FOR dados in (SELECT COALESCE(AAA.code,'') AS cd,COALESCE(AAA.name,'') AS nm,
                   COALESCE(SUM(OL.reforco),0.0) AS reforco,
                   CAST('artigo' AS varchar) AS linha,
                   COALESCE(SUM(OL.anulacao),0.0) AS anulacao,OL.economica_id AS eco_id
                       FROM sncp_orcamento_linha AS OL
                       LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                       WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO
                       WHERE SO.ano=$2 AND SO.tipo_orc='rev' and SO.numero=$3 AND SO.titulo='rece')
                   GROUP BY AAA.code,AAA.name,linha,OL.economica_id)
                       LOOP
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,linha,reforco,abate,economica_id)
                        VALUES (dados.cd,dados.nm,dados.linha,dados.reforco,dados.anulacao,dados.eco_id);
                   END LOOP;
                END IF;
                RETURN TRUE;
                END
                $$ LANGUAGE plpgsql;
        """)

        return True

    def sql_obtem_previsao_atual(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION obtem_previsao_atual(datahora varchar,ano integer) RETURNS BOOLEAN AS
        $$
         DECLARE
          dados RECORD;
          prev_atual numeric;
          abate numeric;
          prev_futura numeric;
         BEGIN
            FOR dados IN (SELECT * FROM sncp_modificacao_imprimir_receita) LOOP
            prev_atual=COALESCE((SELECT SUM(montante) FROM sncp_orcamento_historico AS OH
            WHERE OH.name=$2 AND OH.datahora < $1::TIMESTAMP AND
            OH.economica_id=dados.economica_id AND OH.categoria IN ('51rdota','52rrefo')),0.0);
            abate=COALESCE((SELECT SUM(montante) FROM sncp_orcamento_historico AS OH
            WHERE OH.name=$2 AND OH.datahora < $1::TIMESTAMP
            AND OH.economica_id=dados.economica_id AND OH.categoria = '53rabat'),0.0);
                prev_atual=prev_atual-abate;
            prev_futura=prev_atual+dados.reforco-dados.abate;
            UPDATE sncp_modificacao_imprimir_receita SET previsao_atual=prev_atual,previsao_corrigida=prev_futura
            WHERE id=dados.id;
            END LOOP;
            RETURN TRUE;
         END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_mod_get_parents(self, cr):
        cr.execute("""
        CREATE OR REPLACE function mod_get_parents(codigo varchar) RETURNS boolean AS $$
        DECLARE
        ok boolean=TRUE;
        codigo_atual varchar;
        parent_atual integer;
        linha varchar;
        dados RECORD;
        BEGIN
        FOR dados IN (SELECT AAA.code,AAA.name,AAA.parent_id FROM account_analytic_account AS AAA WHERE code=$1
            LIMIT 1) LOOP

        parent_atual=dados.parent_id;
        IF parent_atual IS NULL
        THEN ok=false;
        END IF;
        END LOOP;
        WHILE (ok=true) LOOP
        FOR dados IN (SELECT code,name,parent_id FROM account_analytic_account WHERE id=parent_atual) LOOP

           codigo_atual=TRIM(dados.code);
           IF LOWER(SUBSTRING(codigo_atual from 1 for 1)) NOT BETWEEN '0' AND '9' THEN
           codigo_atual=SUBSTRING(codigo_atual from 2 for LENGTH(codigo_atual));
           END IF;

           IF LENGTH(codigo_atual) = 2 THEN
              linha='capitulo';
           ELSIF LENGTH(codigo_atual) = 4 THEN
              linha='grupo';
           ELSE
              linha='';
           END IF;

           IF dados.code NOT IN (SELECT PO.codigo FROM sncp_modificacao_imprimir_receita AS PO
           WHERE PO.codigo=dados.code) THEN
            INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,linha) VALUES (dados.code,dados.name,linha);
            parent_atual=dados.parent_id;
            IF parent_atual IS NULL THEN
                ok=false;
            END IF;
           ELSE
              ok=false;
           END IF;
        END LOOP;
        END LOOP;

        RETURN ok;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_atualiza_print_modificacao(self, cr):
        cr.execute("""
        CREATE OR REPLACE function atualiza_print_modificacao() RETURNS boolean AS $$
        DECLARE
            dados RECORD;
            codigo_atual varchar;
            refor numeric;
            abat numeric;
            prev_atual numeric;
            prev_corr numeric;

        BEGIN
            FOR dados IN (SELECT codigo FROM sncp_modificacao_imprimir_receita WHERE linha IN ('grupo','capitulo')) LOOP
            codigo_atual=trim(dados.codigo) || '%';
            refor=( SELECT SUM(MIR.reforco) FROM sncp_modificacao_imprimir_receita  AS MIR
            WHERE MIR.linha='artigo' AND MIR.codigo LIKE codigo_atual);
            abat=(SELECT SUM(MIR.abate) FROM sncp_modificacao_imprimir_receita AS MIR
            WHERE MIR.linha='artigo' AND MIR.codigo LIKE codigo_atual);
            prev_atual=( SELECT SUM(MIR.previsao_atual) FROM sncp_modificacao_imprimir_receita AS MIR
            WHERE MIR.linha='artigo' AND MIR.codigo LIKE codigo_atual);
            prev_corr=( SELECT SUM(MIR.previsao_corrigida) FROM sncp_modificacao_imprimir_receita AS MIR
            WHERE MIR.linha='artigo' AND MIR.codigo LIKE codigo_atual);

            UPDATE sncp_modificacao_imprimir_receita SET reforco=refor,abate=abat,
            previsao_atual=prev_atual,previsao_corrigida=prev_corr WHERE codigo=dados.codigo;
            END LOOP;
            RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_calcula_montante_titulo_mod(self, cr):
        cr.execute("""
        CREATE OR REPLACE function calcula_montante_titulo_mod(codigo_from varchar,codigo_to varchar,nref integer)
        RETURNS numeric AS $$
        BEGIN
        IF $3=0 THEN
            RETURN (SELECT SUM(abate)
                FROM sncp_modificacao_imprimir_receita
                WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2);
        END IF;
        IF $3=1 THEN
            RETURN (SELECT SUM(reforco)
                        FROM sncp_modificacao_imprimir_receita
                        WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2);
        END IF;
        IF $3=2 THEN
                RETURN (SELECT SUM(previsao_atual)
                        FROM sncp_modificacao_imprimir_receita
                            WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2);
            END IF;
        IF $3=3 THEN
            RETURN (SELECT SUM(previsao_corrigida)
                FROM sncp_modificacao_imprimir_receita
                    WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2);
        END IF;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_titulos_mod(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_titulos_mod(despesa boolean)
        RETURNS boolean AS
        $$
        DECLARE
          dados varchar;
          prefixo varchar(1);
          reforco numeric;
          abate numeric;
          prev_atual numeric;
          prev_corr numeric;
        BEGIN
             dados=(SELECT codigo FROM sncp_modificacao_imprimir_receita WHERE linha='artigo' LIMIT 1);
             IF SUBSTRING(dados FROM 1 FOR 1) NOT BETWEEN '0' AND '9' THEN
                prefixo=SUBSTRING(dados FROM 1 FOR 1);
             ELSE
                prefixo='';

             END IF;

             IF $1=FALSE THEN
                reforco=(SELECT calcula_montante_titulo_mod('',prefixo||'08',1));
                abate=(SELECT calcula_montante_titulo_mod('',prefixo||'08',0));
                prev_atual=(SELECT calcula_montante_titulo_mod('',prefixo||'08',2));
                prev_corr=(SELECT calcula_montante_titulo_mod('',prefixo||'08',3));
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,reforco,linha,abate,previsao_atual,
                    previsao_corrigida)
                VALUES('','RECEITAS CORRENTES',reforco,'titulo',abate,prev_atual,prev_corr);
                reforco=(SELECT calcula_montante_titulo_mod(prefixo||'09',prefixo||'zz',1));
                abate=(SELECT calcula_montante_titulo_mod(prefixo||'09',prefixo||'zz',0));
                prev_atual=(SELECT calcula_montante_titulo_mod(prefixo||'09',prefixo||'zz',2));
                prev_corr=(SELECT calcula_montante_titulo_mod(prefixo||'09',prefixo||'zz',3));
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,reforco,linha,abate,previsao_atual,
                    previsao_corrigida)
                VALUES(prefixo||'08zzzzzzzzzzzz','RECEITAS DE CAPITAL',reforco,'titulo',abate,prev_atual,prev_corr);
             ELSE
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,linha)
                VALUES('','DESPESAS CORRENTES','titulo');
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,linha)
                VALUES(prefixo||'06zzzzzzzzzzzz','RECEITAS DE CAPITAL','titulo');
             END IF;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    # AQUI MODIFICAÇÃO DESPESA

    def sql_insere_modificacao_imprimir_despesa(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_modificacao_imprimir_despesa(tipo varchar,ano integer,id integer)
        RETURNS BOOLEAN AS $$
            DECLARE
                dados RECORD;
            BEGIN
            IF $1='alt' THEN

                FOR dados IN (SELECT AAA.name AS nm,AAA2.code AS cod_organica,AAA.code AS cod_economica,
                COALESCE(SUM(OL.reforco),0.0) AS refo,COALESCE(SUM(OL.anulacao),0.0) AS abate,
                OL.economica_id AS eco_id,OL.organica_id AS org_id,CAST('artigo' AS varchar) AS linha
                FROM sncp_orcamento_linha AS OL
                    LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                    LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
                    WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO
                    WHERE SO.ano=$2 AND SO.tipo_orc='alt' and SO.alt_principal=$3 AND SO.titulo='desp')
                    GROUP BY AAA2.code,AAA.code,AAA.name,OL.economica_id,OL.organica_id) LOOP
                        INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha,reforco,abate,
                        economica_id,organica_id)
                        VALUES (dados.cod_economica,dados.cod_organica,dados.nm,dados.linha,dados.refo,dados.abate,
                        dados.eco_id,dados.org_id);
                END LOOP;

                FOR dados IN (SELECT COALESCE(SUM(OL.reforco),0.0) AS refo,
                COALESCE(SUM(OL.anulacao),0.0) AS abate,AAA2.name AS nm,AAA2.code AS cod_organica,
                        OL.organica_id AS org_id,
                CAST('cabecalho2' AS varchar) AS linha
                      FROM sncp_orcamento_linha AS OL
                      LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
                      WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO
                      WHERE SO.ano=$2 AND SO.tipo_orc='alt' AND SO.alt_principal=$3 AND SO.titulo='desp')
                      GROUP BY AAA2.code,AAA2.name,OL.organica_id)
                 LOOP
                  INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha,reforco,abate,
                  organica_id)
                  VALUES ('',dados.cod_organica,dados.nm,dados.linha,dados.refo,dados.abate,dados.org_id);
                END LOOP;

            ELSIF $1='rev' THEN
                FOR dados IN (SELECT AAA.name AS nm,AAA2.code AS cod_organica,AAA.code AS cod_economica,
                COALESCE(SUM(OL.reforco),0.0) AS refo,COALESCE(SUM(OL.anulacao),0.0) AS abate,
                OL.economica_id AS eco_id,OL.organica_id AS org_id,CAST('artigo' AS varchar) AS linha
                FROM sncp_orcamento_linha AS OL
                      LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                      LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
                      WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO
                      WHERE SO.ano=$2 AND SO.tipo_orc='rev' and SO.numero=$3 AND SO.titulo='desp')
                      GROUP BY AAA2.code,AAA.code,AAA.name,OL.economica_id,OL.organica_id) LOOP
                        INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha,reforco,abate,
                        economica_id,organica_id)
                        VALUES (dados.cod_economica,dados.cod_organica,dados.nm,dados.linha,dados.refo,dados.abate,
                        dados.eco_id,dados.org_id);
                END LOOP;

                FOR dados IN (SELECT COALESCE(SUM(OL.reforco),0.0) AS refo,
                COALESCE(SUM(OL.anulacao),0.0) AS abate,AAA2.name AS nm,AAA2.code AS cod_organica,
                OL.organica_id AS org_id,
                CAST('cabecalho2' AS varchar) AS linha
                FROM sncp_orcamento_linha AS OL
                    LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
                    WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO
                    WHERE SO.ano=$2 AND SO.tipo_orc='rev' and SO.numero=$3 AND SO.titulo='desp')
                    GROUP BY AAA2.code,AAA2.name,OL.organica_id)
                    LOOP
                    INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha,reforco,abate,
                    organica_id)
                    VALUES ('',dados.cod_organica,dados.nm,dados.linha,dados.refo,dados.abate,dados.org_id);
                END LOOP;
            END IF;
            RETURN TRUE;
            END
            $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_obtem_mod_desp_previsao_atual(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION obtem_mod_desp_previsao_atual(datahora varchar,ano integer) RETURNS BOOLEAN AS
        $$
         DECLARE
          dados RECORD;
          prev_atual numeric;
          abate numeric;
          prev_futura numeric;
         BEGIN
            FOR dados IN (SELECT * FROM sncp_modificacao_imprimir_despesa) LOOP
            prev_atual=COALESCE((SELECT SUM(montante) FROM sncp_orcamento_historico AS OH
            WHERE OH.name=$2 AND OH.datahora < $1::TIMESTAMP AND
            OH.economica_id=dados.economica_id AND OH.organica_id=dados.organica_id AND
            OH.categoria IN ('01ddota','02drefo')),0.0);
            abate=COALESCE((SELECT SUM(montante) FROM sncp_orcamento_historico AS OH
            WHERE OH.name=$2 AND OH.datahora < $1::TIMESTAMP
            AND OH.economica_id=dados.economica_id AND OH.organica_id=dados.organica_id AND
            OH.categoria = '03dabat'),0.0);
                prev_atual=prev_atual-abate;
            prev_futura=prev_atual+dados.reforco-dados.abate;
            UPDATE sncp_modificacao_imprimir_despesa SET previsao_atual=prev_atual,previsao_corrigida=prev_futura
            WHERE id=dados.id;
            END LOOP;
            RETURN TRUE;
         END
        $$ LANGUAGE plpgsql;

        """)
        return True

    def sql_get_mod_desp_parents_economica(self, cr):
        cr.execute("""
        CREATE OR REPLACE function get_mod_desp_parents_economica(codigo_org varchar,codigo_eco varchar)
        RETURNS boolean AS $$
            DECLARE
                ok boolean=TRUE;
                codigo_atual varchar;
                parent_atual integer;
                linha varchar;
                dados RECORD;
            BEGIN
             FOR dados IN (SELECT AAA.code,AAA.name,AAA.parent_id FROM account_analytic_account AS AAA WHERE code=$2
                    LIMIT 1) LOOP

             parent_atual=dados.parent_id;
             IF parent_atual IS NULL
                THEN ok=false;
             END IF;
            END LOOP;
             WHILE (ok=true) LOOP
               FOR dados IN (SELECT code,name,parent_id FROM account_analytic_account WHERE id=parent_atual) LOOP

                   codigo_atual=TRIM(dados.code);
                   IF LOWER(SUBSTRING(codigo_atual from 1 for 1)) NOT BETWEEN '0' AND '9' THEN
                   codigo_atual=SUBSTRING(codigo_atual from 2 for LENGTH(codigo_atual));
                   END IF;

                   IF LENGTH(codigo_atual) = 2 THEN
                      linha='capitulo';
                   ELSIF LENGTH(codigo_atual) = 4 THEN
                      linha='grupo';
                   ELSE
                      linha='';
                   END IF;

                   IF dados.code NOT IN (SELECT PO.codigo_eco FROM sncp_modificacao_imprimir_despesa AS PO
                   WHERE PO.codigo_eco=dados.code
                   AND PO.codigo_org=$1) THEN
                    INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha)
                    VALUES (dados.code,$1,dados.name,linha);
                    parent_atual=dados.parent_id;
                    IF parent_atual IS NULL THEN
                        ok=false;
                    END IF;
                   ELSE
                      ok=false;
                   END IF;
              END LOOP;
            END LOOP;
            RETURN TRUE;
            END
            $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_get_mod_desp_parents_organica(self, cr):
        cr.execute("""
        CREATE OR REPLACE function get_mod_desp_parents_organica(codigo_org varchar) RETURNS boolean AS $$
        DECLARE
            ok boolean=TRUE;
            codigo_atual varchar;
            parent_atual integer;
            linha varchar;
            dados RECORD;
        BEGIN
         FOR dados IN (SELECT AAA.code,AAA.name,AAA.parent_id FROM account_analytic_account AS AAA WHERE code=$1
                LIMIT 1) LOOP

         parent_atual=dados.parent_id;
         IF parent_atual IS NULL
            THEN ok=false;
         END IF;
        END LOOP;
         WHILE (ok=true) LOOP
           FOR dados IN (SELECT code,name,parent_id FROM account_analytic_account WHERE id=parent_atual) LOOP

               codigo_atual=TRIM(dados.code);
               IF LOWER(SUBSTRING(codigo_atual from 1 for 1)) NOT BETWEEN '0' AND '9' THEN
               codigo_atual=SUBSTRING(codigo_atual from 2 for LENGTH(codigo_atual));
               END IF;

               IF LENGTH(codigo_atual) = 2 THEN
                  linha='cabecalho1';
               ELSE
                  linha='cabecalho2';
               END IF;

               IF dados.code NOT IN (SELECT PO.codigo_org FROM sncp_modificacao_imprimir_despesa AS PO
               WHERE PO.codigo_org=dados.code
               AND PO.codigo_eco='') THEN
                INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha)
                VALUES ('',dados.code,dados.name,linha);
                parent_atual=dados.parent_id;
                IF parent_atual IS NULL THEN
                    ok=false;
                END IF;
               ELSE
                  ok=false;
               END IF;
          END LOOP;
        END LOOP;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_atualiza_print_modificacao_despesa(self, cr):
        cr.execute("""
        CREATE OR REPLACE function atualiza_print_modificacao_despesa() RETURNS boolean AS $$
            DECLARE
                dados RECORD;
                codigo_atual varchar;
                refor numeric;
                abat numeric;
                prev_atual numeric;
                prev_corr numeric;

            BEGIN
                FOR dados IN (SELECT codigo_org,codigo_eco FROM sncp_modificacao_imprimir_despesa
                WHERE linha IN ('grupo','capitulo')) LOOP
                codigo_atual=trim(dados.codigo_eco) || '%';
                refor=( SELECT SUM(MID.reforco) FROM sncp_modificacao_imprimir_despesa  AS MID
                WHERE MID.linha='artigo' AND MID.codigo_org=dados.codigo_org AND MID.codigo_eco LIKE codigo_atual);
                abat=( SELECT SUM(MID.abate) FROM sncp_modificacao_imprimir_despesa  AS MID
                WHERE MID.linha='artigo' AND MID.codigo_org=dados.codigo_org AND MID.codigo_eco LIKE codigo_atual);
                prev_atual=( SELECT SUM(MID.previsao_atual) FROM sncp_modificacao_imprimir_despesa  AS MID
                WHERE MID.linha='artigo' AND MID.codigo_org=dados.codigo_org AND MID.codigo_eco LIKE codigo_atual);
                prev_corr=( SELECT SUM(MID.previsao_corrigida) FROM sncp_modificacao_imprimir_despesa  AS MID
                WHERE MID.linha='artigo' AND MID.codigo_org=dados.codigo_org AND MID.codigo_eco LIKE codigo_atual);

                UPDATE sncp_modificacao_imprimir_despesa SET reforco=refor,abate=abat,
            previsao_atual=prev_atual,previsao_corrigida=prev_corr
            WHERE codigo_org=dados.codigo_org AND codigo_eco=dados.codigo_eco ;
                END LOOP;
                RETURN TRUE;
            END
            $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_mod_desp_check_cab_organica(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION mod_desp_check_cab_organica() RETURNS BOOLEAN AS $$
        DECLARE
          dados RECORD;
        BEGIN
          IF (SELECT COALESCE((SELECT id FROM sncp_modificacao_imprimir_despesa WHERE linha='cabecalho1'),0))=0 THEN
             UPDATE sncp_modificacao_imprimir_despesa SET linha='cabecalho1' WHERE linha='cabecalho2';
          END IF;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    # IMPRESSÂO HISTÓRICO E ACUMULADOS
    def sql_insere_historico_rodape(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_historico_rodape( integer[],orc_hist_cabecalho integer) RETURNS boolean AS
        $$
            DECLARE
                list_hist_ids integer[] = $1;
                hist sncp_orcamento_historico%ROWTYPE;
                x integer;
                nome_documento varchar;
            BEGIN
                FOREACH x IN ARRAY list_hist_ids
                    LOOP
                     SELECT * INTO hist FROM sncp_orcamento_historico WHERE id=x;
                     nome_documento=(SELECT AM.name FROM account_move AS AM WHERE AM.id=hist.doc_contab_id);
                     INSERT INTO sncp_orcamento_historico_rodape(orc_hist_cabecalho_id,name,categoria,datahora,
                         organica_id,economica_id,funcional_id,centrocustos_id,montante,cabimento_id,compromisso_id,
                         doc_contab_id,doc_contab_name)
                     VALUES($2,hist.name,hist.categoria,hist.datahora,hist.organica_id,hist.economica_id,
                         hist.funcional_id,hist.centrocustos_id,hist.montante,hist.cabimento_id,hist.compromisso_id,
                         hist.doc_contab_id,nome_documento);

                    END LOOP;
                RETURN TRUE;
            END;
        $$LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_acumulados_rodape(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_acumulados_rodape( integer[],orc_acum_cabecalho integer) RETURNS boolean AS
        $$
            DECLARE
                list_acum_ids integer[] = $1;
                acum sncp_orcamento_acumulados%ROWTYPE;
                x integer;
                nome_documento varchar;
            BEGIN
                FOREACH x IN ARRAY list_acum_ids
                    LOOP
                     SELECT * INTO acum FROM sncp_orcamento_acumulados WHERE id=x;
                     INSERT INTO sncp_orcamento_acumulados_rodape(orc_acum_cabecalho_id,name,categoria,organica_id,
                     economica_id,
                     funcional_id,montante)
                     VALUES($2,acum.name,acum.categoria,acum.organica_id,acum.economica_id,
                     acum.funcional_id,acum.montante);

                    END LOOP;
                RETURN TRUE;
            END;
        $$LANGUAGE plpgsql;
        """)
        return True

    def sql_compara_strings(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION compara_strings(str1 varchar,str2 varchar) RETURNS INTEGER AS $$
        DECLARE
           x int;
           c1 varchar;
           c2 varchar;
        BEGIN
        IF LENGTH($1)>=LENGTH($2) THEN
            FOR x IN 1..LENGTH($1) LOOP
                c1=COALESCE(substring($1 from x for 1),'');
                c2=COALESCE(substring($2 from x for 1),'');
                IF ascii(c1)>ascii(c2) THEN
                RETURN 1;
                ELSIF ascii(c1)<ascii(c2) THEN
                   RETURN -1;
                END IF;
            END LOOP;
        ELSIF LENGTH($2)>=LENGTH($1) THEN
            FOR x in 1..LENGTH($2) LOOP
                c1=COALESCE(substring($1 from x for 1),'');
                c2=COALESCE(substring($2 from x for 1),'');
                IF ascii(c2)>ascii(c1) THEN
                RETURN -1;
                ELSIF ascii(c2)<ascii(c1) THEN
                   RETURN 1;
                END IF;
            END LOOP;
        END IF;
        RETURN 0;
        END;
        $$LANGUAGE plpgsql;
        """)
        return True

    def create(self, cr, uid, vals, context=None):
        self.teste_existencia_orcamento(cr)
        self.teste_existencia_orcamento_receita(cr)
        self.teste_existencia_orcamento_despesa(cr)
        self.teste_existencia_modificacao_receita(cr)
        self.teste_existencia_modificacao_despesa(cr)
        self.teste_existencia_historico_acumulados(cr)

        if 'tipo_mod' in vals:
            if vals['tipo_mod'] is not False:
                vals['tipo_orc'] = vals['tipo_mod']

        return super(sncp_orcamento, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'tipo_mod' in vals:
            vals['tipo_orc'] = vals['tipo_mod']

        return super(sncp_orcamento, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        db_orc_linhas = self.pool.get('sncp.orcamento.linha')
        linhas_ids = db_orc_linhas.search(cr, uid, [('orcamento_id', '=', ids[0])])

        if len(linhas_ids) != 0:
            db_orc_linhas.unlink(cr, uid, linhas_ids)
        return super(sncp_orcamento, self).unlink(cr, uid, ids, context=context)

    _defaults = {
        'numero': 0,
        'alt_principal': 0,
        'tipo_orc': _get_tipo,
        'state': 'draft',
        'ano': datetime.now().year,
        'preenche_linhas': 0,
        'cab_readonly': 0,
    }

    _order = 'ano,tipo_orc,titulo,numero'

    _constraints = [
        (_mesmo_id_organica_economica_funcional, u'', ['orc_linhas_ids.reforco', 'orc_linhas_ids.anulacao']),
        (_ano_restrict, u'', ['ano']),
    ]

    _sql_constraints = [
        ('orcamento_unique', 'unique (tipo_orc,titulo,ano,numero)',
         u'Orçamento/Modificação com estes parâmetros já existe.'),
    ]

sncp_orcamento()


# _____________________________________________________ORCAMENTO LINHA_______________________________
class sncp_orcamento_linha(osv.Model):
    _name = 'sncp.orcamento.linha'
    _description = u"Linhas do Orçamento"

    def _check_orcamento_montante_sup_zero(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context=context)

        if data.reforco > 0 and data.orcamento_id.tipo_orc in ['orc']:
            return True
        elif (data.reforco > 0 and data.anulacao == 0) or (data.reforco == 0 and data.anulacao > 0):
            return True

        return False

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_orcamento_linha, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'orcamento_id': fields.many2one('sncp.orcamento'),
        'titulo': fields.char(u'Título'),
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')], ),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')]),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')], ),
        'reforco': fields.float(u'Reforço', digits=(12, 2), ),
        'anulacao': fields.float(u'Anulação', digits=(12, 2), ),
        'name': fields.text(u'Observações'), }


    _order = 'name,organica_id, economica_id, funcional_id'

    _constraints = [
        (_check_orcamento_montante_sup_zero, u'Aviso: Se tipo é orçamento a dotação deve ser superior a zero'
                                             u' caso o tipo não seja orçamento ou a dotação>0'
                                             u' e abate=0, ou abate>0 e dotação=0',
         ['reforco', 'anulacao', 'orcamento_id.tipo_orc']),
    ]


sncp_orcamento_linha()