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
import decimal
from decimal import *
from openerp.osv import fields, osv
from openerp.tools.translate import _
import tesouraria


# ________________________________________________________________TIPOS DE MOVIMENTO_____________________________
class sncp_tesouraria_tipo_mov(osv.Model):
    _name = 'sncp.tesouraria.tipo.mov'
    _description = u"Tipo de Movimento"

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'codigo'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['codigo']:
                name = record['codigo'] + ' - ' + name
            res.append((record['id'], name))
        return res

    def on_change_codigo(self, cr, uid, ids, codigo):
        if len(ids) != 0:
            self.write(cr, uid, ids, {'codigo': codigo.upper()})
        return {'value': {'codigo': codigo.upper()}}

    def unlink(self, cr, uid, ids, context=None):

        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_fundos_maneio_rel
            WHERE name = %d
            """ % obj.id)

            res_fmaneio_rel = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_movim_fundos_maneio
            WHERE tipo_mov_tes_id = %d
            """ % obj.id)

            res_mov_fmaneio = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_config_mapas
            WHERE tipo_mov_id = %d
            """ % obj.id)

            res_config_mapas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_movim_internos
            WHERE tipo_mov_id = %d
            """ % obj.id)

            res_mv_int = cr.fetchall()

            if len(res_config_mapas) != 0 or len(res_fmaneio_rel) != 0 or len(res_mov_fmaneio) != 0 or \
               len(res_mv_int) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o tipo de movimento '
                                                    + obj.codigo + u'-' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Tipos de Movimento FM.\n'
                                                    u'2. Tesouraria\Movimentos\Movimentos de Fundo de Maneio.\n'
                                                    u'3. Tesouraria\Configurações\Mapas.\n'
                                                    u'4. Tesouraria\Movimentos\Movimentos Internos.'))

        return super(sncp_tesouraria_tipo_mov, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'codigo': fields.char(u'Código', size=3),
        'name': fields.char(u'Descrição'),
        'conta_id': fields.many2one('account.account', u'Conta de passagem',
                                    domain=[('type', 'not in', ['view'])]),
        'origem_tipo': fields.selection([('cx', u'Caixa'),
                                         ('bk', u'Banco'),
                                         ('fm', u'Fundo de Maneio'),
                                          # ('dc', u'Documentos')
                                         ], u'Tipo da origem'),
        'destino_tipo': fields.selection([('cx', u'Caixa'),
                                          ('bk', u'Banco'),
                                          ('fm', u'Fundo de Maneio'),
                                          # ('dc', u'Documentos')
                                          ], u'Tipo de destino'),
        'mov_interno': fields.boolean(u'Mov. Caixas'),
    }

    _order = 'codigo'

    _sql_constraints = [
        ('tipo_mov_code_unique', 'unique (codigo)', u'O Código têm que ser único.')
    ]

sncp_tesouraria_tipo_mov()
# ________________________________________________________________CONFIGURAÇÃO DE MAPAS___________________________


