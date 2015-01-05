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

import re
import decimal
from decimal import *

from openerp.osv import fields, osv
from openerp.tools.translate import _


# ____________________________________________________________FUNÇÕES COMUNS AO MODULO________________________


def get_sequence(self, cr, uid, context, text, value):
    seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_'+text+'_code_'+unicode(value))
    if seq is False:
        sequence_type = self.pool.get('ir.sequence.type')
        values_type = {
            'name': 'type_'+text+'_name_'+unicode(value),
            'code':  'seq_'+text+'_code_'+unicode(value)}
        sequence_type.create(cr, uid, values_type, context=context)
        sequence = self.pool.get('ir.sequence')
        values = {
            'name': 'seq_'+text+'_name_'+unicode(value),
            'code':  'seq_'+text+'_code_'+unicode(value),
            'number_next': 1,
            'number_increment': 1}
        sequence.create(cr, uid, values, context=context)
        seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_'+text+'_code_'+unicode(value))
    return seq


def sncp_tesouraria_gera_opag_tes2opag(self, cr, uid, ordem_id):
    db_sncp_despesa_pagamentos_ordem = self.pool.get('sncp.despesa.pagamentos.ordem')
    db_sncp_despesa_pagamentos_ordem_linhas_imprimir = self.pool.get('sncp.despesa.pagamentos.ordem.linhas.imprimir')
    db_sncp_despesa_descontos_retencoes_rel_grec = self.pool.get('sncp.despesa.descontos.retencoes.rel.grec')
    db_sncp_despesa_descontos_retencoes_rel_opag = self.pool.get('sncp.despesa.descontos.retencoes.rel.opag')
    db_sncp_comum_param = self.pool.get('sncp.comum.param')

    obj_ordem = db_sncp_despesa_pagamentos_ordem.browse(cr, uid, ordem_id)
    rel_grec_ids = db_sncp_despesa_descontos_retencoes_rel_grec.search(cr, uid, [('opag_id', '=', ordem_id)])
    lista = []  # Recolha de dados
    for rel_grec_id in rel_grec_ids:
        obj_rel_grec = db_sncp_despesa_descontos_retencoes_rel_grec.browse(cr, uid, rel_grec_id)
        if obj_rel_grec.ret_desc_id.opag_imediata:
            lista.append({'montante': obj_rel_grec.montante,
                          'partner_id': obj_rel_grec.ret_desc_id.partner_id.id,
                          'desc_id': obj_rel_grec.ret_desc_id.id})
    dict_parceiros = {}  # Rearranjo por parceiros
    for line in lista:
        if line['partner_id'] in dict_parceiros:
            dict_parceiros[line['partner_id']].append({'montante': line['montante'], 'desc_id': line['desc_id']})
        else:
            dict_parceiros[line['partner_id']] = [{'montante': line['montante'], 'desc_id': line['desc_id']}]

    montante = {}  # Montante de cada parceiro
    for parceiro in dict_parceiros:
        montante[parceiro] = 0
        for desconto in dict_parceiros[parceiro]:
            montante[parceiro] += desconto['montante']

    # Processamento
    for parceiro in dict_parceiros:
        param_ids = db_sncp_comum_param.search(cr, uid, [('state', '=', 'draft')])
        if len(param_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                u'Preencha os parâmetros por defeito no menu:\n'
                                                u'Comum/Parâmetros.'))
        obj_param = db_sncp_comum_param.browse(cr, uid, param_ids[0])
        aux = decimal.Decimal(unicode(montante[parceiro]))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_arrendondado = float(aux)

        if obj_param.desp_mpag.id is not False:
            vals = {
                'tipo': 'opt',
                'partner_id': parceiro,
                'coletiva': False,
                'observ': u'Descontos/Retenções de Ordem de Pagamento '+unicode(obj_ordem.name),
                'meio_pag_id': obj_param.desp_mpag.id,
                'ref_meio': obj_param.desp_mpag.meio,
                'state': 'draft',
                'estado_linhas': 1,
                'estado_descontos': 0,
            }
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina o meio de pagamento padrão em '
                                                u'Comum/Parâmetros.'))

        new_ordem_id = db_sncp_despesa_pagamentos_ordem.create(cr, uid, vals)
        for desconto in dict_parceiros[parceiro]:
            values = {
                'opag_id': new_ordem_id,
                'name': get_sequence(self, cr, uid, {}, 'ordem_linha_imprimir', new_ordem_id),
                'conta_contabil_id': obj_rel_grec.ret_desc_id.cod_contab_id.conta_id.id,
                'organica_id': obj_rel_grec.ret_desc_id.cod_contab_id.organica_id.id,
                'economica_id': obj_rel_grec.ret_desc_id.cod_contab_id.economica_id.id,
                'funcional_id': obj_rel_grec.ret_desc_id.cod_contab_id.funcional_id.id,
                'montante': desconto['montante'],
            }
            db_sncp_despesa_pagamentos_ordem_linhas_imprimir.create(cr, uid, values)
        db_sncp_despesa_pagamentos_ordem.write(cr, uid, new_ordem_id, {'montante_iliq': montante_arrendondado})
        db_sncp_despesa_descontos_retencoes_rel_opag.create(cr, uid, {'opag_id': ordem_id, 'opag_tes_id': new_ordem_id})
    return True

