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

from datetime import datetime, date
import decimal
from decimal import *
from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools.translate import _
import guia
# ___________________________________________________FATURAS A COBRAR_________________________________*


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


class sncp_receita_fact_cobrar(osv.Model):
    _name = 'sncp.receita.fact.cobrar'
    _description = u"Fat Cobrar"

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name'], context=context)
        res = []
        for record in reads:
            result = u'Guia de Receita Nova'
            res.append((record['id'], result))
        return res

    def juros_montante(self, cr, uid, ids, obj_fatura, prop):
        db_sncp_receita_juros = self.pool.get('sncp.receita.juros')
        obj = self.browse(cr, uid, ids[0])

        juros = False
        juros_montante = 0.0
        if obj_fatura.date_due < obj_fatura.date_invoice:

            # Metodos e montantes
            cr.execute("""
                  SELECT sccc.met_juros_id AS juros_id,
                      COALESCE(SUM(ail.price_subtotal),0.0) AS iliquido, act.amount AS IVA_perc
                  FROM (account_invoice_line AS ail LEFT JOIN sncp_comum_codigos_contab AS sccc
                      ON sccc.item_id = ail.product_id) LEFT JOIN account_tax AS act
                      ON act.id = (
                        SELECT tax_id FROM account_invoice_line_tax
                        WHERE  invoice_line_id = ail.id)
                  WHERE  ail.invoice_id = %d AND sccc.met_juros_id IS NOT NULL AND sccc.natureza='rec'
                  GROUP BY sccc.met_juros_id, act.amount
                  """ % obj_fatura.id)
            # [(metodo calculo de juros, montante, taxa em %)]
            record = cr.fetchall()

            # Agrupamento dos metodos
            montantes = {}
            metodos = []
            for rec in record:
                if rec[0] in montantes:
                    montantes[rec[0]] += rec[1] + rec[1] * rec[2]

                    aux = decimal.Decimal(unicode(montantes[rec[0]]))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    montantes[rec[0]] = float(aux)
                else:
                    metodos.append(rec[0])
                    montantes[rec[0]] = rec[1] + rec[1] * rec[2]

                    aux = decimal.Decimal(unicode(montantes[rec[0]]))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    montantes[rec[0]] = float(aux)

            juros = True
            for met in metodos:
                vals = {'datavencimento': datetime.strptime(obj_fatura.date_due, "%Y-%m-%d").date(),
                        'datapagamento': datetime.strptime(obj.data, "%Y-%m-%d %H:%M:%S").date(),
                        'metodo_id': met,
                        'valorbase': montantes[met] * prop, }
                juros_montante += db_sncp_receita_juros.da_valor_juros(cr, uid, ids, vals)

                aux = decimal.Decimal(unicode(juros_montante))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                juros_montante = float(aux)

        return [juros_montante, juros]

    def criar_linhas(self, cr, uid, ids, context):
        db_sncp_receita_fact_cobrar_linhas = self.pool.get('sncp.receita.fact.cobrar.linhas')
        db_account_invoice = self.pool.get('account.invoice')

        self.write(cr, uid, ids, {'state': 1})

        # seleçao das faturas de account.invoice
        obj = self.browse(cr, uid, ids[0])
        if obj.origem == 'part':
            faturas_ids = db_account_invoice.search(cr, uid, [('state', '=', 'open'),
                                                              ('partner_id', '=', obj.partner_id.id),
                                                              ('residual', '>', 0),
                                                              ('type', '=', 'out_invoice')])
        elif obj.origem == 'serv':
            faturas_ids = db_account_invoice.search(cr, uid, [('state', '=', 'open'),
                                                              ('department_id', '=', obj.department_id.id),
                                                              ('residual', '>', 0),
                                                              ('type', '=', 'out_invoice')])
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina a origem por favor.'))

        if len(faturas_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existe nenhuma fatura com estes critérios.'))

        # Processamento das faturas
        for obj_fatura in db_account_invoice.browse(cr, uid, faturas_ids):
            prop = 1
            [juros_montante, juros] = self.juros_montante(cr, uid, ids, obj_fatura, prop)

            values_faturas_cobrar_linha = {
                'fact_cobrar_id': ids[0],
                'linha': guia.get_sequence(self, cr, uid, context, 'fat_cobr', ids[0]),
                'fatura_id': obj_fatura.id,
                'department_id': obj_fatura.department_id.id,
                'partner_id': obj_fatura.partner_id.id,
                'data_venc': obj_fatura.date_due,
                'montante_orig': obj_fatura.amount_total,
                'montante_pend': obj_fatura.residual,
                'montante_cobr': obj_fatura.residual,
                'montante_rema': 0,
                'juros': juros,
                'montante_juro': juros_montante,
                'obsv': None,
            }
            db_sncp_receita_fact_cobrar_linhas.create(cr, uid, values_faturas_cobrar_linha)
        return True

    def verifica_processar(self, cr, uid, ids, context):
        db_account_journal = self.pool.get('account.journal')
        db_sncp_receita_fact_cobrar_linhas = self.pool.get('sncp.receita.fact.cobrar.linhas')
        db_account_invoice = self.pool.get('account.invoice')
        db_account_invoice_line = self.pool.get('account.invoice.line')
        db_res_users = self.pool.get('res.users')
        db_sncp_receita_guia_rec = self.pool.get('sncp.receita.guia.rec')
        db_sncp_comum_param = self.pool.get('sncp.comum.param')
        db_ir_sequence = self.pool.get('ir.sequence')
        db_account_period = self.pool.get('account.period')
        db_product_product = self.pool.get('product.product')
        data = date.today()
        period_id = db_account_period.search(cr, uid,
                                             [('date_start', '<=', unicode(data)),
                                              ('date_stop', '>=', unicode(data))])

        linhas_ids = db_sncp_receita_fact_cobrar_linhas.search(cr, uid, [('fact_cobrar_id', '=', ids[0]),
                                                                         ('juros', '=', True),
                                                                         ('a_processar', '=', True)])
        for obj_linha in db_sncp_receita_fact_cobrar_linhas.browse(cr, uid, linhas_ids):
            param_ids = db_sncp_comum_param.search(cr, uid, [('state', '=', 'draft')])
            if len(param_ids) == 0:
                raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                    u'Preencha os parâmetros por defeito no menu:\n'
                                                    u'Comum/Parâmetros.'))
            obj_param = db_sncp_comum_param.browse(cr, uid, param_ids[0])

            obj_user = db_res_users.browse(cr, uid, uid)
            if obj_param.diario_fat_juros.id is not False:
                obj_jornal = db_account_journal.browse(cr, uid, obj_param.diario_fat_juros.id)
            else:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Defina o diário de fatura de vendas em Comum/Parâmetros.'))

            if obj_jornal.sequence_id.id:
                nov = db_ir_sequence.next_by_id(cr, uid, obj_jornal.sequence_id.id)
            else:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'O diário ' + unicode(obj_jornal.name)
                                       + u' não têm sequência de movimentos associada.'))
            # USAR O PRODUTO ASSOCIADO NOS JUROS OU O PRODUTO DOS CÓDIGOS DE CONTABILIZAÇÃO/LINHA DA FATURA ????
            cr.execute("""
             SELECT sncp_receita_juros.item_id,sncp_comum_codigos_contab.conta_id,
             sncp_comum_codigos_contab.organica_id,sncp_comum_codigos_contab.economica_id,
             sncp_comum_codigos_contab.funcional_id,sncp_receita_juros.id,sncp_comum_codigos_contab.natureza
             FROM sncp_receita_juros,sncp_comum_codigos_contab,account_invoice_line
             WHERE sncp_comum_codigos_contab.met_juros_id = sncp_receita_juros.id AND
             account_invoice_line.product_id = sncp_comum_codigos_contab.item_id
             AND account_invoice_line.invoice_id = %d AND sncp_comum_codigos_contab.natureza IN ('rec','ots')
             """ % obj_linha.fatura_id.id)

            obj_juros_codigos_contab = cr.fetchone()

            if obj_juros_codigos_contab is None:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Defina código de contabilização de natureza receita orçamental/operações '
                                       u'de tesouraria com método de juros associado para os itens '
                                       u'definidos nas linhas da fatura '
                                       + unicode(obj_linha.fatura_id.internal_number) + u'.'))

            values_fatura_juros = {
                'date_due': date.today(),
                'account_id': obj_linha.partner_id.property_account_receivable.id,
                'company_id': obj_user.company_id.id,
                'currency_id': obj_linha.partner_id.property_account_receivable.company_currency_id.id,
                'partner_id': obj_linha.partner_id.id,
                'user_id': uid,
                'journal_id': obj_param.diario_fat_juros.id,
                'state': 'draft',
                'type': 'out_invoice',
                'internal_number': nov,
                'reconciled': False,
                'date_invoice': data,
                'period_id': period_id[0],
                'name': u'Juros relativos à fatura ' + obj_linha.fatura_id.internal_number,
                'commercial_partner_id': obj_linha.partner_id.id,
                'department_id': obj_linha.department_id.id,
            }
            fatura_juros_id = db_account_invoice.create(cr, uid, values_fatura_juros)

            produto = db_product_product.browse(cr, uid, obj_juros_codigos_contab[0])
            uos_id = produto.product_tmpl_id.uos_id.id

            lll = produto.product_tmpl_id.taxes_id
            nova_lista = [elem.id for elem in lll]

            values_fatura_juros_linha = {
                'uos_id': uos_id,
                'product_id': produto.id,
                'account_id': obj_juros_codigos_contab[1],
                'name': '[' + produto.default_code + ']' + produto.name_template,
                'invoice_id': fatura_juros_id,
                'price_unit': obj_linha.montante_juro,
                'company_id': obj_user.company_id.id,
                'discount': 0.0,
                'quantity': 1.0,
                'partner_id': obj_linha.partner_id.id,
                'organica_id': obj_juros_codigos_contab[2],
                'economica_id': obj_juros_codigos_contab[3],
                'funcional_id': obj_juros_codigos_contab[4],
                'invoice_line_tax_id': [(6, 0, nova_lista)],
                'natureza': obj_juros_codigos_contab[6],
            }

            db_account_invoice_line.create(cr, uid, values_fatura_juros_linha)

            # Responsável por passar o estado da fatura para "open"
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'account.invoice', fatura_juros_id, 'invoice_open', cr)

            values_fatura_cobrar_linha = {
                'fact_cobrar_id': ids[0],
                'linha': guia.get_sequence(self, cr, uid, context, 'fat_cobr', ids[0]),
                'fatura_id': fatura_juros_id,
                'department_id': obj_linha.department_id.id,
                'partner_id': obj_linha.partner_id.id,
                'data_venc': obj_linha.data_venc,
                'montante_orig': obj_linha.montante_orig,
                'montante_pend': obj_linha.montante_pend,
                'montante_cobr': obj_linha.montante_cobr,
                'montante_rema': obj_linha.montante_rema,
                'juros': False,
                'montante_juro': 0,
                'a_processar': True,
                'obsv': None, }
            db_sncp_receita_fact_cobrar_linhas.create(cr, uid, values_fatura_cobrar_linha)
        obj_user = db_res_users.browse(cr, uid, uid)
        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]
        unique_key = unicode(obj_user.login) + '|' + unicode(datahora)
        self.write(cr, uid, ids[0], {'name': unique_key})
        values_cria_guia_receita = {
            'natureza': 'rec',
            'unique_key': unique_key,
        }
        guia_id = db_sncp_receita_guia_rec.cria_guia_receita(cr, uid, ids, values_cria_guia_receita, context)
        return self.pool.get('formulario.mensagem.receita').wizard(cr, uid,
                                                                   u'Criada a Guia de Receita com o id '
                                                                   + unicode(guia_id))

    def descartar(self, cr, uid, ids, context):
        cr.execute("""
        DELETE FROM sncp_receita_fact_cobrar_linhas
        WHERE fact_cobrar_id=%d
        """ % ids[0])

        cr.execute("""
        DELETE FROM sncp_receita_fact_cobrar
        WHERE id=%d
        """ % ids[0])

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    _columns = {
        # unique_key
        'name': fields.char(u'Chave', size=30),
        'origem': fields.selection([('part', u'Parceiro de Negócios'), ('serv', u'Serviço')], u'Origem'),
        'department_id': fields.many2one('hr.department', u'Departamento'),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios',
                                      domain=[('customer', '=', True)]),
        'data': fields.datetime(u'Data de emissão'),
        'obsv': fields.text(u'Observações'),
        'fact_cobrar_linhas': fields.one2many('sncp.receita.fact.cobrar.linhas', 'fact_cobrar_id'),
        'state': fields.integer(u'estado')
        # 0 -- preenchimento de formulario
        # 1 -- Visualizaçao de linhas
        # 2 -- Visualizaçao de linhas

    }

    def create(self, cr, uid, vals, context=None):
        if 'partner_id' in vals:
            test_partner_id(self, cr, uid, vals['partner_id'])
        return super(sncp_receita_fact_cobrar, self).create(cr, uid, vals, context=context)

    _defaults = {
        'state': 0,
        'data': unicode(date.today()),
    }


