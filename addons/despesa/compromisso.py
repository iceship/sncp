# -*- encoding: utf-8 -*-
##############################################################################
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

from datetime import *
from openerp.osv import fields, osv
import pytz
from openerp.tools.translate import _
import decimal
from decimal import *
import despesa

# ______________________________________________________________COMPROMISSO_____________________________________


def test_partner_id(self, cr, uid, partner_id):
    db_res_partner = self.pool.get('res.partner')
    obj_partner = db_res_partner.browse(cr, uid, partner_id)
    message = u''

    if obj_partner.property_account_receivable.id is False:
            message += u'Contabilidade/Conta a receber (Cliente)\n'

    if obj_partner.property_account_payable.id is False:
        message += u'Contabilidade/Conta a receber (Fornecedor)\n'

    if len(message) != 0:
        raise osv.except_osv(_(u'Aviso'), _(u'Para evitar futuros erros na execução do programa '
                                            u'deverá preencher os seguintes campos do parceiro de negócio:\n'+message
                                            + u'.'))
    return True


class sncp_despesa_compromisso(osv.Model):
    _name = 'sncp.despesa.compromisso'
    _description = "Compromisso"

    _rec_name = 'compromisso'

    def call_diario(self, cr, uid, ids, context=None):
        compromisso = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT id
        FROM sncp_despesa_compromisso_ano
        WHERE compromisso_id=%d AND ano=%d AND cabimento_id IS NOT NULL
        """ % (compromisso.id, compromisso.ano_ini))

        compromisso_ano_id = cr.fetchone()
        if compromisso_ano_id is not None:

            compromisso_ano_id = compromisso_ano_id[0]

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso_linha WHERE compromisso_ano_id=%d
            """ % compromisso_ano_id)

            ha_linhas = cr.fetchall()

            if len(ha_linhas) == 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Não há linhas para processar.'))

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso_linha
            WHERE compromisso_ano_id = %d AND (economica_id IS NULL OR organica_id IS NULL)
            """ % compromisso_ano_id)

            linhas = cr.fetchall()

            if len(linhas) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Linhas do compromisso mal configuradas.'))

        obj = self.browse(cr, uid, ids[0])
        send = {'tipo': obj.tipo, 'ano_ini': obj.ano_ini, 'ano_fim': obj.ano_fim}
        return self.pool.get('formulario.sncp.despesa.compromisso.diario').wizard(cr, uid, ids, context, send)

    def criar_anos(self, cr, uid, ids, context):
        if context['tipo'] != 'plu' and context['ano_fim'] != context['ano_ini']:
            raise osv.except_osv(_(u'Aviso'), _(u'Só no caso de compromisso plurianual, '
                                                u'o ano final poderá ser maior que o ano inicial.'))

        obj_ano = self.pool.get('sncp.despesa.compromisso.ano')
        self.write(cr, uid, ids, {'next': 1})
        for ano in range(context['ano_ini'], context['ano_fim']+1):
            # primeiro atual
            if ano == context['ano_ini'] and ano == datetime.now().year:
                obj_ano.create(cr, uid, {'editar': 1, 'ano': ano, 'compromisso_id': ids[0], })
            # primeiro dos futuros
            elif ano == context['ano_ini'] and ano > datetime.now().year:
                obj_ano.create(cr, uid, {'editar': 2, 'ano': ano, 'compromisso_id': ids[0], 'estado': 10})
            # todos os outros
            else:
                obj_ano.create(cr, uid, {'ano': ano, 'compromisso_id': ids[0], })

        return True

    def dados_adic(self, cr, uid, ids, context):
        db_sncp_compromisso_dados_adic = self.pool.get('sncp.despesa.compromisso.dados.adic')
        dados_ids = db_sncp_compromisso_dados_adic.search(cr, uid, [('compromisso_id', '=', ids[0])])
        if len(dados_ids) == 0:
            dados_id = db_sncp_compromisso_dados_adic.create(cr, uid, {'compromisso_id': ids[0]})
        else:
            dados_id = dados_ids[0]

        return {'type': 'ir.actions.act_window',
                'name': 'Dados Adicionais',
                'res_model': 'sncp.despesa.compromisso.dados.adic',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': dados_id,
                'target': 'new',
                'context': context,
                'nodestroy': True,
                'edit': True,
                }

    def teste_existencia_compromisso(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'anula_compromisso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_anula_compromisso(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'contabiliza_compromisso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_contabiliza_compromisso(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'da_valor_comprometido_mes'""")
        result = cr.fetchone()
        if result is None:
            self.sql_da_valor_comprometido_mes(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'da_valor_elegivel'""")
        result = cr.fetchone()
        if result is None:
            self.sql_da_valor_elegivel(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'elimina_historico_comp'""")
        result = cr.fetchone()
        if result is None:
            self.sql_elimina_historico_comp(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fundo_da_valor_disponivel'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fundo_da_valor_disponivel(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc
                      WHERE proname = 'insere_linha_movimento_contabilistico_compromisso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_linha_movimento_contabilistico_compromisso(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'ultima_atualizacao'""")
        result = cr.fetchone()
        if result is None:
            self.sql_ultima_atualizacao(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'valida_montantes_agenda'""")
        result = cr.fetchone()
        if result is None:
            self.sql_valida_montantes_agenda(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc
                      WHERE proname = 'insere_movimento_contabilistico_compromisso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_movimento_contabilistico_compromisso(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname='linhas_compromisso_ano_mm_dimensoes' """)
        result = cr.fetchone()
        if result is None:
            self.sql_linhas_compromisso_ano_mm_dimensoes(cr)

        return True

    def compromisso_proc(self, cr, uid, ids, context, vals):
        compromisso = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT cabimento_id
        FROM sncp_despesa_compromisso_ano
        WHERE ano=%d and compromisso_id=%d
        """ % (compromisso.ano_ini, compromisso.id))

        result = cr.fetchone()

        if result is not None:
            cabimento_id = result[0]
            if cabimento_id is None:
                raise osv.except_osv(_(u'Aviso'), _(u'O compromisso não têm cabimento associado.'))

        cr.execute("""
        SELECT id
        FROM account_account AS AA
        WHERE AA.code='041' AND type != 'view'
        """)
        conta_041 = cr.fetchone()

        cr.execute("""
        SELECT id
        FROM account_account AS AA
        WHERE AA.code='051' AND type != 'view'
        """)
        conta_051 = cr.fetchone()

        cr.execute("""
        SELECT id
        FROM account_account AS AA
        WHERE AA.code='042' AND type != 'view'
        """)
        conta_042 = cr.fetchone()

        cr.execute("""
        SELECT id
        FROM account_account AS AA
        WHERE AA.code='052' AND type != 'view'
        """)
        conta_052 = cr.fetchone()

        cr.execute("""
        SELECT id
        FROM account_account AS AA
        WHERE AA.code='043' AND type != 'view'
        """)
        conta_043 = cr.fetchone()

        cr.execute("""
        SELECT id
        FROM account_account AS AA
        WHERE AA.code='053' AND type != 'view'
        """)
        conta_053 = cr.fetchone()

        cr.execute("""
        SELECT id
        FROM account_account AS AA
        WHERE AA.code='044' AND type != 'view'
        """)
        conta_044 = cr.fetchone()

        cr.execute("""
        SELECT id
        FROM account_account AS AA
        WHERE AA.code='054' AND type != 'view'
        """)
        conta_054 = cr.fetchone()

        if conta_041 is None or conta_042 is None or conta_043 is None \
           or conta_044 is None or conta_051 is None or conta_052 is None \
           or conta_053 is None or conta_054 is None:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina as contas com os seguintes códigos:\n'
                                                u'1. 041 com tipo interno diferente de vista.\n'
                                                u'2. 042 com tipo interno diferente de vista.\n'
                                                u'3. 043 com tipo interno diferente de vista.\n'
                                                u'4. 044 com tipo interno diferente de vista.\n'
                                                u'5. 051 com tipo interno diferente de vista.\n'
                                                u'6. 052 com tipo intereno diferente de vista.\n'
                                                u'7. 053 com tipo interno diferente de vista.\n'
                                                u'8. 054 com tipo interno diferente de vista.\n'))
        cr.execute("""
                   SELECT valida_montantes_agenda(%d)
                   """ % compromisso.id)
        mensagem = cr.fetchone()[0]
        if len(mensagem) > 0:
            raise osv.except_osv(_(mensagem), _(u''))

        datahora = datetime.strptime(vals['datahora'], "%Y-%m-%d %H:%M:%S")
        datahora = datahora.replace(tzinfo=pytz.utc)

        cr.execute(""" SELECT contabiliza_compromisso(%d,%d,%d,'%s','%s',%d)""" % (compromisso.id, uid,
                                                                                   vals['diario_id'],
                                                                                   unicode(datahora), vals['ref'],
                                                                                   vals['diario_fut_id']))

        mensagem = cr.fetchone()[0]
        if len(mensagem) > 0:
            raise osv.except_osv(_(mensagem), _(u''))

        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')
        db_ir_sequence = self.pool.get('ir.sequence')
        db_account_journal = self.pool.get('account.journal')

        ano_ids = db_sncp_despesa_compromisso_ano.search(cr, uid, [('compromisso_id', '=', ids[0]),
                                                                   ('ano', '=', datetime.now().year)])
        if len(ano_ids) != 0:
            jornal = db_account_journal.browse(cr, uid, vals['diario_id'])
            if jornal.sequence_id.id:
                name = db_ir_sequence.next_by_id(cr, uid, jornal.sequence_id.id)
                self.write(cr, uid, ids[0], {'compromisso': name})
            else:
                raise osv.except_osv(_(u'Aviso'), _(u'O diário '+unicode(jornal.name)+u' não têm sequência de '
                                                    u'movimentos associada.'))

        else:
            anos_fut_id = db_sncp_despesa_compromisso_ano.search(cr, uid, [('compromisso_id', '=',
                                                                            vals['compromisso_id']),
                                                                           ('ano', '>', datetime.now().year)])

            if len(anos_fut_id) != 0:
                jornal = db_account_journal.browse(cr, uid, vals['diario_fut_id'])
                if jornal.sequence_id.id:
                    name = db_ir_sequence.next_by_id(cr, uid, jornal.sequence_id.id)
                    self.write(cr, uid, ids[0], {'compromisso': name})
                else:
                    raise osv.except_osv(_(u'Aviso'), _(u'O diário '+unicode(jornal.name)+u' não têm sequência de '
                                                        u'movimentos associada.'))
        if 'criar_compromisso' in context:
            return self.pool.get('sncp.despesa.cria.cab.com').insere_relacao(cr, uid, [context['criar_compromisso']],
                                                                             context)
        else:
            return self.imprimir_report(cr, uid, ids, context)

    def imprimir_report(self, cr, uid, ids, context=None):
        # Bloco de verificação de existencia de serviço
        cr.execute("""SELECT report_name FROM ir_act_report_xml WHERE model = 'sncp.despesa.compromisso'""")
        result = cr.fetchone()
        if result is None or result[0] is None:
            return self.pool.get('formulario.mensagem.despesa').wizard(cr, uid, ids, u'O relatório do compromisso não '
                                                                                     u'está definido. \n'
                                                                                     u'Contacte o Administrador do '
                                                                                     u'sistema.')
        else:
            datas = {'ids': ids,
                     'model': 'sncp.despesa.compromisso', }
            return {
                'type': 'ir.actions.report.xml',
                'nodestroy': True,
                'report_name': result[0],
                'datas': datas,
            }

    def compromisso_anul(self, cr, uid, ids, context=None):
        compromisso = self.browse(cr, uid, ids[0])
        cr.execute("""
                  SELECT anula_compromisso(%d)
                  """ % compromisso.id)
        mensagem = cr.fetchone()[0]
        if len(mensagem) > 0:
            raise osv.except_osv(_(mensagem), _(u''))

        # Apagar formulários
        db_formulario_sncp_despesa_compromisso_diario = self.pool.get('formulario.sncp.despesa.compromisso.diario')
        form_ids = db_formulario_sncp_despesa_compromisso_diario.search(cr, uid, [('compromisso_id', '=', ids[0])])
        db_formulario_sncp_despesa_compromisso_diario.unlink(cr, uid, form_ids)
        #

        return True

    def insere_linhas_historico(self, cr, uid, ids, vals):
        db_account_move_line = self.pool.get('account.move.line')
        db_sncp_orcamento_historico = self.pool.get('sncp.orcamento.historico')
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        db_account_move_line.create(cr, uid, {'account_id': vals['id_aa_deb1'], 'date': vals['dict']['date'],
                                              'journal_id': vals['dict']['journal_id'],
                                              'period_id': vals['dict']['period_id'], 'name': vals['dict']['ref'],
                                              'move_id': vals['move_id'], 'debit': vals['linha_fut'].montante,
                                              'organica_id': vals['linha_fut'].organica_id.id,
                                              'economica_id': vals['linha_fut'].economica_id.id,
                                              'funcional_id': vals['linha_fut'].funcional_id.id, })

        new_dit = {'account_id': vals['id_aa_cred1'],
                   'date': vals['dict']['date'],
                   'journal_id': vals['dict']['journal_id'],
                   'period_id': vals['dict']['period_id'],
                   'name': vals['dict']['ref'],
                   'move_id': vals['move_id'],
                   'credit': vals['linha_fut'].montante,
                   'organica_id': vals['linha_fut'].organica_id.id,
                   'economica_id': vals['linha_fut'].economica_id.id,
                   'funcional_id': vals['linha_fut'].funcional_id.id, }
        last_account_move_line_id = db_account_move_line.create(cr, uid, new_dit)

        send2 = {'name': vals['ano_fut'],
                 'categoria': '06futur',
                 'datahora': vals['dh'],
                 'organica_id': vals['linha_fut'].organica_id.id,
                 'economica_id': vals['linha_fut'].economica_id.id,
                 'funcional_id': vals['linha_fut'].funcional_id.id,
                 'centrocustos_id': None,
                 'montante': vals['linha_fut'].montante,
                 'cabimento_id': None,
                 'cabimento_linha_id': None,
                 'compromisso_id': ids[0],
                 'diferenca': 0.0,
                 'compromisso_linha_id': vals['linha_fut'].id,
                 'doc_contab_id': vals['move_id'],
                 'doc_contab_linha_id': last_account_move_line_id, }

        db_sncp_orcamento_historico.insere_valores_historico(cr, uid, [], send2)
        db_sncp_despesa_compromisso_linha.write(cr, uid, vals['linha_fut'].id, {'state_line': 'proc'})

    def prepare_linhas_historico(self, cr, uid, ids, vals):
        datacorrente = datetime.now()
        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')
        db_account_move = self.pool.get('account.move')
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        db_account_account = self.pool.get('account.account')

        dh = datetime.strptime(vals['datahora'], "%Y-%m-%d %H:%M:%S")
        ndata = date(dh.year, dh.month, dh.day)
        anos_futuros_id = db_sncp_despesa_compromisso_ano.search(cr, uid, [('compromisso_id', '=', ids[0]),
                                                                           ('ano', '>', datacorrente.year)])
        record_anos_futuros = db_sncp_despesa_compromisso_ano.browse(cr, uid, anos_futuros_id)

        dicti = db_account_move.account_move_prepare(cr, uid, vals['diario_fut_id'], ndata, vals['ref'])
        dicti['name'] = vals['ref']+' '+'futuro'
        move_id = db_account_move.create(cr, uid, dicti)
        for ano_fut in record_anos_futuros:
            dif_ano_fut_ano_atual = ano_fut.ano - datacorrente.year
            linhas_comp_fut_id = db_sncp_despesa_compromisso_linha.search(cr, uid, [('compromisso_ano_id', '=',
                                                                                     ano_fut.id)])
            linhas_comp_fut = db_sncp_despesa_compromisso_linha.browse(cr, uid, linhas_comp_fut_id)
            for linha_fut in linhas_comp_fut:
                if dif_ano_fut_ano_atual == 1:
                    id_aa_deb1 = db_account_account.search(cr, uid, [('code', '=', '041')])
                    id_aa_cred1 = db_account_account.search(cr, uid, [('code', '=', '051')])
                    para_hist = {'dict': dicti,
                                 'id_aa_deb1': id_aa_deb1[0], 'id_aa_cred1': id_aa_cred1[0],
                                 'move_id': move_id, 'linha_fut': linha_fut,
                                 'ano_fut': ano_fut.ano, 'dh': dh}
                    self.insere_linhas_historico(cr, uid, ids, para_hist)
                elif dif_ano_fut_ano_atual == 2:
                    id_aa_deb1 = db_account_account.search(cr, uid, [('code', '=', '042')])
                    id_aa_cred1 = db_account_account.search(cr, uid, [('code', '=', '052')])
                    para_hist = {'dict': dicti,
                                 'id_aa_deb1': id_aa_deb1[0], 'id_aa_cred1': id_aa_cred1[0],
                                 'move_id': move_id, 'linha_fut': linha_fut,
                                 'ano_fut': ano_fut.ano, 'dh': dh}
                    self.insere_linhas_historico(cr, uid, ids, para_hist)
                elif dif_ano_fut_ano_atual == 3:
                    id_aa_deb1 = db_account_account.search(cr, uid, [('code', '=', '043')])
                    id_aa_cred1 = db_account_account.search(cr, uid, [('code', '=', '053')])
                    para_hist = {'dict': dicti,
                                 'id_aa_deb1': id_aa_deb1[0], 'id_aa_cred1': id_aa_cred1[0],
                                 'move_id': move_id, 'linha_fut': linha_fut,
                                 'ano_fut': ano_fut.ano, 'dh': dh}
                    self.insere_linhas_historico(cr, uid, ids, para_hist)
                elif dif_ano_fut_ano_atual >= 4:
                    id_aa_deb1 = db_account_account.search(cr, uid, [('code', '=', '044')])
                    id_aa_cred1 = db_account_account.search(cr, uid, [('code', '=', '054')])
                    para_hist = {'dict': dicti,
                                 'id_aa_deb1': id_aa_deb1[0], 'id_aa_cred1': id_aa_cred1[0],
                                 'move_id': move_id, 'linha_fut': linha_fut,
                                 'ano_fut': ano_fut.ano, 'dh': dh}
                    self.insere_linhas_historico(cr, uid, ids, para_hist)

    def on_change_teste_ano_fim(self, cr, uid, ids, ano_ini, ano_fim):
        if ano_fim < ano_ini:
            return {'warning': {'title': u'Anos incompatíveis',
                                'message': u'O ano final tem que ser maior ou igual ao ano inicial.'}}
        else:
            return {'value': {}}

    def on_change_teste_ano_ini(self, cr, uid, ids, ano_ini, context=None):
        if datetime.now().year > ano_ini:
            return {'warning': {'title': u'Anos incompatíveis',
                                'message': u'Não pode criar os compromissos para os anos passados.'}}
        else:
            return {'value': {}}

    _columns = {
        'compromisso': fields.char(u'Compromisso', size=12),
        'name': fields.char(u'Referência', size=80),
        'desc2': fields.char(u'', size=80),
        'tipo': fields.selection([('com', u'Comum'),
                                  ('per', u'Permanente'),
                                  ('plu', u'Plurianual'),
                                  ('cal', u'Calendarizado'), ], u'Tipo de Compromisso'),
        'ano_ini': fields.integer(u'Ano de início', size=4),
        'ano_fim': fields.integer(u'Ano final', size=4),
        'partner_id': fields.many2one('res.partner', u'Parceiro', domain=[('supplier', '=', True)]),
        'obsv': fields.char(u'Observações'),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('proc', u'Processado'),
                                   ('anul', u'Anulado'), ], u'Estado'),
        'next': fields.integer(u'next'),
        # next 0 -- "Criar anos disponivel"
        # next 1 -- "Referenciar/associar disponivel
        # next 2 -- "Processar" disponivel
        'anos_id': fields.one2many('sncp.despesa.compromisso.ano', 'compromisso_id', u'Detalhes do ano'),
        'dados_adic_id': fields.one2many('sncp.despesa.compromisso.dados.adic', 'compromisso_id', u'Dados Adicionais'),
    }

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')
        anos_id = db_sncp_despesa_compromisso_ano.search(cr, uid, [('compromisso_id', '=', ids[0])])
        for ano in anos_id:
            db_sncp_despesa_compromisso_ano.unlink(cr, uid, [ano])
        return super(sncp_despesa_compromisso, self).unlink(cr, uid, ids, context=context)

    def sql_linhas_compromisso_ano_mm_dimensoes(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION linhas_compromisso_ano_mm_dimensoes(compromisso_ano_id integer) RETURNS varchar AS $$
        DECLARE
          linha_comp RECORD;
          mensagem varchar='';
          num_linhas integer;
        BEGIN
            FOR linha_comp IN (SELECT * FROM sncp_despesa_compromisso_linha AS CL WHERE CL.compromisso_ano_id=$1) LOOP
                num_linhas=(SELECT COUNT(id)
                      FROM sncp_despesa_compromisso_linha AS CL
                      WHERE CL.compromisso_ano_id=$1 AND CL.economica_id=linha_comp.economica_id AND
                      CL.organica_id=linha_comp.organica_id
                      AND ( (CL.funcional_id IS NULL AND linha_comp.funcional_id IS NULL) OR
                                (CL.funcional_id IS NOT NULL AND CL.funcional_id=linha_comp.funcional_id))
                        );
            IF num_linhas > 1 THEN
               mensagem='A combinação  Orgânica('
                         || (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id=linha_comp.organica_id) ||
                         ')/Económica(' ||
                     (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id=linha_comp.economica_id);
                IF linha_comp.funcional_id IS NULL THEN
                   mensagem= mensagem || ')/Funcional() encontra-se repetida';
                ELSE
                   mensagem=mensagem || ')/Funcional(' ||
                   (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_comp.funcional_id) ||')
                   encontra-se repetida';
                END IF;

            RETURN mensagem;
            END IF;
            END LOOP;
        RETURN mensagem;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_valida_montantes_agenda(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION valida_montantes_agenda(comp_id integer) RETURNS varchar AS
        $$
        DECLARE
            mensagem varchar='';
            compromisso_ano sncp_despesa_compromisso_ano%ROWTYPE;
            compromisso_linha sncp_despesa_compromisso_linha%ROWTYPE;
            montante_agenda numeric;
        BEGIN
             FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano WHERE compromisso_id=$1) LOOP
            FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha
            WHERE compromisso_ano_id=compromisso_ano.id) LOOP
                    montante_agenda=(SELECT COALESCE(SUM(montante),0.0) FROM sncp_despesa_compromisso_agenda
                                     WHERE compromisso_linha_id=compromisso_linha.id);
                    IF montante_agenda!=compromisso_linha.anual_prev THEN
                mensagem='A soma total dos montantes da agenda têm de ser igual ao anual
                          previsto para aquela linha do compromisso';
                END IF;
                    IF LENGTH(mensagem)>0 THEN
                    RETURN mensagem;
                END IF;
            END LOOP;
             END LOOP;
             RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_da_valor_comprometido_mes(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION da_valor_comprometido_mes(dt timestamp,comp_id integer) RETURNS numeric AS
        $$
        DECLARE
            data_ini timestamp;
        BEGIN
           data_ini=(EXTRACT(YEAR FROM $1) ||'-' || EXTRACT(MONTH FROM $1) || '-' ||1 || ' ' || 0 || ':'
               || 0 || ':' || 1)::TIMESTAMP;
        RETURN (SELECT COALESCE(SUM(MONTANTE),0.0)
               FROM sncp_orcamento_historico
               WHERE datahora >= data_ini AND datahora < $1 AND categoria = '05compr' AND compromisso_id <> $2);
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_da_valor_elegivel(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION da_valor_elegivel(linha_id integer,mes_atual integer) RETURNS numeric AS
        $$
        BEGIN
           IF $2<11 THEN
            RETURN (SELECT COALESCE(SUM(montante),0.0)
                FROM sncp_despesa_compromisso_agenda AS AGENDA
                WHERE (AGENDA.name BETWEEN $2 AND $2 + 2) AND compromisso_linha_id=$1
                   );
           ELSIF $2 = 11 THEN
               RETURN (SELECT COALESCE(SUM(montante),0.0)
                FROM sncp_despesa_compromisso_agenda AS AGENDA
                WHERE (AGENDA.name BETWEEN $2 AND $2 + 1) AND compromisso_linha_id=$1
                  );

           ELSE
              RETURN (  SELECT COALESCE(montante,0.0)
                FROM sncp_despesa_compromisso_agenda AS AGENDA
                WHERE AGENDA.name = $2 AND compromisso_linha_id=$1
                  );
           END IF;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_fundo_da_valor_disponivel(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION fundo_da_valor_disponivel(ano_atual integer,mes_atual integer) RETURNS numeric AS
        $$
        BEGIN
           RETURN (SELECT COALESCE(FUNDO.montante-FUNDO.reservado,0.0)
                   FROM sncp_despesa_fundos_disponiveis AS FUNDO
                   WHERE FUNDO.name=$1 and FUNDO.mes = $2
              );
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_ultima_atualizacao(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION ultima_atualizacao(tipo varchar,mes_atual integer,compromisso_id integer,
        ano integer,nmove_id integer) RETURNS boolean AS
        $$
        DECLARE
          compromisso_ano sncp_despesa_compromisso_ano%ROWTYPE;
          compromisso_linha sncp_despesa_compromisso_linha%ROWTYPE;
        BEGIN
           FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO WHERE COMPANO.compromisso_id=$3
           AND COMPANO.ano=$4) LOOP
              FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha AS COMPLINHA
              WHERE COMPLINHA.compromisso_ano_id=compromisso_ano.id ) LOOP
            IF $1 = 'per' OR $1 = 'cal' THEN
               IF $2 < 11 THEN
                UPDATE sncp_despesa_compromisso_agenda AS AGENDA SET last_doc_contab_id=$5
                WHERE AGENDA.compromisso_linha_id=compromisso_linha.id AND (AGENDA.name BETWEEN $2 + 1 AND $2 + 2);
               ELSIF $2 = 11 THEN
                UPDATE sncp_despesa_compromisso_agenda AS AGENDA SET last_doc_contab_id=$5
                WHERE AGENDA.compromisso_linha_id=compromisso_linha.id AND (AGENDA.name = $2 + 1);
               END IF;
            END IF;
            UPDATE sncp_despesa_compromisso_agenda AS AGENDA SET last_doc_contab_id=$5
                WHERE AGENDA.compromisso_linha_id=compromisso_linha.id AND AGENDA.name = $2;
              END LOOP;
           END LOOP;
           RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_linha_movimento_contabilistico_compromisso(self, cr):
        cr.execute("""
            CREATE OR REPLACE FUNCTION insere_linha_movimento_contabilistico_compromisso(conta_id integer,
            journal_id integer, date, ref character varying, move_id integer, valor numeric, organica_id integer,
            economica_id integer, funcional_id integer, deb_creb character varying, partner_id integer)
              RETURNS integer AS
            $$
            DECLARE
                periodo_id integer;
            BEGIN
            periodo_id = get_periodo($3);
            IF $10='credit' THEN
                INSERT INTO account_move_line(account_id,date,journal_id,period_id,name,move_id,credit,organica_id,
                economica_id,funcional_id,partner_id) VALUES($1,$3,$2,periodo_id,$4,$5,$6,$7,$8,$9,$11);
                RETURN (SELECT currval('account_move_line_id_seq'));
            ELSE
                INSERT INTO account_move_line(account_id,date,journal_id,period_id,name,move_id,debit,organica_id,
                economica_id,funcional_id,partner_id) VALUES($1,$3,$2,periodo_id,$4,$5,$6,$7,$8,$9,$11);
                RETURN (SELECT currval('account_move_line_id_seq'));
            END IF;
            END;
            $$  LANGUAGE plpgsql;
        """)
        return True

    def sql_contabiliza_compromisso(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION contabiliza_compromisso(comp_id integer,user_id integer,journal_id integer,dh varchar
        ,ref varchar,journal_fut_id integer) RETURNS varchar AS
        $$
        DECLARE
          dados_anos_futuros_min integer;
          dados_anos_futuros_max integer;
          texto_mov_futur varchar;
          compromisso sncp_despesa_compromisso%ROWTYPE;
          compromisso_ano_atual sncp_despesa_compromisso_ano%ROWTYPE;
          compromisso_ano_futuro sncp_despesa_compromisso_ano%ROWTYPE;
          compromisso_linha sncp_despesa_compromisso_linha%ROWTYPE;
          compromisso_linha_futuro sncp_despesa_compromisso_linha%ROWTYPE;
          mensagem varchar='';
          datahora timestamp;
          nano integer;
          ok boolean;
          move_futuro_ok boolean=FALSE;
          move_id integer;
          move_line_id integer;
          caldata date;
          val_disp numeric;
          val_comp_mes numeric;
          valor_elegivel numeric=0;
          da_val_eleg numeric;
          fundo_disponivel numeric;
          mes integer;
          dif_anos integer;
          array_mes varchar[]='{"Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro",
          "Outubro","Novembro","Dezembro"}';
          conta_credito integer;
          conta_debito integer;
        BEGIN
           datahora=$4::timestamp;
           caldata=$4::date;
           nano=EXTRACT(YEAR FROM datahora);
           mes=EXTRACT(MONTH FROM datahora);
           SELECT * INTO compromisso FROM sncp_despesa_compromisso WHERE id=$1;

           FOR compromisso_ano_atual IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO WHERE COMPANO.ano=nano
           AND COMPANO.compromisso_id = compromisso.id) LOOP
                move_id=insere_movimento_contabilistico($2,$3,caldata,$5,nano);

            FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha
            WHERE compromisso_ano_id=compromisso_ano_atual.id) LOOP
                   val_disp=da_valor_disponivel(compromisso_ano_atual.cabimento_id,compromisso_linha.linha,nano);
                   IF compromisso_linha.montante>val_disp THEN

                   mensagem='O Cabimento têm apenas disponível o montante de ' || to_char(ABS(val_disp),
                   '999G999G999G9990D00') || ' na linha ' || compromisso_linha.linha;
                IF LENGTH(mensagem)>0 THEN
                   RETURN mensagem;
                END IF;
               END IF;
               END LOOP;

               val_comp_mes=da_valor_comprometido_mes(datahora,compromisso.id);

               IF compromisso.tipo='com' or compromisso.tipo='plu' THEN
              valor_elegivel=(SELECT COALESCE(SUM(montante),0.0) FROM sncp_despesa_compromisso_linha
              WHERE compromisso_ano_id=compromisso_ano_atual.id);
               ELSE
              FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha
              WHERE compromisso_ano_id=compromisso_ano_atual.id) LOOP
                     da_val_eleg= da_valor_elegivel(compromisso_linha.id,mes);
                     valor_elegivel=valor_elegivel+da_val_eleg;
                  END LOOP;
               END IF;

               fundo_disponivel=fundo_da_valor_disponivel(nano,mes);

               IF val_comp_mes+valor_elegivel>fundo_disponivel THEN
              mensagem='Não há fundos disponíveis suficientes para o mês de '|| array_mes[mes] || ' de ' || nano;
              IF LENGTH(mensagem)>0 THEN
                RETURN mensagem;
              END IF;
               END IF;

               FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha
               WHERE compromisso_ano_id=compromisso_ano_atual.id) LOOP
              conta_debito=(SELECT default_debit_account_id FROM account_journal WHERE id=$3);
                  conta_credito=(SELECT default_credit_account_id FROM account_journal WHERE id=$3);
                  move_line_id=insere_linha_movimento_contabilistico_compromisso(conta_debito,$3,caldata,$5,
                  move_id,compromisso_linha.montante,compromisso_linha.organica_id,compromisso_linha.economica_id,
                  compromisso_linha.funcional_id,
                  'debit',compromisso.partner_id);
                  move_line_id=insere_linha_movimento_contabilistico_compromisso(conta_credito,$3,caldata,$5,
                  move_id,compromisso_linha.montante,compromisso_linha.organica_id,compromisso_linha.economica_id,
                  compromisso_linha.funcional_id,
                  'credit',compromisso.partner_id);
                  datahora=insere_linha_historico(nano,'05compr',datahora,compromisso_linha.organica_id,
                  compromisso_linha.economica_id,compromisso_linha.funcional_id,compromisso_linha.montante,move_id,
                  move_line_id,
                  NULL,NULL,NULL,compromisso.id,compromisso_linha.id);
                  ok=insere_linha_acumulados(nano,'05compr',compromisso_linha.organica_id,
                 compromisso_linha.economica_id,compromisso_linha.funcional_id,compromisso_linha.montante);
                 UPDATE sncp_despesa_compromisso_linha SET state_line='proc' WHERE id=compromisso_linha.id;
               END LOOP;

           UPDATE sncp_despesa_compromisso_ano SET estado = 2 WHERE id=compromisso_ano_atual.id;
           ok=atualizar_estado(compromisso_ano_atual.cabimento_id,nano);
           ok=ultima_atualizacao(compromisso.tipo,mes,compromisso.id,nano,move_id);
           END LOOP;

           FOR compromisso_ano_futuro IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO WHERE COMPANO.ano>nano
           AND COMPANO.compromisso_id = compromisso.id) LOOP
            IF move_futuro_ok=FALSE THEN
                dados_anos_futuros_min =(SELECT MIN(COMP_ANO.ano)
                                  FROM sncp_despesa_compromisso_ano AS COMP_ANO
                                  WHERE COMP_ANO.ano>nano
                                 AND COMP_ANO.compromisso_id = compromisso.id);
                dados_anos_futuros_max =(SELECT MAX(COMP_ANO.ano)
                                          FROM sncp_despesa_compromisso_ano AS COMP_ANO
                                          WHERE COMP_ANO.ano>nano
                                         AND COMP_ANO.compromisso_id = compromisso.id);

                IF dados_anos_futuros_min!=dados_anos_futuros_max THEN
                   texto_mov_futur=dados_anos_futuros_min::varchar || '-' || dados_anos_futuros_max::varchar;
                ELSE
                   texto_mov_futur=dados_anos_futuros_min::varchar;
                END IF;

                move_id=insere_movimento_contabilistico_compromisso($2,$6,caldata,$5,texto_mov_futur);
                move_futuro_ok=TRUE;
                END IF;
                dif_anos=compromisso_ano_futuro.ano-nano;
                FOR compromisso_linha_futuro IN (SELECT * FROM sncp_despesa_compromisso_linha
                WHERE compromisso_ano_id=compromisso_ano_futuro.id) LOOP
                   IF dif_anos=1 THEN
                    conta_debito=(SELECT id FROM account_account AS AA WHERE AA.code='041');
                    conta_credito=(SELECT id FROM account_account AS AA WHERE AA.code='051');
                    ELSIF dif_anos=2 THEN
                    conta_debito=(SELECT id FROM account_account AS AA WHERE AA.code='042');
                    conta_credito=(SELECT id FROM account_account AS AA WHERE AA.code='052');
                    ELSIF dif_anos=3 THEN
                    conta_debito=(SELECT id FROM account_account AS AA WHERE AA.code='043');
                    conta_credito=(SELECT id FROM account_account AS AA WHERE AA.code='053');
                    ELSIF dif_anos>=4 THEN
                    conta_debito=(SELECT id FROM account_account AS AA WHERE AA.code='044');
                    conta_credito=(SELECT id FROM account_account AS AA WHERE AA.code='054');
                  END IF;
                   move_line_id=insere_linha_movimento_contabilistico_compromisso(conta_debito,$6,caldata,$5,
                    move_id,compromisso_linha_futuro.montante,compromisso_linha_futuro.organica_id,
                    compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,
                  'debit',compromisso.partner_id);
                    move_line_id=insere_linha_movimento_contabilistico_compromisso(conta_credito,$6,caldata,$5,
                    move_id,compromisso_linha_futuro.montante,compromisso_linha_futuro.organica_id,
                    compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,
                  'credit',compromisso.partner_id);
                  datahora=insere_linha_historico(compromisso_ano_futuro.ano,'06futur',datahora,
                  compromisso_linha_futuro.organica_id,
                  compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,
                  compromisso_linha_futuro.montante,move_id,move_line_id,
                  NULL,NULL,NULL,compromisso.id,compromisso_linha_futuro.id);
                  ok=insere_linha_acumulados(compromisso_ano_futuro.ano,'06futur',compromisso_linha_futuro.organica_id,
                 compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,
                 compromisso_linha_futuro.montante);
                 UPDATE sncp_despesa_compromisso_linha SET state_line='proc' WHERE id=compromisso_linha_futuro.id;
                END LOOP;
           UPDATE sncp_despesa_compromisso_ano SET estado = 2 WHERE id=compromisso_ano_futuro.id;
           END LOOP;
           UPDATE sncp_despesa_compromisso SET state='proc' WHERE id=$1;
           RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_elimina_historico_comp(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION elimina_historico_comp(name integer,categoria varchar,compromisso_id integer)
        RETURNS boolean AS $$
        DECLARE
            lin sncp_orcamento_historico%ROWTYPE;
            ok boolean;
        BEGIN
             FOR lin in SELECT * FROM sncp_orcamento_historico AS SOH WHERE SOH.name = $1 AND SOH.categoria = $2
             AND SOH.compromisso_id=$3
             LOOP
             ok=elimina_acumulados(lin.name,lin.categoria,lin.organica_id,lin.economica_id,lin.funcional_id,
             lin.montante);
            DELETE FROM sncp_orcamento_historico WHERE id=lin.id;
             END LOOP;
        RETURN TRUE;
        END;$$ LANGUAGE plpgsql;
        """)
        return True

    def sql_anula_compromisso(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION anula_compromisso(comp_id integer) RETURNS varchar AS
        $$
        DECLARE
          mensagem varchar='';
          ok boolean;
          ano_atual integer;
          compromisso_relacoes sncp_despesa_compromisso_relacoes%ROWTYPE;
          compromisso_ano sncp_despesa_compromisso_ano%ROWTYPE;
          move_ano_atual integer;
          move_ano_futuro integer;
        BEGIN
           FOR compromisso_relacoes in (SELECT * FROM sncp_despesa_compromisso_relacoes COMPREL WHERE COMPREL.name=$1)
           LOOP
               mensagem='Não é possível anular. Ordem de compra ou fatura associada';
               IF LENGTH(mensagem)>0 THEN
                  RETURN mensagem;
               END IF;
           END LOOP;
           ano_atual=(SELECT EXTRACT(YEAR FROM datahora) FROM sncp_orcamento_historico WHERE compromisso_id=$1 LIMIT 1);

           move_ano_atual=(SELECT doc_contab_id FROM sncp_orcamento_historico AS SOH WHERE SOH.name=ano_atual
                              AND SOH.categoria='05compr' AND compromisso_id=$1
                              LIMIT 1);
           move_ano_futuro=(SELECT doc_contab_id FROM sncp_orcamento_historico AS SOH WHERE SOH.name>ano_atual
                              AND SOH.categoria='06futur' AND compromisso_id=$1
                              LIMIT 1);
           FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO
           WHERE COMPANO.compromisso_id=$1) LOOP
             IF compromisso_ano.ano = ano_atual THEN
            ok=elimina_historico_comp(compromisso_ano.ano,'05compr',$1);
            DELETE FROM sncp_despesa_compromisso_agenda WHERE compromisso_linha_id IN
            (SELECT id FROM sncp_despesa_compromisso_linha WHERE compromisso_ano_id=compromisso_ano.id);
             ELSE
                ok=elimina_historico_comp(compromisso_ano.ano,'06futur',$1);
             END IF;
             UPDATE sncp_despesa_compromisso_linha SET state_line='anul' WHERE compromisso_ano_id=compromisso_ano.id;
           END LOOP;
           IF move_ano_atual IS NOT NULL THEN
              DELETE FROM account_move_line AS ML WHERE ML.move_id=move_ano_atual;
              DELETE FROM account_move WHERE id= move_ano_atual;
           END IF;

           IF move_ano_futuro IS NOT NULL THEN
              DELETE FROM account_move_line AS ML WHERE ML.move_id=move_ano_futuro;
              DELETE FROM account_move WHERE id= move_ano_futuro;
           END IF;

           UPDATE sncp_despesa_compromisso SET state='anul' WHERE id=$1;
        RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_movimento_contabilistico_compromisso(self, cr):
        cr.execute("""
            CREATE OR REPLACE FUNCTION insere_movimento_contabilistico_compromisso(user_id integer, journal_id integer,
            date, ref character varying, texto varchar)
              RETURNS integer AS
            $$
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
                END;
            $$
            LANGUAGE plpgsql;
        """)
        return True

    def create(self, cr, uid, vals, context=None):
        test_partner_id(self, cr, uid, vals['partner_id'])
        self.teste_existencia_compromisso(cr)
        return super(sncp_despesa_compromisso, self).create(cr, uid, vals)

    _order = 'compromisso'
    _defaults = {'state': 'draft',
                 'next': 0,
                 'ano_ini': int(datetime.now().year),
                 'ano_fim': int(datetime.now().year),
                 'tipo': 'com', }

