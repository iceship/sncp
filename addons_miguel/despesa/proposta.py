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
from openerp.tools.translate import _
import despesa

# ___________________________________________________________RELAÇÕES_____________________________________________


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


class sncp_despesa_pagamentos_rel(osv.Model):
    _name = 'sncp.despesa.pagamentos.rel'
    _description = u"Relação entre Fatura e Linha do Compromisso"

    _columns = {
        'invoice_id': fields.many2one('account.invoice', u'Fatura de compras'),
        'comprom_linha_id': fields.many2one('sncp.despesa.compromisso.linha', u'Linha de compromisso'),
        'montante_proc': fields.float(u'Montante em processamento', digits=(12, 2)),
        'montante_pag': fields.float(u'Montante pago', digits=(12, 2)),
        'name': fields.char(u'Referência da Fatura'),
    }


sncp_despesa_pagamentos_rel()

# __________________________________________________________PROPOSTA____________________________________________


class sncp_despesa_pagamentos_proposta(osv.Model):
    _name = 'sncp.despesa.pagamentos.proposta'
    _description = u"Proposta de Pagamento"

    def create(self, cr, uid, vals, context=None):
        test_partner_id(self, cr, uid, vals['res_partner_id'])
        name = despesa.get_sequence(self, cr, uid, context, 'prop', 0)
        vals['name'] = name
        return super(sncp_despesa_pagamentos_proposta, self).create(cr, uid, vals, context=context)

    def total_a_pagar(self, cr, uid, ids, fields, arg, context):
        soma = {}
        db_sncp_despesa_pagamentos_proposta_linha = self.pool.get('sncp.despesa.pagamentos.proposta.linha')
        for proposta_id in ids:
            linha_ids = db_sncp_despesa_pagamentos_proposta_linha.search(cr, uid, [('proposta_id', '=', proposta_id)])
            soma[proposta_id] = 0.0
            for linha in linha_ids:
                obj_linha = db_sncp_despesa_pagamentos_proposta_linha.browse(cr, uid, linha)
                soma[proposta_id] += obj_linha.montante_pag

            aux = decimal.Decimal(unicode(soma[proposta_id]))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            soma[proposta_id] = float(aux)
        return soma

    def criar_linhas_proposta(self, cr, uid, ids, context):
        proposta = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'estado': 1})
        db_account_invoice = self.pool.get('account.invoice')
        db_sncp_despesa_faturas_aprovadas = self.pool.get('sncp.despesa.faturas.aprovadas')
        db_sncp_despesa_pagamentos_proposta_linha = self.pool.get('sncp.despesa.pagamentos.proposta.linha')
        db_sncp_despesa_pagamentos_rel = self.pool.get('sncp.despesa.pagamentos.rel')
        faturas_aprovadas_ids = db_sncp_despesa_faturas_aprovadas.search(cr, uid, [])
        faturas_aprovadas = db_sncp_despesa_faturas_aprovadas.browse(cr, uid, faturas_aprovadas_ids)

        invoice_ids = []
        for fatura_aprovada in faturas_aprovadas:
            invoice_ids.append(fatura_aprovada.invoice_id.id)

        if len(invoice_ids) != 0:
            pass
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existe nenhuma fatura aprovada.'))

        cli_invoice_ids = db_account_invoice.search(cr, uid, [('id', 'in', invoice_ids),
                                                              ('partner_id', '=', proposta.res_partner_id.id)])
        if len(cli_invoice_ids) != 0:
            pass
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existe nenhuma fatura aprovada associada a este cliente.'))

        date_invoice_ids = db_account_invoice.search(cr, uid, [('id', 'in', cli_invoice_ids),
                                                               ('date_due', '<=', proposta.vencimento)])
        if len(date_invoice_ids) != 0:
            pass
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existe nenhuma fatura aprovada até à data indicada.'))

        res_invoice_ids = db_account_invoice.search(cr, uid, [('id', 'in', date_invoice_ids),
                                                              ('residual', '!=', 0.0)])
        if len(res_invoice_ids) != 0:
            pass
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existe nenhuma fatura com valor por pagar.'))

        lista_faturas = []
        for obj_fatura in db_account_invoice.browse(cr, uid, res_invoice_ids):
            lista_faturas.append((obj_fatura.id, obj_fatura.date_due, obj_fatura.residual))

        if proposta.criterio == 'antig1':
            key = lambda fatura: fatura[1]
            reverse = False
        elif proposta.criterio == 'antig2':
            key = lambda fatura: fatura[1]
            reverse = True
        elif proposta.criterio == 'valor1':
            key = lambda fatura: fatura[2]
            reverse = False
        elif proposta.criterio == 'valor2':
            key = lambda fatura: fatura[2]
            reverse = True
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Contacte o administrador do sistema.'))

        lista_faturas_ordenada = sorted(lista_faturas, key=key, reverse=reverse)

        soma_montantes = 0.0
        soma_total = proposta.total_pagar

        linhas_id = db_sncp_despesa_pagamentos_proposta_linha.search(cr, uid, [('proposta_id', '=', proposta.id)])
        for linha in db_sncp_despesa_pagamentos_proposta_linha.browse(cr, uid, linhas_id):
            soma_montantes += linha.invoice_id.residual

        aux = decimal.Decimal(unicode(soma_montantes))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        soma_montantes = float(aux)

        for fatura_ordenada in lista_faturas_ordenada:
            invoice_id = fatura_ordenada[0]
            obj = db_account_invoice.browse(cr, uid, invoice_id)
            pagamentos_rel_id = db_sncp_despesa_pagamentos_rel.search(cr, uid, [('invoice_id', '=', invoice_id)])

            if soma_montantes + obj.residual <= proposta.montante_max:
                soma_montantes += obj.residual
                datatempo = datetime.strptime(obj.date_due, "%Y-%m-%d")
                data_due = date(datatempo.year, datatempo.month, datatempo.day)
                maturidade = data_due - date.today()
                if len(pagamentos_rel_id) != 0:
                    obj_pagamento = db_sncp_despesa_pagamentos_rel.browse(cr, uid, pagamentos_rel_id[0])
                    soma_total += obj.residual - obj_pagamento.montante_proc

                    aux = decimal.Decimal(unicode(obj.residual - obj_pagamento.montante_proc))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    res_dif_proc = float(aux)

                    temp = {
                        'proposta_id': ids[0],
                        'name': despesa.get_sequence(self, cr, uid, context, 'prop_lin', ids[0]),
                        'invoice_id': invoice_id,
                        'vencimento': obj.date_due,
                        'maturidade': maturidade.days,
                        'montante_orig': obj.amount_total,
                        'montante_res': res_dif_proc,
                        'montante_pag': res_dif_proc,
                    }
                else:
                    soma_total += obj.residual
                    temp = {
                        'proposta_id': ids[0],
                        'name': despesa.get_sequence(self, cr, uid, context, 'prop_lin', ids[0]),
                        'invoice_id': invoice_id,
                        'vencimento': obj.date_due,
                        'maturidade': maturidade.days,
                        'montante_orig': obj.amount_total,
                        'montante_res': obj.residual,
                        'montante_pag': obj.residual,
                    }
                db_sncp_despesa_pagamentos_proposta_linha.create(cr, uid, temp)

        aux = decimal.Decimal(unicode(soma_total))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        soma_total = float(aux)
        self.write(cr, uid, ids, {'total_pagar': soma_total})
        return True

    def criar_linhas_manual(self, cr, uid, ids, context):
        db_sncp_despesa_pagamentos_proposta_linha = self.pool.get('sncp.despesa.pagamentos.proposta.linha')
        vals = {
            'proposta_id': ids[0],
            'name': despesa.get_sequence(self, cr, uid, context, 'prop_lin', ids[0]),
            'manual': 1,
        }
        return db_sncp_despesa_pagamentos_proposta_linha.create(cr, uid, vals)

    def proposta_imp_env(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state': 'impr'})
        return True

    def _get_data(self, cr, uid, context):
        data = date(datetime.now().year + 10, 12, 31)
        return unicode(data)

    def ver_linhas(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        db_sncp_despesa_pagamentos_proposta_linha = self.pool.get('sncp.despesa.pagamentos.proposta.linha')
        linhas_propostas_ids = db_sncp_despesa_pagamentos_proposta_linha.search(cr, uid, [('proposta_id', '=', ids[0])])
        return {
            'type': 'ir.actions.act_window',
            'name': u'Linhas de Proposta Número ' + unicode(obj.name),
            'res_model': 'sncp.despesa.pagamentos.proposta.linha',
            'view_mode': 'tree',
            'view_type': 'form',
            'domain': [('id', 'in', linhas_propostas_ids)],
            'target': 'new',
        }

    def proposta_aprov(self, cr, uid, ids, context):
        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]
        self.write(cr, uid, ids, {'aprov_data': datahora, 'aprov_user': uid, 'state': 'aprov'})
        return {'type': 'ir.actions.client', 'tag': 'reload', }

    def proposta_rejeit(self, cr, uid, ids, context):
        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]
        self.write(cr, uid, ids, {'aprov_data': datahora, 'aprov_user': uid, 'state': 'rejeit'})
        return {'type': 'ir.actions.client', 'tag': 'reload', }

    def proposta_recuperar(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'aprov_data': False, 'aprov_user': None, 'state': 'impr'})
        return {'type': 'ir.actions.client', 'tag': 'reload', }

    def call_order(self, cr, uid, ids, context):
        db_sncp_despesa_pagamentos_ordem = self.pool.get('sncp.despesa.pagamentos.ordem')
        obj = self.browse(cr, uid, ids[0])
        self.write(cr, uid, obj.id, {'gera_ordem': 1})

        vals = {
            'proposta_id': ids[0],
            'partner_id': obj.res_partner_id.id,
            'montante_iliq': obj.total_pagar,
        }

        ordem_id = db_sncp_despesa_pagamentos_ordem.create(cr, uid, vals)
        vals['ordem_id'] = ordem_id
        return db_sncp_despesa_pagamentos_ordem.criar_linhas_ordem(cr, uid, vals, context)

    _columns = {
        'name': fields.char(u'Número'),
        'data': fields.datetime(u'Data da proposta'),
        'res_partner_id': fields.many2one('res.partner', u'Parceiro de Negócios'),
        'todas': fields.boolean(u'Seleccionar Todas'),
        'montante_max': fields.float(u'Montante Máximo Total', digits=(12, 2)),
        'vencimento': fields.date(u'Vencimento até'),
        'criterio': fields.selection([('antig1', u'Da mais antiga à mais recente'),
                                      ('antig2', u'Da mais recente à mais antiga'),
                                      ('valor1', u'Da mais barata à mais cara'),
                                      ('valor2', u'Da mais cara à mais barata'), ], u'Critério'),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('impr', u'Impressa/Enviada'),
                                   ('aprov', u'Aprovada'),
                                   ('rejeit', u'Rejeitada'), ], u'Estado'),
        'aprov_data': fields.datetime(u'Data de aprovação'),
        'aprov_user': fields.many2one('res.users', u'Aprovada por'),
        'proposta_linha_id': fields.one2many('sncp.despesa.pagamentos.proposta.linha', 'proposta_id', u''),
        'total_pagar': fields.function(total_a_pagar, arg=None, method=False, type="float",
                                       string=u'Total a pagar:', store=True),
        'estado': fields.integer(u''),
        # 0 - criar linhas disponivel
        # 1 - criar linhas indisponivel
        'gera_ordem': fields.integer(u''),

    }

    _defaults = {
        'data': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day)),
        'montante_max': 999999999999.99,
        'gera_ordem': 0,
        'vencimento': lambda self, cr, uid, ctx: self._get_data(cr, uid, ctx),
        'criterio': 'antig1',
        'state': 'draft',
    }

    _order = 'name'

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_despesa_pagamentos_proposta_linha = self.pool.get('sncp.despesa.pagamentos.proposta.linha')
        db_sncp_despesa_pagamentos_ordem = self.pool.get('sncp.despesa.pagamentos.ordem')

        linhas_proposta_ids = db_sncp_despesa_pagamentos_proposta_linha.search(cr, uid, [('proposta_id', '=', ids[0])])

        ordem_proposta_ids = db_sncp_despesa_pagamentos_ordem.search(cr, uid, [('proposta_id', '=', ids[0])])

        if len(linhas_proposta_ids) != 0:
            db_sncp_despesa_pagamentos_proposta_linha.unlink(cr, uid, linhas_proposta_ids)

        if len(ordem_proposta_ids) != 0:
            db_sncp_despesa_pagamentos_ordem.unlink(cr, uid, ordem_proposta_ids)

        return super(sncp_despesa_pagamentos_proposta, self).unlink(cr, uid, ids, context=context)


