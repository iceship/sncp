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

import controlo


def get_sequence(self, cr, uid, context, text, value):
    # TEXT
    # para linhas de guia 'guia_rec'
    # para meios de guia  'meio_guia_rec'
    # para faturas cobrar linhas 'fat_cobr'

    seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_'+text+'_code_'+unicode(value))
    if seq is False:
        sequence_type = self.pool.get('ir.sequence.type')
        values_type = {
            'name': 'type_'+text+'_name_'+unicode(value),
            'code':  'seq_'+text+'_code_'+unicode(value), }
        sequence_type.create(cr, uid, values_type, context=context)
        sequence = self.pool.get('ir.sequence')
        values = {
            'name': 'seq_'+text+'_name_'+unicode(value),
            'code':  'seq_'+text+'_code_'+unicode(value),
            'number_next': 1,
            'number_increment': 1, }
        sequence.create(cr, uid, values, context=context)
        return self.pool.get('ir.sequence').get(cr, uid, 'seq_'+text+'_code_'+unicode(value))
    else:
        return seq


def test_item_id(self, cr, uid, item_id):
    db_product_product = self.pool.get('product.product')
    obj_product = db_product_product.browse(cr, uid, item_id)
    message = ''

    if hasattr(obj_product.product_tmpl_id, 'property_account_expense'):
        if obj_product.product_tmpl_id.property_account_expense.id is False:
            message += u'Contabilidade/Conta de Despesa associada ao fornecedor\n'
    else:
        message += u'Contabilidade/Conta de Despesa associada ao fornecedor\n'

    if hasattr(obj_product.product_tmpl_id, 'property_account_income'):
        if obj_product.product_tmpl_id.property_account_income.id is False:
            message += u'Contabilidade/Conta de Despesa associada ao cliente\n'
    else:
        message += u'Contabilidade/Conta de Despesa associada ao cliente\n'

    if obj_product.product_tmpl_id.list_price <= 0:
        message += u'Informação/Preço de Venda\n'

    if obj_product.default_code is False:
        message += u'Informação/Referência Interna\n'

    if len(obj_product.product_tmpl_id.taxes_id) == 0:
        message += u'Contabilidade/Impostos a Cliente\n'

    if len(obj_product.product_tmpl_id.supplier_taxes_id) == 0:
        message += u'Contabilidade/Impostos do Fornecedor\n'

    if obj_product.product_tmpl_id.categ_id.id is not False:
        x = obj_product.product_tmpl_id.categ_id.property_stock_valuation_account_id.id

        if x is False:
            message += u' Para as categorias dos artigos defina a Conta de avaliação de stock'

    if len(message) != 0:
        raise osv.except_osv(_(u'Aviso'), _(u'Para evitar futuros erros na execução do programa '
                                            u'deverá preencher os seguintes campos do artigo:\n'+message))
    return True
# _____________________________________________________GUIA RECEITA________________________________