# ________________________________________________________________CAIXAS_______________________________________


class sncp_tesouraria_caixas(osv.Model):
    _name = 'sncp.tesouraria.caixas'
    _description = u"Caixas"
    _rec_name = 'codigo'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'codigo'], context=context)
        res = []
        for record in reads:
            name = 'Caixa' + ' - ' + record['codigo']
            res.append((record['id'], name))
        return res

    def on_change_codigo(self, cr, uid, ids, codigo):
        if len(ids) != 0:
            self.write(cr, uid, ids, {'codigo': codigo.upper()})
        return {'value': {'codigo': codigo.upper()}}

    _columns = {
        'codigo': fields.char(u'Código', size=5),
        'name': fields.char(u'Descrição'),
        'saldo': fields.float(u'Saldo', digits=(12, 2)),
        'conta_id': fields.many2one('account.account', u'Conta Patrimonial',
                                    domain=[('type', 'not in', ['view'])]),
        'diario_id': fields.many2one('account.journal', u'Diário'),
        'caixa_user': fields.many2many('sncp.tesouraria.caixas.utilizadores', 'sncp_tesouraria_caixa_user_rel',
                                       'caixa_id', 'caixa_user',  u'pai'),
    }

    def unlink(self, cr, uid, ids, context=None):

        cr.execute("""
        SELECT id
        FROM sncp_despesa_pagamentos_ordem
        WHERE caixa_id = %d
        """ % ids[0])

        ordem_pagamentos = cr.fetchall()

        if len(ordem_pagamentos) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar esta caixa pois existem ordens'
                                                u' de pagamento associadas a esta caixa.'))

        cr.execute("""
        SELECT id
        FROM sncp_despesa_pagamentos_reposicoes
        WHERE caixa_id = %d
        """ % ids[0])

        reposicoes = cr.fetchall()

        if len(reposicoes) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar esta caixa pois existem guias '
                                                u' de reposições abatidas a pagamento'
                                                u' associadas a esta caixa.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movim_fundos_maneio
        WHERE caixa_id = %d
        """ % ids[0])

        movim_fundos_maneio = cr.fetchall()

        if len(movim_fundos_maneio) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar esta caixa pois existem movimentos'
                                                u' de fundos de maneio associados a esta caixa.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movimentos
        WHERE caixa_id = %d
        """ % ids[0])

        movim_fundos_maneio = cr.fetchall()

        if len(movim_fundos_maneio) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar esta caixa pois existem movimentos'
                                                u' de tesouraria associados a esta caixa.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movim_internos
        WHERE orig_caixa_id = %d OR dest_caixa_id = %d
        """ % (ids[0], ids[0]))

        movim_internos = cr.fetchall()

        if len(movim_internos) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar esta caixa pois existem movimentos'
                                                u' internos associados a esta caixa.'))

        cr.execute("""
        DELETE FROM sncp_tesouraria_caixas_utilizadores
        WHERE id IN (SELECT caixa_user FROM sncp_tesouraria_caixa_user_rel WHERE caixa_id = %d)
        """ % ids[0])

        cr.execute("""
        DELETE FROM sncp_tesouraria_caixa_user_rel
        WHERE caixa_id = %d
        """ % ids[0])

        return super(sncp_tesouraria_caixas, self).unlink(cr, uid, ids, context=context)

    _order = 'codigo'

    _sql_constraints = [
        ('caixa_codigo_unique', 'unique (codigo)', u'Caixa com este código já está registada!')
    ]


sncp_tesouraria_caixas()
# ________________________________________________________________CAIXAS UTILIZADORES__________________________


class sncp_tesouraria_caixas_utilizadores(osv.Model):
    _name = 'sncp.tesouraria.caixas.utilizadores'
    _description = u"Utilizadores das caixas"

    _columns = {
        'caixa_id': fields.many2many('sncp.tesouraria.caixas', 'sncp_tesouraria_caixa_user_rel',
                                     'caixa_user', 'caixa_id', u'filho'),
        'name': fields.many2one('res.users', u'Utilizador'),
        'default': fields.boolean(u'Padrão'),
    }

sncp_tesouraria_caixas_utilizadores()
# ________________________________________________________________CONTAS BANCARIAS___________________________


class sncp_tesouraria_contas_bancarias(osv.Model):
    _name = 'sncp.tesouraria.contas.bancarias'
    _description = u"Contas Bancárias"

    _rec_name = 'codigo'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'codigo'], context=context)
        res = []
        for record in reads:
            name = 'Banco' + ' - ' + record['codigo']
            res.append((record['id'], name))
        return res

    def on_change_codigo(self, cr, uid, ids, codigo):
        if len(ids) != 0:
            self.write(cr, uid, ids, {'codigo': codigo.upper()})
        return {'value': {'codigo': codigo.upper()}}

    def conta_bancaria_bloqueada(self, cr, uid, ids, context):
        db_sncp_tesouraria_series = self.pool.get('sncp.tesouraria.series')
        db_sncp_tesouraria_cheques = self.pool.get('sncp.tesouraria.cheques')
        series_ids = db_sncp_tesouraria_series.search(cr, uid, [('banco_id', '=', ids[0])])
        cheques_ids = db_sncp_tesouraria_cheques.search(cr, uid, [('serie_id', 'in', series_ids)])

        cr.execute("""
        SELECT id
        FROM sncp_despesa_pagamentos_ordem
        WHERE banco_id = %d
        """ % ids[0])

        ordem_pagamentos = cr.fetchall()

        if len(ordem_pagamentos) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode bloquear este banco pois existem ordens'
                                                u' de pagamento associadas a este banco.'))

        cr.execute("""
        SELECT id
        FROM sncp_despesa_pagamentos_reposicoes
        WHERE banco_id = %d
        """ % ids[0])

        reposicoes = cr.fetchall()

        if len(reposicoes) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode bloquear este banco pois existem guias '
                                                u' de reposições abatidas a pagamento'
                                                u' associadas a este banco.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movimentos
        WHERE banco_id = %d
        """ % ids[0])

        movim_fundos_maneio = cr.fetchall()

        if len(movim_fundos_maneio) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode bloquear este banco pois existem movimentos'
                                                u' de tesouraria associados a este banco.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movim_internos
        WHERE orig_banco_id = %d OR dest_banco_id = %d
        """ % (ids[0], ids[0]))

        movim_internos = cr.fetchall()

        if len(movim_internos) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode bloquear este banco pois existem movimentos'
                                                u' internos associados a este banco.'))

        self.write(cr, uid, ids, {'state': 'blq'})
        db_sncp_tesouraria_series.write(cr, uid, series_ids, {'estado': 2})
        db_sncp_tesouraria_cheques.write(cr, uid, cheques_ids, {'estado': 1})
        return True

    def conta_bancaria_encerrada(self, cr, uid, ids, context):
        db_sncp_tesouraria_series = self.pool.get('sncp.tesouraria.series')
        db_sncp_tesouraria_cheques = self.pool.get('sncp.tesouraria.cheques')
        series_ids = db_sncp_tesouraria_series.search(cr, uid, [('banco_id', '=', ids[0])])
        cheques_ids = db_sncp_tesouraria_cheques.search(cr, uid, [('serie_id', 'in', series_ids)])

        cr.execute("""
        SELECT id
        FROM sncp_despesa_pagamentos_ordem
        WHERE banco_id = %d
        """ % ids[0])

        ordem_pagamentos = cr.fetchall()

        if len(ordem_pagamentos) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode encerrar este banco pois existem ordens'
                                                u' de pagamento associadas a este banco.'))

        cr.execute("""
        SELECT id
        FROM sncp_despesa_pagamentos_reposicoes
        WHERE banco_id = %d
        """ % ids[0])

        reposicoes = cr.fetchall()

        if len(reposicoes) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode encerrar este banco pois existem guias '
                                                u' de reposições abatidas a pagamento'
                                                u' associadas a este banco.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movimentos
        WHERE banco_id = %d
        """ % ids[0])

        movim_fundos_maneio = cr.fetchall()

        if len(movim_fundos_maneio) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode encerrar este banco pois existem movimentos'
                                                u' de tesouraria associados a este banco.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movim_internos
        WHERE orig_banco_id = %d OR dest_banco_id = %d
        """ % (ids[0], ids[0]))

        movim_internos = cr.fetchall()

        if len(movim_internos) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode encerrar este banco pois existem movimentos'
                                                u' internos associados a este banco.'))

        self.write(cr, uid, ids, {'state': 'enc'})
        db_sncp_tesouraria_series.write(cr, uid, series_ids, {'estado': 2})
        db_sncp_tesouraria_cheques.write(cr, uid, cheques_ids, {'estado': 1})
        return True

    def conta_bancaria_ativa(self, cr, uid, ids, context):
        db_sncp_tesouraria_series = self.pool.get('sncp.tesouraria.series')
        db_sncp_tesouraria_cheques = self.pool.get('sncp.tesouraria.cheques')
        series_ids = db_sncp_tesouraria_series.search(cr, uid, [('banco_id', '=', ids[0])])
        cheques_ids = db_sncp_tesouraria_cheques.search(cr, uid, [('serie_id', 'in', series_ids)])

        self.write(cr, uid, ids, {'state': 'act'})
        db_sncp_tesouraria_series.write(cr, uid, series_ids, {'estado': 1})
        db_sncp_tesouraria_cheques.write(cr, uid, cheques_ids, {'estado': 0})
        return True

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_tesouraria_series = self.pool.get('sncp.tesouraria.series')
        series_id = db_sncp_tesouraria_series.search(cr, uid, [('banco_id', '=', ids[0])])
        if len(series_id) != 0:
            for serie_id in series_id:
                db_sncp_tesouraria_series.unlink(cr, uid, [serie_id], context=context)
        return super(sncp_tesouraria_contas_bancarias, self).unlink(cr, uid, ids, context=context)

    def serie(self, cr, uid, ids, context):
        return self.pool.get('formulario.tesouraria.series').wizard(cr, uid, ids, context)

    _columns = {
        'codigo': fields.char(u'Código da conta', size=5),
        'name': fields.char(u'Descrição'),
        'conta': fields.char(u'Conta bancária', size=21),
        'iban': fields.char(u'IBAN', size=30),
        'tipo': fields.selection([('ord', u'À Ordem'),
                                  ('prz', u'A Prazo'),
                                  ('tit', u'Títulos Negociáveis'),
                                  ('out', u'Outras')], u'Tipo de Conta'),
        'moeda_id': fields.many2one('res.currency', u'Moeda'),
        'conta_id': fields.many2one('account.account', u'Conta Patrimonial',
                                    domain=[('type', 'not in', ['view'])]),
        'diario_id': fields.many2one('account.journal', u'Diário'),
        'state': fields.selection([('act', u'Ativa'),
                                   ('blq', u'Bloqueada'),
                                   ('enc', u'Encerrada'), ], u'Estado'),
        'saldo': fields.float(u'Saldo', digits=(12, 2)),
        'series_id': fields.one2many('sncp.tesouraria.series', 'banco_id', u'Série'),
        'swift': fields.char(u'BIG/SWIFT', size=11),

    }

    def on_change_swift(self, cr, uid, ids, swift):
        swift = swift.upper()
        re_name = re.compile('^([A-Z0-9]){8,11}$')

        if re_name.match(swift):
            if len(ids) != 0:
                self.write(cr, uid, ids, {'swift': swift})
            return {'value': {'swift': swift}}
        else:
            return {
                'warning': {'title': u'Aviso',
                            'message': u'O campo BIG/SWIFT só pode conter algarismos e/ou letras maiúsculas do '
                                       u' alfabeto inglês (no mínimo 8 carateres).'}
            }

    def swift_limit(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        re_name = re.compile('^([A-Z0-9]){8,11}$')

        if re_name.match(obj.swift):
            return True
        else:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'O campo BIG/SWIFT só pode conter algarismos e/ou letras maiúsculas'
                                   + u' do alfabeto inglês (no mínimo 8 carateres).'))

    _order = 'codigo'

    _defaults = {
        'state': 'act'
    }

    _constraints = [(swift_limit, u'', 'swift')]

sncp_tesouraria_contas_bancarias()
# ________________________________________________________________SERIES_______________________________________


class sncp_tesouraria_series(osv.Model):
    _name = 'sncp.tesouraria.series'
    _description = u"Séries de cheques"

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_tesouraria_cheques = self.pool.get('sncp.tesouraria.cheques')
        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_cheques
        WHERE state IN ('pago','impr') and serie_id = %d
        """ % ids[0])

        res_cheques = cr.fetchall()

        if len(res_cheques) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Esta série contêm cheques utilizados.'))

        cheques_id = db_sncp_tesouraria_cheques.search(cr, uid, [('serie_id', '=', ids[0])])
        if len(cheques_id) != 0:
            for cheque_id in cheques_id:
                db_sncp_tesouraria_cheques.unlink(cr, uid, cheque_id, context=context)
        return super(sncp_tesouraria_series, self).unlink(cr, uid, ids, context=context)

    def serie_de_cheques(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'estado': 1})
        return self.pool.get('formulario.tesouraria.cheques').wizard(cr, uid, ids, context=context)

    _columns = {
        'banco_id': fields.many2one('sncp.tesouraria.contas.bancarias', u'Conta Bancária'),
        'name': fields.char(u'Série', size=5),
        'cheques_id': fields.one2many('sncp.tesouraria.cheques', 'serie_id', u'Cheques'),
        'estado': fields.integer(u'Estado'),
        # 1 - lista de cheques disponivel e editavel( apenas alterar o estado)
        # 2 - criar cheques invisivel e lista de cheques nao editavel(botões de alteração de estado
        # não disponiveis)
    }

    _order = 'name'

