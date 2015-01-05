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

from datetime import datetime, date
from datetime import timedelta
import re
from decimal import *
from openerp.osv import fields, osv
from openerp.tools.translate import _
import guia

# ______________________________________________________JUROS_________________________________________________


class sncp_receita_juros(osv.Model):
    _name = 'sncp.receita.juros'
    _description = u"Juros"

    def criar_novo(self, cr, uid, ids, context):
        db_sncp_receita_juros_periodo = self.pool.get('sncp.receita.juros.periodos')
        seq = guia.get_sequence(self, cr, uid, context, 'juros', ids[0])

        if int(seq) > 99:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'O número máximo de periodos é 99.'))
        db_sncp_receita_juros_periodo.create(cr, uid, {'juros_id': ids[0], 'name': seq})

    def da_quantidade(self, tipo_periodo, data_inicial, data_final):

        if tipo_periodo == 'dia':
            dif_data = data_final-data_inicial+timedelta(days=1)
            ndias = dif_data.days
            return ndias
        elif tipo_periodo == 'mes':
            nmeses = data_final.month-data_inicial.month
            for i in range(data_inicial.year+1, data_final.year+1):
                nmeses += 12

            if data_final.day > data_inicial.day:
                nmeses += 1

            return nmeses
        else:
            nanos = data_final.year-data_inicial.year
            if data_final.month > data_inicial.month:
                nanos += 1

            if data_final.month == data_inicial.month:
                if data_final.day > data_inicial.day:
                    nanos += 1

            return nanos

    def da_valor_juros(self, cr, uid, ids, vals,):
        # vals = {
        #       'datavencimento': date,
        #       'datapagamento': date,
        #       'metodo_id': ,
        #       'valorbase': ,
        #       }

        nperiodos = 0
        primeiro_periodo = False
        ultimo_periodo = False
        db_sncp_receita_juros_periodos = self.pool.get('sncp.receita.juros.periodos')
        db_sncp_receita_juros_periodos_linhas = self.pool.get('sncp.receita.juros.periodos.linhas')
        data_inicial = vals['datavencimento']
        data_final = vals['datapagamento']

        obj_juro = self.browse(cr, uid, vals['metodo_id'])
        if obj_juro.ignora is True:
            data_aux = date(data_final.year, data_final.month, 1)-timedelta(days=1)
            data_final = data_aux

        if data_final <= data_inicial:
            return 0

        periodo_ids = db_sncp_receita_juros_periodos.search(cr, uid, [('juros_id', '=', obj_juro.id),
                                                                      ('data_ini', '<=', unicode(data_inicial)),
                                                                      ('data_fim', '>=', unicode(data_final)), ])
        if len(periodo_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existem períodos para processar.'))

        data_inicio_periodo = False
        periodos = db_sncp_receita_juros_periodos.browse(cr, uid, periodo_ids)
        quantidade = ['']
        sequencia = ['']

        for periodo in periodos:
            dt_ini = datetime.strptime(periodo.data_ini, "%Y-%m-%d").date()
            dt_fim = datetime.strptime(periodo.data_fim, "%Y-%m-%d").date()
            if (dt_ini <= data_inicial <= dt_fim) or (dt_ini < data_final):
                if not primeiro_periodo:
                    data_inicio_periodo = data_inicial+timedelta(days=1)
                else:
                    data_aux_ini = datetime.strptime(periodo.data_ini, "%Y-%m-%d")
                    data_inicio_periodo = data_aux_ini.date()
                primeiro_periodo = True
            if dt_fim >= data_final:
                data_fim_periodo = data_final
                ultimo_periodo = True
            else:
                data_aux_fim = datetime.strptime(periodo.data_fim, "%Y-%m-%d")
                data_fim_periodo = data_aux_fim.date()

            if primeiro_periodo:
                nperiodos += 1
                npquantidade = self.da_quantidade(obj_juro.periodo, data_inicio_periodo, data_fim_periodo)
                quantidade.append(npquantidade)
                sequencia.append(periodo.name)
            if ultimo_periodo:
                break

        montante_periodo = [0.0]
        for i in range(1, nperiodos+1):
            n_linhas = 0
            substitui = ['']
            montante_periodo.append(0.0)
            periodo_id = db_sncp_receita_juros_periodos.search(cr, uid, [('name', '=', sequencia[i]),
                                                                         ('juros_id', '=', obj_juro.id), ])
            periodo = db_sncp_receita_juros_periodos.browse(cr, uid, periodo_id[0])

            cr.execute("""
            SELECT id FROM sncp_receita_juros_periodos_linhas AS JPL
            WHERE seq_juros_id=%d
            ORDER BY JPL.name
            """ % periodo.id)

            tup_per = cr.fetchall()

            if len(tup_per) == 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Não existem linhas para processar.'))

            juros_periodos_linhas_ids = [elem[0] for elem in tup_per]
            juros_periodos_linhas = db_sncp_receita_juros_periodos_linhas.browse(cr, uid, juros_periodos_linhas_ids)
            for juros_periodos_linha in juros_periodos_linhas:
                n_linhas += 1
                substitui.append(juros_periodos_linha.substitui)
            n_linhas = 0
            periodos_a_calcular = quantidade[i]
            for juros_periodos_linha in juros_periodos_linhas:
                if periodos_a_calcular <= 0:
                    break
                n_linhas += 1
                indice = juros_periodos_linhas_ids.index(juros_periodos_linha.id)
                if(indice == len(juros_periodos_linhas_ids)-1
                   or substitui[n_linhas+1] is False
                   or juros_periodos_linha.name >= periodos_a_calcular):
                    if juros_periodos_linha.name >= periodos_a_calcular:
                        montante_periodo[i] += self.calcula_juros_linha(obj_juro.periodo,
                                                                        periodos_a_calcular,
                                                                        juros_periodos_linha.taxa_tipo,
                                                                        vals['valorbase'],
                                                                        juros_periodos_linha.taxa_perc)
                        periodos_a_calcular = 0
                    else:
                        montante_periodo[i] += self.calcula_juros_linha(obj_juro.periodo,
                                                                        periodos_a_calcular,
                                                                        juros_periodos_linha.taxa_tipo,
                                                                        vals['valorbase'],
                                                                        juros_periodos_linha.taxa_perc)
                        periodos_a_calcular -= juros_periodos_linha.name

        somatotal = sum(montante_periodo)
        aux = Decimal(somatotal)
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_a_pagar = float(aux)
        return montante_a_pagar

    def calcula_juros_linha(self, tipo_periodo, num_periodos, taxa_tipo, valor_base, perc):
        if tipo_periodo == 'dia':
            if taxa_tipo == 'fix':
                valor = valor_base * perc/100
            elif taxa_tipo == 'dia':
                valor = valor_base * num_periodos * perc/100
            elif taxa_tipo == 'mes':
                valor = valor_base * num_periodos * perc/100/30
            elif taxa_tipo == 'ano':
                valor = valor_base * num_periodos * perc/100/360
            else:
                valor = 0
        elif tipo_periodo == 'mes':
            if taxa_tipo == 'fix':
                valor = valor_base * perc/100
            elif taxa_tipo == 'dia':
                valor = valor_base * num_periodos * perc/100*30
            elif taxa_tipo == 'mes':
                valor = valor_base * num_periodos * perc/100
            elif taxa_tipo == 'ano':
                valor = valor_base * num_periodos * perc/100/12
            else:
                valor = 0
        elif taxa_tipo == 'ano':
            if taxa_tipo == 'fix':
                valor = valor_base * perc/100
            elif taxa_tipo == 'dia':
                valor = valor_base * num_periodos * perc/100*360
            elif taxa_tipo == 'mes':
                valor = valor_base * num_periodos * perc/100*12
            elif taxa_tipo == 'ano':
                valor = valor_base * num_periodos * perc/100
            else:
                valor = 0
        else:
            valor = 0

        aux = Decimal(valor)
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        valor = float(aux)
        return valor

    _columns = {
        'name': fields.char(u'Método de Cálculo', size=3),
        'descricao': fields.char(u'Descrição', size=50),
        'contagem': fields.selection([
            ('pag', 'No Pagamento'),
            ('mes', 'Mensalmente'),
            ('ano', 'Anualmente'), ], u'Contagem'),
        'periodo': fields.selection([
            ('dia', 'Dias'),
            ('mes', 'Meses'),
            ('ano', 'Anos'), ], u'Períodos de Contagem'),
        'item_id': fields.many2one('product.product', u'Item'),
        'ignora': fields.boolean(u'Ignora os dias do mês em curso'),
        'aviso': fields.boolean(u'Imprime aviso legal nas faturas'),
        'mensagem': fields.char(u'Aviso legal das faturas'),
        'periodo_id': fields.one2many('sncp.receita.juros.periodos', 'juros_id')
    }
    _order = 'name'

    _defaults = {
        'ignora': False,
        'aviso': False,
    }

    def _name_limit(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        re_name = re.compile('^([A-Z0-9]){1,3}$')
        if re_name.match(obj.name):
            return True
        else:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'O campo Método do Cálculo é composto por maiúsculas ou algarismos'
                                   u' no máximo de 3 carateres.'))

    def _restrict_item_id(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        return guia.test_item_id(self, cr, uid, obj.item_id.id)

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_comum_codigos_contab
            WHERE met_juros_id = %d
            """ % obj.id)

            res_cod_contab = cr.fetchall()

            if len(res_cod_contab) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o juro ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Códigos de Contabilização.'))

            cr.execute("""
            DELETE FROM sncp_receita_juros_periodos_linhas
            WHERE seq_juros_id IN (SELECT id FROM sncp_receita_juros_periodos WHERE juros_id = %d)
            """ % nid)
            cr.execute("""
            DELETE FROM sncp_receita_juros_periodos WHERE juros_id = %d
            """ % nid)

        return super(sncp_receita_juros, self).unlink(cr, uid, ids, context=context)

    _constraints = [
        (_name_limit, u'', ['name']),
        (_restrict_item_id, u'', ['item_id']),
    ]

sncp_receita_juros()

# _____________________________________________________PERIODOS________________________________________________


class sncp_receita_juros_periodos(osv.Model):
    _name = 'sncp.receita.juros.periodos'
    _description = u"Juros Períodos"

    def atualiza_data_final(self, cr, uid, ids, juros_id, name, data_ini):
        if int(name) > 1:
            periodo_anterior_id = self.search(cr, uid, [('name', '=', int(name)-1),
                                                        ('juros_id', '=', juros_id)])
            data_aux = datetime.strptime(data_ini, '%Y-%m-%d')
            data_fim = date(data_aux.year+100, 12, 31)
            data_ini = date(data_aux.year, data_aux.month, data_aux.day)
            data_ant_fim = data_ini - timedelta(days=1)
            self.write(cr, uid, periodo_anterior_id, {'data_fim': unicode(data_ant_fim)})
            self.write(cr, uid, ids, {'data_ini': unicode(data_ini), 'data_fim': unicode(data_fim)})
        else:

            data_aux = datetime.strptime(data_ini, '%Y-%m-%d')
            data_fim = date(data_aux.year+100, 12, 31)
            self.write(cr, uid, ids[0], {'data_ini': unicode(data_ini), 'data_fim': unicode(data_fim)})
        return {'value': {'data_ini': unicode(data_ini), 'data_fim': unicode(data_fim)}}

    _columns = {
        'juros_id': fields.many2one('sncp.receita.juros', u'Método de Cálculo'),
        'name': fields.integer(u'Sequência', size=2),
        'data_ini': fields.date(u'Data Inicial'),
        'data_fim': fields.date(u'Data Final'),
        'linha_id': fields.one2many('sncp.receita.juros.periodos.linhas', 'seq_juros_id')
    }

    _order = 'name'

sncp_receita_juros_periodos()

# ____________________________________________________PERIODOS LINHAS________________________________________


class sncp_receita_juros_periodos_linhas(osv.Model):
    _name = 'sncp.receita.juros.periodos.linhas'
    _description = u"Juros Períodos Linhas"

    _columns = {
        'seq_juros_id': fields.many2one('sncp.receita.juros.periodos', u'Período'),
        'name': fields.integer(u'Até', size=6),
        'taxa_perc': fields.float(u'Taxa', digits=(3, 6)),
        'taxa_tipo': fields.selection([
            ('fix', 'Fixa'),
            ('dia', 'Ao Dia'),
            ('mes', 'Ao mês'),
            ('ano', 'Ao ano'), ], u''),
        'substitui': fields.boolean(u'Substitui anterior'),

    }

    _order = 'name'

    _defaults = {
        'substitui': False,
    }

sncp_receita_juros_periodos_linhas()