class sncp_receita_guia_rec(osv.Model):
    _name = 'sncp.receita.guia.rec'
    _description = u"Guia de Receita"

    def atualiza(self, cr, uid, ids, context=None):
        return True

    def on_change_part_depart(self, cr, uid, ids, partner_id, department_id, context=None):
        db_res_partner = self.pool.get('res.partner')
        db_hr_department = self.pool.get('hr.department')

        if partner_id is False:
            if department_id is False:
                if len(ids) != 0:
                    self.write(cr, uid, ids, {'partner_department': None})
            else:
                obj_departamento = db_hr_department.browse(cr, uid, department_id)
                if len(ids) != 0:
                    self.write(cr, uid, ids, {'partner_department': obj_departamento.name})
        elif department_id is False:
            if partner_id is False:
                if len(ids) != 0:
                    self.write(cr, uid, ids, {'partner_department': None})
            else:
                obj_parceiro = db_res_partner.browse(cr, uid, partner_id)
                if len(ids) != 0:
                    self.write(cr, uid, ids, {'partner_department': obj_parceiro.name})
        else:
            obj_parceiro = db_res_partner.browse(cr, uid, partner_id)
            obj_departamento = db_hr_department.browse(cr, uid, department_id)
            if len(ids) != 0:
                self.write(cr, uid, ids, {'partner_department': obj_parceiro.name+'/'+obj_departamento.name})

        return {}

    def montante_original(self, cr, uid, ids, vals):
        db_account_tax = self.pool.get('account.tax')
        cr.execute("""SELECT *  FROM account_invoice_line_tax WHERE invoice_line_id = %d"""
                   % vals['linha_fatura'].id)
        record = cr.fetchone()
        taxa = 0.0
        if record is None:
            pass
        else:
            obj_taxa = db_account_tax.browse(cr, uid, record[1])
            taxa = obj_taxa.amount
        aux = decimal.Decimal(unicode((taxa+1)*vals['linha_fatura'].price_subtotal))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_original = float(aux)
        aux1 = decimal.Decimal(unicode(taxa*vals['linha_fatura'].price_subtotal))
        aux1 = aux1.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_taxa = float(aux1)
        return [montante_original, montante_taxa, taxa]

    def cria_guia_receita(self, cr, uid, ids, vals, context):
        # vals = {
        #     'natureza': 'rec',
        #     'unique_key': '',
        # }
        db_sncp_receita_guia_rec_linhas = self.pool.get('sncp.receita.guia.rec.linhas')
        db_sncp_receita_guia_rec_rel = self.pool.get('sncp.receita.guia.rec.rel')

        guia_id = None
        categoria = 'evn'
        if vals['natureza'] == 'rec':
            # cabeçalho
            db_sncp_receita_fact_cobrar = self.pool.get('sncp.receita.fact.cobrar')
            db_sncp_receita_fact_cobrar_linhas = self.pool.get('sncp.receita.fact.cobrar.linhas')
            db_account_invoice_line = self.pool.get('account.invoice.line')
            fact_cobr_id = db_sncp_receita_fact_cobrar.search(cr, uid, [('name', '=', vals['unique_key'])])
            obj_fact_cobr = db_sncp_receita_fact_cobrar.browse(cr, uid, fact_cobr_id[0])
            linhas_cobrar_ids = db_sncp_receita_fact_cobrar_linhas.search(cr, uid, [('fact_cobrar_id', '=',
                                                                                     obj_fact_cobr.id),
                                                                                    ('a_processar', '=', True)])
            montante_total = 0.0
            for obj_linha_cobr in db_sncp_receita_fact_cobrar_linhas.browse(cr, uid, linhas_cobrar_ids):
                if guia_id is None:
                    partner_department = ''
                    cr.execute("""
                        SELECT name
                        FROM res_partner
                        WHERE id = %d
                        """ % obj_fact_cobr.partner_id.id)

                    nome_parceiro = cr.fetchone()

                    if nome_parceiro is not None:
                        partner_department += nome_parceiro[0]

                        cr.execute("""
                        SELECT name
                        FROM hr_department
                        WHERE id = %d
                        """ % obj_fact_cobr.department_id.id)

                    nome_departamento = cr.fetchone()
                    if nome_departamento is not None:
                        partner_department += u'/'+nome_departamento[0]

                    values_guia = {
                        'department_id': obj_fact_cobr.department_id.id,
                        'partner_id': obj_fact_cobr.partner_id.id,
                        'origem': obj_fact_cobr.origem,
                        'obsv': obj_fact_cobr.obsv,
                        'categoria': categoria,
                        'natureza': vals['natureza'],
                        'data_emissao': obj_fact_cobr.data,
                        'partner_department': partner_department,
                        }

                    guia_id = self.create(cr, uid, values_guia)

                cr.execute("""
                    SELECT create_uid
                    FROM sncp_receita_guia_rec
                    WHERE id=%d
                """ % guia_id)

                user_id = cr.fetchone()
                if user_id is not None:
                    user_id = user_id[0]

                self.write(cr, uid, guia_id, {'user_id': user_id})

                proporcao = obj_linha_cobr.montante_cobr / obj_linha_cobr.montante_orig
                #   ___________________PROCESSAMENTO DE LINHAS DA FATURA___________________
                linhas_fatura_ids = db_account_invoice_line.search(cr, uid, [('invoice_id', '=',
                                                                             obj_linha_cobr.fatura_id.id)])
                for obj_linha_fatura in db_account_invoice_line.browse(cr, uid, linhas_fatura_ids):
                    diti = {'linha_fatura': obj_linha_fatura}
                    [montante_orig, montante_taxa, taxa_amount] = self.montante_original(cr, uid, ids, diti)
                    montante_orig_prop = montante_orig * proporcao
                    montante_total += montante_orig_prop
                    montante_taxa_prop = montante_taxa * proporcao

                    aux = decimal.Decimal(unicode(montante_orig_prop))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    montante_orig_prop = float(aux)

                    aux1 = decimal.Decimal(unicode(montante_taxa_prop))
                    aux1 = aux1.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    montante_taxa_prop = float(aux1)

                    linha_guia_ids = db_sncp_receita_guia_rec_linhas.search(cr, uid, [
                        ('natureza', '=', obj_linha_fatura.natureza),
                        ('conta_id', '=', obj_linha_fatura.account_id.id),
                        ('economica_id', '=', obj_linha_fatura.economica_id.id),
                        ('tax_rate', '=', taxa_amount),
                        ('guia_rec_id', '=', guia_id)])
                    if len(linha_guia_ids) != 0:
                        obj_linha_guia = db_sncp_receita_guia_rec_linhas.browse(cr, uid, linha_guia_ids[0])

                        if obj_linha_fatura.natureza == 'ots':
                            aux = decimal.Decimal(unicode(montante_taxa_prop+obj_linha_guia.montante_tax))
                            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                            montante_tax = float(aux)

                            aux = decimal.Decimal(unicode(montante_orig_prop+obj_linha_guia.montante_ots))
                            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                            montante_ots = float(aux)

                            db_sncp_receita_guia_rec_linhas.write(cr, uid, linha_guia_ids, {'montante_tax':
                                                                                            montante_tax,
                                                                                            'montante_ots':
                                                                                            montante_ots})
                        else:
                            aux = decimal.Decimal(unicode(montante_taxa_prop+obj_linha_guia.montante_tax))
                            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                            montante_tax = float(aux)

                            aux = decimal.Decimal(unicode(montante_orig_prop+obj_linha_guia.montante_orc))
                            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                            montante_orc = float(aux)

                            db_sncp_receita_guia_rec_linhas.write(cr, uid, linha_guia_ids, {'montante_tax':
                                                                                            montante_tax,
                                                                                            'montante_orc':
                                                                                            montante_orc})
                    else:
                        if not obj_linha_fatura.natureza:
                            raise osv.except_osv(_(u'Aviso'), _(u'Natureza não definida para a linha da fatura '
                                                                + obj_linha_fatura.invoice_id.internal_number
                                                                + u' com o produto '
                                                                + obj_linha_fatura.product_id.name_template))

                        cr.execute("""
                        SELECT id
                        FROM sncp_comum_codigos_contab
                        WHERE item_id = %d AND natureza = '%s'
                        """ % (obj_linha_fatura.product_id.id, obj_linha_fatura.natureza))

                        cod_contab_id = cr.fetchone()

                        if cod_contab_id is not None:
                            cod_contab_id = cod_contab_id[0]
                        else:
                            raise osv.except_osv(_(u'Para o produto '
                                                   + unicode(obj_linha_fatura.product_id.name_template)),
                                                 _(u' não existe código de contabilização de natureza '
                                                   u' receita orçamental ou operações de tesouraria.'))

                        values_guia_linha = {
                            'montante_tax': montante_taxa_prop,
                            'guia_rec_id': guia_id,
                            'name': get_sequence(self, cr, uid, context, 'guia_rec', guia_id),
                            'tax_rate': taxa_amount,
                            'natureza': obj_linha_fatura.natureza,
                            'conta_id': obj_linha_fatura.account_id.id,
                            'economica_id': obj_linha_fatura.economica_id.id,
                            'obsv': obj_linha_cobr.obsv,
                            'cod_contab_id': cod_contab_id,
                        }
                        guia_linha_id = db_sncp_receita_guia_rec_linhas.create(cr, uid, values_guia_linha)
                        if obj_linha_fatura.natureza == 'ots':
                            db_sncp_receita_guia_rec_linhas.write(cr, uid, guia_linha_id,
                                                                  {'montante_ots': montante_orig_prop})
                        else:
                            db_sncp_receita_guia_rec_linhas.write(cr, uid, guia_linha_id,
                                                                  {'montante_orc': montante_orig_prop})

                db_sncp_receita_guia_rec_rel.create(cr, uid, {'guia_id': guia_id,
                                                              'fatura_id': obj_linha_cobr.fatura_id.id,
                                                              'montante_pend': obj_linha_cobr.montante_pend,
                                                              'montante_cobr': obj_linha_cobr.montante_cobr, })

            aux = decimal.Decimal(unicode(montante_total))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_total = float(aux)

            self.write(cr, uid, guia_id, {'montante': montante_total})

            # #### CRIAÇÃO DE MEIOS
            db_sncp_receita_guia_rec_meios = self.pool.get('sncp.receita.guia.rec.meios')
            meios_vals = {
                'guia_rec_id': guia_id,
                'meio_rec': 'num',
                'montante': montante_total,
            }

            db_sncp_receita_guia_rec_meios.create(cr, uid, meios_vals)
            # ########################

            db_sncp_receita_fact_cobrar_linhas.unlink(cr, uid, linhas_cobrar_ids)
            db_sncp_receita_fact_cobrar.unlink(cr, uid, fact_cobr_id)

        elif vals['natureza'] == 'ots':
            origem = 'part'
            values = {}
            # cabeçalho
            db_sncp_receita_op_tes = self.pool.get('sncp.receita.op.tes')
            tes_id = db_sncp_receita_op_tes.search(cr, uid, [('name', '=', vals['unique_key'])])
            obj = db_sncp_receita_op_tes.browse(cr, uid, tes_id[0])
            values['natureza'] = vals['natureza']
            values['categoria'] = categoria
            values['origem'] = origem
            values['department_id'] = obj.department_id.id
            values['partner_id'] = obj.partner_id.id
            values['data_emissao'] = obj.data

            if values['partner_id'] is False:
                if values['department_id'] is False:
                    values['partner_department'] = None
                else:
                    values['partner_department'] = obj.department_id.name

            elif values['department_id'] is False:
                if values['partner_id'] is False:
                    values['partner_department'] = None
                else:
                    values['partner_department'] = obj.partner_id.name

            else:
                values['partner_department'] = obj.partner_id.name+'/'+obj.department_id.name

            values['obsv'] = obj.obsv
            values['state'] = 'cri'
            guia_id = self.create(cr, uid, values)

            cr.execute("""
                        SELECT create_uid
                        FROM sncp_receita_guia_rec
                        WHERE id=%d
                        """ % guia_id)

            user_id = cr.fetchone()
            if user_id is not None:
                user_id = user_id[0]

            self.write(cr, uid, guia_id, {'user_id': user_id})
            # linhas
            db_sncp_receita_guia_rec_linhas = self.pool.get('sncp.receita.guia.rec.linhas')
            db_sncp_receita_op_tes_linhas = self.pool.get('sncp.receita.op.tes.linhas')
            db_sncp_receita_codigos_contab = self.pool.get('sncp.comum.codigos.contab')
            linhas_cobrar_ids = db_sncp_receita_op_tes_linhas.search(cr, uid, [('op_tes_id', '=', tes_id[0])])
            montante = 0.00
            for obj_linha_cobr in linhas_cobrar_ids:
                valines = dict()
                valines['guia_rec_id'] = guia_id
                valines['name'] = get_sequence(self, cr, uid, context, 'guia_rec', guia_id,)

                obj_linha = db_sncp_receita_op_tes_linhas.browse(cr, uid, obj_linha_cobr)
                valines['desc'] = obj_linha.desc
                valines['tax_rate'] = obj_linha.tax_rate
                valines['obsv'] = obj_linha.obsv
                valines['montante_ots'] = obj_linha.montante
                valines['montante_tax'] = obj_linha.montante_tax
                montante += obj_linha.montante

                cod_contab_id = obj_linha.cod_contab_id.id
                obj_cod_contab = db_sncp_receita_codigos_contab.browse(cr, uid, cod_contab_id)
                valines['conta_id'] = obj_cod_contab.conta_id.id
                valines['cod_contab_id'] = cod_contab_id
                valines['economica_id'] = obj_cod_contab.economica_id.id
                valines['natureza'] = 'ots'

                db_sncp_receita_guia_rec_linhas.create(cr, uid, valines)

            aux = decimal.Decimal(unicode(montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante = float(aux)
            self.write(cr, uid, guia_id, {'montante': montante})

            # #### CRIAÇÃO DE MEIOS
            db_sncp_receita_guia_rec_meios = self.pool.get('sncp.receita.guia.rec.meios')
            meios_vals = {
                'guia_rec_id': guia_id,
                'meio_rec': 'num',
                'montante': montante,
            }

            db_sncp_receita_guia_rec_meios.create(cr, uid, meios_vals)
            # ########################
            db_sncp_receita_op_tes.unlink(cr, uid, tes_id)

        return guia_id

    def movimento_contabilistico_liquidacao(self, cr, uid, ids, vals):
        # values_movimento={
        #     'diario_liq':
        #     'datahora':
        # }
        db_account_move = self.pool.get('account.move')
        db_account_move_line = self.pool.get('account.move.line')
        db_ir_sequence = self.pool.get('ir.sequence')
        db_account_journal = self.pool.get('account.journal')
        db_sncp_receita_guia_rec_linhas = self.pool.get('sncp.receita.guia.rec.linhas')
        db_sncp_orcamento_historico = self.pool.get('sncp.orcamento.historico')

        obj_jornal = db_account_journal.browse(cr, uid, vals['diario_liq'])
        if obj_jornal.sequence_id.id:
            nog = db_ir_sequence.next_by_id(cr, uid, obj_jornal.sequence_id.id)
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'O diário '+unicode(obj_jornal.name)
                                                + u' não têm sequência de movimentos associada.'))

        obj = self.browse(cr, uid, ids[0])
        if not obj.name:
            self.write(cr, uid, ids, {'name': nog})
        else:
            nog = obj.name
        ndata = vals['datahora'].date()
        self.write(cr, uid, ids, {'liquidada': vals['datahora']})
        ref = 'Guia de Receita ' + nog

        dicti = db_account_move.account_move_prepare(cr, uid, vals['diario_liq'], ndata, ref)
        dicti['name'] = nog

        move_id = db_account_move.create(cr, uid, dicti)

        self.write(cr, uid, ids, {'doc_liquida_id': move_id})

        valores_debito = {
            'account_id': obj_jornal.default_debit_account_id.id,
            'date': dicti['date'], 'journal_id': dicti['journal_id'],
            'period_id': dicti['period_id'], 'name': dicti['ref'],
            'move_id': move_id, 'debit': obj.montante,
            'partner_id': obj.partner_id.id}

        move_line_id = db_account_move_line.create(cr, uid, valores_debito)

        linhas_guia_ids = db_sncp_receita_guia_rec_linhas.search(cr, uid, [('guia_rec_id', '=', obj.id)])
        for obj_linha_guia in db_sncp_receita_guia_rec_linhas.browse(cr, uid, linhas_guia_ids):
            if obj_linha_guia.natureza == 'rec':
                credit = obj_linha_guia.montante_orc
            else:
                credit = obj_linha_guia.montante_ots
            valores_credito = {'account_id': obj_linha_guia.conta_id.id,
                               'date': dicti['date'], 'journal_id': dicti['journal_id'],
                               'period_id': dicti['period_id'], 'name': dicti['ref'],
                               'move_id': move_id, 'credit': credit,
                               'partner_id': obj.partner_id.id}
            move_line_id = db_account_move_line.create(cr, uid, valores_credito)
            if obj_linha_guia.natureza == 'rec' and obj.natureza == 'rec':
                send = {'name': ndata.year,
                        'categoria': '57rliqd',
                        'datahora': vals['datahora'],
                        'organica_id': None,
                        'economica_id': obj_linha_guia.economica_id.id,
                        'funcional_id': None,
                        'montante': obj_linha_guia.montante_orc,
                        'centrocustos_id': None,
                        'cabimento_id': None,
                        'cabimento_linha_id': None,
                        'compromisso_id': None,
                        'compromisso_linha_id': None,
                        'doc_contab_id': move_id,
                        'doc_contab_linha_id': move_line_id, }
                db_sncp_orcamento_historico.insere_valores_historico(cr, uid, [], send)

        return [move_id, move_line_id, nog]

    def liquida_guia_receita(self, cr, uid, ids, vals):
        # vals = {
        #   'diario_id': ,
        #   'datahora': ,
        # }
        db_sncp_receita_guia_rec_rel = self.pool.get('sncp.receita.guia.rec.rel')
        db_account_journal = self.pool.get('account.journal')
        db_account_voucher = self.pool.get('account.voucher')
        db_account_voucher_line = self.pool.get('account.voucher.line')

        obj = self.browse(cr, uid, ids[0])
        valores_mov_contab = {
            'diario_liq': vals['diario_id'],
            'datahora': vals['datahora'],
        }
        [move_id, move_line_id, nog] = \
            self.movimento_contabilistico_liquidacao(cr, uid, ids, valores_mov_contab)
        if obj.natureza == 'rec':
            rel_ids = db_sncp_receita_guia_rec_rel.search(cr, uid, [('guia_id', '=', obj.id)])
            for obj_rel in db_sncp_receita_guia_rec_rel.browse(cr, uid, rel_ids):

                cr.execute("""
                SELECT COALESCE(residual,0.0)
                FROM account_invoice
                WHERE id = %d
                """ % obj_rel.fatura_id.id)

                residual = cr.fetchone()

                if residual is not None:
                    residual = residual[0]
                else:
                    residual = 0.0

                residual -= obj_rel.montante_cobr

                aux = decimal.Decimal(unicode(residual))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                residual = float(aux)

                cr.execute("""
                UPDATE account_invoice
                SET residual = %f
                WHERE id = %d
                """ % (residual, obj_rel.fatura_id.id))

            obj_journal = db_account_journal.browse(cr, uid, vals['diario_id'])
            values = {
                'type': 'receipt',
                'date': vals['datahora'],
                'journal_id': vals['diario_id'],
                'account_id': obj_journal.default_debit_account_id.id,
                'state': 'posted',
                'amount': obj.montante,
                'number': nog,
                'move_id': move_id,
                'partner_id': obj.partner_id.id,
                'pay_now': 'pay_now',
                'reference': obj.name,
                'pre_line': False,
                'payment_option': 'without_writeoff',
                'comment': 'Write-Off',
                'payment_rate_currency_id': 1,
                'payment_rate': 1.0,
                'is_multi_currency': False,
            }
            voucher_id = db_account_voucher.create(cr, uid, values)
            # _____________________________  LINHAS DO VOUCHER

            rel_ids = db_sncp_receita_guia_rec_rel.search(cr, uid, [('guia_id', '=', obj.id)])
            for obj_rel in db_sncp_receita_guia_rec_rel.browse(cr, uid, rel_ids):
                values_linha = {'voucher_id': voucher_id,
                                'name': obj_rel.fatura_id.name,
                                'account_id': obj_rel.fatura_id.account_id.id,
                                'untax_amount': 0.0,
                                'amount': obj_rel.montante_cobr,
                                'reconcile': False,
                                'type': 'cr',
                                'move_line_id': move_line_id, }
                db_account_voucher_line.create(cr, uid, values_linha)
        return True

    def cobra_guia_receita(self, cr, uid, ids, vals):
        # vals = {
        #   'datahora': ,
        #   'diario_id': pag,
        #   'diario_liq': ,
        #   'opag': ,
        # }

        db_account_move = self.pool.get('account.move')
        db_account_move_line = self.pool.get('account.move.line')
        db_ir_sequence = self.pool.get('ir.sequence')
        db_account_journal = self.pool.get('account.journal')
        db_sncp_receita_guia_rec_linhas = self.pool.get('sncp.receita.guia.rec.linhas')
        db_sncp_orcamento_historico = self.pool.get('sncp.orcamento.historico')
        db_sncp_tesouraria_movimentos = self.pool.get('sncp.tesouraria.movimentos')
        db_sncp_comum_param = self.pool.get('sncp.comum.param')

        obj_jornal = db_account_journal.browse(cr, uid, vals['diario_id'])
        if obj_jornal.sequence_id.id:
            nog = db_ir_sequence.next_by_id(cr, uid, obj_jornal.sequence_id.id)
        else:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'O diário '+unicode(obj_jornal.name)
                                   + u' não têm sequência de movimentos associada.'))
        obj = self.browse(cr, uid, ids[0])
        ndata = vals['datahora'].date()
        self.write(cr, uid, ids, {'cobrada': vals['datahora']})
        ref = 'Guia de Receita ' + nog

        dicti = db_account_move.account_move_prepare(cr, uid, vals['diario_id'], ndata, ref)
        dicti['name'] = nog

        move_id = db_account_move.create(cr, uid, dicti)
        self.write(cr, uid, ids, {'doc_cobra_id': move_id})
        obj_jornal_liquidacao = db_account_journal.browse(cr, uid, vals['diario_liq'])
        conta_id = [0, 0]
        caixa_id = [0, 0]
        banco_id = [0, 0]
        fundo_id = [0, 0]
        if 'opag' in vals:
            if vals['opag'].ref_meio == 'cx':
                conta_id = vals['opag'].caixa_id.conta_id.id
                caixa_id[1] = vals['opag'].caixa_id.id
            elif vals['opag'].ref_meio == 'bk':
                conta_id = vals['opag'].banco_id.conta_id.id
                banco_id[1] = vals['opag'].banco_id.id
            else:
                conta_id = vals['opag'].fundo_id.conta_id.id
                fundo_id[1] = vals['opag'].fundo_id.id

        else:
            if 'caixa_id' in vals:
                conta_id = vals['caixa_id'].conta_id.id
                caixa_id[1] = vals['caixa_id'].id

        linhas_guia_ids = db_sncp_receita_guia_rec_linhas.search(cr, uid, [('guia_rec_id', '=', obj.id)])
        montante_ot = 0

        valores_credito = {'account_id': obj_jornal_liquidacao.default_debit_account_id.id,
                           'date': dicti['date'], 'journal_id': dicti['journal_id'],
                           'period_id': dicti['period_id'], 'name': dicti['ref'],
                           'move_id': move_id, 'credit': obj.montante,
                           'partner_id': obj.partner_id.id}
        db_account_move_line.create(cr, uid, valores_credito)
        valores_debito = {
            'account_id': conta_id,
            'date': dicti['date'], 'journal_id': dicti['journal_id'],
            'period_id': dicti['period_id'], 'name': dicti['ref'],
            'move_id': move_id, 'debit': obj.montante,
            'partner_id': obj.partner_id.id}
        move_line_id = db_account_move_line.create(cr, uid, valores_debito)

        for obj_linha_guia in db_sncp_receita_guia_rec_linhas.browse(cr, uid, linhas_guia_ids):
            # Account move
            if obj.natureza == 'rec':
                if obj_linha_guia.natureza == 'rec':
                    send = {'name': ndata.year,
                            'categoria': '58cobra',
                            'datahora': vals['datahora'],
                            'organica_id': None,
                            'economica_id': obj_linha_guia.economica_id.id,
                            'funcional_id': None,
                            'montante': obj_linha_guia.montante_orc,
                            'centrocustos_id': None,
                            'cabimento_id': None,
                            'cabimento_linha_id': None,
                            'compromisso_id': None,
                            'compromisso_linha_id': None,
                            'doc_contab_id': move_id,
                            'doc_contab_linha_id': move_line_id, }
                    db_sncp_orcamento_historico.insere_valores_historico(cr, uid, [], send)
                    montante_ot += obj_linha_guia.montante_ots
                else:
                    montante_ot += obj_linha_guia.montante_ots
        param_ids = db_sncp_comum_param.search(cr, uid, [('state', '=', 'draft')])
        if len(param_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                u'Preencha os parâmetros por defeito no menu:\n'
                                                u'Comum/Parâmetros.'))
        obj_param = db_sncp_comum_param.browse(cr, uid, param_ids[0])
        aux = decimal.Decimal(unicode(montante_ot))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_ot = float(aux)
        if obj_param.otes_mpag.id is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina o meio de recebimento padrão em '
                                                u'Comum/Parâmetros.'))
        else:
            if obj_param.otes_mpag.meio != 'cx':
                raise osv.except_osv(_(u'Aviso'), _(u'O meio de recebimento padrão deve ser do "meio" '
                                                    u'caixa.'))
            meio_pag_id = obj_param.otes_mpag.id,

        vals = {'datahora': vals['datahora'],
                'name': obj.name,
                'montante': obj.montante,
                'em_cheque': 0,
                'montante_ot': montante_ot,
                'origem': 'recpag',
                'origem_id': meio_pag_id,
                'caixa_id': caixa_id,
                'banco_id': banco_id,
                'fmaneio_id': fundo_id, }

        db_sncp_tesouraria_movimentos.cria_movimento_tesouraria(cr, uid, ids, vals)

        self.write(cr, uid, ids, {'state': 'rec', 'user_id': uid})
        return True

    def criar_linhas(self, cr, uid, ids, context):
        seq = get_sequence(self, cr, uid, context, 'guia_rec', ids[0])
        return self.pool.get('sncp.receita.guia.rec.linhas').create(cr, uid, {'name': seq,
                                                                              'guia_rec_id': ids[0],
                                                                              'natureza': 'ots'})

    def limpa_meios(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        cr.execute("""
        DELETE FROM sncp_receita_guia_rec_meios
        WHERE guia_rec_id=%d
        """ % ids[0])

        db_sncp_receita_guia_rec_meios = self.pool.get('sncp.receita.guia.rec.meios')
        meios_vals = {
            'guia_rec_id': ids[0],
            'meio_rec': 'num',
            'montante': obj.montante,
        }

        db_sncp_receita_guia_rec_meios.create(cr, uid, meios_vals)

        return True

    def anula_guia_receita(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        if obj.natureza == 'rec':
            db_sncp_receita_guia_rec_rel = self.pool.get('sncp.receita.guia.rec.rel')
            guia_rec_rel_ids = db_sncp_receita_guia_rec_rel.search(cr, uid, [('guia_id', '=', obj.id)])
            if len(guia_rec_rel_ids) != 0:
                db_sncp_receita_guia_rec_rel.unlink(cr, uid, guia_rec_rel_ids, context)
        elif obj.natureza == 'ots':
            pass
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'A natureza está mal definida.'))

        db_sncp_receita_guia_rec_linhas = self.pool.get('sncp.receita.guia.rec.linhas')
        guia_rec_linhas_ids = db_sncp_receita_guia_rec_linhas.search(cr, uid, [('guia_rec_id', '=', obj.id)])
        if len(guia_rec_linhas_ids) != 0:
            db_sncp_receita_guia_rec_linhas.unlink(cr, uid, guia_rec_linhas_ids, context)

        db_sncp_receita_guia_rec_meios = self.pool.get('sncp.receita.guia.rec.meios')
        guia_rec_meios_ids = db_sncp_receita_guia_rec_meios.search(cr, uid, [('guia_rec_id', '=', obj.id)])
        if len(guia_rec_meios_ids) != 0:
            db_sncp_receita_guia_rec_meios.unlink(cr, uid, guia_rec_meios_ids, context)

        return super(sncp_receita_guia_rec, self).unlink(cr, uid, ids, context)

    def cobrar(self, cr, uid, ids, context):
        db_sncp_receita_guia_rec_meios = self.pool.get('sncp.receita.guia.rec.meios')
        meios_ids = db_sncp_receita_guia_rec_meios.search(cr, uid, [('guia_rec_id', '=', ids[0])])
        db_sncp_receita_guia_rec_meios.write(cr, uid, meios_ids, {'edit': 1})
        return self.pool.get('formulario.sncp.tesouraria.guia.cobrar.diario').wizard(cr, uid, ids)

    def cobrar_end(self, cr, uid, ids):
        db_sncp_receita_guia_rec_meios = self.pool.get('sncp.receita.guia.rec.meios')
        meios_ids = db_sncp_receita_guia_rec_meios.search(cr, uid, [('guia_rec_id', '=', ids[0])])
        obj = self.browse(cr, uid, ids[0])
        total_guia = obj.montante
        total = 0.0

        for obj_meio in db_sncp_receita_guia_rec_meios.browse(cr, uid, meios_ids):
            total += obj_meio.montante

        aux = decimal.Decimal(unicode(total))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        total = float(aux)

        if total == total_guia:
            self.write(cr, uid, ids, {'estado': 1})
            return True
        else:
            aux = decimal.Decimal(unicode(total_guia-total))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_dif = float(aux)
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'O valor não coberto pelos meios de pagamento é de '
                                   + unicode(montante_dif)+u'.'))

    def cobranca(self, cr, uid, ids, context):
        db_sncp_receita_guia_rec_meios = self.pool.get('sncp.receita.guia.rec.meios')
        db_formulario_sncp_tesouraria_guia_cobrar_diario = \
            self.pool.get('formulario.sncp.tesouraria.guia.cobrar.diario')
        formulario_id = db_formulario_sncp_tesouraria_guia_cobrar_diario.search(cr, uid, [('guia_id', '=', ids[0])])
        obj_formulario = db_formulario_sncp_tesouraria_guia_cobrar_diario.browse(cr, uid, max(formulario_id))
        meios_ids = db_sncp_receita_guia_rec_meios.search(cr, uid, [('guia_rec_id', '=', ids[0])])
        obj = self.browse(cr, uid, ids[0])
        total_guia = obj.montante
        total = 0.0

        for obj_meio in db_sncp_receita_guia_rec_meios.browse(cr, uid, meios_ids):
            total += obj_meio.montante

        aux = decimal.Decimal(unicode(total))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        total = float(aux)

        if total == total_guia:
            datahora = datetime.strptime(obj_formulario.name, "%Y-%m-%d %H:%M:%S")
            values_liquida = {'diario_id': obj_formulario.diario_liq_id.id,
                              'datahora': datahora, }
            self.liquida_guia_receita(cr, uid, ids, values_liquida)

            values_cobra = {'datahora': datahora, 'diario_id': obj_formulario.diario_cobr_id.id,
                            'diario_liq': obj_formulario.diario_liq_id.id, 'caixa_id': obj_formulario.caixa_id}

            self.cobra_guia_receita(cr, uid, ids, values_cobra)
        else:
            aux = decimal.Decimal(unicode(total_guia-total))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_dif = float(aux)
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'O valor não coberto pelos meios de pagamento é de '
                                   + unicode(montante_dif)+u'.'))
        # Apagar formulários
        db_formulario_sncp_tesouraria_guia_cobrar_diario.unlink(cr, uid, formulario_id)

        # Bloco de verificação de existência de controlo
        controlo.trata_info(self, cr, uid, obj.id, context=context)
        ##
        return self.imprimir_report(cr, uid, ids, context=context)

    def imprimir_report(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'impressa': True})
        datas = {'ids': ids,
                 'model': 'sncp.receita.guia.rec', }
        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.receita.guia.rec.report',
            'datas': datas,
        }

    def anula_cobranca(self, cr, uid, ids, context):
        db_sncp_orcamento_historico = self.pool.get('sncp.orcamento.historico')
        db_sncp_tesouraria_folha_caixa = self.pool.get('sncp.tesouraria.folha.caixa')
        db_sncp_tesouraria_movimentos = self.pool.get('sncp.tesouraria.movimentos')
        obj = self.browse(cr, uid, ids[0])
        data = unicode(datetime.strptime(obj.cobrada, "%Y-%m-%d %H:%M:%S").date())
        fechada = db_sncp_tesouraria_folha_caixa.folha_caixa_fechada(cr, uid, ids, data)
        if fechada:
            raise osv.except_osv(_(u'Aviso'), _(u'Mapa de Tesouraria de ' + unicode(data) + u' está fechado.'))
        else:

            # Bloco de anulação de cobrança
            db_sncp_tesouraria_movimentos.elimina_movimento_tesouraria(cr, uid, ids, {
                'name': obj.name,
                'datahora': obj.cobrada
            })

            if obj.natureza == 'rec':
                dh = datetime.strptime(obj.cobrada, "%Y-%m-%d %H:%M:%S")
                ndata = dh.date()

                send = {'name': ndata.year,
                        'categoria': '58cobra',
                        'doc_contab_id': obj.doc_cobra_id.id}

                db_sncp_orcamento_historico.elimina_valores_historico(cr, uid, ids, send)

            cr.execute("""DELETE FROM account_move_line
            WHERE move_id = %d""" % obj.doc_cobra_id.id)
            cr.execute("""DELETE FROM account_move
            WHERE id = %d""" % obj.doc_cobra_id.id)
            cr.execute("""DELETE FROM sncp_receita_guia_rec_meios
            WHERE guia_rec_id = %d""" % obj.id)

            # Bloco de anulação de Liquidação
            if obj.natureza == 'rec':
                cr.execute("""
                SELECT id
                FROM account_voucher
                WHERE number = '%s'
                """ % obj.name)

                voucher_id = cr.fetchone()
                if voucher_id is not None:
                    cr.execute("""DELETE FROM account_voucher_line
                                  WHERE voucher_id = '%s'""" % voucher_id[0])
                    cr.execute("""
                    DELETE FROM account_voucher
                    WHERE id = %d
                    """ % voucher_id[0])

            # actualização de faturas
            cr.execute("""SELECT  fatura_id, montante_cobr FROM sncp_receita_guia_rec_rel
                WHERE guia_id = %d""" % obj.id)
            result = cr.fetchall()
            for res in result:
                cr.execute("""UPDATE account_invoice SET residual = residual + %f
                    WHERE id = %d""" % (res[1], res[0]))
            cr.execute("""DELETE FROM sncp_receita_guia_rec_rel
                WHERE guia_id = %d""" % obj.id)
            # historico
            if obj.natureza == 'rec':
                dh = datetime.strptime(obj.liquidada, "%Y-%m-%d %H:%M:%S")
                ndata = dh.date()

                send = {'name': ndata.year,
                        'categoria': '57rliqd',
                        'doc_contab_id': obj.doc_liquida_id.id}

                db_sncp_orcamento_historico.elimina_valores_historico(cr, uid, ids, send)

            cr.execute("""DELETE FROM account_move_line
            WHERE move_id = %d""" % obj.doc_liquida_id.id)
            cr.execute("""DELETE FROM account_move
            WHERE id = %d""" % obj.doc_liquida_id.id)

            cr.execute("""
            DELETE FROM sncp_receita_controlo_guias
            WHERE guia_id = %d""" % obj.id)

            self.write(cr, uid, ids, {'name': None, 'liquidada': None, 'state': 'cri',
                                      'cobrada': None, 'impressa': False, 'estado': 0})
            if 'op' in context:
                return True
            else:
                return {'type': 'ir.actions.client', 'tag': 'reload'}

    _columns = {
        'name': fields.char(u'Número', size=12),
        'natureza': fields.selection([('rec', u'Receita Orçamental'),
                                      ('ots', u'Operações de Tesouraria')], u'Natureza'),
        'categoria': fields.selection([('evn', u'Eventual'), ('vrt', u'Virtual')], u'Categoria'),
        'origem': fields.selection([('part', u'Parceiro de Negócios'), ('serv', u'Serviço')], u'Origem'),
        'department_id': fields.many2one('hr.department', u'Departamento'),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios'),
        'data_emissao': fields.datetime(u'Data de emissão'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'impressa': fields.boolean(u'Impressa'),
        'liquidada': fields.datetime(u'Liquidada em '),
        'cobrada': fields.datetime(u'Cobrada em'),
        'user_id': fields.many2one('res.users', u'Cobrada por'),
        'obsv': fields.text(u'Observações'),
        'state': fields.selection([('cri', u'Criada'), ('liq', u'Liquidada'), ('rec', u'Recebida')], u''),
        'doc_liquida_id': fields.many2one('account.move', u'Documento de Liquidação'),
        'doc_cobra_id': fields.many2one('account.move', u'Documento de Cobrança'),
        'partner_department': fields.char(u'Parceiro/Departamento'),
        'linhas_id': fields.one2many('sncp.receita.guia.rec.linhas', 'guia_rec_id'),
        'meios_id': fields.one2many('sncp.receita.guia.rec.meios', 'guia_rec_id'),
        'rel_id': fields.one2many('sncp.receita.guia.rec.rel', 'guia_id'),
        'estado': fields.integer(u'Controlo de meios e wizard'),
        # 0 -- Botao Cobrar disponivel
        # 1 -- Botao continuar Disponivel
    }

    _order = 'name'

    _defaults = {
        'natureza': 'ots',
        'origem': 'part',
        'categoria': 'evn',
        'state': 'cri',
        'estado': 0,
    }

    def sql_meios_pagamento(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION meios_pagamento(guia_rec_id integer) RETURNS varchar
        AS
        $$
        DECLARE
          conta integer;
          meio_pag varchar='';
          guia_rec_meios sncp_receita_guia_rec_meios%ROWTYPE;
        BEGIN
           conta=(SELECT COUNT(*) FROM sncp_receita_guia_rec_meios AS GRM WHERE GRM.guia_rec_id=$1);
           FOR guia_rec_meios IN (SELECT * FROM sncp_receita_guia_rec_meios AS GRM WHERE GRM.guia_rec_id=$1) LOOP
               IF guia_rec_meios.meio_rec='num' THEN
                  meio_pag=CONCAT(meio_pag,'Numerário ');
               ELSIF guia_rec_meios.meio_rec='chq' THEN
                  meio_pag=CONCAT(meio_pag,'Cheque ');
               ELSIF guia_rec_meios.meio_rec='dep' THEN
                  meio_pag=CONCAT(meio_pag,'Talão de Depósito ');
               ELSIF guia_rec_meios.meio_rec='trf' THEN
                  meio_pag=CONCAT(meio_pag,'Transferência Bancária ');
               ELSIF guia_rec_meios.meio_rec='cdc' THEN
                  meio_pag=CONCAT(meio_pag,'Crédito em conta ');
               ELSE
                  meio_pag=CONCAT(meio_pag,'Outros ');
               END IF;
               meio_pag=CONCAT(meio_pag,guia_rec_meios.obs);
               IF conta=1 THEN
                  RETURN meio_pag;
               ELSE
                  meio_pag=CONCAT(meio_pag,' ',guia_rec_meios.montante,'; ');
               END IF;
           END LOOP;
           RETURN meio_pag;
        END;$$  LANGUAGE plpgsql;
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

    def teste_existencia_guia_receita(self, cr):
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

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'meios_pagamento'""")
        result = cr.fetchone()
        if result is None:
            self.sql_meios_pagamento(cr)

        return True

    def create(self, cr, uid, vals, context=None):
        self.teste_existencia_guia_receita(cr)
        return super(sncp_receita_guia_rec, self).create(cr, uid, vals, context=context)

sncp_receita_guia_rec()
# _____________________________________________________GUIA RECEITA LINHA___________________________


class sncp_receita_guia_rec_linhas(osv.Model):
    _name = 'sncp.receita.guia.rec.linhas'
    _description = u"Linhas da Guia de Receita"

    _columns = {
        'guia_rec_id': fields.many2one('sncp.receita.guia.rec', u'Guia de receita'),
        'name': fields.integer(u'Linha'),
        'desc': fields.char(u'Descrição', size=50),
        'tax_rate': fields.float(u'Taxa de IVA', digits=(3, 2)),
        'natureza': fields.selection([('rec', u'Receita Orçamental'),
                                      ('ots', u'Operações de Tesouraria')], u'Natureza'),
        'cod_contab_id': fields.many2one('sncp.comum.codigos.contab', u'Código de Contabilidade'),
        'conta_id': fields.many2one('account.account', u'Patrimonial'),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')],),
        'montante_tax': fields.float(u'Valor IVA', digits=(12, 2)),
        'montante_ots': fields.float(u'Não orçamental', digits=(12, 2)),
        'montante_orc': fields.float(u'Orçamental', digits=(12, 2)),
        'obsv': fields.char(u'Observações', size=5),
        # Variaveis de estado e processamento
        'calc_montante': fields.float(u'Usado na on_change_cod_contab', digits=(2, 3)),

    }
    _order = 'name'

    _defaults = {
        'natureza': 'rec',
        'calc_montante': 0,
    }

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_receita_guia_rec_linhas, self).unlink(cr, uid, ids, context=context)

sncp_receita_guia_rec_linhas()

# _____________________________________________________GUIA RECEITA MEIOS___________________________


class sncp_receita_guia_rec_meios(osv.Model):
    _name = 'sncp.receita.guia.rec.meios'
    _description = u"Meios da Guia de Receita"

    def on_change_montante(self, cr, uid, ids, meio_rec, obs, montante):
        obj_meio = self.browse(cr, uid, ids[0])
        db_sncp_receita_guia_rec = self.pool.get('sncp.receita.guia.rec')
        obj_guia = db_sncp_receita_guia_rec.browse(cr, uid, obj_meio.guia_rec_id.id)

        if montante < 0.01:
            raise osv.except_osv(_(u'Aviso'), _(u'O montante mínimo é de 1 cêntimo.'))
        if montante > obj_guia.montante:
            raise osv.except_osv(_(u'Aviso'), _(u'O montante máximo é de '
                                                + unicode(obj_guia.montante)+u' euros.'))

        meios_ids = self.search(cr, uid, [('guia_rec_id', '=', obj_meio.guia_rec_id.id)])
        sum_montante = 0.0
        for obj_meio in self.browse(cr, uid, meios_ids):
            if obj_meio.id != ids[0]:
                sum_montante += obj_meio.montante
                aux = decimal.Decimal(unicode(sum_montante))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                sum_montante = float(aux)

        aux = decimal.Decimal(unicode(obj_meio.montante - montante))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        new_montante = float(aux)

        if new_montante > 0:
            self.write(cr, uid, ids, {'obs': obs, 'meio_rec': meio_rec, 'montante': montante, 'edit': 1})
            valores = {
                'guia_rec_id': obj_meio.guia_rec_id.id,
                'meio_rec': 'num',
                'montante': new_montante,

            }
            self.create(cr, uid, valores)

            message = u'Antes de cobrar, clique no botão "Atualiza Meios".'
            return {'value': {'obs': obs, 'meio_rec': meio_rec, 'montante': montante, 'edit': 1},
                    'warning': {'title': 'Aviso', 'message': message}}
        elif new_montante == 0.0:
            cr.execute("""
             DELETE FROM sncp_receita_guia_rec_meios
             WHERE guia_rec_id=%d and id!=%d
             """ % (obj_guia.id, obj_meio.id))
            return {'value': {'obs': obs, 'meio_rec': meio_rec, 'montante': montante}}
        else:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'A soma dos montantes dos meios não pode ultrapassar '
                                   u'o montante total da Guia da Receita que é de ' +
                                   unicode(obj_guia.montante)+u' euros.'))

    _columns = {
        'guia_rec_id': fields.many2one('sncp.receita.guia.rec', u'Guia de receita'),
        'state': fields.related('guia_rec_id', 'state', type="char", store=True),
        'name': fields.integer(u'Sequência'),
        'meio_rec': fields.selection([('num', u'Numerário'),
                                      ('chq', u'Cheque'),
                                      ('dep', u'Talão de Depósito'),
                                      ('trf', u'Transferência Bancária'),
                                      ('cdc', u'Crédito em conta'),
                                      ('out', u'Outros'), ], u'Meio de Recebimento'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'obs': fields.char(u'Observações'),
        'edit': fields.integer(u'Serve para controlo de atualização'),
        # 0 -- sem botão
        # 1 -- com botão save
    }

    def montantes_validos(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        rel_meios_ids = self.search(cr, uid, [('guia_rec_id', '=', obj.guia_rec_id.id)])
        total = 0
        for obj_rel_meio in self.browse(cr, uid, rel_meios_ids):
            a = obj_rel_meio.montante
            total += a
        if total > obj.guia_rec_id.montante:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'A soma dos montantes dos meios não pode ultrapassar'
                                   u' o montante total da receita.'))
        return True

    _constraints = [(montantes_validos, u'', ['montante'])]

    def create(self, cr, uid, vals, context=None):
        vals['name'] = get_sequence(self, cr, uid, {}, 'meio_guia_rec', vals['guia_rec_id'])
        return super(sncp_receita_guia_rec_meios, self).create(cr, uid, vals)

    _order = 'name'

sncp_receita_guia_rec_meios()

# _____________________________________________________GUIA RECEITA RELACOES___________________________


class sncp_receita_guia_rec_rel(osv.Model):
    _name = 'sncp.receita.guia.rec.rel'
    _description = u"Relação entre Guias de Faturas"

    _columns = {
        'guia_id': fields.many2one('sncp.receita.guia.rec', u'Guia de receita'),
        'fatura_id': fields.many2one('account.invoice', u'Fatura'),
        'montante_pend': fields.float(u'Montante pendente', digits=(12, 2)),
        'montante_cobr': fields.float(u'Montante a cobrar', digits=(12, 2)),
    }

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_receita_guia_rec_rel, self).unlink(cr, uid, ids, context=context)

sncp_receita_guia_rec_rel()