sncp_tesouraria_series()
# ________________________________________________________________CHEQUES_______________________________________


class sncp_tesouraria_cheques(osv.Model):
    _name = 'sncp.tesouraria.cheques'
    _description = u"Cheques"

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_tesouraria_cheques, self).unlink(cr, uid, ids, context=context)

    def cheque_danificado(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state': 'dani'})
        return True

    def cheque_anulado(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state': 'anul'})
        return True

    def cheque_rejeitado(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state': 'reje'})
        return True

    _columns = {
        'serie_id': fields.many2one('sncp.tesouraria.series', u'Série'),
        'numero': fields.char(u'Número', size=15),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'data_emissao': fields.date(u'Data de emissão'),
        'state': fields.selection([('nutl', u'Não utilizado'),
                                   ('dani', u'Danificado'),
                                   ('impr', u'Impresso'),
                                   ('anul', u'Anulado'),
                                   ('reje', u'Rejeitado'),
                                   ('pago', u'Pago'), ], u'Estado'),
        'opag_id': fields.many2one('sncp.despesa.pagamentos.ordem', u'Ordem de pagamento'),
        'data_reconcil': fields.date(u'Data de Reconciliação'),
        'estado': fields.integer(u'Estado'),
        # 1 para conta bloqueada ou encerrada (botões de alteração de estado invisiveis)
        # 0 para conta ativa (botões de alteração de estado visiveis)
    }

    _order = 'numero'
    _defaults = {
        'state': 'nutl',
        'estado': 0,
    }

sncp_tesouraria_cheques()