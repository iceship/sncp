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


# __________________________________________________________ORDEM________________________________________________

class sncp_despesa_pagamentos_ordem(osv.Model):
    _name = 'sncp.despesa.pagamentos.ordem'
    _description = u"Ordem de Pagamento"
    # Em create accionar funções:
    # -- on_change_codigo
    # -- on_change_meio

    # Heranças na tesouraria

    # verifica_liquidado
    # pag_ord_liq
    # atualiza_historico
    # movimento_contabilistico_pagamento
    # pagar
    # anular_pagar
    # on_change_meio

    def call_param(self, cr, uid, ids, context=None):
        return self.pool.get('formulario.sncp.despesa.pagamentos.ordem.diario').wizard(cr, uid, ids)

    def criar_linhas_ordem(self, cr, uid, send1, context):
        db_account_invoice_line = self.pool.get('account.invoice.line')
        db_sncp_despesa_pagamentos_proposta_linha = self.pool.get('sncp.despesa.pagamentos.proposta.linha')
        db_sncp_despesa_pagamentos_ordem_linha = self.pool.get('sncp.despesa.pagamentos.ordem.linha')
        db_sncp_despesa_pagamentos_rel = self.pool.get('sncp.despesa.pagamentos.rel')
        db_account_invoice = self.pool.get('account.invoice')
        db_sncp_despesa_pagamentos_ordem_rel = self.pool.get('sncp.despesa.pagamentos.ordem.rel')
        db_sncp_despesa_pagamentos_ordem_linhas_imprimir = \
            self.pool.get('sncp.despesa.pagamentos.ordem.linhas.imprimir')

        db_sncp_despesa_pagamentos_proposta = self.pool.get('sncp.despesa.pagamentos.proposta')

        lin_prop_ids = db_sncp_despesa_pagamentos_proposta_linha.search(cr, uid,
                                                                        [('proposta_id', '=', send1['proposta_id'])])
        numero_linha = 1
        sum_total_linhas = 0.0
        obj_proposta = db_sncp_despesa_pagamentos_proposta.browse(cr, uid, send1['proposta_id'])
        total_a_pagar = obj_proposta.total_pagar

        if len(lin_prop_ids) != 0:
            for lin_prop in db_sncp_despesa_pagamentos_proposta_linha.browse(cr, uid, lin_prop_ids):
                fatura_id = lin_prop.invoice_id.id
                fatura = db_account_invoice.browse(cr, uid, fatura_id)
                linhas_fatura_ids = db_account_invoice_line.search(cr, uid, [('invoice_id', '=', fatura_id)])

                if len(linhas_fatura_ids) != 0:
                    for linha_fatura in db_account_invoice_line.browse(cr, uid, linhas_fatura_ids):
                        send = {'linha_fatura': linha_fatura}
                        val_orig_lin_fat = self.montante_original(cr, uid, [], send)
                        rel_ids = db_sncp_despesa_pagamentos_rel.search(cr, uid, [('invoice_id', '=', fatura_id)])

                        vpl = (val_orig_lin_fat * total_a_pagar) / fatura.amount_total

                        aux = decimal.Decimal(unicode(vpl))
                        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                        vpl = float(aux)

                        sum_total_linhas += vpl

                        vals = {'opag_id': send1['ordem_id'],
                                'account_invoice_id': fatura_id,
                                'account_invoice_line_id': linha_fatura.id,
                                'compromisso_id':
                                linha_fatura.linha_compromisso_id.compromisso_ano_id.compromisso_id.id,
                                'compromisso_linha_id': linha_fatura.linha_compromisso_id.id,
                                'montante': vpl, }

                        db_sncp_despesa_pagamentos_ordem_rel.create(cr, uid, vals)

                        db_sncp_despesa_pagamentos_ordem_linha.create(cr, uid, vals)

                        db_res_partner = self.pool.get('res.partner')
                        parceiro = db_res_partner.browse(cr, uid, send1['partner_id'])

                        lista_procura = [('opag_id', '=', send1['ordem_id']),
                                         ('conta_contabil_id', '=', parceiro.property_account_payable.id),
                                         ('organica_id', '=', linha_fatura.organica_id.id),
                                         ('economica_id', '=', linha_fatura.economica_id.id),
                                         ('funcional_id', '=', linha_fatura.funcional_id.id)]

                        imprimir_ids = db_sncp_despesa_pagamentos_ordem_linhas_imprimir.search(cr, uid, lista_procura)

                        if len(imprimir_ids) != 0:
                            obj_imp = db_sncp_despesa_pagamentos_ordem_linhas_imprimir.browse(cr, uid, imprimir_ids[0])
                            aux = decimal.Decimal(unicode(obj_imp.montante + vpl))
                            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                            montante_imp = float(aux)
                            db_sncp_despesa_pagamentos_ordem_linhas_imprimir.write(cr, uid, imprimir_ids,
                                                                                   {'montante': montante_imp})
                        else:
                            imprimir = {'opag_id': send1['ordem_id'],
                                        'name': numero_linha,
                                        'num_fat_parceiro': fatura.supplier_invoice_number,
                                        'conta_contabil_id': parceiro.property_account_payable.id,
                                        'organica_id': linha_fatura.organica_id.id,
                                        'economica_id': linha_fatura.economica_id.id,
                                        'funcional_id': linha_fatura.funcional_id.id,
                                        'montante': vpl, }
                            numero_linha += 1

                            db_sncp_despesa_pagamentos_ordem_linhas_imprimir.create(cr, uid, imprimir)

                        if len(rel_ids) != 0:
                            relacao = db_sncp_despesa_pagamentos_rel.browse(cr, uid, rel_ids[0])
                            aux = decimal.Decimal(unicode(relacao.montante_proc + vpl))
                            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                            montante_proc = float(aux)
                            db_sncp_despesa_pagamentos_rel.write(cr, uid, rel_ids, {'montante_proc': montante_proc})
                        else:
                            fatura = db_account_invoice.browse(cr, uid, fatura_id)

                            nvals = {
                                'invoice_id': fatura_id,
                                'comprom_linha_id': linha_fatura.linha_compromisso_id.id,
                                'montante_proc': vpl,
                                'name': fatura.supplier_invoice_number,
                            }

                            db_sncp_despesa_pagamentos_rel.create(cr, uid, nvals)
                else:
                    raise osv.except_osv(_(u'Aviso'), _(u'Não existe linhas associadas à fatura.'))
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existe linhas associadas à proposta.'))

        aux = decimal.Decimal(unicode(sum_total_linhas))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        sum_total_linhas = float(aux)

        if sum_total_linhas != total_a_pagar:
            aux2 = decimal.Decimal(unicode(total_a_pagar - sum_total_linhas))
            aux2 = aux2.quantize(Decimal('0.01'), ROUND_HALF_UP)
            dif = float(aux2)

            linhas_ids = db_sncp_despesa_pagamentos_ordem_linha.search(cr, uid, [('opag_id', '=', send1['ordem_id'])])

            linhas_imp_ids = db_sncp_despesa_pagamentos_ordem_linhas_imprimir.search(cr, uid, [('opag_id', '=',
                                                                                                send1['ordem_id'])])

            if len(linhas_ids) != 0 and len(linhas_imp_ids) != 0:

                linha_id = max(linhas_ids)
                linha_imp_id = max(linhas_imp_ids)

                linha = db_sncp_despesa_pagamentos_ordem_linha.browse(cr, uid, linha_id)
                linha_imprimir = db_sncp_despesa_pagamentos_ordem_linhas_imprimir.brows(cr, uid, linha_imp_id)

                aux3 = decimal.Decimal(unicode(linha.montante + dif))
                aux3 = aux3.quantize(Decimal('0.01'), ROUND_HALF_UP)
                linha_montante = float(aux3)

                db_sncp_despesa_pagamentos_ordem_linha.write(cr, uid, linha.id, {'montante': linha_montante})

                aux4 = decimal.Decimal(unicode(linha_imprimir.montante + dif))
                aux4 = aux4.quantize(Decimal('0.01'), ROUND_HALF_UP)
                linha_montante_imprimir = float(aux4)

                db_sncp_despesa_pagamentos_ordem_linhas_imprimir.write(cr, uid, linha_imprimir.id,
                                                                       {'montante': linha_montante_imprimir})

        return True

    def pag_ord_rascunho(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft',
                                  'conferida_user_id': None,
                                  'conferida_data': None})
        return True

    def pag_ord_cnf(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.serie_id.id:
            if obj.serie_id.banco_id.id != obj.banco_id.id:
                raise osv.except_osv(_(u'Aviso'), _(u'Série não corresponde ao banco seleccionado.'))

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_cheques
            WHERE serie_id = %d AND state = 'nutl'
            """ % obj.serie_id.id)

            res_cheque = cr.fetchall()

            if len(res_cheque) == 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Não existem cheques '
                                                    u'para se efetuar o pagamento.'))

        if obj.meio_pag_id.id is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Falta definir o meio de pagamento.'))
        self.atualiza_montantes(cr, uid, ids)
        self.montantes_linha_igual_total_pagar_proposta(cr, uid, ids)
        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]
        self.write(cr, uid, ids, {'state': 'cnf', 'conferida_user_id': uid, 'conferida_data': datahora})
        return True

    def pag_ord_aut(self, cr, uid, ids, context=None):
        db_sncp_comum_param = self.pool.get('sncp.comum.param')
        db_ir_sequence = self.pool.get('ir.sequence')
        param_ids = db_sncp_comum_param.search(cr, uid, [('state', '=', 'draft')])
        if len(param_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                u'Preencha os parâmetros por defeito no menu:\n'
                                                u'Comum/Parâmetros.'))
        parametros = db_sncp_comum_param.browse(cr, uid, param_ids[0])

        if parametros.diario_liq_id.sequence_id.id:
            numord = db_ir_sequence.next_by_id(cr, uid, parametros.diario_liq_id.sequence_id.id)
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'O diário ' + unicode(parametros.diario_liq_id.name) +
                                                u' não têm sequência de movimentos associada.'))

        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]

        self.write(cr, uid, ids, {'state': 'aut',
                                  'autorizada_user_id': uid,
                                  'autorizada_data': datahora,
                                  'name': numord})

        return self.imprimir_report(cr, uid, ids, context=context)

    def imprimir_report(self, cr, uid, ids, context=None):
        datas = {
            'ids': ids,
            'model': 'sncp.despesa.pagamentos.ordem',
        }

        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.despesa.pagamentos.ordem.report',
            'datas': datas,
        }

    def pag_ord_desaut(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cnf',
                                  'name': None,
                                  'autorizada_user_id': None,
                                  'autorizada_data': None})
        return True

    def montante_original(self, cr, uid, ids, vals):
        db_account_tax = self.pool.get('account.tax')
        cr.execute("""SELECT *  FROM account_invoice_line_tax WHERE invoice_line_id = %d""" % vals['linha_fatura'].id)
        record = cr.fetchone()
        taxa = 0.0
        if record is None:
            pass
        else:
            obj_taxa = db_account_tax.browse(cr, uid, record[1])
            taxa = obj_taxa.amount
        aux = decimal.Decimal(unicode((taxa + 1) * vals['linha_fatura'].price_subtotal))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_original = float(aux)
        return montante_original

    def desconto_visivel(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'estado_descontos': 1})
        return True

    def atualiza_montantes(self, cr, uid, ids):
        db_sncp_despesa_descontos_retencoes = self.pool.get('sncp.despesa.descontos.retencoes')
        db_sncp_despesa_descontos_retencoes_rel_grec = self.pool.get('sncp.despesa.descontos.retencoes.rel.grec')

        montante_desc = 0
        montante_ret = 0

        rel_grec_ids = db_sncp_despesa_descontos_retencoes_rel_grec.search(cr, uid, [('opag_id', '=', ids)])
        for obj_rel_grec in db_sncp_despesa_descontos_retencoes_rel_grec.browse(cr, uid, rel_grec_ids):
            obj_desc = db_sncp_despesa_descontos_retencoes.browse(cr, uid, obj_rel_grec.ret_desc_id.id)
            if obj_desc.natureza == 'desc':
                montante_desc += obj_rel_grec.montante

            elif obj_desc.natureza == 'rete':
                montante_ret += obj_rel_grec.montante

        aux = decimal.Decimal(unicode(montante_ret))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_ret = float(aux)

        aux = decimal.Decimal(unicode(montante_desc))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_desc = float(aux)

        self.write(cr, uid, ids, {'montante_desc': montante_desc, 'montante_ret': montante_ret})

    def on_change_codigo(self, cr, uid, ids, meio_pag_id, passed_id, descr):
        obj = None
        estado_serie = 0
        if not passed_id:
            return {}
        if descr in ['caixa', 'cx']:
            db_sncp_tesouraria_caixas = self.pool.get('sncp.tesouraria.caixas')
            obj = db_sncp_tesouraria_caixas.browse(cr, uid, passed_id)
        elif descr in ['banco', 'bk']:
            db_sncp_comum_meios_pagamento = self.pool.get('sncp.comum.meios.pagamento')
            obj_meio_pagamento = db_sncp_comum_meios_pagamento.browse(cr, uid, meio_pag_id)
            db_sncp_tesouraria_contas_bancarias = self.pool.get('sncp.tesouraria.contas.bancarias')
            obj = db_sncp_tesouraria_contas_bancarias.browse(cr, uid, passed_id)
            if obj_meio_pagamento.echeque is True:
                cr.execute("""
                SELECT id
                FROM sncp_tesouraria_series
                WHERE banco_id = %d
                """ % obj.id)

                series_id = cr.fetchall()

                if len(series_id) == 1:
                    estado_serie = 1
                    series_id = [elem[0] for elem in series_id]
                elif len(series_id) > 1:
                    estado_serie = 2
                    series_id = [elem[0] for elem in series_id]

                if len(ids) != 0:
                    if len(series_id) == 1:
                        self.write(cr, uid, ids, {'bcfm': obj.codigo,
                                                  'estado_serie': estado_serie,
                                                  'serie_id': series_id[0]})

                    elif len(series_id) > 1:
                        self.write(cr, uid, ids, {'bcfm': obj.codigo,
                                                  'estado_serie': estado_serie})

                    if len(series_id) > 1:
                        return {'domain': {'serie_id': [('id', 'in', series_id)]},
                                'value': {'estado_serie': estado_serie}}
                    elif len(series_id) == 1:
                        return {'value': {'estado_serie': estado_serie}}
                    else:
                        raise osv.except_osv(_(u'Aviso'), _(u'Defina as séries para o Banco - '
                                                            + obj.codigo + u'.'))
        elif descr in ['fundo', 'fm']:
            db_sncp_tesouraria_fundos_maneio = self.pool.get('sncp.tesouraria.fundos.maneio')
            obj = db_sncp_tesouraria_fundos_maneio.browse(cr, uid, passed_id)

        if len(ids) != 0:
            self.write(cr, uid, ids, {'bcfm': obj.codigo, 'estado_serie': estado_serie,
                                      'serie_id': None})

        return {}

    _columns = {
        'name': fields.char(u'Ordem de pagamento', size=12),
        'tipo': fields.selection([('orc', u'Orçamental'),
                                  ('opt', u'Operações de Tesouraria'), ], u'Tipo'),
        'proposta_id': fields.many2one('sncp.despesa.pagamentos.proposta', 'Proposta'),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios',
                                      domain=[('supplier', '=', True)]),
        'nif': fields.related('partner_id', 'vat', type="char", store=True, string="NIF"),
        'coletiva': fields.boolean(u'Integrada em ordem colectiva'),
        'meio_pag_id': fields.many2one('sncp.comum.meios.pagamento', u'Meio de Pagamento',
                                       domain=[('tipo', 'in', ['pag']), ('meio', 'not in', ['dc'])], ),
        'meio_desc': fields.related('meio_pag_id', 'name', type="char", string=u"Meio de Pagamento", store=True),
        'ref_meio': fields.char(u'Meio'),
        'bcfm': fields.char(u'Código'),
        # tesouraria/heranca/sncp.despesa.pagamentos.ordem
        # banco_id
        # caixa_id
        # fundo_id
        'num_pag': fields.char(u'N.º Cheque/Outro', size=15),
        'montante_iliq': fields.float(u'Montante ilíquido', digits=(12, 2)),
        'montante_desc': fields.float(u'Montante de descontos', digits=(12, 2)),
        'montante_ret': fields.float(u'Montante de retenções', digits=(12, 2)),
        'conferida_user_id': fields.many2one('res.users', u'Conferida por'),
        'conferida_data': fields.datetime(u'Conferida em'),
        'autorizada_user_id': fields.many2one('res.users', u'Autorizada por'),
        'autorizada_data': fields.datetime(u'Autorizada em'),
        'referencia': fields.char(u'Referência', size=15),
        'liquidada': fields.datetime(u'Liquidação'),
        'paga': fields.datetime(u'Pagamento'),
        'observ': fields.char(u'Observações'),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('cnf', u'Conferida'),
                                   ('aut', u'Autorizada'),
                                   ('rej', u'Rejeitada'),
                                   ('liq', u'Liquidada'),
                                   ('pag', u'Paga'), ], u'Estado'),
        'doc_liquida_id': fields.many2one('account.move', u'Documento de Liquidação'),
        'doc_pagam_id': fields.many2one('account.move', u'Documento de Pagamento'),
        'ordem_linha_id': fields.one2many('sncp.despesa.pagamentos.ordem.linha', 'opag_id', u''),
        'estado_descontos': fields.integer(u'descontos'),
        # 0 -- criar descontos visivel, page invisivel
        # 1 -- criar descontos invisivel, page visivel
        'anular': fields.integer(u'Pode Anular'),
        'estado_serie': fields.integer(u''),
        'descontos_retencoes_id': fields.one2many('sncp.despesa.descontos.retencoes.rel.grec', 'opag_id', u'')
    }

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_despesa_pagamentos_ordem_linha = self.pool.get('sncp.despesa.pagamentos.ordem.linha')
        db_sncp_despesa_pagamentos_ordem_linhas_imprimir = self.pool.get(
            'sncp.despesa.pagamentos.ordem.linhas.imprimir')
        db_sncp_despesa_descontos_retencoes_rel_grec = self.pool.get('sncp.despesa.descontos.retencoes.rel.grec')
        db_sncp_despesa_pagamentos_ordem_rel = self.pool.get('sncp.despesa.pagamentos.ordem.rel')

        linha_ids = db_sncp_despesa_pagamentos_ordem_linha.search(cr, uid, [('opag_id', '=', ids[0])])
        linhas_imprimir_ids = db_sncp_despesa_pagamentos_ordem_linhas_imprimir.search(cr, uid,
                                                                                      [('opag_id', '=', ids[0])])
        descontos_ids = db_sncp_despesa_descontos_retencoes_rel_grec.search(cr, uid, [('opag_id', '=', ids[0])])
        rel_opag_ids = db_sncp_despesa_pagamentos_ordem_rel.search(cr, uid, [('opag_id', '=', ids[0])])

        obj = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT opag_id
        FROM sncp_despesa_descontos_retencoes_rel_opag
        WHERE opag_tes_id = %d
        """ % obj.id)

        res_ordem_ot = cr.fetchall()

        if len(res_ordem_ot) != 0:
            opag_id = res_ordem_ot[0][0]
            ordem = self.browse(cr, uid, opag_id)
            raise osv.except_osv(_(u'Aviso'), _(u'Esta ordem de pagamento está associada à ordem de '
                                                u'pagamento ' + ordem.name + u'.'))

        if len(linha_ids) != 0:
            db_sncp_despesa_pagamentos_ordem_linha.unlink(cr, uid, linha_ids)
        if len(linhas_imprimir_ids) != 0:
            db_sncp_despesa_pagamentos_ordem_linhas_imprimir.unlink(cr, uid, linhas_imprimir_ids)
        if len(descontos_ids) != 0:
            db_sncp_despesa_descontos_retencoes_rel_grec.unlink(cr, uid, descontos_ids)
        if len(rel_opag_ids) != 0:
            db_sncp_despesa_pagamentos_ordem_rel.unlink(cr, uid, rel_opag_ids)

        return super(sncp_despesa_pagamentos_ordem, self).unlink(cr, uid, ids, context=context)

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

    def teste_existencia_ordem_pagamento(self, cr):
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
        self.teste_existencia_ordem_pagamento(cr)
        return super(sncp_despesa_pagamentos_ordem, self).create(cr, uid, vals, context=context)

    _defaults = {
        'state': 'draft',
        'tipo': 'orc',
        'estado_serie': 0,
    }

    def montantes_validos(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.montante_ret + obj.montante_desc > obj.montante_iliq:
            raise osv.except_osv(_(u'Aviso'), _(u'A soma dos montantes dos Descontos/Retenções não pode ultrapassar'
                                                u' o montante ilíquido.'))
        return True

    def montantes_linha_igual_total_pagar_proposta(self, cr, uid, ids):
        db_sncp_despesa_pagamentos_proposta = self.pool.get('sncp.despesa.pagamentos.proposta')
        db_sncp_despesa_pagamentos_ordem_linha = self.pool.get('sncp.despesa.pagamentos.ordem.linha')
        db_sncp_despesa_pagamentos_ordem_linhas_imprimir = self.pool.get(
            'sncp.despesa.pagamentos.ordem.linhas.imprimir')
        pag_ordem = self.browse(cr, uid, ids[0])
        proposta = db_sncp_despesa_pagamentos_proposta.browse(cr, uid, pag_ordem.proposta_id.id)
        linhas_ordem_id = db_sncp_despesa_pagamentos_ordem_linha.search(cr, uid, [('opag_id', '=', pag_ordem.id)])
        soma_montantes_linha = 0.0
        if pag_ordem.tipo == 'opt':
            linhas_ordem_imprimir_ids = db_sncp_despesa_pagamentos_ordem_linhas_imprimir.search(cr, uid, [
                ('opag_id', '=', pag_ordem.id)])
            if len(linhas_ordem_imprimir_ids) != 0:
                linhas_imprimir = db_sncp_despesa_pagamentos_ordem_linhas_imprimir.browse(cr, uid,
                                                                                          linhas_ordem_imprimir_ids)
                for linhas_ordem_imprimir in linhas_imprimir:
                    soma_montantes_linha += linhas_ordem_imprimir.montante

                aux = decimal.Decimal(unicode(soma_montantes_linha))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                soma_montantes_linha = float(aux)

                total = pag_ordem.montante_iliq
                if soma_montantes_linha != total:
                    raise osv.except_osv(_(u'A soma dos montantes das linhas da ordem a imprimir'),
                                         _(u'deve ser igual ao montante ilíquido da ordem de pagamento.'))

        else:
            if len(linhas_ordem_id) != 0:
                linhas_ordem = db_sncp_despesa_pagamentos_ordem_linha.browse(cr, uid, linhas_ordem_id)

                for linha_ordem in linhas_ordem:
                    soma_montantes_linha += linha_ordem.montante

                aux = decimal.Decimal(unicode(soma_montantes_linha))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                soma_montantes_linha = float(aux)

                if soma_montantes_linha == proposta.total_pagar:
                    return True
                else:
                    raise osv.except_osv(_(u'A soma dos montantes das linhas da ordem'),
                                         _(u'deve ser igual ao total a pagar da proposta.'))
        return True

    _constraints = [
        (montantes_linha_igual_total_pagar_proposta, u'', ['ordem_linha_id.montante']),
        (montantes_validos, u'', ['montante_iliq', 'montante_ret', 'montante_desc'])
    ]


sncp_despesa_pagamentos_ordem()

# ___________________________________________________________ORDEM LINHA_________________________________________


class sncp_despesa_pagamentos_ordem_linha(osv.Model):
    _name = 'sncp.despesa.pagamentos.ordem.linha'
    _description = u"Linhas da Ordem de Pagamento"

    _columns = {
        'opag_id': fields.many2one('sncp.despesa.pagamentos.ordem', u'Ordem de Pagamento'),
        'account_invoice_id': fields.many2one('account.invoice', u'Fatura'),
        'account_invoice_line_id': fields.many2one('account.invoice.line', u'Linha da Fatura'),
        'compromisso_id': fields.many2one('sncp.despesa.compromisso', u'Compromisso'),
        'compromisso_linha_id': fields.many2one('sncp.despesa.compromisso.linha', u'Linha do compromisso'),
        'montante': fields.float(u'Montante', digits=(12, 2)),

    }

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_despesa_pagamentos_ordem_linha, self).unlink(cr, uid, ids, context=context)


