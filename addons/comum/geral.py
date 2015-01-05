# -*- coding: utf-8 -*-
# #############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime, date, timedelta
import re
from openerp.osv import fields, osv
from openerp.tools.translate import _


def test_item_id(self, cr, uid, item_id, natureza):
    db_product_product = self.pool.get('product.product')
    obj_product = db_product_product.browse(cr, uid, item_id)
    message = ''

    if natureza in ['rec', 'ots']:
        if hasattr(obj_product.product_tmpl_id, 'property_account_income'):
            if obj_product.product_tmpl_id.property_account_income.id is False:
                message += u'Contabilidade/Conta de Despesa associada ao cliente\n'
        else:
            message += u'Contabilidade/Conta de Despesa associada ao cliente\n'

        if obj_product.product_tmpl_id.sale_ok is False:
            message += u'Seleccionar opção "Pode ser vendido"\n'

    elif natureza == 'des':
        if hasattr(obj_product.product_tmpl_id, 'property_account_expense'):
            if obj_product.product_tmpl_id.property_account_expense.id is False:
                message += u'Contabilidade/Conta de Despesa associada ao fornecedor\n'
        else:
            message += u'Contabilidade/Conta de Despesa associada ao fornecedor\n'

        if obj_product.product_tmpl_id.purchase_ok is False:
            message += u'Seleccionar opção "Pode ser comprado"\n'

        if hasattr(obj_product.product_tmpl_id, 'property_stock_account_input'):
            if obj_product.product_tmpl_id.property_stock_account_input.id is False:
                message += u'Contabilidade/Avaliação do Inventário/' \
                           u'Tempo Real(automatizado) e Conta Stock de Entrada\n'
        else:
            message += u'Contabilidade/Avaliação do Inventário/' \
                       u'Tempo Real(automatizado) e Conta Stock de Entrada\n'

        if hasattr(obj_product.product_tmpl_id, 'property_stock_account_output'):
            if obj_product.product_tmpl_id.property_stock_account_output.id is False:
                message += u'Contabilidade/Avaliação do Inventário/' \
                           u'Tempo Real(automatizado) e Conta de saída de Stock\n'
        else:
            message += u'Contabilidade/Avaliação do Inventário/' \
                       u'Tempo Real(automatizado) e Conta de saída de Stock\n'

        res_id = u'product.template,' + unicode(obj_product.product_tmpl_id.id)

        cr.execute("""
        SELECT value_float
        FROM ir_property
        WHERE name = 'standard_price' AND res_id = '%s'
        """ % res_id)

        standard_price = cr.fetchone()

        if standard_price is None or standard_price[0] <= 0:
            message += u'Procurements/Preço de Custo (valor positivo)\n'

    if obj_product.default_code is False:
        message += u'Informação/Referência Interna\n'

    if len(obj_product.product_tmpl_id.taxes_id) == 0:
        message += u'Contabilidade/Impostos a Cliente\n'

    if len(obj_product.product_tmpl_id.supplier_taxes_id) == 0:
        message += u'Contabilidade/Impostos do Fornecedor\n'

    if obj_product.product_tmpl_id.type != 'product':
        message += u' Informação/Tipo de Artigo/Artigo Armazenável\n'

    if obj_product.product_tmpl_id.categ_id.id is not False:
        x = obj_product.product_tmpl_id.categ_id.property_stock_valuation_account_id.id

        if x is False:
            message += u' Para as categorias dos artigos defina a Conta de avaliação de stock.'

    if len(message) != 0:
        raise osv.except_osv(_(u'Aviso'),
                             _(u'Para evitar futuros erros na execução do programa '
                               u'deverá preencher os seguintes campos do artigo:\n' + message))
    return True


def get_sequence(self, cr, uid, context, text, value):
    # tipos de sequencia
    # Sequencia  'text' +_id

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