sncp_receita_fact_cobrar()

# ____________________________________________________FATURAS A COBRAR LINHAS__________________________*


class sncp_receita_fact_cobrar_linhas(osv.Model):
    _name = 'sncp.receita.fact.cobrar.linhas'
    _description = u"Fat Cobrar Linhas"

    def on_change_montante_cobr(self, cr, uid, ids, fact_cobrar_id, fatura_id, pend, cobr, orig):
        db_sncp_receita_fact_cobrar = self.pool.get('sncp.receita.fact.cobrar')
        db_account_invoice = self.pool.get('account.invoice')
        obj_fatura = db_account_invoice.browse(cr, uid, fatura_id)
        prop = cobr / orig
        [montante_juro, juro] = db_sncp_receita_fact_cobrar.juros_montante(cr, uid, [fact_cobrar_id],
                                                                           obj_fatura, prop)

        aux = decimal.Decimal(unicode(pend - cobr))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_pend_cobr = float(aux)

        if len(ids) != 0:
            self.write(cr, uid, ids[0], {'montante_rema': montante_pend_cobr, 'montante_juro': montante_juro})
        return {'value': {'montante_rema': montante_pend_cobr, 'montante_juro': montante_juro}}

    def on_change_processar(self, cr, uid, ids, fact_cobrar_id, a_processar):
        db_sncp_receita_fact_cobrar = self.pool.get('sncp.receita.fact.cobrar')

        if a_processar is True:
            db_sncp_receita_fact_cobrar.write(cr, uid, fact_cobrar_id, {'state': 2})
            return {}
        else:
            gerar = False
            linhas_ids = self.search(cr, uid, [('fact_cobrar_id', '=', fact_cobrar_id)])
            for obj_linhas in self.browse(cr, uid, linhas_ids):
                if obj_linhas.a_processar is True and obj_linhas.id != ids[0]:
                    gerar = True
            if gerar is True:
                db_sncp_receita_fact_cobrar.write(cr, uid, fact_cobrar_id, {'state': 2})
                return {}
            else:
                db_sncp_receita_fact_cobrar.write(cr, uid, fact_cobrar_id, {'state': 1})
                return {}

    _columns = {
        'fact_cobrar_id': fields.many2one('sncp.receita.fact.cobrar', u'Faturas a cobrar'),
        'name': fields.related('fact_cobrar_id', 'origem', type="char", store=True),
        'linha': fields.integer(u'Linha'),
        'fatura_id': fields.many2one('account.invoice', u'Fatura'),
        'department_id': fields.many2one('hr.department', u'Departamento'),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios'),
        'data_venc': fields.date(u'Data de vencimento'),
        'montante_orig': fields.float(u'Montante original', digits=(12, 2)),
        'montante_pend': fields.float(u'Montante pendente', digits=(12, 2)),
        'montante_cobr': fields.float(u'Montante a cobrar', digits=(12, 2)),
        'montante_rema': fields.float(u'Montante remanescente', digits=(12, 2)),
        'juros': fields.boolean(u'Juros'),
        'montante_juro': fields.float(u'Montante de juros', digits=(12, 2)),
        'a_processar': fields.boolean(u'Sel.'),
        'obsv': fields.char(u'Observações', size=5),
    }