sncp_despesa_pagamentos_proposta()

# ___________________________________________________________PROPOSTA LINHA______________________________________


class sncp_despesa_pagamentos_proposta_linha(osv.Model):
    _name = 'sncp.despesa.pagamentos.proposta.linha'
    _description = u"Linhas da Proposta de Pagamento"

    def montante_pag_limitado(self, cr, uid, ids, context=None):
        proposta_linha = self.browse(cr, uid, ids[0])
        if 0.0 <= proposta_linha.montante_pag <= proposta_linha.montante_res:
            return True
        return False

    def on_change_invoice_id(self, cr, uid, ids, invoice_id, proposta_id, total_pagar):
        db_sncp_despesa_pagamentos_proposta = self.pool.get('sncp.despesa.pagamentos.proposta')
        obj_proposta = db_sncp_despesa_pagamentos_proposta.browse(cr, uid, proposta_id)

        db_account_invoice = self.pool.get('account.invoice')
        obj_fatura = db_account_invoice.browse(cr, uid, invoice_id)

        db_sncp_despesa_pagamentos_rel = self.pool.get('sncp.despesa.pagamentos.rel')
        pagamentos_rel_id = db_sncp_despesa_pagamentos_rel.search(cr, uid, [('invoice_id', '=', invoice_id)])

        db_sncp_despesa_pagamentos_proposta_linha = self.pool.get('sncp.despesa.pagamentos.proposta.linha')

        if obj_fatura.partner_id.id != obj_proposta.res_partner_id.id:
            raise osv.except_osv(_(u'Aviso'), _(u'O parceiro de negócios não está associado a esta fatura.'))

        if obj_fatura.date_due > obj_proposta.vencimento:
            raise osv.except_osv(_(u'Aviso'), _(u'A data de vencimento da fatura é superior à da proposta.'))

        if obj_fatura.residual == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A fatura não têm valor por pagar.'))

        linhas_id = db_sncp_despesa_pagamentos_proposta_linha.search(cr, uid, [('proposta_id', '=', proposta_id)])

        linhas_id.remove(ids[0])
        soma_montantes = 0.0
        soma_total = total_pagar
        for linha in db_sncp_despesa_pagamentos_proposta_linha.browse(cr, uid, linhas_id):
            soma_montantes += linha.invoice_id.residual

        aux = decimal.Decimal(unicode(soma_montantes))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        soma_montantes = float(aux)

        if soma_montantes + obj_fatura.residual <= obj_proposta.montante_max:
            datatempo = datetime.strptime(obj_fatura.date_due, "%Y-%m-%d")
            data_due = date(datatempo.year, datatempo.month, datatempo.day)
            maturidade = data_due - date.today()
            if len(pagamentos_rel_id) != 0:
                obj_pagamento = db_sncp_despesa_pagamentos_rel.browse(cr, uid, pagamentos_rel_id[0])
                soma_total += obj_fatura.residual - obj_pagamento.montante_proc

                aux = decimal.Decimal(unicode(obj_fatura.residual - obj_pagamento.montante_proc))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                res_dif_proc = float(aux)

                temp = {
                    'invoice_id': invoice_id,
                    'supplier_invoice_number': obj_fatura.supplier_invoice_number,
                    'vencimento': obj_fatura.date_due,
                    'maturidade': maturidade.days,
                    'montante_orig': obj_fatura.amount_total,
                    'montante_res': res_dif_proc,
                    'montante_pag': res_dif_proc,
                }
            else:
                soma_total += obj_fatura.residual
                temp = {
                    'invoice_id': invoice_id,
                    'supplier_invoice_number': obj_fatura.supplier_invoice_number,
                    'vencimento': obj_fatura.date_due,
                    'maturidade': maturidade.days,
                    'montante_orig': obj_fatura.amount_total,
                    'montante_res': obj_fatura.residual,
                    'montante_pag': obj_fatura.residual,
                }
            self.write(cr, uid, ids, temp)
            aux = decimal.Decimal(unicode(soma_total))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            soma_total = float(aux)
            db_sncp_despesa_pagamentos_proposta.write(cr, uid, proposta_id, {'total_pagar': soma_total})

            return {'value': {'vencimento': obj_fatura.date_due,
                              'maturidade': maturidade.days,
                              'supplier_invoice_number': obj_fatura.supplier_invoice_number,
                              'montante_orig': obj_fatura.amount_total,
                              'montante_res': obj_fatura.residual,
                              'montante_pag': obj_fatura.residual,
                              'invoice_id': invoice_id}}

        return {}

    _columns = {
        'proposta_id': fields.many2one('sncp.despesa.pagamentos.proposta', u'Proposta'),
        'name': fields.integer(u'Ordem'),
        'invoice_id': fields.many2one('account.invoice', u'Fatura de compras'),
        'vencimento': fields.date(u'Data de vencimento'),
        'maturidade': fields.integer(u'Maturidade'),
        'montante_orig': fields.float(u'Valor Original', digits=(12, 2)),
        'montante_res': fields.float(u'Valor por Pagar', digits=(12, 2)),
        'montante_pag': fields.float(u'Valor a Pagar', digits=(12, 2)),
        'supplier_invoice_number': fields.related('invoice_id', 'supplier_invoice_number', type="char",
                                                  string=u"Número de fatura do fornecedor", store=True),
        'manual': fields.integer(u'Manualmente'),
        # 0 -- linha copiada da outra fatura
        # 1 -- linha criada manualmente
    }

    _order = 'name'

    _defaults = {
        'manual': 0,
    }

    _constraints = [(montante_pag_limitado, u'O Valor a Pagar deve ser menor do que o Valor por Pagar e não negativo',
                     ['montante_pag'])]

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_despesa_pagamentos_proposta_linha, self).unlink(cr, uid, ids, context=context)


sncp_despesa_pagamentos_proposta_linha()