# ______________________________________________________Calendário_________________________________________
class sncp_comum_calendario(osv.Model):
    _name = 'sncp.comum.calendario'
    _description = u"Calendário"

    def copiar_ano(self, cr, uid, ids, context):

        self.write(cr, uid, ids, {'state': 1})

        obj_calendario = self.browse(cr, uid, ids[0])
        ano_calc = obj_calendario.name + 1
        ano_calc_id = self.create(cr, uid, {'name': ano_calc})

        db_sncp_comum_feriados = self.pool.get('sncp.comum.feriados')
        feriados_ids = db_sncp_comum_feriados.search(cr, uid, [('ano_id', '=', ids[0]),
                                                               ('tipo', '=', 'fix')])
        for record in db_sncp_comum_feriados.browse(cr, uid, feriados_ids):
            record_data = datetime.strptime(record.data, "%Y-%m-%d")
            data = record_data.date()
            data = data.replace(year=ano_calc)
            vals = {'ano_id': ano_calc_id,
                    'name': record.name,
                    'data': unicode(data),
                    'tipo': 'fix'}
            db_sncp_comum_feriados.create(cr, uid, vals)

        number = ano_calc % 19 + 1
        data = None
        if number == 1:
            data = date(ano_calc, 4, 14)
        elif number == 2:
            data = date(ano_calc, 4, 3)
        elif number == 3:
            data = date(ano_calc, 3, 23)
        elif number == 4:
            data = date(ano_calc, 4, 11)
        elif number == 5:
            data = date(ano_calc, 3, 31)
        elif number == 6:
            data = date(ano_calc, 4, 18)
        elif number == 7:
            data = date(ano_calc, 4, 8)
        elif number == 8:
            data = date(ano_calc, 3, 28)
        elif number == 9:
            data = date(ano_calc, 4, 16)
        elif number == 10:
            data = date(ano_calc, 4, 5)
        elif number == 11:
            data = date(ano_calc, 3, 25)
        elif number == 12:
            data = date(ano_calc, 4, 13)
        elif number == 13:
            data = date(ano_calc, 4, 2)
        elif number == 14:
            data = date(ano_calc, 3, 22)
        elif number == 15:
            data = date(ano_calc, 4, 10)
        elif number == 16:
            data = date(ano_calc, 3, 30)
        elif number == 17:
            data = date(ano_calc, 4, 17)
        elif number == 18:
            data = date(ano_calc, 4, 7)
        elif number == 19:
            data = date(ano_calc, 3, 27)

        data_pascoa = data + timedelta(days=(6 - data.weekday()))

        db_sncp_comum_feriados.create(cr, uid, {'ano_id': ano_calc_id,
                                                'name': u'Páscoa',
                                                'data': unicode(data_pascoa),
                                                'tipo': 'mov'})
        db_sncp_comum_feriados.create(cr, uid, {'ano_id': ano_calc_id,
                                                'name': 'Carnaval',
                                                'data': unicode(data_pascoa - timedelta(days=47)),
                                                'tipo': 'mov'})
        db_sncp_comum_feriados.create(cr, uid, {'ano_id': ano_calc_id,
                                                'name': u'Sexta-Feira Santa',
                                                'data': unicode(data_pascoa - timedelta(days=2)),
                                                'tipo': 'mov'})
        return True

    _columns = {
        'name': fields.integer(u'Ano', size=4),
        'feriado_id': fields.one2many('sncp.comum.feriados', 'ano_id', u''),
        'state': fields.integer(u'copiado')
        # 0 -- botão copiar disponivel
        # 1 -- ano ja esta copiado
    }

    def unlink(self, cr, uid, ids, context=None):
        if self.browse(cr, uid, ids[0]).name == date.today().year:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode apagar o ano corrente.'))
        ano_futuro_id = self.search(cr, uid, [('name', '=', self.browse(cr, uid, ids[0]).name + 1)])
        if len(ano_futuro_id) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode apagar o ano do meio do calendário.'))
        feriados_ids = self.pool.get('sncp.comum.feriados').search(cr, uid, [('ano_id', '=', ids[0])])
        if len(feriados_ids) != 0:
            self.pool.get('sncp.comum.feriados').unlink(cr, uid, feriados_ids)
            # state 0 para anterior
        ano_anterior_id = self.search(cr, uid, [('name', '=', self.browse(cr, uid, ids[0]).name - 1)])
        if len(ano_anterior_id) != 0:
            self.write(cr, uid, ano_anterior_id, {'state': 0})
        return super(sncp_comum_calendario, self).unlink(cr, uid, ids)

    _defaults = {'state': 0}

    _sql_constraints = [
        ('ano_unique', 'unique (name)', u'Este ano já está registado'),
    ]