sncp_receita_fact_cobrar_linhas()

# _____________________________________________________OPERAÇOES DE TESOURARIA_________________________*


class sncp_receita_op_tes(osv.Model):
    _name = 'sncp.receita.op.tes'
    _description = u"Op. Tes."

    _columns = {
        # unique_key
        'name': fields.char(u'Chave', size=30),
        'ordem': fields.char(u'Ordem de Pagamento', size=12),
        'department_id': fields.many2one('hr.department', u'Departamento'),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios',
                                      domain=[('customer', '=', True)]),
        'data': fields.datetime(u'Data de emissão'),
        'obsv': fields.text(u'Observações'),
        'op_tes_linhas_id': fields.one2many('sncp.receita.op.tes.linhas', 'op_tes_id', u'Linhas da OP Tesouraria'),
        'estado': fields.integer(u'')
        # 0 - Aparece o botão criar linhas
        # 1 - Aparece as linhas e o botão prosseguir
        # 2 - Aparece o botão criar guia de receita
        # 3 - Desaparece o botão criar guia de receita
    }

    def create(self, cr, uid, vals, context=None):
        test_partner_id(self, cr, uid, vals['partner_id'])
        return super(sncp_receita_op_tes, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        linhas_ids = self.pool.get('sncp.receita.op.tes.linhas').search(cr, uid, [('op_tes_id', '=', ids[0])])
        if len(linhas_ids) != 0:
            self.pool.get('sncp.receita.op.tes.linhas').unlink(cr, uid, linhas_ids)
        return super(sncp_receita_op_tes, self).unlink(cr, uid, ids)

    _defaults = {
        'data': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                                 datetime.now().minute, datetime.now().second)),
        'estado': 0,
    }