class sncp_tesouraria_config_mapas(osv.Model):
    _name = 'sncp.tesouraria.config.mapas'
    _description = u"Configuração de Mapas"

    def create(self, cr, uid, vals, context=None):
        numero = 0
        if 'meio_pag_id' in vals:
            numero = tesouraria.get_sequence(self, cr, uid, {}, 'meio_pag', vals['meio_pag_id'])
        elif 'tipo_mov_id' in vals:
            numero = tesouraria.get_sequence(self, cr, uid, {}, 'tipo_mov', vals['tipo_mov_id'])

        vals['name'] = int(numero)
        return super(sncp_tesouraria_config_mapas, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'origem' in vals:
            if vals['origem'] == 'recpag':
                vals['tipo_mov_id'] = False
            elif vals['origem'] == 'movtes':
                vals['meio_pag_id'] = False

        return super(sncp_tesouraria_config_mapas, self).write(cr, uid, ids, vals, context=context)

    def on_change_origem(self, cr, uid, ids, origem):
        if origem == 'recpag':
            return {'value': {'tipo_mov_id': False, }}
        elif origem == 'movtes':
            return {'value': {'meio_pag_id': False, }}
        else:
            return {}

    _columns = {
        'origem': fields.selection([
            ('recpag', u'Recebimento/Pagamento'),
            ('movtes', u'Movimento de Tesouraria')], u'Origem'),
        'meio_pag_id': fields.many2one('sncp.comum.meios.pagamento', u'Meio de Pagamento',
                                       domain=[('meio', 'not in', ['dc'])]),
        'tipo_mov_id': fields.many2one('sncp.tesouraria.tipo.mov', u'Tipo Movimento de Tesouraria'),
        'name': fields.integer(u'Sequência'),
        'natureza': fields.selection([
            ('entra', u'Entrada'),
            ('saida', u'Saída')], u'Natureza'),
        'meio': fields.selection([('cx', u'Caixa'),
                                  ('do', u'Depósitos à Ordem'),
                                  ('dp', u'Depósitos a Prazo'),
                                  ('fm', u'Fundo de Maneio'),
                                  # ('dc', u'Documentos')
                                  ], u'Meio Movimentado'),
        'coluna': fields.selection([
            ('01rece', u'Receita Orçamental'),
            ('02rapg', u'Reposições Abatidas nos Pagamentos'),
            ('03otsr', u'Operações de Tesouraria (recebimentos)'),
            ('04bncl', u'Bancos (levantamentos)'),
            ('05fmnl', u'Fundos de Maneio (levantamentos)'),
            # ('06cobr', u'Documentos de Cobrança (entradas)'),
            ('11desp', u'Despesa Orçamental'),
            ('12otsp', u'Operações de Tesouraria (pagamentos)'),
            ('13bncd', u'Bancos (depósitos)'),
            ('14fmnp', u'Fundos de Maneio (pagamentos)'),
            # ('15cobp', u'Documentos de Cobrança (saídas)'),
            ], u'Coluna'),
    }

    _order = 'origem,meio_pag_id,tipo_mov_id,name'

sncp_tesouraria_config_mapas()
# ________________________________________________________________TIPOS DE MOVIMENTO_____________________________


class sncp_tesouraria_movimentos(osv.Model):
    _name = 'sncp.tesouraria.movimentos'
    _description = u"Movimentos de Tesouraria"
    # No create accionar as funções
    # -- escreve_datahora

    # Recebe datahora em formato datetime
    def escreve_datahora(self, cr, uid, ids, datahora):
        data = unicode(date(datahora.year, datahora.month, datahora.day))
        z = unicode(datahora.second).zfill(2)
        hora = unicode(datahora.hour).zfill(2)+':'+unicode(datahora.minute).zfill(2)+':' + z
        self.write(cr, uid, ids, {'data': data, 'hora': hora})
        return True

    def cria_movimento_tesouraria(self, cr, uid, ids, vals):
        # Todos os campos presentes na ficha devem ser inicializados.
        # Se não são utilizados o valor atribuido é 0(zero)
        #     'datahora': dh,
        #     'name': '',
        #     'montante': obj.montante,
        #     'em_cheque': obj.mont_em_cheque,
        #     'montante_ot': obj.montante_ot,
        #     'origem':'recpag'|| 'movtes',
        #     'origem_id': obj.meio_pag_id.id || obj.tipo_mov_tes_id.id,
        #     'caixa_id': caixa_id,#Lista [Saida,Entrada]
        #     'banco_id': banco_id,#Lista [Saida,Entrada]
        #     'fmaneio_id': fundo_id,#Lista [Saida,Entrada]
        # Retorna o movimento_id(lista)
        # Chamar função                                escreve datahora

        montante_oo = 0
        db_sncp_tesouraria_config_mapas = self.pool.get('sncp.tesouraria.config.mapas')
        if vals['origem'] == 'recpag':
            montante_oo = vals['montante']-vals['montante_ot']

            aux = decimal.Decimal(unicode(montante_oo))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_oo = float(aux)

            mapas_ids = db_sncp_tesouraria_config_mapas.search(cr, uid, [('origem', '=', vals['origem']),
                                                                         ('meio_pag_id', '=', vals['origem_id']),
                                                                         ('tipo_mov_id', '=', None)])
        elif vals['origem'] == 'movtes':
            mapas_ids = db_sncp_tesouraria_config_mapas.search(cr, uid, [('origem', '=', vals['origem']),
                                                                         ('meio_pag_id', '=', None),
                                                                         ('tipo_mov_id', '=', vals['origem_id'])])
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Contacte o administrador do sistema.'))

        if len(mapas_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não foi encontrado nenhum mapa de tesouraria'
                                                u' correspondente à operaçao pretendida.'))
        movimento_id = []

        for mapa_id in mapas_ids:
            caixa = 0
            banco = 0
            fmaneio = 0
            obj_tesour = False
            obj_mapa = db_sncp_tesouraria_config_mapas.browse(cr, uid, mapa_id)
            if obj_mapa.meio == 'cx':
                if obj_mapa.natureza == 'saida':
                    caixa = vals['caixa_id'][0]
                elif obj_mapa.natureza == 'entra':
                    caixa = vals['caixa_id'][1]
                db_sncp_tesouraria_caixas = self.pool.get('sncp.tesouraria.caixas')
                if caixa != 0:
                    obj_tesour = db_sncp_tesouraria_caixas.browse(cr, uid, caixa)
                else:
                    pass

            elif obj_mapa.meio in ['do', 'dp']:
                if obj_mapa.natureza == 'saida':
                    banco = vals['banco_id'][0]
                elif obj_mapa.natureza == 'entra':
                    banco = vals['banco_id'][1]
                db_sncp_tesouraria_contas_bancarias = self.pool.get('sncp.tesouraria.contas.bancarias')
                if banco != 0:
                    obj_tesour = db_sncp_tesouraria_contas_bancarias.browse(cr, uid, banco)
                else:
                    pass

            elif obj_mapa.meio == 'fm':
                if obj_mapa.natureza == 'saida':
                    fmaneio = vals['fmaneio_id'][0]
                elif obj_mapa.natureza == 'entra':
                    fmaneio = vals['fmaneio_id'][1]
                db_sncp_tesouraria_fundos_maneio = self.pool.get('sncp.tesouraria.fundos.maneio')
                if fmaneio != 0:
                    obj_tesour = db_sncp_tesouraria_fundos_maneio.browse(cr, uid, fmaneio)
                else:
                    pass
            elif obj_mapa.meio == 'dc':
                raise osv.except_osv(_(u'Erro'), _(u'Esta parte do código está por fazer.'))
            else:
                raise osv.except_osv(_(u'Aviso'), _(u'O mapa está mal preenchido.'))

            # Criar movimentos
            if obj_mapa.coluna in ['01rece', '11desp'] and montante_oo > 0:
                if obj_tesour is not False:
                    valores = {
                        'datahora': vals['datahora'],        'name': vals['name'],
                        'sequencia': obj_mapa.name,         'montante': montante_oo,
                        'em_cheque': vals['em_cheque'],     'origem': obj_mapa.origem,
                        'caixa_id': caixa,                  'banco_id': banco,
                        'fmaneio_id': fmaneio,              'codigo': obj_tesour.codigo,
                        'conta_id': obj_tesour.conta_id.id, 'natureza': obj_mapa.natureza,
                        'meio': obj_mapa.meio,              'coluna': obj_mapa.coluna,
                    }
                    movimento_id.append(self.create(cr, uid, valores))
            elif obj_mapa.coluna in ['03otsr', '12otsp'] and vals['montante_ot'] > 0:
                if obj_tesour is not False:
                    valores = {
                        'datahora': vals['datahora'],            'name': vals['name'],
                        'sequencia': obj_mapa.name,             'montante': vals['montante_ot'],
                        'em_cheque': vals['em_cheque'],         'origem': obj_mapa.origem,
                        'caixa_id': caixa,                      'banco_id': banco,
                        'fmaneio_id': fmaneio,                  'codigo': obj_tesour.codigo,
                        'conta_id': obj_tesour.conta_id.id,     'natureza': obj_mapa.natureza,
                        'meio': obj_mapa.meio,                  'coluna': obj_mapa.coluna,
                    }
                    movimento_id.append(self.create(cr, uid, valores))
            else:
                if obj_tesour is not False:
                    valores = {
                        'datahora': vals['datahora'],            'name': vals['name'],
                        'sequencia': obj_mapa.name,             'montante': vals['montante'],
                        'em_cheque': vals['em_cheque'],         'origem': obj_mapa.origem,
                        'caixa_id': caixa,                      'banco_id': banco,
                        'fmaneio_id': fmaneio,                  'codigo': obj_tesour.codigo,
                        'conta_id': obj_tesour.conta_id.id,     'natureza': obj_mapa.natureza,
                        'meio': obj_mapa.meio,                  'coluna': obj_mapa.coluna,
                    }
                    movimento_id.append(self.create(cr, uid, valores))

        if len(movimento_id) != 0:
            datahora = datetime.strptime(unicode(vals['datahora']), "%Y-%m-%d %H:%M:%S")
            self.escreve_datahora(cr, uid, movimento_id, datahora)
            return movimento_id
        else:
            return True

    def elimina_movimento_tesouraria(self, cr, uid, ids, vals):
        # {
        #   'name': ,
        #   'datahora': }
        data = unicode(datetime.strptime(vals['datahora'], "%Y-%m-%d %H:%M:%S").date())
        db_sncp_tesouraria_folha_caixa = self.pool.get('sncp.tesouraria.folha.caixa')
        fechada = db_sncp_tesouraria_folha_caixa.folha_caixa_fechada(cr, uid, ids, data)
        if fechada:
            raise osv.except_osv(_(u'Aviso'), _(u'O Mapa de Tesouraria de '+data+u' está fechado.'))
        else:
            cr.execute("""
                DELETE FROM sncp_tesouraria_movimentos
                WHERE name = '%s' AND datahora = '%s'""" % (vals['name'], vals['datahora']))
            return True

    _columns = {
        'datahora': fields.datetime(u'Hora'),
        'data': fields.date(u'Data'),
        'hora': fields.char(u'Hora', size=8),
        'name': fields.char(u'Documento', size=12),
        'sequencia': fields.integer(u'Sequência'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'em_cheque': fields.float(u'Montante em cheque', digits=(12, 2)),
        # O montante em numerário é a diferença entre o montante e o montante em cheque;
        'origem': fields.selection([('recpag', u'Recebimento/Pagamento'),
                                    ('movtes', u'Movimento de Tesouraria')], u'Origem'),
        'caixa_id': fields.many2one('sncp.tesouraria.caixas', u'Caixa'),
        'banco_id': fields.many2one('sncp.tesouraria.contas.bancarias', u'Banco'),
        'fmaneio_id': fields.many2one('sncp.tesouraria.fundos.maneio', u'Fundo de Maneio'),
        'codigo': fields.char(u'Código', size=5),
        'conta_id': fields.many2one('account.account', u'Conta SNCP'),
        'natureza': fields.selection([
            ('entra', u'Entrada'),
            ('saida', u'Saída'), ], u'Natureza'),
        'meio': fields.selection([('cx', u'Caixa'),
                                  ('do', u'Depósitos à Ordem'),
                                  ('dp', u'Depósitos a Prazo'),
                                  ('fm', u'Fundo de Maneio'),
                                  ('dc', u'Documentos'),
                                  ], u'Meio Movimentado'),
        'coluna': fields.selection([
            ('01rece', u'Receita Orçamental'),
            ('02rpag', u'Reposições Abatidas nos Pagamentos'),
            ('03otsr', u'Operações de Tesouraria (recebimentos)'),
            ('04bncl', u'Bancos (levantamentos)'),
            ('05fmnl', u'Fundos de Maneio (levantamentos)'),
            ('06cobr', u'Documentos de Cobrança (entradas)'),
            ('11desp', u'Despesa Orçamental'),
            ('12otsp', u'Operações de Tesouraria (pagamentos)'),
            ('13bncd', u'Bancos (depósitos)'),
            ('14fmnp', u'Fundos de Maneio (pagamentos)'),
            ('15cobp', u'Documentos de Cobrança (saídas)'), ], u'Coluna'),
        'reconcil_date': fields.datetime(u'Reconciliado em'),
        'reconsil_user': fields.many2one('res.users', u'Reconciliado por'),
    }

    _order = 'data,hora,name,sequencia'

sncp_tesouraria_movimentos()
# ________________________________________________________________MOVIMENTOS INTERNOS_____________________________


class sncp_tesouraria_movim_internos(osv.Model):
    _name = 'sncp.tesouraria.movim.internos'
    _description = u"Movimentos Internos"

    def prosseguir(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state': 'fromto', 'processar': 1})
        return True

    def continuar(self, cr, uid, ids, context):
        self.mesma_tipo_origem_destino(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'processar': 2})
        return True

    def on_change_de_para(self, cr, uid, ids, fromto, oque, fromto_id):
        obj_tesour = None
        if oque == 'Caixa - ':
            db_sncp_tesouraria_caixas = self.pool.get('sncp.tesouraria.caixas')
            obj_tesour = db_sncp_tesouraria_caixas.browse(cr, uid, fromto_id)
        elif oque == 'Banco - ':
            db_sncp_tesouraria_contas_bancarias = self.pool.get('sncp.tesouraria.contas.bancarias')
            obj_tesour = db_sncp_tesouraria_contas_bancarias.browse(cr, uid, fromto_id)
        elif oque == 'Fundo Maneio - ':
            db_sncp_tesouraria_fundos_maneio = self.pool.get('sncp.tesouraria.fundos.maneio')
            obj_tesour = db_sncp_tesouraria_fundos_maneio.browse(cr, uid, fromto_id)
        self.write(cr, uid, ids, {fromto: oque+unicode(obj_tesour.codigo)})
        return {}

    def processar(self, cr, uid, ids, context):
        return self.processa_movim_interno(cr, uid, ids)

    def processa_movim_interno(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        db_ir_sequence = self.pool.get('ir.sequence')
        db_account_move = self.pool.get('account.move')
        db_account_journal = self.pool.get('account.journal')
        db_account_move_line = self.pool.get('account.move.line')
        db_sncp_tesouraria_caixas = self.pool.get('sncp.tesouraria.caixas')
        db_sncp_tesouraria_movimentos = self.pool.get('sncp.tesouraria.movimentos')
        db_sncp_tesouraria_fundos_maneio = self.pool.get('sncp.tesouraria.fundos.maneio')
        db_sncp_tesouraria_contas_bancarias = self.pool.get('sncp.tesouraria.contas.bancarias')

        self.write(cr, uid, ids, {'processar': 3})
        caixa_id = [0, 0]
        banco_id = [0, 0]
        fmaneio_id = [0, 0]
        conta_id = [0, 0]

        # Aceder a conta e atualizar saldo origem
        if obj.de == 'cx':
            conta_id[0] = obj.orig_caixa_id.conta_id.id
            obj_caixa = db_sncp_tesouraria_caixas.browse(cr, uid, obj.orig_caixa_id.id)
            diario_id = obj_caixa.diario_id.id
            caixa_id[0] = obj_caixa.id
            aux = decimal.Decimal(unicode(obj_caixa.saldo-obj.montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_cx = float(aux)

            db_sncp_tesouraria_caixas.write(cr, uid, obj_caixa.id, {'saldo': montante_cx})
        elif obj.de == 'bk':
            conta_id[0] = obj.orig_banco_id.conta_id.id
            obj_banco = db_sncp_tesouraria_contas_bancarias.browse(cr, uid, obj.orig_banco_id.id)
            diario_id = obj_banco.diario_id.id
            banco_id[0] = obj_banco.id
            aux = decimal.Decimal(unicode(obj_banco.saldo-obj.montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_bk = float(aux)

            db_sncp_tesouraria_contas_bancarias.write(cr, uid, obj_banco.id, {'saldo': montante_bk})
        elif obj.de == 'fm':
            conta_id[0] = obj.orig_fmaneio_id.conta_id.id
            obj_fmaneio = db_sncp_tesouraria_fundos_maneio.browse(cr, uid, obj.orig_fmaneio_id.id)
            diario_id = obj_fmaneio.diario_id.id
            fmaneio_id[0] = obj_fmaneio.id
            aux = decimal.Decimal(unicode(obj_fmaneio.saldo-obj.montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_fm = float(aux)

            db_sncp_tesouraria_fundos_maneio.write(cr, uid, obj_fmaneio.id, {'saldo': montante_fm})
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Tipo de Movimento está mal definido.'))

        datahora = datetime.strptime(obj.datahora, "%Y-%m-%d %H:%M:%S")
        dicti = db_account_move.account_move_prepare(cr, uid, diario_id, datahora.date(), obj.ref_lanc)
        jornal = db_account_journal.browse(cr, uid, diario_id)
        if jornal.sequence_id.id:
            name = db_ir_sequence.next_by_id(cr, uid, jornal.sequence_id.id)
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'O diário '+unicode(jornal.name) +
                                                u' não têm sequência de movimentos associada.'))
        dicti['name'] = name
        move_id = db_account_move.create(cr, uid, dicti)

        # Processar as contas
        db_account_move_line.create(cr, uid, {'account_id': conta_id[0],
                                              'date': dicti['date'],
                                              'journal_id': dicti['journal_id'],
                                              'period_id': dicti['period_id'],
                                              'name': dicti['name'],
                                              'move_id': move_id,
                                              'credit': obj.montante, })
        # Conta de passagem
        if obj.tipo_mov_id.conta_id.id is not False:
            db_account_move_line.create(cr, uid, {'account_id':  obj.tipo_mov_id.conta_id.id,
                                                  'date': dicti['date'],
                                                  'journal_id': dicti['journal_id'],
                                                  'period_id': dicti['period_id'],
                                                  'name': dicti['name'],
                                                  'move_id': move_id,
                                                  'debit': obj.montante, })
            db_account_move_line.create(cr, uid, {'account_id': obj.tipo_mov_id.conta_id.id,
                                                  'date': dicti['date'],
                                                  'journal_id': dicti['journal_id'],
                                                  'period_id': dicti['period_id'],
                                                  'name': dicti['name'],
                                                  'move_id': move_id,
                                                  'credit': obj.montante, })
        # Atualizar saldo destino
        if obj.para == 'cx':
            obj_caixa = db_sncp_tesouraria_caixas.browse(cr, uid, obj.dest_caixa_id.id)
            caixa_id[1] = obj_caixa.id
            conta_id[1] = obj_caixa.conta_id.id
            aux = decimal.Decimal(unicode(obj_caixa.saldo+obj.montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_caixa = float(aux)

            db_sncp_tesouraria_caixas.write(cr, uid, obj_caixa.id, {'saldo': montante_caixa})
        elif obj.para == 'bk':
            obj_banco = db_sncp_tesouraria_contas_bancarias.browse(cr, uid, obj.dest_banco_id.id)
            banco_id[1] = obj_banco.id
            conta_id[1] = obj_banco.conta_id.id
            aux = decimal.Decimal(unicode(obj_banco.saldo+obj.montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_banco = float(aux)

            db_sncp_tesouraria_contas_bancarias.write(cr, uid, obj_banco.id, {'saldo': montante_banco})
        elif obj.para == 'fm':
            obj_fmaneio = db_sncp_tesouraria_fundos_maneio.browse(cr, uid, obj.dest_fmaneio_id.id)
            fmaneio_id[1] = obj_fmaneio.id
            conta_id[1] = obj_fmaneio.conta_id.id
            aux = decimal.Decimal(unicode(obj_fmaneio.saldo+obj.montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_fmaneio = float(aux)

            db_sncp_tesouraria_fundos_maneio.write(cr, uid, obj_fmaneio.id, {'saldo': montante_fmaneio})
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Tipo de Movimento está mal definido.'))

        # Processar Contas
        db_account_move_line.create(cr, uid, {'account_id': conta_id[1],
                                              'date': dicti['date'],
                                              'journal_id': dicti['journal_id'],
                                              'period_id': dicti['period_id'],
                                              'name': dicti['name'], 'move_id': move_id,
                                              'debit': obj.montante, })
        # Atualizar campos
        self.write(cr, uid, ids[0], {'name': name, 'movimento_id': move_id})
        if obj.tipo_mov_id.mov_interno is False:
            values = {'datahora': obj.datahora,
                      'name': name,
                      'montante': obj.montante,
                      'em_cheque': obj.em_cheque,
                      'montante_ot': 0,
                      'origem': 'movtes',
                      'origem_id': obj.tipo_mov_id.id,
                      'caixa_id': caixa_id,
                      'banco_id': banco_id,
                      'fmaneio_id': fmaneio_id}
            db_sncp_tesouraria_movimentos.cria_movimento_tesouraria(cr, uid, ids, values)
        return True

    _columns = {
        'datahora': fields.datetime(u'Data de transação'),
        'name': fields.char(u'Número', size=12),
        'tipo_mov_id': fields.many2one('sncp.tesouraria.tipo.mov',  u'Tipo Movimento de Tesouraria'),
        'de': fields.related('tipo_mov_id', 'origem_tipo', type="char", store=True, string="de"),
        'para': fields.related('tipo_mov_id', 'destino_tipo', type="char", store=True, string="to"),
        'orig_caixa_id': fields.many2one('sncp.tesouraria.caixas', u'Caixa'),
        'orig_banco_id': fields.many2one('sncp.tesouraria.contas.bancarias', u'Banco',
                                         domain=[('state', 'in', ['act'])]),
        'orig_fmaneio_id': fields.many2one('sncp.tesouraria.fundos.maneio', u'Fundo de Maneio',
                                           domain=[('ativo', '=', True)]),
        'orig_codigo': fields.char(u'Código da origem', size=5),
        'origem': fields.char(u'Origem'),    # Só para lista
        'dest_caixa_id': fields.many2one('sncp.tesouraria.caixas', u'Caixa'),
        'dest_banco_id': fields.many2one('sncp.tesouraria.contas.bancarias', u'Banco',
                                         domain=[('state', 'in', ['act'])]),
        'dest_fmaneio_id': fields.many2one('sncp.tesouraria.fundos.maneio', u'Fundo de Maneio',
                                           domain=[('ativo', '=', True)]),
        'dest_codigo': fields.char(u'Código do destino', size=5),
        'destino': fields.char(u'Destino'),  # Só para lista
        'montante': fields.float(u'Montante total', digits=(12, 2)),
        'em_cheque': fields.float(u'Montante em cheque', digits=(12, 2)),
        'ref_lanc': fields.char(u'Referência de Lançamento', size=50),
        'movimento_id': fields.many2one('account.move', u'Movimento contábil'),
        'state': fields.selection([('draft', u''), ('fromto', u'')]),
        'processar': fields.integer(u''),
        # 1 -- por campos todos a readonly e aparecer botão de continuar
        # 2 -- aparece o botão processar movimento interno
        # 3 -- desaparece o botão processar movimento interno
    }

    _order = 'datahora,name'

    _defaults = {
        'datahora': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                     datetime.now().hour, datetime.now().minute, datetime.now().second)),
        'processar': 0,
        'state': 'draft',
    }

    def exclui_fm_rel(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        db_sncp_tesouraria_fundos_maneio_rel = self.pool.get('sncp.tesouraria.fundos.maneio.rel')

        fm_rel_ids = db_sncp_tesouraria_fundos_maneio_rel.search(cr, uid, [('name', '=', obj.tipo_mov_id.id)])
        if len(fm_rel_ids) != 0:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Este tipo de movimento de tesouraria têm '
                                   u'associação com os fundos de maneio.'))
        return True

    def mesma_tipo_origem_destino(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.tipo_mov_id.origem_tipo == obj.tipo_mov_id.destino_tipo:
            if obj.tipo_mov_id.origem_tipo == 'cx':
                if obj.orig_caixa_id.id == obj.dest_caixa_id.id:
                    raise osv.except_osv(_(u'Aviso'), _(u'Caixa de origem diferente de caixa de destino.'))
            elif obj.tipo_mov_id.origem_tipo == 'bk':
                if obj.orig_banco_id.id == obj.dest_banco_id.id:
                    raise osv.except_osv(_(u'Aviso'), _(u'Banco de origem diferente de banco de destino.'))
            elif obj.tipo_mov_id.origem_tipo == 'fm':
                if obj.orig_fmaneio_id.id == obj.dest_fmaneio_id.id:
                    raise osv.except_osv(_(u'Aviso'), _(u'Fundo de origem diferente de fundo de destino.'))
        return True

    _constraints = [
        (exclui_fm_rel, u'', ['tipo_mov_id']),
    ]

sncp_tesouraria_movim_internos()