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

from datetime import datetime
import decimal
from decimal import *
from openerp.osv import fields, osv
from openerp.tools.translate import _
import tesouraria

# ________________________________________________ ORDEM (DESPESA)___________________________


class sncp_despesa_pagamentos_ordem(osv.Model):
    _inherit = 'sncp.despesa.pagamentos.ordem'

    def call_questionario(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        aux = decimal.Decimal(unicode(obj.montante_iliq - obj.montante_desc - obj.montante_ret))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_liq = float(aux)

        text = u'Anular a Ordem de Pagamento ' + unicode(obj.name) + u', de ' \
               + unicode(obj.paga) + u' no valor líquido de ' + unicode(montante_liq) + u'€' \
               u' a favor do ' + unicode(obj.partner_id.name) + u'?'

        text = text.replace(u'.', u',')
        return self.pool.get('formulario.mensagem.tesouraria').wizard(cr, uid, ids, text)

    def verifica_liquidado(self, cr, uid, ids, vals, context=None):
        db_account_move = self.pool.get('account.move')
        db_account_move_line = self.pool.get('account.move.line')
        db_res_users = self.pool.get('res.users')
        db_ir_sequence = self.pool.get('ir.sequence')
        db_account_journal = self.pool.get('account.journal')
        db_res_partner = self.pool.get('res.partner')
        db_account_invoice = self.pool.get('account.invoice')
        db_sncp_receita_op_tes = self.pool.get('sncp.receita.op.tes')
        db_account_tax = self.pool.get('account.tax')
        db_sncp_receita_op_tes_linhas = self.pool.get('sncp.receita.op.tes.linhas')
        db_sncp_despesa_pagamentos_rel = self.pool.get('sncp.despesa.pagamentos.rel')
        db_sncp_despesa_descontos_retencoes_rel_grec = self.pool.get('sncp.despesa.descontos.retencoes.rel.grec')
        db_sncp_receita_guia_rec = self.pool.get('sncp.receita.guia.rec')
        db_account_voucher = self.pool.get('account.voucher')
        db_account_voucher_line = self.pool.get('account.voucher.line')

        utilizador = db_res_users.browse(cr, uid, uid)

        obj_jornal = db_account_journal.browse(cr, uid, vals['diario_liq'])
        obj = self.browse(cr, uid, ids[0])
        dh = datetime.strptime(vals['datatransacao'], "%Y-%m-%d %H:%M:%S")
        ndata = dh.date()
        self.write(cr, uid, ids, {'liquidada': dh})
        ref = 'Ordem de pagamento ' + obj.name

        dicti = db_account_move.account_move_prepare(cr, uid, vals['diario_liq'], ndata, ref)
        dicti['name'] = obj.name
        move_id = db_account_move.create(cr, uid, dicti)
        self.write(cr, uid, ids, {'doc_liquida_id': move_id})
        valores = {'account_id': obj_jornal.default_credit_account_id.id,
                   'date': dicti['date'], 'journal_id': dicti['journal_id'],
                   'period_id': dicti['period_id'], 'name': dicti['ref'],
                   'move_id': move_id, 'credit': obj.montante_iliq,
                   'partner_id': obj.partner_id.id}
        db_account_move_line.create(cr, uid, valores)

        obj_parceiro = db_res_partner.browse(cr, uid, obj.partner_id.id)

        if obj.tipo == 'opt':
            db_account_move_line.create(cr, uid, {
                'account_id': obj_parceiro.property_account_payable.id, 'date': dicti['date'],
                'journal_id': dicti['journal_id'],
                'period_id': dicti['period_id'], 'name': dicti['ref'], 'move_id': move_id,
                'debit': obj.montante_iliq,
                'partner_id': obj.partner_id.id})
        else:
            cr.execute("""
            SELECT DISTINCT account_invoice_id
            FROM sncp_despesa_pagamentos_ordem_linha
            WHERE opag_id=%d
            """ % obj.id)
            lista_faturas = cr.fetchall()

            faturas_ids = [elem[0] for elem in lista_faturas]

            faturas_id = db_account_invoice.search(cr, uid, [('id', 'in', faturas_ids)])
            if len(faturas_id) == 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Não existem faturas associadas a este parceiro.'))

            conta_id = obj_parceiro.property_account_payable.id

            cr.execute("""
                            SELECT supplier_invoice_number
                            FROM account_invoice
                            WHERE id IN
                                  ( SELECT DISTINCT account_invoice_id
                                    FROM sncp_despesa_pagamentos_ordem_linha
                                    WHERE opag_id = %d)
                            """ % obj.id)

            lista = cr.fetchall()
            reference = ''
            if len(lista) == 0:
                cr.execute("""
                            SELECT AI.internal_number
                            FROM account_invoice AS AI
                            WHERE id IN
                                  ( SELECT DISTINCT account_invoice_id
                                    FROM sncp_despesa_pagamentos_ordem_linha
                                    WHERE opag_id = %d)
                            """ % obj.id)
                lista = cr.fetchall()

            for word in lista:
                if word[0] is None:
                    pass
                else:
                    if len(reference)+len(word[0]) > 64:
                        break
                    else:
                        reference += word[0] + u'; '

            # Pagamentos
            values = {
                'type': 'payment',
                'date': dh,
                'journal_id': vals['diario_pag'],
                'account_id': conta_id,
                'state': 'posted',
                'amount': obj.montante_iliq,
                'number': obj.name,
                'move_id': move_id,
                'partner_id': obj_parceiro.id,
                'pay_now': 'pay_now',
                'reference': reference,  # Numeros das Faturas dos Fornecedores
                'pre_line': False,
                'payment_option': 'without_writeoff',
                'comment': 'Write-Off',
                'payment_rate_currency_id': 1,
                'payment_rate': 1.0,
                'is_multi_currency': False,
            }
            voucher_id = db_account_voucher.create(cr, uid, values)

            for fatura_id in faturas_id:
                rel_id = db_sncp_despesa_pagamentos_rel.search(cr, uid, [('invoice_id', '=', fatura_id)])
                if len(rel_id) == 0:
                    raise osv.except_osv(_(u'Aviso'),
                                         _(u'Não existe ordem de pagamento associado a esta fatura.'))
                rel = db_sncp_despesa_pagamentos_rel.browse(cr, uid, rel_id[0])
                valor_liquidado = rel.montante_proc
                last_move_line_id = db_account_move_line.create(cr, uid, {
                    'account_id': conta_id, 'date': dicti['date'], 'journal_id': dicti['journal_id'],
                    'period_id': dicti['period_id'], 'name': dicti['ref'], 'move_id': move_id,
                    'debit': valor_liquidado, 'partner_id': obj.partner_id.id})

                aux = decimal.Decimal(unicode(rel.montante_pag+valor_liquidado))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante_pag = float(aux)

                aux = decimal.Decimal(unicode(rel.montante_proc-valor_liquidado))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante_proc = float(aux)

                db_sncp_despesa_pagamentos_rel.write(cr, uid, rel_id, {'montante_pag': montante_pag,
                                                                       'montante_proc': montante_proc})
                obj_fatura = db_account_invoice.browse(cr, uid, fatura_id)

                aux = decimal.Decimal(unicode(obj_fatura.residual-valor_liquidado))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante_fatura = float(aux)

                cr.execute("""
                UPDATE account_invoice
                SET residual = %f
                WHERE id = %d
                """ % (montante_fatura, fatura_id))

                cr.execute("""
                            SELECT COALESCE(SUM(montante),0.0)
                            FROM sncp_despesa_pagamentos_ordem_linha
                            WHERE opag_id=%d AND account_invoice_id = %d
                            """ % (obj.id, obj_fatura.id))

                amount = cr.fetchone()[0]
                values_linha = {
                    'voucher_id': voucher_id,
                    'name': obj_fatura.supplier_invoice_number,
                    'account_id': obj_jornal.default_credit_account_id.id,
                    'untax_amount': 0.0,
                    'amount': amount,
                    'reconcile': False,
                    'type': 'dr',
                    'move_line_id': last_move_line_id,
                }
                db_account_voucher_line.create(cr, uid, values_linha)

                # O bloco de atualização de historico
                values_historico = {'ano': ndata.year, 'dh': dh, 'move_id': move_id, 'categoria': '08dliqd',
                                    'move_line_id': last_move_line_id}
                self.atualiza_historico(cr, uid, [obj.id], values_historico)

                # Se houver retenções/descontos

        if vals['estado'] > 0:
            login = utilizador.login
            datahora = unicode(datetime.now())
            if datahora.find('.') != -1:
                datahora = datahora[:datahora.find('.')]
            chave_unica = login[:10]+'|'+unicode(datahora)
            rel_grec_ids = db_sncp_despesa_descontos_retencoes_rel_grec.search(cr, uid, [('opag_id', '=', obj.id)])

            numero_ret = 0
            numero_desc = 0
            obsv = None
            if len(rel_grec_ids) != 0:
                for rel_grec in db_sncp_despesa_descontos_retencoes_rel_grec.browse(cr, uid, rel_grec_ids):
                    if rel_grec.ret_desc_id.natureza == 'desc':
                        numero_desc += 1
                    else:
                        numero_ret += 1

                if numero_ret > 0:
                    if numero_desc > 0:
                        obsv = u'Descontos e Retenções'
                    else:
                        obsv = u'Retenções'
                elif numero_desc > 0:
                    if numero_ret > 0:
                        obsv = u'Descontos e Retenções'
                    else:
                        obsv = u'Descontos'

            obsv += u' da Ordem de Pagamento '+obj.name

            criar_op_tes = {'name': chave_unica,
                            'ordem': obj.name,
                            'department_id': vals['departamento_id'],
                            'partner_id': obj_parceiro.id,
                            'data': dh,
                            'obsv': obsv, }

            opt_tes_id = db_sncp_receita_op_tes.create(cr, uid, criar_op_tes)
            linha_tes = 1
            for rel_grec in db_sncp_despesa_descontos_retencoes_rel_grec.browse(cr, uid, rel_grec_ids):
                item = rel_grec.ret_desc_id.cod_contab_id.item_id

                cr.execute("""SELECT * FROM product_taxes_rel WHERE prod_id = %d""" % item.id)

                record = cr.fetchone()
                taxa = 0.0
                if record is None:
                    pass
                else:
                    obj_taxa = db_account_tax.browse(cr, uid, record[1])
                    taxa = obj_taxa.amount
                tax_rate = taxa
                montante_tax = rel_grec.montante-(rel_grec.montante/(1+tax_rate))

                aux = decimal.Decimal(unicode(montante_tax))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante_tax = float(aux)
                criar_linhas = {
                    'op_tes_id': opt_tes_id,
                    'name': linha_tes,
                    'cod_contab_id': rel_grec.ret_desc_id.cod_contab_id.id,
                    'desc':  rel_grec.ret_desc_id.name,
                    'montante': rel_grec.montante,
                    'tax_rate': tax_rate,
                    'montante_tax': montante_tax,
                    'obsv': None,
                }
                linha_tes += 1

                db_sncp_receita_op_tes_linhas.create(cr, uid, criar_linhas)

            criar_guia_receita = {'natureza': 'ots',
                                  'unique_key': chave_unica, }
            guia_id = db_sncp_receita_guia_rec.cria_guia_receita(cr, uid, [], criar_guia_receita, context=context)
            db_sncp_despesa_descontos_retencoes_rel_grec.write(cr, uid, rel_grec_ids, {'guia_rec_id': guia_id})

            obj_journal_guia_receb = db_account_journal.browse(cr, uid, vals['diario_liq_guia_rec'])
            if obj_journal_guia_receb.sequence_id.id:
                ngr = db_ir_sequence.next_by_id(cr, uid, obj_journal_guia_receb.sequence_id.id)
            else:
                raise osv.except_osv(_(u'Aviso'), _(u'O diário '+unicode(obj_journal_guia_receb.name) +
                                                    u' não têm sequência de movimentos associada.'))

            db_sncp_receita_guia_rec.write(cr, uid, guia_id, {'name': ngr})
            if obj.observ is not False:
                self.write(cr, uid, ids, {'observ': obj.observ + u'\nDescontos/Retenções constantes '
                                                                 u'da Guia de Recebimento '+ngr})
            else:
                self.write(cr, uid, ids, {'observ': u'Descontos/Retenções constantes da Guia de Recebimento '+ngr})

            cr.execute("""
                        SELECT id
                        FROM sncp_despesa_descontos_retencoes
                        WHERE opag_imediata = TRUE
                        AND id in (SELECT ret_desc_id FROM sncp_despesa_descontos_retencoes_rel_grec
                                      WHERE opag_id=%d)
                        """ % obj.id)

            desc_ret = cr.fetchall()
            if len(desc_ret) != 0:
                tesouraria.sncp_tesouraria_gera_opag_tes2opag(self, cr, uid, obj.id)

        return True

    def pag_ord_liq(self, cr, uid, ids, vals, context=None):
        self.verifica_liquidado(cr, uid, vals['opag_id'], vals)
        self.write(cr, uid, vals['opag_id'], {'state': 'liq'})
        self.pagar(cr, uid, vals['opag_id'], vals)
        self.write(cr, uid, vals['opag_id'], {'state': 'pag'})
        return True

    def atualiza_historico(self, cr, uid, ids, vals):
        db_sncp_orcamento_historico = self.pool.get('sncp.orcamento.historico')
        cr.execute("""
                    SELECT organica_id,economica_id,funcional_id,COALESCE(SUM(montante),0.0)
                    FROM sncp_despesa_pagamentos_ordem_linhas_imprimir
                    WHERE opag_id=%d
                    GROUP BY organica_id,economica_id,funcional_id
                    """ % ids[0])

        matriz = cr.fetchall()

        for linha in matriz:

            send = {'name': vals['ano'],
                    'categoria': vals['categoria'],
                    'datahora': vals['dh'],
                    'organica_id': linha[0],
                    'economica_id': linha[1],
                    'funcional_id': linha[2],
                    'montante': linha[3],
                    'centrocustos_id': None,
                    'cabimento_id': None,
                    'cabimento_linha_id': None,
                    'compromisso_id': None,
                    'compromisso_linha_id': None,
                    'doc_contab_id': vals['move_id'],
                    'doc_contab_linha_id': vals['move_line_id'], }
            db_sncp_orcamento_historico.insere_valores_historico(cr, uid, [], send)
        return True

    def movimento_contabilistico_pagamento(self, cr, uid, ids, vals):
        # values_movimento={
        #     'diario_pag':
        #     'diario_liq':
        #     'datahora':
        # }

        db_account_move = self.pool.get('account.move')
        db_account_move_line = self.pool.get('account.move.line')
        db_account_journal = self.pool.get('account.journal')
        obj = self.browse(cr, uid, ids[0])
        dh = datetime.strptime(vals['datahora'], "%Y-%m-%d %H:%M:%S")
        ndata = dh.date()
        self.write(cr, uid, ids, {'paga': dh})
        ref = u'Ordem de pagamento '+obj.name
        dicti = db_account_move.account_move_prepare(cr, uid, vals['diario_pag'], ndata, ref)
        dicti['name'] = obj.name
        move_id = db_account_move.create(cr, uid, dicti)
        self.write(cr, uid, ids, {'doc_pagam_id': move_id})
        conta_id = [0, 0]
        obj_jornal_liq = db_account_journal.browse(cr, uid, vals['diario_liq'])
        conta_id[0] = obj_jornal_liq.default_credit_account_id.id
        valores_debito = {'account_id': obj_jornal_liq.default_credit_account_id.id,
                          'date': dicti['date'], 'journal_id': dicti['journal_id'],
                          'period_id': dicti['period_id'], 'name': dicti['ref'],
                          'move_id': move_id, 'debit': obj.montante_iliq,
                          'partner_id': obj.partner_id.id}
        db_account_move_line.create(cr, uid, valores_debito)
        conta_id = [0, 0]
        if obj.ref_meio == 'cx':
            conta_id[1] = obj.caixa_id.conta_id.id
        elif obj.ref_meio == 'bk':
            conta_id[1] = obj.banco_id.conta_id.id
        elif obj.ref_meio == 'fm':
            conta_id[1] = obj.fundo_id.conta_id.id
        valores_credito = {'account_id': conta_id[1],
                           'date': dicti['date'], 'journal_id': dicti['journal_id'],
                           'period_id': dicti['period_id'], 'name': dicti['ref'],
                           'move_id': move_id, 'credit': obj.montante_iliq,
                           'partner_id': obj.partner_id.id}
        last_move_line_id = db_account_move_line.create(cr, uid, valores_credito)
        return [ndata, dh, move_id, last_move_line_id,
                obj.name, [obj.caixa_id.id, 0], [obj.banco_id.id, 0], [obj.fundo_id.id, 0]]

    def pagar(self, cr, uid, ids, vals):
        db_sncp_tesouraria_movimentos = self.pool.get('sncp.tesouraria.movimentos')
        db_sncp_despesa_descontos_retencoes_rel_grec = self.pool.get('sncp.despesa.descontos.retencoes.rel.grec')
        db_sncp_receita_guia_rec = self.pool.get('sncp.receita.guia.rec')
        db_sncp_tesouraria_cheques = self.pool.get('sncp.tesouraria.cheques')
        # Movimento contabilistico, cabeçalho e linhas

        values_movimento = {
            'diario_pag': vals['diario_pag'],
            'diario_liq': vals['diario_liq'],
            'datahora': vals['datatransacao'],
        }
        [ndata, dh, move_id, last_move_line_id, nop, caixa_id, banco_id, fundo_id] = \
            self.movimento_contabilistico_pagamento(cr, uid, ids, values_movimento)
        obj = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'doc_pagam_id': move_id})
        # O bloco de atualização de historico
        if obj.tipo != 'opt':
            values_historico = {'ano': ndata.year, 'dh': dh, 'move_id': move_id, 'categoria': '09pagam',
                                'move_line_id': last_move_line_id}
            self.atualiza_historico(cr, uid, [obj.id], values_historico)

        montante_ot = 0.00
        if obj.tipo == 'opt':
            montante_ot = obj.montante_iliq
        dict_movimento = {
            'datahora': dh,                         'montante': obj.montante_iliq,
            'name': nop,                            'origem_id': obj.meio_pag_id.id,
            'em_cheque': 0,                         'origem': 'recpag',
            'caixa_id': caixa_id,                   'montante_ot': montante_ot,
            'banco_id': banco_id,
            'fmaneio_id': fundo_id,
        }
        db_sncp_tesouraria_movimentos.cria_movimento_tesouraria(cr, uid, [], dict_movimento)

        rel_grec_ids = db_sncp_despesa_descontos_retencoes_rel_grec.search(cr, uid, [('opag_id', '=', ids[0])])
        if len(rel_grec_ids) != 0:
            values_liq = {'diario_id': vals['diario_liq_guia_rec'], 'datahora': dh}
            obj_rel_grec = db_sncp_despesa_descontos_retencoes_rel_grec.browse(cr, uid, rel_grec_ids[0])
            db_sncp_receita_guia_rec.liquida_guia_receita(cr, uid, [obj_rel_grec.guia_rec_id.id], values_liq)

            values_cobra = {'datahora': dh,
                            'diario_id': vals['diario_pag_guia_rec'],
                            'diario_liq': vals['diario_liq_guia_rec'],
                            'opag': obj, }
            db_sncp_receita_guia_rec.cobra_guia_receita(cr, uid, [obj_rel_grec.guia_rec_id.id], values_cobra)

        self.write(cr, uid, obj.id, {'anular': 0})

        if obj.serie_id.id:
            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_cheques
            WHERE state = 'nutl' and serie_id = %d
            ORDER BY numero
            """ % obj.serie_id.id)

            primeiro_cheque = cr.fetchone()

            if primeiro_cheque is not None:
                primeiro_cheque = primeiro_cheque[0]
                obj_cheque = db_sncp_tesouraria_cheques.browse(cr, uid, primeiro_cheque)
            else:
                raise osv.except_osv(_(u'Aviso'), _(u'Não existem cheques '
                                                    u'para se efetuar o pagamento.'))

            self.write(cr, uid, obj.id, {'num_pag': obj_cheque.numero})

            montante_liq = obj.montante_iliq - obj.montante_desc - obj.montante_ret
            aux = decimal.Decimal(unicode(montante_liq))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_liq = float(aux)

            vals_cheque = {
                'partner_id': obj.partner_id.id,
                'montante': montante_liq,
                'data_emissao': ndata,
                'state': 'pago',
                'opag_id': obj.id,
            }

            db_sncp_tesouraria_cheques.write(cr, uid, obj_cheque.id, vals_cheque)

        return True

    def anular_pagar(self, cr, uid, ids, context=None):
        db_sncp_tesouraria_cheques = self.pool.get('sncp.tesouraria.cheques')
        db_sncp_tesouraria_movimentos = self.pool.get('sncp.tesouraria.movimentos')
        db_sncp_orcamento_historico = self.pool.get('sncp.orcamento.historico')
        db_sncp_despesa_pagamentos_rel = self.pool.get('sncp.despesa.pagamentos.rel')
        db_account_invoice = self.pool.get('account.invoice')
        db_sncp_receita_guia_rec = self.pool.get('sncp.receita.guia.rec')
        db_sncp_tesouraria_folha_caixa = self.pool.get('sncp.tesouraria.folha.caixa')
        obj = self.browse(cr, uid, ids[0])
        nome_guia = u''
        # VERIFICAÇÃO DA ORDENS DE PAGAMENTOS ASSOCIADAS A ESTA TEREM SIDO PAGAS NÃO PODENDO ANULAR SEM
        # PRIMEIRO ANULAR ESTAS CASO CONSIGA
        cr.execute("""
        SELECT id FROM sncp_despesa_pagamentos_ordem
        WHERE id IN (SELECT opag_tes_id FROM sncp_despesa_descontos_retencoes_rel_opag WHERE opag_id = %d)
        AND state = 'pag'
        """ % obj.id)

        ots_pagas_ids = cr.fetchall()

        if len(ots_pagas_ids) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Existem ordem de pagamentos associadas a esta '
                                                u'que já foram pagas. Anule primeiro o pagamento das'
                                                u' mesmas.'))

        # ANULAR PAGAMENTO
        data = unicode(datetime.strptime(obj.paga, "%Y-%m-%d %H:%M:%S").date())
        fechada = db_sncp_tesouraria_folha_caixa.folha_caixa_fechada(cr, uid, ids, data)
        if fechada:
            if obj.tipo == 'orc':
                self.write(cr, uid, obj.id, {'anular': 1})
            text = u'O Mapa da data ' + data + u' encontra-se fechado.\nConsidere criar uma guia de reposição ' \
                                               u'abatida a pagamento se a ordem de pagamento é do tipo orçamental ' \
                                               u'para acerto de valores.'
            return self.pool.get('formulario.mensagem.despesa').wizard(cr, uid, [], text)
        else:
            cr.execute("""
            SELECT DISTINCT guia_rec_id
            FROM sncp_despesa_descontos_retencoes_rel_grec
            WHERE opag_id = %d
            """ % obj.id)

            guia_id = cr.fetchone()

            if isinstance(guia_id, tuple):
                guia_id = guia_id[0]

            cr.execute("""
            UPDATE sncp_despesa_descontos_retencoes_rel_grec SET guia_rec_id=NULL
            WHERE opag_id = %d
            """ % obj.id)

            if guia_id is not None:
                obj_guia = db_sncp_receita_guia_rec.browse(cr, uid, guia_id)
                nome_guia = obj_guia.name or u''
                if context is None:
                    context = dict()
                    context['op'] = True
                if obj_guia.state != 'cri':
                    db_sncp_receita_guia_rec.anula_cobranca(cr, uid, [guia_id], context=context)

            db_sncp_tesouraria_movimentos.elimina_movimento_tesouraria(cr, uid, ids,
                                                                       {'name': obj.name,
                                                                        'datahora': obj.paga})
            if obj.tipo == 'orc':
                dh = datetime.strptime(obj.paga, "%Y-%m-%d %H:%M:%S")
                ndata = dh.date()

                send = {'name': ndata.year,
                        'categoria': '09pagam',
                        'doc_contab_id': obj.doc_pagam_id.id}

                db_sncp_orcamento_historico.elimina_valores_historico(cr, uid, ids, send)

            cr.execute("""DELETE FROM account_move_line
            WHERE move_id = %d""" % obj.doc_pagam_id.id)
            cr.execute("""DELETE FROM account_move
            WHERE id = %d""" % obj.doc_pagam_id.id)

            # ANULAR LIQUIDAÇÃO
            cr.execute("""
            DELETE FROM sncp_despesa_pagamentos_ordem
            WHERE id IN (SELECT opag_tes_id FROM sncp_despesa_descontos_retencoes_rel_opag WHERE opag_id = %d)
            """ % obj.id)

            cr.execute("""
            DELETE FROM sncp_despesa_descontos_retencoes_rel_opag WHERE opag_id = %d
            """ % obj.id)

            if guia_id is not None:
                db_sncp_receita_guia_rec.anula_guia_receita(cr, uid, [guia_id], context=context)

            if obj.tipo == 'orc':
                dh = datetime.strptime(obj.liquidada, "%Y-%m-%d %H:%M:%S")
                ndata = dh.date()

                send = {'name': ndata.year,
                        'categoria': '08dliqd',
                        'doc_contab_id': obj.doc_liquida_id.id}

                db_sncp_orcamento_historico.elimina_valores_historico(cr, uid, ids, send)

                cr.execute("""
                SELECT id
                FROM account_voucher
                WHERE number = '%s'
                """ % obj.name)

                voucher_id = cr.fetchone()
                if voucher_id is not None:
                    cr.execute("""
                    DELETE FROM account_voucher_line
                    WHERE voucher_id = %d
                    """ % voucher_id[0])
                    cr.execute("""
                    DELETE FROM account_voucher
                    WHERE id = %d
                    """ % voucher_id[0])

                cr.execute("""
                SELECT DISTINCT account_invoice_id
                FROM sncp_despesa_pagamentos_ordem_linha
                WHERE opag_id = %d
                """ % obj.id)
                lista_faturas = cr.fetchall()

                faturas_ids = [elem[0] for elem in lista_faturas]

                for fatura_id in faturas_ids:
                    rel_id = db_sncp_despesa_pagamentos_rel.search(cr, uid, [('invoice_id', '=', fatura_id)])
                    if len(rel_id) == 0:
                        raise osv.except_osv(_(u'Aviso'),
                                             _(u'Não existe ordem de pagamento associado a esta fatura.'))
                    rel = db_sncp_despesa_pagamentos_rel.browse(cr, uid, rel_id[0])
                    valor_pago = rel.montante_pag

                    aux = decimal.Decimal(unicode(rel.montante_pag-valor_pago))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    montante_pag = float(aux)

                    aux = decimal.Decimal(unicode(rel.montante_proc+valor_pago))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    montante_proc = float(aux)

                    db_sncp_despesa_pagamentos_rel.write(cr, uid, rel_id, {'montante_pag': montante_pag,
                                                                           'montante_proc': montante_proc})
                    obj_fatura = db_account_invoice.browse(cr, uid, fatura_id)

                    aux = decimal.Decimal(unicode(obj_fatura.residual+valor_pago))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    montante_fatura = float(aux)

                    cr.execute("""
                    UPDATE account_invoice
                    SET residual = %f
                    WHERE id = %d
                    """ % (montante_fatura, fatura_id))

            cr.execute("""DELETE FROM account_move_line
            WHERE move_id = %d""" % obj.doc_liquida_id.id)
            cr.execute("""DELETE FROM account_move
            WHERE id = %d""" % obj.doc_liquida_id.id)

            # ATUALIZAR CAMPOS DA ORDEM DE PAGAMENTO
            obs_op = obj.observ
            observ = u''
            if obs_op:
                pos = obs_op.find(u'Descontos/Retenções constantes da Guia de Recebimento ' + nome_guia)
                if pos != -1:
                    if pos > 0:
                        observ = obs_op[:pos-1]
                else:
                    observ = obs_op

            cheque_id = db_sncp_tesouraria_cheques.search(cr, uid, [('opag_id', '=', obj.id)])

            if len(cheque_id) != 0:
                vals_cheque = {
                    'state': 'anul',
                    }

                db_sncp_tesouraria_cheques.write(cr, uid, cheque_id, vals_cheque)
            self.write(cr, uid, ids, {'name': None, 'conferida_user_id': None, 'conferida_data': None,
                                      'autorizada_user_id': None, 'autorizada_data': None, 'liquidada': None,
                                      'paga': None, 'state': 'draft', 'doc_liquidada_id': None,
                                      'doc_pagam_id': None, 'observ': observ, 'anular': None, 'num_pag': None})

            return {'type': 'ir.actions.client', 'tag': 'reload'}

    def on_change_meio(self, cr, uid, ids, meio_pag_id):
        if meio_pag_id is not False:
            db_sncp_comum_meios_pagamento = self.pool.get('sncp.comum.meios.pagamento')
            obj = db_sncp_comum_meios_pagamento.browse(cr, uid, meio_pag_id)
            if len(ids) != 0:
                if obj.meio == 'bk':
                    cr.execute("""
                    UPDATE sncp_despesa_pagamentos_ordem
                    SET caixa_id = NULL, fundo_id = NULL, banco_id = NULL,
                    estado_serie = 0, serie_id = NULL
                    WHERE id = %d
                    """ % ids[0])

                elif obj.meio == 'cx':
                    cr.execute("""
                    UPDATE sncp_despesa_pagamentos_ordem
                    SET banco_id = NULL, caixa_id = NULL, fundo_id = NULL, serie_id = NULL,
                    estado_serie = 0
                    WHERE id = %d
                    """ % ids[0])
                elif obj.meio == 'fm':
                    cr.execute("""
                    UPDATE sncp_despesa_pagamentos_ordem
                    SET fundo_id = NULL, banco_id = NULL, caixa_id = NULL, serie_id = NULL,
                    estado_serie = 0
                    WHERE id = %d
                    """ % ids[0])

                self.write(cr, uid, ids, {'ref_meio': obj.meio, 'estado_serie': 0})
            return {'value': {'ref_meio': obj.meio, 'estado_serie': 0, 'banco_id': None,
                              'caixa_id': None, 'fundo_id': None, 'serie_id': None}}
        return {'value': {'ref_meio': None, 'estado_serie': 0, 'serie_id': None}}

    _columns = {
        'banco_id': fields.many2one('sncp.tesouraria.contas.bancarias', u'Banco',
                                    domain=[('tipo', 'in', ['ord']), ('state', 'in', ['act'])]),
        'caixa_id': fields.many2one('sncp.tesouraria.caixas', u'Caixa'),
        'fundo_id': fields.many2one('sncp.tesouraria.fundos.maneio', u'Fundo de Maneio',
                                    domain=[('ativo', '=', True)]),
        'serie_id': fields.many2one('sncp.tesouraria.series', u'Série'),
    }

sncp_despesa_pagamentos_ordem()


class sncp_despesa_pagamentos_reposicoes(osv.Model):
    _inherit = 'sncp.despesa.pagamentos.reposicoes'

    def call_param(self, cr, uid, ids, context=None):
        return self.pool.get('formulario.sncp.tesouraria.pagamentos.reposicoes.diario').wizard(cr, uid, ids)

    def movimento_contabilistico(self, cr, uid, vals, norepo):
        db_sncp_despesa_pagamentos_reposicoes_linha = self.pool.get('sncp.despesa.pagamentos.reposicoes.linha')
        db_account_move = self.pool.get('account.move')
        db_account_move_line = self.pool.get('account.move.line')
        db_account_journal = self.pool.get('account.journal')

        obj = self.browse(cr, uid, vals['repo_id'])
        dh = datetime.strptime(vals['data'], "%Y-%m-%d %H:%M:%S")
        ndata = dh.date()
        ref = obj.opag_id.name

        obj_jornal = db_account_journal.browse(cr, uid, vals['diario_cob_id'])

        dicti = db_account_move.account_move_prepare(cr, uid, vals['diario_cob_id'], ndata, ref)
        dicti['narration'] = obj.motivo
        dicti['name'] = norepo
        move_id = db_account_move.create(cr, uid, dicti)

        valores_debito = {'account_id': obj_jornal.default_debit_account_id.id,
                          'date': dicti['date'], 'journal_id': dicti['journal_id'],
                          'period_id': dicti['period_id'], 'name': dicti['ref'],
                          'move_id': move_id, 'debit': obj.montante,
                          'partner_id': obj.opag_id.partner_id.id}

        db_account_move_line.create(cr, uid, valores_debito)

        linhas_grap_ids = db_sncp_despesa_pagamentos_reposicoes_linha.search(cr, uid, [('reposicao_id', '=', obj.id)])

        for linha_grap in db_sncp_despesa_pagamentos_reposicoes_linha.browse(cr, uid, linhas_grap_ids):

            if obj.opag_id.partner_id.property_account_payable.id is False:
                raise osv.except_osv(_(u'Aviso '), _(u'Defina as contas do parceiro de negócios '
                                                     + unicode(obj.opag_id.partner_id.name)+u'.'))
            else:
                valores_credito = {'account_id': obj.opag_id.partner_id.property_account_payable.id,
                                   'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                   'period_id': dicti['period_id'], 'name': dicti['ref'],
                                   'move_id': move_id, 'credit': linha_grap.montante_repor,
                                   'partner_id': obj.opag_id.partner_id.id}

                db_account_move_line.create(cr, uid, valores_credito)

        conta_id = False
        if vals['caixa_id'] is not False:
            cr.execute("""
            SELECT conta_id
            FROM sncp_tesouraria_caixas
            WHERE id=%d
            """ % vals['caixa_id'])

            conta_id = cr.fetchone()

            if conta_id is None:
                raise osv.except_osv(_(u'Aviso'), _(u'A caixa selecionada não têm conta associada.'))
            else:
                conta_id = conta_id[0]

        elif vals['banco_id'] is not False:
            cr.execute("""
            SELECT conta_id
            FROM sncp_tesouraria_contas_bancarias
            WHERE id=%d
            """ % vals['banco_id'])

            conta_id = cr.fetchone()

            if conta_id is None:
                raise osv.except_osv(_(u'Aviso'), _(u'O banco selecionado não têm conta associada.'))
            else:
                conta_id = conta_id[0]

        elif vals['fundo_id'] is not False:
            cr.execute("""
            SELECT conta_id
            FROM sncp_tesouraria_fundos_maneio
            WHERE id=%d
            """ % vals['fundo_id'])

            conta_id = cr.fetchone()

            if conta_id is None:
                raise osv.except_osv(_(u'Aviso'), _(u'O fundo de maneio '
                                                    u' selecionado não têm conta associada.'))
            else:
                conta_id = conta_id[0]

        caixa_banco_fundo_valores_debito = {'account_id': conta_id,
                                            'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                            'period_id': dicti['period_id'], 'name': dicti['ref'],
                                            'move_id': move_id, 'debit': obj.montante,
                                            'partner_id': obj.opag_id.partner_id.id}

        db_account_move_line.create(cr, uid, caixa_banco_fundo_valores_debito)

        jornal_valores_credito = {'account_id': obj_jornal.default_debit_account_id.id,
                                  'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                  'period_id': dicti['period_id'], 'name': dicti['ref'],
                                  'move_id': move_id, 'credit': obj.montante,
                                  'partner_id': obj.opag_id.partner_id.id}

        last_move_line_id = db_account_move_line.create(cr, uid, jornal_valores_credito)

        return [move_id, last_move_line_id, ndata]

    def insere_historico(self, cr, uid, ano, categoria, data, linha, move_id, last_move_line_id):
        db_sncp_orcamento_historico = self.pool.get('sncp.orcamento.historico')
        montante = 0.0
        if categoria == '08dliqd':
            montante = -1*linha.montante_repor
        elif categoria == '09pagam':
            montante = -1*linha.montante_repor
        elif categoria == '10repos':
            montante = linha.montante_repor

        send = {'name': ano,
                'categoria': categoria,
                'datahora': data,
                'organica_id': linha.account_invoice_line_id.organica_id.id,
                'economica_id': linha.account_invoice_line_id.economica_id.id,
                'funcional_id': linha.account_invoice_line_id.funcional_id.id,
                'montante': montante,
                'centrocustos_id': None,
                'cabimento_id': None,
                'cabimento_linha_id': None,
                'compromisso_id': None,
                'compromisso_linha_id': None,
                'doc_contab_id': move_id,
                'doc_contab_linha_id': last_move_line_id, }

        db_sncp_orcamento_historico.insere_valores_historico(cr, uid, [], send)

    def cobrar(self, cr, uid, ids, vals):
        db_sncp_despesa_pagamentos_reposicoes_linha = self.pool.get('sncp.despesa.pagamentos.reposicoes.linha')
        db_ir_sequence = self.pool.get('ir.sequence')
        db_account_journal = self.pool.get('account.journal')
        db_sncp_tesouraria_movimentos = self.pool.get('sncp.tesouraria.movimentos')
        db_sncp_despesa_pagamentos_rel = self.pool.get('sncp.despesa.pagamentos.rel')

        db_account_voucher = self.pool.get('account.voucher')
        db_account_voucher_line = self.pool.get('account.voucher.line')
        obj = self.browse(cr, uid, vals['repo_id'])
        obj_jornal = db_account_journal.browse(cr, uid, vals['diario_cob_id'])
        if obj_jornal.sequence_id.id:
            norepo = db_ir_sequence.next_by_id(cr, uid, obj_jornal.sequence_id.id)
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'O diário '+unicode(obj_jornal.name) +
                                                u' não têm sequência de movimentos associada.'))

        [move_id, last_move_line_id, ndata] = self.movimento_contabilistico(cr, uid, vals, norepo)

        linha_grap_ids = db_sncp_despesa_pagamentos_reposicoes_linha.search(cr, uid, [('reposicao_id', '=', obj.id)])

        for linha in db_sncp_despesa_pagamentos_reposicoes_linha.browse(cr, uid, linha_grap_ids):

            cr.execute("""
            SELECT COALESCE(residual,0.0)
            FROM account_invoice
            WHERE id = %d
            """ % linha.account_invoice_line_id.invoice_id.id)

            residual = cr.fetchone()

            if residual is not None:
                residual = residual[0]
            else:
                residual = 0.0

            residual += linha.montante_repor

            aux = decimal.Decimal(unicode(residual))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            residual = float(aux)

            cr.execute("""
                UPDATE account_invoice
                SET residual = %f
                WHERE id = %d
                """ % (residual, linha.account_invoice_line_id.invoice_id.id))

            rel_id = db_sncp_despesa_pagamentos_rel.search(cr, uid, [('invoice_id', '=',
                                                                      linha.account_invoice_line_id.invoice_id.id)])

            if len(rel_id) != 0:
                relacao = db_sncp_despesa_pagamentos_rel.browse(cr, uid, rel_id[0])
                montante_pago = relacao.montante_pag+linha.montante_repor

                aux = decimal.Decimal(unicode(montante_pago))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante_pago = float(aux)

                db_sncp_despesa_pagamentos_rel.write(cr, uid, rel_id, {'montante_pag': montante_pago})

        cr.execute("""
                      SELECT DISTINCT REPLINHA.name
                      FROM  sncp_despesa_pagamentos_reposicoes_linha AS REPLINHA
                      WHERE reposicao_id = %d
                  """ % obj.id)

        lista = cr.fetchall()
        reference = ''
        for word in lista:
            if word[0] is None:
                pass
            else:
                if len(reference)+len(word[0]) > 64:
                    break
                else:
                    reference += word[0] + '; '

        # CRIA VOUCHER COM MONTANTES NEGATIVOS
        values = {'type': 'payment',
                  'date': vals['data'],
                  'journal_id': vals['diario_cob_id'],
                  'account_id': obj.opag_id.partner_id.property_account_payable.id,
                  'state': 'posted',
                  'amount': -1*obj.montante,
                  'number': norepo,
                  'move_id': move_id,
                  'partner_id': obj.opag_id.partner_id.id,
                  'pay_now': 'pay_now',
                  'reference': reference,
                  'pre_line': False,
                  'payment_option': 'without_writeoff',
                  'comment': 'Write-Off',
                  'payment_rate_currency_id': 1,
                  'payment_rate': 1.0,
                  'is_multi_currency': False, }

        voucher_id = db_account_voucher.create(cr, uid, values)
        for linha in db_sncp_despesa_pagamentos_reposicoes_linha.browse(cr, uid, linha_grap_ids):

            values_linha = {'voucher_id': voucher_id,
                            'name': linha.name,
                            'account_id': obj_jornal.default_credit_account_id.id,
                            'untax_amount': 0.0,
                            'amount': -1*linha.montante_repor,
                            'reconcile': False,
                            'type': 'dr',
                            'move_line_id': last_move_line_id, }

            db_account_voucher_line.create(cr, uid, values_linha)

        linhas_grap_ids = db_sncp_despesa_pagamentos_reposicoes_linha.search(cr, uid, [('reposicao_id', '=', obj.id)])

        # INSERE 3 LINHAS NO HISTÓRICOS
        # REPOSIÇÃO
        # LIQUIDAÇÃO
        # PAGAMENTO
        for linha in db_sncp_despesa_pagamentos_reposicoes_linha.browse(cr, uid, linhas_grap_ids):
            self.insere_historico(cr, uid, ndata.year, '10repos', vals['data'], linha, move_id, last_move_line_id)
            self.insere_historico(cr, uid, ndata.year, '08dliqd', vals['data'], linha, move_id, last_move_line_id)
            self.insere_historico(cr, uid, ndata.year, '09pagam', vals['data'], linha, move_id, last_move_line_id)

        # CRIA MOVIMENTO DE TESOURARIA
        # [0,obj.caixa_id.id], [0,obj.banco_id.id], [0,obj.fundo_id.id]
        dict_movimento = {
            'datahora': vals['data'],               'montante': obj.montante,
            'name': norepo,                         'origem_id': vals['meio_pag_id'],
            'em_cheque': 0,                         'origem': 'recpag',
            'caixa_id': [0, vals['caixa_id']],       'montante_ot': 0.00,
            'banco_id': [0, vals['banco_id']],
            'fmaneio_id': [0, vals['fundo_id']],
        }

        db_sncp_tesouraria_movimentos.cria_movimento_tesouraria(cr, uid, [], dict_movimento)

        rep_vals = {'meio_pag_id': vals['meio_pag_id'],
                    'meio_desc': vals['meio_desc'],
                    'ref_meio': vals['ref_meio'],
                    'bcfm': vals['bcfm'],
                    'banco_id': vals['banco_id'],
                    'caixa_id': vals['caixa_id'],
                    'fundo_id': vals['fundo_id'],
                    'num_pag': vals['name'],
                    'name': norepo,
                    'cobrada_emp': uid,
                    'cobrada_data': vals['data'],
                    'doc_cobranca_id': move_id,
                    'state': 'cobrd',
                    'imprimir': 1, }

        self.write(cr, uid, vals['repo_id'], rep_vals)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    _columns = {
        'banco_id': fields.many2one('sncp.tesouraria.contas.bancarias', u'Banco',
                                    domain=[('tipo', 'in', ['ord'])]),
        'caixa_id': fields.many2one('sncp.tesouraria.caixas', u'Caixa'),
        'fundo_id': fields.many2one('sncp.tesouraria.fundos.maneio', u'Fundo de Maneio'),

    }

sncp_despesa_pagamentos_reposicoes()