#  ______________________________________________________FERIADOS_________________________________________


class sncp_comum_feriados(osv.Model):
    _name = 'sncp.comum.feriados'
    _description = u"Calendario/Feriados"

    def on_change_create(self, cr, uid, ids, tipo):
        if tipo == 'fix':
            return {}
        else:
            return {'warning': {'title': u'Feriados móveis',
                                'message': u'Os feriados móveis são inseridos manualmente para cada ano. '
                                           u'Para automatizar o processo consulte o administrador de sistema.'}}

    _columns = {
        'ano_id': fields.many2one('sncp.comum.calendario'),
        'data': fields.date(u'Data', ),
        'name': fields.char(u'Descrição', size=30, ),
        'tipo': fields.selection([
                                 ('fix', u'Fixo'),
                                 ('mov', u'Móvel'), ], u'Tipo', ),
    }

    def create(self, cr, uid, vals, context=None):
        data = None
        if type(vals['data']) in [str, unicode]:
            data = datetime.strptime(vals['data'], "%Y-%m-%d")
        elif type(vals['data']) is tuple:
            data = date(vals['data'][0], vals['data'][1], vals['data'][2])
        vals['data'] = data
        feriado_id = super(sncp_comum_feriados, self).create(cr, uid, vals, context=context)
        return feriado_id

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_comum_feriados, self).unlink(cr, uid, ids)

    _order = 'data'

    _sql_constraints = [
        ('data_unique', 'unique (data)', u'Esta data já está registada como feriado'),
    ]


# __________________________________________________________CVP__________________________________________


class sncp_comum_cpv(osv.Model):
    _name = 'sncp.comum.cpv'
    _description = u"Vocabulário Comum para os Contratos Públicos"

    _columns = {
        'name': fields.char(u'Descrição', size=255, ),
        'codigo_120': fields.char(u'Código CPV', size=10, ),
    }
    _order = 'codigo_120'

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_comum_codigos_contab
            WHERE cpv_id = %d
            """ % obj.id)

            res_cod_contab = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso_dados_adic
            WHERE cpv_id = %d
            """ % obj.id)

            res_comp = cr.fetchall()

            if len(res_cod_contab) != 0 or len(res_comp):
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o cpv ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Códigos de Contabilização.\n'
                                                    u'2. Compromissos.'))
        return super(sncp_comum_cpv, self).unlink(cr, uid, ids, context=context)

    _sql_constraints = [
        ('codigo_cpv_unique', 'unique (codigo_120)', u'O código tem que ser único!'),
    ]


#  ______________________________________________________MEIOS PAGAMENTO__________________________________


class sncp_comum_meios_pagamento(osv.Model):
    _name = 'sncp.comum.meios.pagamento'
    _description = u"Meios de Pagamento"

    _rec_name = 'name'

    _columns = {
        'metodo': fields.char(u'Método', size=3, ),
        'name': fields.char(u'Descrição', ),
        'meio': fields.selection([('cx', u'Caixa'),
                                  ('bk', u'Banco'),
                                  ('fm', u'Fundo de Maneio'),
                                  # ('dc', u'Documentos')
                                  ], u'Meio', ),
        'tipo': fields.selection([('rec', 'Recebimento'), ('pag', 'Pagamento')],
                                 u'Recebimento/Pagamento', ),
        'echeque': fields.boolean(u'É cheque?'),
    }

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_comum_param
            WHERE otes_mpag = %d OR desp_mpag = %d
            """ % (obj.id, obj.id))

            res_param = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_ordem
            WHERE meio_pag_id = %d
            """ % obj.id)

            res_ordem = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_reposicoes
            WHERE meio_pag_id = %d
            """ % obj.id)

            res_repo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_config_mapas
            WHERE meio_pag_id = %d
            """ % obj.id)

            res_tes_mapa = cr.fetchall()

            if len(res_ordem) != 0 or len(res_param) != 0 or len(res_repo) != 0 or len(res_tes_mapa) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o meio de pagamento ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Ordens de Pagamento.\n'
                                                    u'2. Parâmetros.\n'
                                                    u'3. Reposições.\n'
                                                    u'4. Tesouraria\Configurações\Mapas.'))

        return super(sncp_comum_meios_pagamento, self).unlink(cr, uid, ids, context=context)

    _order = 'metodo'

    _sql_constraints = [
        ('metodo_pagamento_unique', 'unique (metodo)', u'Este método já está registado'),
    ]