sncp_despesa_compromisso()
# ______________________________________________________________ANO_____________________________________________


class sncp_despesa_compromisso_ano(osv.Model):
    _name = 'sncp.despesa.compromisso.ano'
    _description = "Anos de Compromisso"

    def referenciar_cabimento(self, cr, uid, ids, context):
        db_sncp_despesa_compromisso = self.pool.get('sncp.despesa.compromisso')
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        db_sncp_despesa_cabimento_linha = self.pool.get('sncp.despesa.cabimento.linha')

        db_sncp_despesa_compromisso.write(cr, uid, context['compromisso_id'], {'next': 2})

        anos_ids = self.search(cr, uid, [('compromisso_id', '=', context['compromisso_id'])])
        self.write(cr, uid, anos_ids, {'next_comp': 2})

        for ano in self.browse(cr, uid, anos_ids):

            linhas_ids = db_sncp_despesa_cabimento_linha.search(cr, uid, [('cabimento_id', '=',
                                                                           context['cabimento_id'])])
            linhas = db_sncp_despesa_cabimento_linha.browse(cr, uid, linhas_ids)
            compromisso = db_sncp_despesa_compromisso.browse(cr, uid, context['compromisso_id'])
            for lin in linhas:
                linha_comp_id = db_sncp_despesa_compromisso_linha.create(cr, uid, {
                    'linha': despesa.get_sequence(self, cr, uid, context, 'comp_ano', ano.id),
                    'compromisso_ano_id': ano.id,
                    'organica_id': lin.organica_id.id,
                    'economica_id': lin.economica_id.id,
                    'funcional_id': lin.funcional_id.id, }, context=context)

                if ano.ano == compromisso.ano_ini:
                    db_sncp_despesa_compromisso_linha.write(cr, uid, linha_comp_id, {'estado': 1})

                obj_agenda = self.pool.get('sncp.despesa.compromisso.agenda')
                # ####### CRIAÇÃO DE MESES NA AGENDA
                for mes in range(1, 13):
                    obj_agenda.create(cr, uid, {'name': mes, 'compromisso_linha_id': linha_comp_id})

        cr.execute(""" UPDATE sncp_despesa_compromisso_ano SET cabimento_id=NULL
                       WHERE compromisso_id=%d""" % context['compromisso_id'])

        return True

    def calcula_data(self, cr, uid, mes, ano):
        db_sncp_comum_feriados = self.pool.get('sncp.comum.feriados')
        if mes + 1 > 12:
            ano += 1
            mes = 1
        else:
            mes += 1

        data = date(ano, mes, 1)-timedelta(days=1)

        while data.weekday() >= 5 or len(db_sncp_comum_feriados.search(cr, uid, [('data', '=', unicode(data))])) != 0:
                data = data-timedelta(days=1)

        return data

    def criar_linha_compromisso(self, cr, uid, ids, context):

        db_sncp_despesa_compromisso = self.pool.get('sncp.despesa.compromisso')
        db_sncp_despesa_compromisso.write(cr, uid, context['compromisso_id'], {'next': 2})

        # -- TIPO PLURIANUAL ANO INICIAL > ANO ACTUAL
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        if context['tipo'] == 'plu' and context['ano'] > datetime.now().year:
            anos_ids = self.search(cr, uid, [('compromisso_id', '=', context['compromisso_id'])])
            for ano in self.browse(cr, uid, anos_ids):
                diti = {'linha': despesa.get_sequence(self, cr, uid, context, 'comp_ano', ano.id),
                        'compromisso_ano_id': ano.id}
                linha_comp_id = db_sncp_despesa_compromisso_linha.create(cr, uid, diti)

                if ano.editar == 2:
                    db_sncp_despesa_compromisso_linha.write(cr, uid, linha_comp_id, {'estado': 2})

                obj_agenda = self.pool.get('sncp.despesa.compromisso.agenda')
                for mes in range(1, 13):
                    data = self.calcula_data(cr, uid, mes, ano.ano)
                    obj_agenda.create(cr, uid, {'data_prevista': data, 'name': mes,
                                                'compromisso_linha_id': linha_comp_id})
            return True

        # -- ANO INICIAL == ANO ACTUAL PARA TODOS OS TIPOS
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        db_sncp_despesa_cabimento_linha = self.pool.get('sncp.despesa.cabimento.linha')
        anos_ids = self.search(cr, uid, [('compromisso_id', '=', context['compromisso_id'])])
        self.write(cr, uid, anos_ids, {'estado': 1})
        for ano in self.browse(cr, uid, anos_ids):
            if ano.ano == date.today().year:
                self.write(cr, uid, ano.id, {'cabimento_id':  context['cabimento_id']})
            linhas_ids = db_sncp_despesa_cabimento_linha.search(cr, uid,
                                                                [('cabimento_id', '=', context['cabimento_id'])])
            linhas = db_sncp_despesa_cabimento_linha.browse(cr, uid, linhas_ids)
            for lin in linhas:
                if ano.ano == date.today().year:
                    cr.execute("""
                    SELECT da_valor_disponivel(%d,%d,%d)
                    """ % (context['cabimento_id'], lin.linha, ano.ano))
                    val_disponivel = cr.fetchone()[0]

                linha_comp_id = db_sncp_despesa_compromisso_linha.create(cr, uid, {'linha': lin.linha,
                                                                                   'compromisso_ano_id': ano.id,
                                                                                   'organica_id': lin.organica_id.id,
                                                                                   'economica_id': lin.economica_id.id,
                                                                                   'funcional_id': lin.funcional_id.id},
                                                                         context=context)

                if ano.ano == date.today().year:
                    if context['tipo'] == 'com':
                        db_sncp_despesa_compromisso_linha.write(cr, uid, linha_comp_id, {'montante': val_disponivel,
                                                                                         'anual_prev': val_disponivel})

                if ano.editar != 0:
                    db_sncp_despesa_compromisso_linha.write(cr, uid, linha_comp_id, {'estado': 1})

                obj_agenda = self.pool.get('sncp.despesa.compromisso.agenda')
                # ####### CRIAÇÃO DE MESES NA AGENDA
                if context['ano'] == datetime.now().year:
                    if context['tipo'] == 'com':
                        data = self.calcula_data(cr, uid, datetime.now().month, ano.ano)
                        obj_agenda.create(cr, uid, {'data_prevista': data,
                                                    'name': datetime.now().month,
                                                    'compromisso_linha_id': linha_comp_id,
                                                    'montante': val_disponivel})
                    else:
                        for mes in range(datetime.now().month, 13):
                            data = self.calcula_data(cr, uid, mes, ano.ano)
                            obj_agenda.create(cr, uid, {'data_prevista': data, 'name': mes,
                                                        'compromisso_linha_id': linha_comp_id})
                else:
                    for mes in range(1, 13):
                        data = self.calcula_data(cr, uid, mes, ano.ano)
                        obj_agenda.create(cr, uid, {'data_prevista': data,
                                                    'name': mes, 'compromisso_linha_id': linha_comp_id})
        return True

    def atualiza_montantes_linhas_historico(self, cr, uid, ids, vals):
        db_account_move_line = self.pool.get('account.move.line')
        db_sncp_orcamento_historico = self.pool.get('sncp.orcamento.historico')
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        db_sncp_despesa_compromisso = self.pool.get('sncp.despesa.compromisso')
        comp = db_sncp_despesa_compromisso.browse(cr, uid, ids[0])
        db_account_move_line.create(cr, uid, {'account_id': vals['id_aa_deb1'], 'date': vals['dict']['date'],
                                              'journal_id': vals['dict']['journal_id'],
                                              'period_id': vals['dict']['period_id'], 'name': vals['dict']['ref'],
                                              'move_id': vals['move_id'], 'debit': abs(vals['diferenca']),
                                              'organica_id': vals['linha_fut'].organica_id.id,
                                              'economica_id': vals['linha_fut'].economica_id.id,
                                              'funcional_id': vals['linha_fut'].funcional_id.id,
                                              'partner_id': comp.partner_id.id})
        last_account_move_line_id = db_account_move_line.create(cr, uid,
                                                                {'account_id': vals['id_aa_cred1'],
                                                                 'date': vals['dict']['date'],
                                                                 'journal_id': vals['dict']['journal_id'],
                                                                 'period_id': vals['dict']['period_id'],
                                                                 'name': vals['dict']['ref'],
                                                                 'move_id': vals['move_id'],
                                                                 'credit': abs(vals['diferenca']),
                                                                 'organica_id': vals['linha_fut'].organica_id.id,
                                                                 'economica_id': vals['linha_fut'].economica_id.id,
                                                                 'funcional_id': vals['linha_fut'].funcional_id.id,
                                                                 'partner_id': comp.partner_id.id})
        send = {'name': vals['ano_fut'],
                'categoria': '06futur',
                'datahora': vals['dh'],
                'organica_id': vals['linha_fut'].organica_id.id,
                'economica_id': vals['linha_fut'].economica_id.id,
                'funcional_id': vals['linha_fut'].funcional_id.id,
                'centrocustos_id': None,
                'montante': vals['linha_fut'].montante,
                'diferenca': vals['diferenca'],
                'cabimento_id': None,
                'cabimento_linha_id': None,
                'compromisso_id': ids[0],
                'compromisso_linha_id': vals['linha_fut'].id,
                'doc_contab_id': vals['move_id'],
                'doc_contab_linha_id': last_account_move_line_id,
                }

        db_sncp_orcamento_historico.insere_valores_historico(cr, uid, [], send)
        db_sncp_despesa_compromisso_linha.write(cr, uid, vals['linha_fut'].id, {'state_line': 'proc'})

    def prepara_linhas_historico(self, cr, uid, ids, vals, diferenca_linhas):
        datacorrente = datetime.now()
        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')
        db_account_move = self.pool.get('account.move')
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        db_account_account = self.pool.get('account.account')

        dh = datetime.strptime(vals['datahora'], "%Y-%m-%d %H:%M:%S")
        ndata = date(dh.year, dh.month, dh.day)
        anos_futuros_id = db_sncp_despesa_compromisso_ano.search(cr, uid, [('compromisso_id', '=', ids[0]),
                                                                           ('ano', '>', datacorrente.year)])

        anos_futuros = db_sncp_despesa_compromisso_ano.browse(cr, uid, anos_futuros_id)
        dicti = db_account_move.account_move_prepare(cr, uid, vals['diario_fut_id'], ndata, vals['ref'])
        dicti['name'] = vals['ref']+' '+'futuro'
        move_id = db_account_move.create(cr, uid, dicti)
        for ano_fut in anos_futuros:
            dif_ano_fut_ano_atual = ano_fut.ano-datacorrente.year
            linhas_comp_fut_id = db_sncp_despesa_compromisso_linha.search(cr, uid, [('compromisso_ano_id', '=',
                                                                                     ano_fut.id)])
            linhas_comp_fut = db_sncp_despesa_compromisso_linha.browse(cr, uid, linhas_comp_fut_id)
            for linha_fut in linhas_comp_fut:
                    if dif_ano_fut_ano_atual == 1:
                        id_aa_deb1 = db_account_account.search(cr, uid, [('code', '=', '041')])
                        id_aa_cred1 = db_account_account.search(cr, uid, [('code', '=', '051')])
                        dicionario = diferenca_linhas[ano_fut.ano]
                        dif = dicionario[linha_fut.id]
                        para_hist = {'dict': dicti,
                                     'id_aa_deb1': id_aa_deb1[0], 'id_aa_cred1': id_aa_cred1[0],
                                     'move_id': move_id, 'linha_fut': linha_fut,
                                     'ano_fut': ano_fut.ano, 'dh': dh, 'diferenca': dif}
                        self.atualiza_montantes_linhas_historico(cr, uid, ids, para_hist)
                    elif dif_ano_fut_ano_atual == 2:
                        id_aa_deb1 = db_account_account.search(cr, uid, [('code', '=', '042')])
                        id_aa_cred1 = db_account_account.search(cr, uid, [('code', '=', '052')])
                        dicionario = diferenca_linhas[ano_fut.ano]
                        dif = dicionario[linha_fut.id]
                        para_hist = {'dict': dicti,
                                     'id_aa_deb1': id_aa_deb1[0], 'id_aa_cred1': id_aa_cred1[0],
                                     'move_id': move_id, 'linha_fut': linha_fut,
                                     'ano_fut': ano_fut.ano, 'dh': dh, 'diferenca': dif}
                        self.atualiza_montantes_linhas_historico(cr, uid, ids, para_hist)

                    elif dif_ano_fut_ano_atual == 3:
                        id_aa_deb1 = db_account_account.search(cr, uid, [('code', '=', '043')])
                        id_aa_cred1 = db_account_account.search(cr, uid, [('code', '=', '053')])
                        dicionario = diferenca_linhas[ano_fut.ano]
                        dif = dicionario[linha_fut.id]
                        para_hist = {'dict': dicti,
                                     'id_aa_deb1': id_aa_deb1[0], 'id_aa_cred1': id_aa_cred1[0],
                                     'move_id': move_id, 'linha_fut': linha_fut,
                                     'ano_fut': ano_fut.ano, 'dh': dh, 'diferenca': dif}
                        self.atualiza_montantes_linhas_historico(cr, uid, ids, para_hist)

                    elif dif_ano_fut_ano_atual >= 4:
                        id_aa_deb1 = db_account_account.search(cr, uid, [('code', '=', '044')])
                        id_aa_cred1 = db_account_account.search(cr, uid, [('code', '=', '054')])
                        dicionario = diferenca_linhas[ano_fut.ano]
                        dif = dicionario[linha_fut.id]
                        para_hist = {'dict': dicti,
                                     'id_aa_deb1': id_aa_deb1[0], 'id_aa_cred1': id_aa_cred1[0],
                                     'move_id': move_id, 'linha_fut': linha_fut,
                                     'ano_fut': ano_fut.ano, 'dh': dh, 'diferenca': dif}
                        self.atualiza_montantes_linhas_historico(cr, uid, ids, para_hist)

    def atualizar_montantes(self, cr, uid, ids, context):
        # ##### SQL CALL FUNCTION

        cr.execute("""
                   SELECT valida_montantes_agenda(%d)
                   """ % context['compromisso_id'])

        mensagem = cr.fetchone()[0]
        if len(mensagem) > 0:
            raise osv.except_osv(_(mensagem), _(u''))

        db_sncp_despesa_compromisso = self.pool.get('sncp.despesa.compromisso')
        formulario_compromisso = self.pool.get('formulario.sncp.despesa.compromisso.diario')
        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        db_sncp_orcamento_historico = self.pool.get('sncp.orcamento.historico')
        db_account_move = self.pool.get('account.move')
        db_account_journal = self.pool.get('account.journal')
        db_account_move_line = self.pool.get('account.move.line')
        form_ids = formulario_compromisso.search(cr, uid, [('compromisso_id', '=', context['compromisso_id'])])
        obj = formulario_compromisso.browse(cr, uid, max(form_ids))
        vals = dict()
        vals['ref'] = obj.name
        vals['datahora'] = obj.datahora
        vals['dia_mes_pag'] = obj.dia_mes_pag
        vals['diario_id'] = obj.diario_id.id
        vals['diario_fut_id'] = obj.diario_fut_id.id
        comp = db_sncp_despesa_compromisso.browse(cr, uid, context['compromisso_id'])
        diferenca_linhas = {}
        datacorrente = datetime.now()
        move_id = False

        anos_id = db_sncp_despesa_compromisso_ano.search(cr, uid, [('compromisso_id', '=', comp.id)])
        anos = db_sncp_despesa_compromisso_ano.browse(cr, uid, anos_id)
        anos_futuros_id = db_sncp_despesa_compromisso_ano.search(cr, uid, [('compromisso_id', '=', comp.id),
                                                                           ('ano', '>', datacorrente.year)])
        ano_atual_id = db_sncp_despesa_compromisso_ano.search(cr, uid, [('compromisso_id', '=', comp.id),
                                                                        ('ano', '=', datacorrente.year)])

        for ano in anos:
            dicionario = {}
            linhas_comp_id = db_sncp_despesa_compromisso_linha.search(cr, uid, [('compromisso_ano_id', '=', ano.id)])
            linhas_comp = db_sncp_despesa_compromisso_linha.browse(cr, uid, linhas_comp_id)
            for linha_comp in linhas_comp:
                if ano.ano == datacorrente.year:
                    linha_comp_hist_id = db_sncp_orcamento_historico.search(cr, uid,
                                                                            [('name', '=', ano.ano),
                                                                             ('categoria', '=', '05compr'),
                                                                             ('organica_id', '=',
                                                                              linha_comp.organica_id.id),
                                                                             ('economica_id', '=',
                                                                              linha_comp.economica_id.id),
                                                                             ('funcional_id', '=',
                                                                              linha_comp.funcional_id.id)])
                    linha_comp_hist = db_sncp_orcamento_historico.browse(cr, uid, linha_comp_hist_id[0])

                    aux = decimal.Decimal(unicode(linha_comp.montante - linha_comp_hist.montante))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    diferenca = float(aux)

                    dicionario[linha_comp.id] = diferenca
                else:
                    linha_comp_hist_id = db_sncp_orcamento_historico.search(cr, uid,
                                                                            [('name', '=', ano.ano),
                                                                             ('categoria', '=', '06futur'),
                                                                             ('organica_id', '=',
                                                                              linha_comp.organica_id.id),
                                                                             ('economica_id', '=',
                                                                              linha_comp.economica_id.id),
                                                                             ('funcional_id',
                                                                              '=',
                                                                              linha_comp.funcional_id.id)])
                    linha_comp_hist = db_sncp_orcamento_historico.browse(cr, uid, linha_comp_hist_id[0])

                    aux = decimal.Decimal(unicode(linha_comp.montante - linha_comp_hist.montante))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    diferenca = float(aux)

                    dicionario[linha_comp.id] = diferenca
            diferenca_linhas[ano.ano] = dicionario

        num_dicionarios_com_diferencas_zero = 0
        for ano in anos:
            lista = diferenca_linhas[ano.ano].values()
            zeros = 0
            for elem in lista:
                if elem == 0.0:
                    zeros += 1

            if zeros == len(lista):
                num_dicionarios_com_diferencas_zero += 1

        if num_dicionarios_com_diferencas_zero != len(diferenca_linhas):
            if len(ano_atual_id) != 0:
                ano_atual = db_sncp_despesa_compromisso_ano.browse(cr, uid, ano_atual_id[0])
                linhas_comp_ano_atual_id = db_sncp_despesa_compromisso_linha.search(cr, uid,
                                                                                    [('compromisso_ano_id', '=',
                                                                                      ano_atual.id)])
                linhas_comp_ano_atual = db_sncp_despesa_compromisso_linha.browse(cr, uid, linhas_comp_ano_atual_id)
                for linha_comp_ano_atual in linhas_comp_ano_atual:

                    # ##### SQL CALL FUNCTION
                    cr.execute("""
                    SELECT da_valor_disponivel(%d,%d,%d)
                    """ % (ano_atual.cabimento_id.id, linha_comp_ano_atual.linha, ano_atual.ano))

                    val_disponivel = cr.fetchone()[0]

                    dicionario = diferenca_linhas[ano_atual.ano]
                    if dicionario[linha_comp_ano_atual.id] > val_disponivel:
                        raise osv.except_osv(_(u'Aviso'),
                                             _(u'O valor remanescente no cabimento é de apenas '
                                               + unicode(val_disponivel)+u'.'))

                # ##### SQL CALL FUNCTION
                cr.execute("""
                SELECT da_valor_comprometido_mes('%s',%d)
                """ % (vals['datahora'], comp.id))
                valcompmes = cr.fetchone()[0]
                valorelegivel = 0
                for linha_comp in linhas_comp_ano_atual:
                    valorelegivel += linha_comp.montante

                aux = decimal.Decimal(unicode(valorelegivel))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                valorelegivel = float(aux)

                send = {'name': ano_atual.ano, 'mes': datacorrente.month}
                mes = {1: u'Janeiro', 2: u'Fevereiro', 3: u'Março', 4: u'Abril',
                       5: u'Maio', 6: u'Junho', 7: u'Julho', 8: u'Agosto',
                       9: u'Setembro', 10: u'Outubro', 11: u'Novembro', 12: u'Dezembro'}
                # ##### SQL CALL FUNCTION
                cr.execute("""
                SELECT fundo_da_valor_disponivel(%d,%d)
                """ % (ano_atual.ano, datacorrente.month))
                fundo_disponivel = cr.fetchone()[0]
                if valcompmes + valorelegivel > fundo_disponivel:
                    raise osv.except_osv(_(u'Aviso'),
                                         _(u'Não há fundos disponíveis suficientes para o mês de '
                                           + mes[send['mes']]+u' de '+unicode(vals['name'])+u'.'))

                dh = datetime.strptime(vals['datahora'], "%Y-%m-%d %H:%M:%S")
                ndata = date(dh.year, dh.month, dh.day)
                ano = ndata.year
                dicti = db_account_move.account_move_prepare(cr, uid, vals['diario_id'], ndata, vals['ref'])
                dicti['name'] = vals['ref']+' '+unicode(ano)
                move_id = db_account_move.create(cr, uid, dicti)

                for linha_comp in linhas_comp_ano_atual:
                    jornal = db_account_journal.browse(cr, uid, vals['diario_id'])
                    if jornal.default_credit_account_id.id is False and jornal.default_debit_account_id.id is False:
                        raise osv.except_osv(_(u'Aviso'),
                                             _(u'Defina a conta a débito e/ou a crédito do diário '+
                                               unicode(obj.diario_id.name) + u'.'))

                    mont_dif = abs(diferenca_linhas[linha_comp.compromisso_ano_id.ano][linha_comp.id])
                    db_account_move_line.create(cr, uid, {'account_id': jornal.default_debit_account_id.id,
                                                          'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                                          'period_id': dicti['period_id'], 'name': dicti['ref'],
                                                          'move_id': move_id, 'debit': mont_dif,
                                                          'organica_id': linha_comp.organica_id.id,
                                                          'economica_id': linha_comp.economica_id.id,
                                                          'funcional_id': linha_comp.funcional_id.id,
                                                          'partner_id': comp.partner_id.id})

                    new_dt = {'account_id': jornal.default_credit_account_id.id,
                              'date': dicti['date'],
                              'journal_id': dicti['journal_id'],
                              'period_id': dicti['period_id'],
                              'name': dicti['ref'],
                              'move_id': move_id,
                              'credit': mont_dif,
                              'organica_id': linha_comp.organica_id.id,
                              'economica_id': linha_comp.economica_id.id,
                              'funcional_id': linha_comp.funcional_id.id,
                              'partner_id': comp.partner_id.id}
                    last_account_move_line_id = db_account_move_line.create(cr, uid, new_dt)

                    dicionario = diferenca_linhas[ano_atual.ano]
                    dif = dicionario[linha_comp.id]

                    send = {
                        'name': ano, 'categoria': '05compr', 'datahora': dh,
                        'organica_id': linha_comp.organica_id.id, 'economica_id': linha_comp.economica_id.id,
                        'funcional_id': linha_comp.funcional_id.id, 'centrocustos_id': None,
                        'montante': linha_comp.montante, 'cabimento_id': None, 'diferenca': dif,
                        'cabimento_linha_id': None, 'compromisso_id': comp.id,
                        'compromisso_linha_id': linha_comp.id, 'doc_contab_id': move_id,
                        'doc_contab_linha_id': last_account_move_line_id}
                    db_sncp_orcamento_historico.insere_valores_historico(cr, uid, [], send)
                    db_sncp_despesa_compromisso_linha.write(cr, uid, linha_comp.id, {'state_line': 'proc'})

                if len(anos_futuros_id) != 0:
                    self.prepara_linhas_historico(cr, uid, [context['compromisso_id']], vals, diferenca_linhas)
            else:
                if len(anos_futuros_id) != 0:
                    self.prepara_linhas_historico(cr, uid, [context['compromisso_id']], vals, diferenca_linhas)

            db_sncp_despesa_compromisso.write(cr, uid, [comp.id], {'state': 'proc'})
            if len(ano_atual_id) != 0:
                record_ano_atual = db_sncp_despesa_compromisso_ano.browse(cr, uid, ano_atual_id[0])
                # ##### SQL CALL FUNCTION
                cr.execute("""
                SELECT atualizar_estado(%d,%d)
                """ % (record_ano_atual.cabimento_id.id, record_ano_atual.ano))
                # ##### SQL CALL FUNCTION
                cr.execute("""
                SELECT ultima_atualizacao('%s',%d,%d,%d,%d)
                """ % (comp.tipo, datacorrente.month, comp.id, record_ano_atual.ano, move_id))

    def get_comp_tipo(self, cr, uid, ids, fields, arg, context):
        comp_tipo = {}
        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')
        for comp_ano_id in ids:
            obj = db_sncp_despesa_compromisso_ano.browse(cr, uid, comp_ano_id)
            comp_tipo[comp_ano_id] = obj.compromisso_id.tipo or None
        return comp_tipo

    def get_comp_next(self, cr, uid, ids, fields, arg, context):
        comp_tipo = {}
        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')
        for comp_ano_id in ids:
            obj = db_sncp_despesa_compromisso_ano.browse(cr, uid, comp_ano_id)
            comp_tipo[comp_ano_id] = obj.compromisso_id.next or False
        return comp_tipo

    def get_comp_state(self, cr, uid, ids, fields, arg, context):
        comp_tipo = {}
        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')
        for comp_ano_id in ids:
            obj = db_sncp_despesa_compromisso_ano.browse(cr, uid, comp_ano_id)
            comp_tipo[comp_ano_id] = obj.compromisso_id.state or None
        return comp_tipo

    _columns = {
        'compromisso_id': fields.many2one('sncp.despesa.compromisso', u'Compromisso'),
        'ano': fields.integer('Ano', size=4),
        'cabimento_id': fields.many2one('sncp.despesa.cabimento', u'Cabimento', domain=[('origem_id', '=', None),
                                                                                        ('state', '=', 'cont'), ]),
        'linha_comp_id': fields.one2many('sncp.despesa.compromisso.linha', 'compromisso_ano_id',
                                         u'Detalhes das linhas'),
        'name': fields.char(u'Observações'),
        'tipo_comp': fields.function(get_comp_tipo, arg=None, method=False, type="char",
                                     store=True),
        'estado': fields.integer(u'Estado'),
        # 0  -- o botao "Criar Linhas" disponivel
        # 1  -- as linhas são editaveis
        # 2 -- contabilizado, "Atualizar montantes montantes" disponivel
        'editar': fields.integer(u'Editar'),
        # 0 -- outros anos
        # 1 -- ano atual
        # 2 -- primeiro dos futuros
        'next_comp': fields.function(get_comp_next, arg=None, method=False, type="integer",
                                     store=True),
        'state_comp': fields.function(get_comp_state, arg=None, method=False, type="char",
                                      store=True),
        }

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        linhas_comp_id = db_sncp_despesa_compromisso_linha.search(cr, uid, [('compromisso_ano_id', '=', ids[0])])
        for linha_comp in linhas_comp_id:
            db_sncp_despesa_compromisso_linha.unlink(cr, uid, [linha_comp])
        return super(sncp_despesa_compromisso_ano, self).unlink(cr, uid, ids, context=context)

    _order = 'ano'

    _defaults = {'editar': 0, 'estado': 0}

    def _mesmo_id_organica_economica_funcional(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT linhas_compromisso_ano_mm_dimensoes(%d)
        """ % obj.id)

        mensagem = cr.fetchone()[0]
        if len(mensagem) != 0:
            raise osv.except_osv(_(mensagem), _(u''))

        return True

    def _cabimento_mesmo_ano(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])
        if record.cabimento_id.id is not False:

            data_cab = datetime.strptime(record.cabimento_id.data, "%Y-%m-%d").date()
            if record.compromisso_id.ano_ini > data_cab.year and record.compromisso_id.state == 'draft':
                return True

            if record.ano == data_cab.year:
                return True

            else:
                raise osv.except_osv(_(u'Aviso'), _(u'O ano de contabilização do cabimento '
                                                    u'não corresponde ao ano do compromisso.'))

        else:
            return True

    _constraints = [
        (_mesmo_id_organica_economica_funcional, u'', ['linha_comp_id.montante']),
        (_cabimento_mesmo_ano, u'', ['cabimento_id'])]

sncp_despesa_compromisso_ano()
# ______________________________________________________________ LINHA__________________________________________


class sncp_despesa_compromisso_linha(osv.Model):
    _name = 'sncp.despesa.compromisso.linha'
    _description = "Linhas de Compromisso"

    def on_change_dim(self, cr, uid, ids, comp_id, linha, dim_id, dim):
        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')

        anos_id = db_sncp_despesa_compromisso_ano.search(cr, uid, [('compromisso_id', '=', comp_id)])

        for ano in db_sncp_despesa_compromisso_ano.browse(cr, uid, anos_id):
            linha_id = db_sncp_despesa_compromisso_linha.search(cr, uid, [('compromisso_ano_id', '=', ano.id),
                                                                          ('linha', '=', linha)])
            db_sncp_despesa_compromisso_linha.write(cr, uid, linha_id, {dim: dim_id})
        return {}

    def on_change_montante(self, cr, uid, ids, montante, context=None):
        record = self.browse(cr, uid, ids[0])
        if montante <= 0.0:
            raise osv.except_osv(_(u'Aviso'), _(u'Montante da linha do compromisso deve ser positivo.'))

        if record.tipo_comp in ['com', 'plu']:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'montante': montante, 'anual_prev': montante, })

            return {'value': {'montante': montante, 'anual_prev': montante, }}
        else:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'montante': montante, })
            return {'value': {'montante': montante, }}

    def _anual_prev_sup_igual_montante(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])

        if record.tipo_comp in ['per', 'cal']:
            if record.anual_prev < record.montante:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u' Caso o tipo seja permanente\nou calendarizado o anual previsto '
                                       u'deve ser igual ou superior ao montante da linha do compromisso.'))

        return True

    def on_change_anual_prev(self, cr, uid, ids, anual_prev, montante, context=None):
        db_sncp_despesa_compromisso_agenda = self.pool.get('sncp.despesa.compromisso.agenda')
        record = self.browse(cr, uid, ids[0])
        if record.tipo_comp not in ['com', 'plu']:
            if anual_prev < montante:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Caso o tipo seja permanente\nou calendarizado o anual previsto '
                                       u'deve ser igual ou superior ao montante da linha do compromisso.'))

            if len(ids) != 0:
                self.write(cr, uid, ids, {'anual_prev': anual_prev})

            cr.execute("""
                     SELECT id
                     FROM sncp_despesa_compromisso_agenda
                     WHERE compromisso_linha_id=%d
                     ORDER BY id
                 """ % ids[0])

            lista = cr.fetchall()

            val_mes = anual_prev/len(lista)

            aux = decimal.Decimal(unicode(val_mes))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            val_mes = float(aux)

            soma = 0.0
            agendas = []
            for agenda_id in lista:
                agenda = db_sncp_despesa_compromisso_agenda.browse(cr, uid, agenda_id[0])
                if agenda.name != 12:
                    soma += val_mes
                    db_sncp_despesa_compromisso_agenda.write(cr, uid, agenda.id, {'montante': val_mes})
                    agendas.append(agenda.id)

            aux = decimal.Decimal(unicode(soma))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            soma = float(aux)

            final_val = anual_prev-soma
            aux = decimal.Decimal(unicode(final_val))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            final_val = float(aux)

            db_sncp_despesa_compromisso_agenda.write(cr, uid, lista[len(lista)-1], {'montante': final_val})
            agendas.append(lista[len(lista)-1][0])

            return {'value': {'anual_prev': anual_prev, 'agenda_id': agendas}}
        return {}

    def get_comp_tipo(self, cr, uid, ids, fields, arg, context):
        comp_tipo = {}
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        for comp_linha_id in ids:
            obj = db_sncp_despesa_compromisso_linha.browse(cr, uid, comp_linha_id)
            comp_tipo[comp_linha_id] = obj.compromisso_ano_id.compromisso_id.tipo or None
        return comp_tipo

    def get_comp_ano_estado_ano(self, cr, uid, ids, fields, arg, context):
        estado_ano = {}
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        for comp_linha_id in ids:
            obj = db_sncp_despesa_compromisso_linha.browse(cr, uid, comp_linha_id)
            estado_ano[comp_linha_id] = obj.compromisso_ano_id.estado or False
        return estado_ano

    def get_comp_state(self, cr, uid, ids, fields, arg, context):
        comp_state = {}
        db_sncp_despesa_compromisso_linha = self.pool.get('sncp.despesa.compromisso.linha')
        for comp_linha_id in ids:
            obj = db_sncp_despesa_compromisso_linha.browse(cr, uid, comp_linha_id)
            comp_state[comp_linha_id] = obj.compromisso_ano_id.compromisso_id.state or None
        return comp_state

    _columns = {
        'compromisso_ano_id': fields.many2one('sncp.despesa.compromisso.ano', u'Compromisso Anual'),
        'tipo_comp': fields.function(get_comp_tipo, arg=None, method=False, type="char",
                                     store=True),
        'state_comp': fields.function(get_comp_state, arg=None, method=False, type="char",
                                      store=True),
        'estado_ano': fields.function(get_comp_ano_estado_ano, arg=None, method=False, type="integer",
                                      store=True),
        'linha': fields.integer(u'Linha'),
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')]),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')]),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')],),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'anual_prev': fields.float(u'Anual Previsto', digits=(12, 2)),
        'state_line': fields.selection([('draft', u'Rascunho'),
                                        ('proc', u'Processado'),
                                        ('anul', u'Anulado'), ], u'Estado'),
        'name': fields.char(u'Observações'),
        'agenda_id': fields.one2many('sncp.despesa.compromisso.agenda', 'compromisso_linha_id', u'Agenda'),
        'estado': fields.integer(u''),
        # controla o botão apagar linha
        # 0 -- invisivel (anos futuros)
        # 1 -- pode apagar( 1 ano) referenciado
        # 2 -- posso apagar, posso editar -> criado diretamente
    }

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_despesa_compromisso_agenda = self.pool.get('sncp.despesa.compromisso.agenda')
        agendas_id = db_sncp_despesa_compromisso_agenda.search(cr, uid, [('compromisso_linha_id', '=', ids[0])])
        if len(agendas_id) != 0:
            db_sncp_despesa_compromisso_agenda.unlink(cr, uid, agendas_id)
        return super(sncp_despesa_compromisso_linha, self).unlink(cr, uid, ids, context=context)

    def delete(self, cr, uid, ids, context):
        comp_ano = self.pool.get('sncp.despesa.compromisso.ano')
        comp_ano_obj = comp_ano.browse(cr, uid, context['compromisso_ano_id'])
        comp_id = comp_ano_obj.compromisso_id.id
        comp_anos_ids = comp_ano.search(cr, uid, [('compromisso_id', '=', comp_id)])
        for ano_id in comp_anos_ids:
            linha_id = self.search(cr, uid, [('compromisso_ano_id', '=', ano_id), ('linha', '=', context['linha'])])
            self.unlink(cr, uid, [linha_id[0]])
        return {'type': 'ir.actions.client', 'tag': 'reload', }

    _order = 'linha'

    _defaults = {
        'state_line': 'draft',
        'estado': 0,
        'montante': 0.01,
        'anual_prev': 0.01,
    }

    _constraints = [
        (_anual_prev_sup_igual_montante, u'', ['montante', 'anual_prev']), ]

sncp_despesa_compromisso_linha()
# ______________________________________________________________ AGENDA_________________________________________


class sncp_despesa_compromisso_agenda(osv.Model):
    _name = 'sncp.despesa.compromisso.agenda'
    _description = "Agenda de Compromisso"

    def on_change_montante(self, cr, uid, ids, montante, context=None):
        if montante < 0.0:
            raise osv.except_osv(_(u'Aviso'), _(u'Montante da linha da agenda deve ser 0 ou positivo.'))
        self.write(cr, uid, ids, {'montante': montante})
        return {'value': {'montante': montante}}

    _columns = {
        'compromisso_linha_id': fields.many2one('sncp.despesa.compromisso.linha', u'Compromisso Anual'),
        'name': fields.integer(u'Mês'),
        'montante': fields.float(u'Valor a pagar', digits=(12, 2)),
        'data_prevista': fields.date(u'Data prevista'),
        'last_doc_contab_id': fields.many2one('account.move',  u'Última contabilização')
    }

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_despesa_compromisso_agenda, self).unlink(cr, uid, ids, context=context)

    _order = 'name'

sncp_despesa_compromisso_agenda()
# _______________________________________________________________RELAÇOES_______________________________________


class sncp_despesa_compromisso_relacoes(osv.Model):
    _name = 'sncp.despesa.compromisso.relacoes'
    _description = "Relação entre Compromisso, Ordem de Compra e Faturas"

    def insere_relacao(self, cr, uid, ids, vals):
        # vals = {
        #   'account_invoice_id':
        #   'purchase_order_id':
        #   'compromisso_id'
        # }

        if vals['purchase_order_id'] and not vals['account_invoice_id']:
            self.create(cr, uid, {'name': vals['compromisso_id'],
                                  'purchase_order_id': vals['purchase_order_id'],
                                  'account_invoice_id': None})
        elif vals['account_invoice_id'] and not vals['purchase_order_id']:
            cr.execute("""SELECT purchase_id from purchase_invoice_rel WHERE invoice_id = %d"""
                       % vals['purchase_order_id'])
            list_ids = cr.fetchall()
            if len(list_ids) != 0:
                rel_id = self.search(cr, uid, [('name', '=', vals['compromisso_id'])])
                if len(rel_id) != 0:
                    self.write(cr, uid, rel_id, {'account_invoice_id': vals['account_invoice_id']})
                    return True
                else:
                    novo_id = self.create(cr, uid, {'name': vals['compromisso_id'],
                                                    'purchase_order_id': None, })

                    cr.execute("""
                    INSERT INTO sncp_despesa_compromisso_faturas(compromisso_relacoes_id,fatura_id)
                    VALUES(%d,%d)
                    """ % (novo_id, vals['account_invoice_id']))
                    return True

        else:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'É necessário indicar ou ordem de compra ou de fatura'+unicode(vals)+u'.'))

    def anula_relacao(self, cr, uid, ids, vals):

        if vals['purchase_order_id']:
            obj_id = self.search(cr, uid, [('purchase_order_id', '=', vals['purchase_order_id'])])
            obj = self.browse(cr, uid, obj_id[0])

            cr.execute("""
            SELECT *
            FROM sncp_despesa_compromisso_relacoes_faturas
            WHERE compromisso_relacoes_id=%d
            """ % obj.id)
            lista = cr.fetchall()

            if len(lista) != 0:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Há uma fatura associada a '
                                       u'esta ordem de compra.'))
            else:
                self.unlink(cr, uid, obj_id)
                return True

        elif vals['account_invoice_id']:
            cr.execute("""
            SELECT compromisso_relacoes_id
            FROM sncp_despesa_compromisso_relacoes
            WHERE fatura_id=%d
            """ % vals['account_invoice_id'])
            lista = cr.fetchall()

            for elem in lista:
                obj = self.browse(cr, uid, elem[0])
                if obj.purchase_order_id.id is False:
                    self.unlink(cr, uid, obj.id)
                else:
                    cr.execute("""
                    DELETE FROM sncp_despesa_compromisso_relacoes_faturas WHERE compromisso_relacoes_id=%d
                    """ % obj.id)

        return True

    _columns = {
        'name': fields.many2one('sncp.despesa.compromisso', u'Compromisso'),
        'purchase_order_id': fields.many2one('purchase.order', u'Ordem de Compra'),
        'account_invoice_id': fields.many2many('account.invoice', 'sncp_despesa_compromisso_relacoes_faturas',
                                               'compromisso_relacoes_id', 'fatura_id', u'Fatura de compra')
    }

    _order = 'name,purchase_order_id,account_invoice_id'

    _sql_constraints = [
        ('compromisso_unique', 'unique (name)', u'Este Compromisso já existe'),
        ('order_unique', 'unique (purchase_order_id)', u'Esta Ordem já existe'),
    ]

sncp_despesa_compromisso_relacoes()
# ____________________________________________________________DADOS ADICIONAIS__________________________________


class sncp_despesa_compromisso_dados_adic(osv.Model):
    _name = 'sncp.despesa.compromisso.dados.adic'
    _description = "Dados Adicionais do Compromisso"

    def save(self, cr, uid, ids, context):
        return True

    def on_change_tc_visto(self, cr, uid, ids, tc_visto):

        if tc_visto is False:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'tc_remessa': False, 'tc_data': False, 'tc_res': False})
            return {
                'value': {'tc_remessa': False, 'tc_data': False, 'tc_res': False}
                }

        return {}

    _columns = {
        'compromisso_id': fields.many2one('sncp.despesa.compromisso', u'Compromisso'),
        'procedimento_id': fields.many2one('sncp.despesa.procedimentos', u'Tipo de Procedimento'),
        'fundamento_id': fields.many2one('sncp.despesa.fundamentos', u'Fundamento'),
        'cpv_id': fields.many2one('sncp.comum.cpv', u'Código CPV'),
        'criterio': fields.selection([('material', u'Critério material'),
                                      ('negociac', u'Procedimento de negociação'),
                                      ('ajuste', u'Ajuste direto'), ], u'Critério negocial'),
        'autoriza_esp': fields.date(u'Autorização especial da AM'),
        'natureza_id': fields.many2one('sncp.despesa.naturezas', u'Natureza do Contrato'),
        'publicado': fields.char(u'Publicado no Base'),
        'data_contrado': fields.date(u'Data do contrato'),
        'prazo': fields.integer(u'Prazo de execução (dias)'),
        'preco_contrat': fields.float(u'Preço contratual', digits=(12, 2)),
        'data_fecho': fields.date(u'Data de fecho do contrato'),
        'preco_efetivo': fields.float(u'Preço efetivo'),
        'name': fields.char(u'Referência do contrato'),
        'contr_alter': fields.boolean(u'Contrato alterado'),
        'contr_revog': fields.boolean(u'Contrato revogado'),
        'contr_resol': fields.boolean(u'Contrato resolvido'),
        'notas': fields.text(u'Outros aspetos do contrato'),
        'tc_visto': fields.boolean(u'Sujeito a visto do TC'),
        'tc_remessa': fields.date(u'Remessa ao TC'),
        'tc_data': fields.date(u'Data do Visto'),
        'tc_res': fields.char(u'Resolução do TC'),
        'cofinanciamento_id': fields.many2one('sncp.despesa.cofinanciamentos', u'Programa Co-Financiado'),
    }

sncp_despesa_compromisso_dados_adic()
