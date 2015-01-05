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

from datetime import datetime
import decimal
from decimal import *
from openerp.osv import fields, osv
from openerp.tools.translate import _


class sncp_despesa_pagamentos_reposicoes(osv.Model):
    _name = 'sncp.despesa.pagamentos.reposicoes'
    _description = u"Reposições das Ordens de Pagamento"

    def montante_a_repor(self, cr, uid, ids, fields, arg, context):
        soma = {}
        db_sncp_despesa_pagamentos_reposicoes_linha = self.pool.get('sncp.despesa.pagamentos.reposicoes.linha')
        for reposicao_id in ids:
            linha_ids = db_sncp_despesa_pagamentos_reposicoes_linha.search(cr, uid,
                                                                           [('reposicao_id', '=', reposicao_id)])
            soma[reposicao_id] = 0.0
            for linha in linha_ids:
                obj_linha = db_sncp_despesa_pagamentos_reposicoes_linha.browse(cr, uid, linha)
                soma[reposicao_id] += obj_linha.montante_repor

            aux = decimal.Decimal(unicode(soma[reposicao_id]))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            soma[reposicao_id] = float(aux)
        return soma

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name'], context=context)
        res = []
        for record in reads:
            result = u'Reposição'
            res.append((record['id'], result))
        return res

    def _get_departamento(self, cr, uid, ctx):
        cr.execute("""SELECT department_id FROM hr_employee
                      WHERE resource_id IN (SELECT id FROM resource_resource WHERE user_id = %d)
                      LIMIT 1
                   """ % uid)

        res_depart = cr.fetchone()

        if res_depart is None or res_depart is None:
            return False
        else:
            return res_depart[0]

    def on_change_opag_id(self, cr, uid, ids, opag_id, data, departamento_id, motivo):
        db_sncp_despesa_pagamentos_reposicoes_linha = self.pool.get('sncp.despesa.pagamentos.reposicoes.linha')

        if len(ids) != 0 and opag_id is not False:

            cr.execute("""
            DELETE FROM sncp_despesa_pagamentos_reposicoes_linha
            WHERE reposicao_id=%d
            """ % ids[0])

            cr.execute("""
            SELECT account_invoice_id,account_invoice_line_id,compromisso_id,compromisso_linha_id,montante
            FROM sncp_despesa_pagamentos_ordem_rel
            WHERE opag_id=%d
            """ % opag_id)

            pag_ord_rels = cr.fetchall()
            rep_linhas = []
            if len(pag_ord_rels) != 0:
                for pag_ord_rel in pag_ord_rels:

                    cr.execute("""
                    SELECT internal_number
                    FROM account_invoice
                    WHERE id=%d
                    """ % pag_ord_rel[0])

                    nome = cr.fetchone()
                    if nome is not None:
                        nome = nome[0]

                    cr.execute("""
                    SELECT compromisso
                    FROM sncp_despesa_compromisso
                    WHERE id=%d
                    """ % pag_ord_rel[2])

                    compromisso = cr.fetchone()
                    if compromisso is not None:
                        compromisso = compromisso[0]

                    vals = {
                        'reposicao_id': ids[0],
                        'name': nome,
                        'account_invoice_line_id': pag_ord_rel[1],
                        'compromisso': compromisso,
                        'compromisso_linha_id': pag_ord_rel[3],
                        'montante': pag_ord_rel[4],
                    }
                    rep_linha_id = db_sncp_despesa_pagamentos_reposicoes_linha.create(cr, uid, vals)
                    rep_linhas.append(rep_linha_id)

            cr.execute("""
            SELECT CONCAT(COALESCE(RP.vat,''),' ',COALESCE(RP.name,''))
            FROM res_partner AS RP
            WHERE id = (SELECT partner_id FROM sncp_despesa_pagamentos_ordem WHERE id=%d)
            """ % opag_id)

            parceiro = cr.fetchone()

            self.write(cr, uid, ids, {'opag_id': opag_id, 'parceiro': parceiro[0]}, )
            return {'value': {'opag_id': opag_id, 'parceiro': parceiro[0], 'reposicao_linha_id': rep_linhas}}

        return {}

    def continuar(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'estado_linhas': 1})
        obj = self.browse(cr, uid, ids[0])
        self.on_change_opag_id(cr, uid, ids, obj.opag_id.id, obj.data, obj.departamento_id.id, obj.motivo)
        return True

    def finalizar(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'estado_linhas': 2})
        return True

    def confirma(self, cr, uid, ids, context=None):
        db_sncp_despesa_pagamentos_reposicoes_linha = self.pool.get('sncp.despesa.pagamentos.reposicoes.linha')
        rep_linha_ids = db_sncp_despesa_pagamentos_reposicoes_linha.search(cr, uid, [('reposicao_id', '=', ids[0]),
                                                                                     ('montante_repor', '=', 0.0)])

        if len(rep_linha_ids) != 0:
            db_sncp_despesa_pagamentos_reposicoes_linha.unlink(cr, uid, rep_linha_ids, context=context)

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def imprimir_report(self, cr, uid, ids, context=None):
        datas = {
            'ids': ids,
            'model': 'sncp.despesa.pagamentos.reposicoes',
        }
        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.despesa.pagamentos.reposicoes.report',
            'datas': datas,
        }

    _columns = {
        'name': fields.char(u'Número da Guia de Reposição', size=12),
        'data': fields.datetime(u'Data e hora'),
        'departamento_id': fields.many2one('hr.department', u'Departamento'),
        'opag_id': fields.many2one('sncp.despesa.pagamentos.ordem', u'Ordem de Pagamento',
                                   domain=[('state', '=', 'pag'), ('tipo', '=', 'orc'), ('anular', '=', 1)]),
        'data_pag_op': fields.related('opag_id', 'paga', type="char", string=u"OP Paga", store=True),
        'montante_iliq': fields.related('opag_id', 'montante_iliq', type="float",
                                        string=u"Montante Ilíquido", store=True),
        'nome_parceiro': fields.related('opag_id', 'partner_id', 'name', type="char",
                                        store=True, string=u"Nome do Parceiro"),
        'parceiro': fields.char(u'Parceiro de Negócios'),
        'motivo': fields.text(u'Motivo para a reposição'),
        'montante': fields.function(montante_a_repor, arg=None, method=False, type="float",
                                    string=u'Montante Reposto', store=True),

        'meio_pag_id': fields.many2one('sncp.comum.meios.pagamento', u'Meio de Pagamento',
                                       domain=[('tipo', 'in', ['rec']), ('meio', 'not in', ['fm', 'dc'])], ),
        'meio_desc': fields.related('meio_pag_id', 'name', type="char", string=u"Meio de Pagamento", store=True),
        'ref_meio': fields.char(u'Meio'),
        'bcfm': fields.char(u'Código'),
        # tesouraria/heranca/sncp.despesa.pagamentos.reposicoes
        # banco_id
        # caixa_id
        # fundo_id
        'num_pag': fields.char(u'N.º Cheque/Outro', size=15),
        'cobrada_emp': fields.many2one('res.users', u'Cobrada por'),
        'cobrada_data': fields.datetime(u'Cobrada em'),
        'doc_cobranca_id': fields.many2one('account.move', u'Documento de Cobrança'),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('cobrd', u'Cobrada')], u'Estado'),
        'reposicao_linha_id': fields.one2many('sncp.despesa.pagamentos.reposicoes.linha', 'reposicao_id', u''),
        'estado_linhas': fields.integer(u''),
        'imprimir': fields.integer(u''),
    }

    _defaults = {
        'state': 'draft',
        'estado_linhas': 0,
        'imprimir': 0,
        'data': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                 datetime.now().hour, datetime.now().minute, datetime.now().second)),
        'departamento_id': lambda self, cr, uid, ctx: self._get_departamento(cr, uid, ctx),
    }

    _order = 'name'

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_despesa_pagamentos_reposicoes_linha = self.pool.get('sncp.despesa.pagamentos.reposicoes.linha')

        linha_ids = db_sncp_despesa_pagamentos_reposicoes_linha.search(cr, uid, [('reposicao_id', '=', ids[0])])

        if len(linha_ids) != 0:
            db_sncp_despesa_pagamentos_reposicoes_linha.unlink(cr, uid, linha_ids, context=context)

        super(sncp_despesa_pagamentos_reposicoes, self).unlink(cr, uid, ids, context=context)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

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
        m_dez text[] := array['','dez','vinte','trinta','quarenta','cinquenta','sessenta','setenta','oitenta',
        'noventa'] ;
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

    def teste_existencia_reposicoes(self, cr):
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

        return True

    def create(self, cr, uid, vals, context=None):
        self.teste_existencia_reposicoes(cr)
        return super(sncp_despesa_pagamentos_reposicoes, self).create(cr, uid, vals, context=context)