# ______________________________________________________CONDIÇOES DE PAGAMENTO___________________________


class sncp_comum_cond_pagam(osv.Model):
    _name = 'sncp.comum.cond.pagam'
    _description = u"Condições de Pagamento"

    def on_change_anual_true(self, cr, uid, ids, anual):
        if anual is True:
            return {
                'value': {'quantidade': 0,
                          'estado': 1,
                          'tipo': 'nap',
                          'contagem': 'napl'}}
        else:
            return {
                'value': {'estado': 0,
                          'dia': 0,
                          'mes': False}
            }

    def _restrict_contagem(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.anual is False and obj.contagem == 'napl':
            raise osv.except_osv(_(u'Aviso'), _(u'A contagem não pode ser "Não aplicável".'))
        return True

    def teste_anos(self, ano):
        if ano % 4 == 0:
            if ano % 100 == 0 and ano % 400 != 0:
                return False
            else:
                return True
        else:
            return False

    def teste_meses(self, mes, ano):
        if mes in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif mes in [4, 6, 9, 11]:
            return 30
        elif mes in [2] and ano > 0:
            bi = self.teste_anos(ano)
            if bi:
                return 29
            elif bi is False:
                return 28
        elif mes in [2] and ano <= 0:
            return 28

    def check_mes(self, mes, ano):
        novo_mes = mes
        novo_ano = ano
        while novo_mes > 12:
            novo_mes -= 12
            novo_ano += 1

        return novo_mes, novo_ano

    def da_data_vencimento(self, cr, uid, ids, vals, context=None):
        # vals = {
        #   'cond_pagam_id': ,
        #   'dataemissao': datetime,
        # }
        obj = self.browse(cr, uid, vals['cond_pagam_id'])
        data_ini = vals['dataemissao']
        data_venc = False
        if obj.anual is True:
            ano = data_ini.year
            mes_ini = data_ini.month
            dia_ini = data_ini.day

            if mes_ini > int(obj.mes):
                ano += 1

            if mes_ini == int(obj.mes):
                if dia_ini > obj.dia:
                    ano += 1

            if int(obj.mes) == 2:
                if obj.dia > 28:
                    if self.teste_anos(ano) is True:
                        dia_ini = obj.dia
                    else:
                        dia_ini = 28

            elif int(obj.mes) in [4, 6, 9, 11]:
                if obj.dia > 30:
                    dia_ini = 30
                else:
                    dia_ini = obj.dia
            else:
                if obj.dia > 31:
                    dia_ini = 31
                else:
                    dia_ini = obj.dia

            data_venc = date(ano, int(obj.mes), dia_ini)

        elif obj.anual is False:
            if obj.contagem == 'fmes':
                if data_ini.month < 12:
                    data_ini = date(data_ini.year, data_ini.month + 1, 1) - timedelta(days=1)
                else:
                    data_ini = date(data_ini.year + 1, 1, 1) - timedelta(days=1)
            elif obj.contagem == 'imes':
                data_ini = date(data_ini.year, data_ini.month, 1)
            elif obj.contagem == 'napl':
                raise osv.except_osv(_(u'receita/da_data_vencimento/contagem'),
                                     _(u'Ocorreu um erro inesperado, contacte o administrador do sistema.'))
            if obj.tipo == 'dia' and obj.contagem == 'imes':
                data_ini = data_ini - timedelta(days=1)
            # Teste ao tipo
            if obj.tipo == 'dia':
                data_venc = data_ini + timedelta(days=obj.quantidade)
            elif obj.tipo == 'mes':
                dia = data_ini.day
                mes = obj.quantidade + data_ini.month
                ano = data_ini.year
                tup = self.check_mes(mes, ano)
                ultimo_dia = self.teste_meses(tup[0], tup[1])
                if dia > ultimo_dia:
                    dia = ultimo_dia
                data_venc = date(tup[1], tup[0], dia)

            else:
                raise osv.except_osv(_(u'receita/da_data_vencimento/contagem'),
                                     _(u'Ocorreu um erro inesperado, contacte o administrador do sistema.'))

        if data_venc < vals['dataemissao']:
            if obj.tipo == 'dia':
                if data_venc.month < 12:
                    data_venc = date(data_venc.year, data_venc.month + 1, data_venc.day)
                else:
                    data_venc = date(data_venc.year + 1, 1, data_venc.day)
            elif obj.tipo == 'mes':
                if data_venc.month < 12:
                    data_venc = date(data_venc.year, data_venc.month + 1, data_venc.day)
                else:
                    data_venc = date(data_venc.year + 1, 1, data_venc.day)
            elif obj.anual is True:
                data_venc = date(data_venc.year + 1, data_venc.month, data_venc.day)

        if obj.dias_descanso == 'mant':
            return data_venc
        else:
            # Teste dos feriados e fim de semana
            db_sncp_comum_feriados = self.pool.get('sncp.comum.feriados')
            feriados_id = db_sncp_comum_feriados.search(cr, uid, [('data', '=', unicode(data_venc))])
            while data_venc.weekday() >= 5 or len(feriados_id) != 0:
                if obj.dias_descanso == 'ante':
                    data_venc = data_venc - timedelta(days=1)
                elif obj.dias_descanso == 'adia':
                    data_venc = data_venc + timedelta(days=1)
                feriados_id = db_sncp_comum_feriados.search(cr, uid, [('data', '=', unicode(data_venc))])
            return data_venc

    _columns = {
        'name': fields.char(u'Código', size=3),
        'descricao': fields.char(u'Descrição'),
        'quantidade': fields.integer(u'Quantidade'),
        'tipo': fields.selection([('dia', u'Dia'),
                                  ('mes', u'Mês'),
                                  ('nap', u'Não Aplicável'), ], u'Tipo'),
        'contagem': fields.selection([('imed', u'Imediata'),
                                      ('imes', u'Início do mês'),
                                      ('fmes', u'Final do mês'),
                                      ('napl', u'Não Aplicável'), ], u'A contar de'),
        'anual': fields.boolean(u'Anual'),
        'dia': fields.integer(u'Dia'),  # Testar as possibilidades quando tiver tempo
        'mes': fields.selection([
                                ('1', u'Janeiro'),
                                ('2', u'Fevereiro'),
                                ('3', u'Março'),
                                ('4', u'Abril'),
                                ('5', u'Maio'),
                                ('6', u'Junho'),
                                ('7', u'Julho'),
                                ('8', u'Agosto'),
                                ('9', u'Setembro'),
                                ('10', u'Outubro'),
                                ('11', u'Novembro'),
                                ('12', u'Dezembro'), ], u'Mês'),
        'dias_descanso': fields.selection([('mant', u'Mantém'),
                                           ('ante', u'Antecipa'),
                                           ('adia', u'Adia'), ], u'Nos dias de descanso'),
        'payment_term_id': fields.many2one('account.payment.term', u'Standard'),
        'estado': fields.integer(u'Variavel de controlo de aparencias'),
        # 1: anual=true; tipo, contagem, quantidade readonly
        # 0: anual=false; dia, mes readonly
    }

    _order = 'name'

    _defaults = {
        'estado': 0,
        'dias_descanso': 'mant',
        'dia': 1,
    }

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_comum_codigos_contab
            WHERE cond_pag_id = %d
            """ % obj.id)

            res_cod_contab = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo_config
            WHERE cond_pagam_id = %d
            """ % obj.id)

            res_controlo = cr.fetchall()

            if len(res_cod_contab) != 0 or len(res_controlo) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a condição de pagamento ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Códigos de Contabilização.\n'
                                                    u'2. Receita\Controlo de Receitas Renováveis\Configurações'
                                                    u'\Configuração Geral.'))

        return super(sncp_comum_cond_pagam, self).unlink(cr, uid, ids, context=context)

    def _name_limit(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        re_name = re.compile('^([A-Z0-9]){1,3}$')
        if re.match(re_name, obj.name):
            return True
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'O campo Código é composto por maiúsculas ou algarismos'
                                                u' no máximo de 3 carateres.'))

    def _dia_valido(self, cr, uid, ids):
        record = self.browse(cr, uid, ids[0])
        if record.mes:
            ultimo_dia = self.teste_meses(int(record.mes), 0)
            if record.dia > ultimo_dia or record.dia <= 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Para aquele mês o dia é inválido.'))
        return True

    _constraints = [
        (_name_limit, u'', ['name']),
        (_restrict_contagem, u'', ['contagem']),
        (_dia_valido, u'', ['mes', 'dia']),
    ]

    _sql_constraints = [
        ('cond_pagam_unique', 'unique (name)', u'Este código já existe!'),
        ('payment_term_unique', 'unique (payment_term_id)', u'Este Termo de Pagamento já existe!')
    ]