sncp_receita_op_tes()

# ____________________________________________________OPERAÇOES DE TESOURARIA LINHAS___________________*


class sncp_receita_op_tes_linhas(osv.Model):
    _name = 'sncp.receita.op.tes.linhas'
    _description = u"Op. Tes. Linhas"

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_receita_op_tes_linhas, self).unlink(cr, uid, ids)

    def on_change_cod_contab(self, cr, uid, ids, cod_contab_id):
        db_sncp_comum_codigos_contab = self.pool.get('sncp.comum.codigos.contab')
        obj_codigo_contab = db_sncp_comum_codigos_contab.browse(cr, uid, cod_contab_id)

        montante = obj_codigo_contab.item_id.product_tmpl_id.list_price

        cr.execute("""SELECT *  FROM product_taxes_rel WHERE prod_id = %d""" % obj_codigo_contab.item_id.id)
        record = cr.fetchone()
        if record is None:
            tax_rate = 0.0
        else:
            db_account_tax = self.pool.get('account.tax')
            obj_taxa = db_account_tax.browse(cr, uid, record[1])
            tax_rate = obj_taxa.amount

        aux = decimal.Decimal(unicode(tax_rate * montante))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_tax = float(aux)

        if len(ids) != 0:
            self.write(cr, uid, ids, {'montante': montante, 'tax_rate': tax_rate, 'montante_tax': montante_tax})
        return {'value': {
            'montante': montante,
            'tax_rate': tax_rate,
            'montante_tax': montante_tax,
        }}

    def on_change_montante(self, cr, uid, ids, montante, iva):
        aux = decimal.Decimal(unicode(montante * iva))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_iva = float(aux)

        if len(ids) != 0:
            self.write(cr, uid, ids, {'montante': montante,
                                      'tax_rate': iva,
                                      'montante_tax': montante_iva})

        return {'value': {
            'montante': montante,
            'tax_rate': iva,
            'montante_tax': montante_iva,
        }}

    def create(self, cr, uid, vals, context=None):
        vals['name'] = guia.get_sequence(self, cr, uid, context, 'op_tes', vals['op_tes_id'])
        if 'montante' not in vals and 'tax_rate' not in vals and 'montante_tax' not in vals:
            ditionario = self.on_change_cod_contab(cr, uid, [], vals['cod_contab_id'])
            vals['montante'] = ditionario['value']['montante']
            vals['tax_rate'] = ditionario['value']['tax_rate']
            vals['montante_tax'] = ditionario['value']['montante_tax']
        elif 'montante' in vals and 'tax_rate' not in vals and 'montante_tax' not in vals:
            ditionario = self.on_change_cod_contab(cr, uid, [], vals['cod_contab_id'])
            ditionario_montante = self.on_change_montante(cr, uid, [], vals['montante'],
                                                          ditionario['value']['tax_rate'])
            vals['montante'] = vals['montante']
            vals['tax_rate'] = ditionario['value']['tax_rate']
            vals['montante_tax'] = ditionario_montante['value']['montante_tax']

        return super(sncp_receita_op_tes_linhas, self).create(cr, uid, vals, context=context)

    _columns = {
        'op_tes_id': fields.many2one('sncp.receita.op.tes', u'Operações de Tesouraria'),
        'name': fields.integer(u'Linha'),
        'cod_contab_id': fields.many2one('sncp.comum.codigos.contab', u'Código de contabilização'),
        'desc': fields.char(u'Descrição'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'tax_rate': fields.float(u'Taxa de IVA', digits=(3, 2)),
        'montante_tax': fields.float(u'Montante de IVA', digits=(12, 2)),
        'obsv': fields.char(u'Observações'),
    }


sncp_receita_op_tes_linhas()
# _____________________________________________________________________________FIM TABELAS TEMPORARIAS_*