sncp_despesa_pagamentos_reposicoes()


class sncp_despesa_pagamentos_reposicoes_linha(osv.Model):
    _name = 'sncp.despesa.pagamentos.reposicoes.linha'
    _description = u"Linhas das Reposições das Ordens de Pagamento"

    _columns = {
        'reposicao_id': fields.many2one('sncp.despesa.pagamentos.reposicoes', u'Guia de Reposição'),
        'name': fields.char(u'Fatura', size=12),
        'account_invoice_line_id': fields.many2one('account.invoice.line', u'Linha da Fatura'),
        'compromisso': fields.char(u'Compromisso', size=12),
        'compromisso_linha_id': fields.many2one('sncp.despesa.compromisso.linha', u'Linha do compromisso'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'montante_repor': fields.float(u'Montante a repor', digits=(12, 2)),
    }

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_despesa_pagamentos_reposicoes_linha, self).unlink(cr, uid, ids, context=context)

    _order = 'name'

    _defaults = {
        'montante_repor': 0.0,
    }

    def montante_limit(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])

        if obj.montante < 0.0 or obj.montante_repor > obj.montante:
            raise osv.except_osv(_(u'Aviso'), _(u'O montante a repor não pode ser negativo '
                                                u' e não pode ser superior ao montante da ordem.'))
        return True

    _constraints = [
        (montante_limit, u'', ['montante'])
    ]


sncp_despesa_pagamentos_reposicoes_linha()