# ______________________________________________________CODIGOS DE CONTABILIZAÇÃO________________________


class sncp_comum_codigos_contab(osv.Model):
    _name = 'sncp.comum.codigos.contab'
    _description = u"Codigos de Contabilização"

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            if record['code'] is False:
                code = ''
            else:
                code = record['code']
            result = code + ' ' + record['name']
            res.append((record['id'], result))
        return res

    def get_code(self, cr, uid, ids, fields, arg, context):
        codigo = {}
        db_sncp_comum_codigos_contab = self.pool.get('sncp.comum.codigos.contab')
        for cod_contab_id in ids:
            obj = db_sncp_comum_codigos_contab.browse(cr, uid, cod_contab_id)
            codigo[cod_contab_id] = obj.item_id.default_code or None
        return codigo

    def get_ean13(self, cr, uid, ids, fields, arg, context):
        ean13 = {}
        db_sncp_comum_codigos_contab = self.pool.get('sncp.comum.codigos.contab')
        for cod_contab_id in ids:
            obj = db_sncp_comum_codigos_contab.browse(cr, uid, cod_contab_id)
            ean13[cod_contab_id] = obj.item_id.ean13 or None
        return ean13

    def get_name_template(self, cr, uid, ids, fields, arg, context):
        name_template = {}
        db_sncp_comum_codigos_contab = self.pool.get('sncp.comum.codigos.contab')
        for cod_contab_id in ids:
            obj = db_sncp_comum_codigos_contab.browse(cr, uid, cod_contab_id)
            name_template[cod_contab_id] = obj.item_id.name_template or None
        return name_template

    _columns = {
        'item_id': fields.many2one('product.product', u'Item'),
        'code': fields.function(get_code, arg=None, method=False, type="char",
                                string=u'Código', store=True),
        'ean13': fields.function(get_ean13, arg=None, method=False, type="char",
                                 string=u'Código EAN 13', store=True),
        'natureza': fields.selection([('rec', u'Receita Orçamental'),
                                      ('des', u'Despesa Orçamental'),
                                      ('ots', u'Operações de tesouraria')], u'Natureza'),
        'name': fields.function(get_name_template, arg=None, method=False, type="char",
                                string=u'Nome', store=True),
        'conta_id': fields.many2one('account.account', u'Patrimonial',
                                    domain=[('type', 'not in', ['view'])], ),
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')], ),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')], ),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')], ),
        'cond_pag_id': fields.many2one('sncp.comum.cond.pagam', u'Condições de Pagamento'),
        # # addons/receita/herancas.py/sncp_comum_codigos_contab met_juros_id'
        'cpv_id': fields.many2one('sncp.comum.cpv', u'Vocabulário Comum Contr. Pública'),
    }

    _order = 'item_id, natureza'

    def _restrict_item_id(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        return test_item_id(self, cr, uid, obj.item_id.id, obj.natureza)

    def write(self, cr, uid, ids, vals, context=None):
        if 'natureza' in vals:
            if vals['natureza'] == 'des':
                vals['cond_pag_id'] = False
                vals['met_juros_id'] = False
            elif vals['natureza'] in ['rec', 'ots']:
                vals['cpv_id'] = False

        return super(sncp_comum_codigos_contab, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_despesa_descontos_retencoes
            WHERE cod_contab_id = %d
            """ % obj.id)

            res_desc = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo_config
            WHERE cod_contab_id = %d
            """ % obj.id)

            res_controlo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_fatura_modelo_linha
            WHERE cod_contab_id = %d
            """ % obj.id)

            res_modelo_linha = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_guia_rec_linhas
            WHERE cod_contab_id = %d
            """ % obj.id)

            res_guia_linhas = cr.fetchall()

            if len(res_controlo) != 0 or len(res_desc) != 0 or len(res_modelo_linha) != 0 or \
               len(res_guia_linhas):
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o código de contabilização '
                                                    + obj.code + u' ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Receita\Controlo de Receitas Renováveis\Configuração'
                                                    u'\Configurações Gerais.\n'
                                                    u'2. Descontos e Retenções.\n'
                                                    u'3. Receita\Faturação Recorrente\Modelos de Faturas.\n'
                                                    u'4. Guias de Receita.'))

        return super(sncp_comum_codigos_contab, self).unlink(cr, uid, ids, context=context)

    _constraints = [
        (_restrict_item_id, u'', ['item_id']),
    ]