sncp_despesa_pagamentos_ordem_linha()

# __________________________________________________________________ORDEM IMPRIMIR______________________________


class sncp_despesa_pagamentos_ordem_linhas_imprimir(osv.Model):
    _name = 'sncp.despesa.pagamentos.ordem.linhas.imprimir'
    _description = u"Linhas de Impressão da Ordem de Pagamento"

    _columns = {
        'opag_id': fields.many2one('sncp.despesa.pagamentos.ordem', u'Ordem de Pagamento'),
        'name': fields.integer(u'Linha'),
        'num_fat_parceiro': fields.char(u'Fatura', size=15),
        'conta_contabil_id': fields.many2one('account.account', u'Conta SNCP'),
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')]),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')]),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')], ),
        'montante': fields.float(u'Valor', digits=(12, 2)),
    }

    _order = 'name'

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_despesa_pagamentos_ordem_linhas_imprimir, self).unlink(cr, uid, ids, context=context)


sncp_despesa_pagamentos_ordem_linhas_imprimir()

# _________________________________________________________________ORDEM fatura compromisso


class sncp_despesa_pagamentos_ordem_rel(osv.Model):
    _name = 'sncp.despesa.pagamentos.ordem.rel'
    _description = u"Ord. de Pag., Fat., L. da Fat., Comp. e L. do Comp."

    _columns = {
        'opag_id': fields.many2one('sncp.despesa.pagamentos.ordem', u'Ordem de Pagamento'),
        'account_invoice_id': fields.many2one('account.invoice', u'Fatura'),
        'account_invoice_line_id': fields.many2one('account.invoice.line', u'Linha da Fatura'),
        'compromisso_id': fields.many2one('sncp.despesa.compromisso', u'Compromisso'),
        'compromisso_linha_id': fields.many2one('sncp.despesa.compromisso.linha', u'Linha do compromisso'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
    }

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_despesa_pagamentos_ordem_rel, self).unlink(cr, uid, ids, context=context)


sncp_despesa_pagamentos_ordem_rel()