# ========================================= REFERENCIAS GEOGRAFICAS =====================================

# __________________________________________ Freguesias ________________________________________________


class sncp_comum_freguesias(osv.Model):
    _name = 'sncp.comum.freguesias'
    _description = u"Freguesias"

    _columns = {
        'name': fields.char(u'Nome de Freguesia', size=64),
        'coord_centro': fields.char(u'Coordenadas do Centro', size=30),
        'populacao': fields.integer(u'População'),
        'eleitores': fields.integer(u'Eleitores inscritos'),
    }

    def _restrict_populacao(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.populacao < 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A população duma freguesia não pode ser negativa.'))
        else:
            return True

    def _restrict_eleitores(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.eleitores < 0:
            raise osv.except_osv(_(u'Aviso'), _(u'O número de eleitores não pode ser negativo.'))
        else:
            return True

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_comum_bairros
            WHERE freguesia_id = %d
            """ % obj.id)

            res_bairro = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_comum_arruamentos
            WHERE freguesia1_id = %d OR freguesia2_id = %d
            """ % (obj.id, obj.id))

            res_arru = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo
            WHERE freguesia_id = %d
            """ % obj.id)

            res_controlo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_regproc_aquis_alien_parcel
            WHERE freguesia_id = %d
            """ % obj.id)

            res_alien_parcel = cr.fetchall()

            if len(res_controlo) != 0 or len(res_alien_parcel) != 0 or len(res_arru) != 0 or \
               len(res_bairro) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a freguesia '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Receita\Controlo de Receitas Renováveis.\n'
                                                    u'2. Aquisições e Alienações.\n'
                                                    u'3. Arruamentos.\n'
                                                    u'4. Bairros.'))
        return super(sncp_comum_freguesias, self).unlink(cr, uid, ids, context=None)

    _constraints = [
        (_restrict_populacao, u'', ['populacao']),
        (_restrict_eleitores, u'', ['eleitores']),
    ]


# __________________________________________ Bairros ________________________________________________


class sncp_comum_bairros(osv.Model):
    _name = 'sncp.comum.bairros'
    _description = u"Bairros"

    _columns = {
        'name': fields.char(u'Nome do Bairro', size=64),
        'coord_centro': fields.char(u'Coordenadas do Centro', size=30),
        'freguesia_id': fields.many2one('sncp.comum.freguesias', u'Freguesia'),
    }

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_comum_arruamentos
            WHERE bairro_id = %d
            """ % obj.id)

            res_arru = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo
            WHERE bairro_id = %d
            """ % obj.id)

            res_controlo = cr.fetchall()

            if len(res_arru) != 0 or len(res_controlo) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o bairro '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Receita\Controlo de Receitas Renováveis.\n'
                                                    u'2. Arruamentos.'))

        return super(sncp_comum_bairros, self).unlink(cr, uid, ids, context=context)

# __________________________________________ Arruamentos ________________________________________________


class sncp_comum_arruamentos(osv.Model):
    _name = 'sncp.comum.arruamentos'
    _description = u"Arruamentos"

    def open_map(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj = self.browse(cr, uid, ids, context=context)[0]
        url = "http://maps.google.com/maps?oi=map&q="
        if obj.name:
            url += obj.name.replace(' ', '+')
        if obj.bairro_id:
            url += '+' + obj.bairro_id.name.replace(' ', '+')
        if obj.freguesia1_id:
            url += '+' + obj.freguesia1_id.name.replace(' ', '+')

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }

    def open_inicio(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj = self.browse(cr, uid, ids, context=context)[0]
        url = "http://maps.google.com/maps?oi=map&q="

        if obj.inicio_coord:
            url += '+' + obj.inicio_coord.replace(' ', '+')

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }

    def open_termo(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj = self.browse(cr, uid, ids, context=context)[0]
        url = "http://maps.google.com/maps?oi=map&q="

        if obj.termo_coord:
            url += '+' + obj.termo_coord.replace(' ', '+')
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }

    _columns = {
        'name': fields.char(u'Nome de Arruamento', size=64),
        'inicio_desc': fields.char(u'Início', size=64),
        'inicio_coord': fields.char(u'Coord. do Início', size=30, ),
        'termo_desc': fields.char(u'Termo', size=64),
        'termo_coord': fields.char(u'Coordenadas do Termo', size=30),
        'bairro_id': fields.many2one('sncp.comum.bairros', u'Bairro'),
        'freguesia1_id': fields.many2one('sncp.comum.freguesias', u'Freguesia'),
        'freguesia2_id': fields.many2one('sncp.comum.freguesias', u'Freguesia'),
        'n1_freg1': fields.char(u'Primeiro número', size=6),
        'n2_freg1': fields.char(u'Último número', size=6),
        'n1_freg2': fields.char(u'Primeiro número', size=6),
        'n2_freg2': fields.char(u'Último número', size=6),
    }

    def _check_bairro(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.bairro_id.freguesia_id.id == obj.freguesia1_id.id or\
           obj.bairro_id.freguesia_id.id == obj.freguesia2_id.id:
            return True
        return False

    _constraints = [
        (_check_bairro, u'O bairro seleccionado não pertence a freguesia', ['bairro_id']),
    ]

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo
            WHERE arruamento_id = %d
            """ % obj.id)

            res_controlo = cr.fetchall()

            if len(res_controlo) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o arruamento '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Receita\Controlo de Receitas Renováveis.'))
        return super(sncp_comum_arruamentos, self).unlink(cr, uid, ids,)


# ========================================= Avisos e notificações =====================================


class sncp_comum_etiquetas(osv.Model):
    _name = 'sncp.comum.etiquetas'
    _description = u'Etiquetas de Avisos e Notificações'

    _columns = {
        'name': fields.char(u'Etiqueta', size=6),
        'descr': fields.char(u'Descrição'),
        'model_id': fields.many2one('ir.model', u'Modelo de dados'),
        'path': fields.char(u'Caminho (notação de pontos)'),
    }
