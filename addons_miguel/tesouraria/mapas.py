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

from datetime import datetime, date, timedelta
import decimal
from decimal import *

from openerp.osv import fields, osv
from openerp.tools.translate import _


# ________________________________________________DIARIOS DOS MAPAS____________________________________________________

class sncp_tesouraria_mapas_diario(osv.Model):
    _name = 'sncp.tesouraria.mapas.diario'
    _description = u"Mapas diários"

    def imprimir_report_diario(self, cr, uid, ids, context):
        context['mapa'] = True
        return self.pool.get('sncp.tesouraria.folha.caixa').imprimir_report_diario(cr, uid, ids, context)

    def imprimir_report_caixa(self, cr, uid, ids, context):
        context['mapa'] = True
        return self.pool.get('sncp.tesouraria.folha.caixa').imprimir_report_caixa(cr, uid, ids, context)

    _columns = {
        'name': fields.date(u'Data'),
        'ano': fields.integer(u'Ano', size=4),
        'numero': fields.integer(u'Número'),
        'folha_linhas': fields.integer(u'Linhas da Folha'),
        'folha_pagina': fields.integer(u'Páginas da folha'),
        'resumo_linhas': fields.integer(u'Linhas do Resumo'),
        'fechado': fields.boolean(u'Fechado'),
        'linhas_id': fields.one2many('sncp.tesouraria.mapas.diario.linhas', 'mapa_id'), }

    _order = 'name'

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            db_sncp_tesouraria_mapas_diario_linhas = self.pool.get('sncp.tesouraria.mapas.diario.linhas')
            db_sncp_tesouraria_mapas_diario_resumo = self.pool.get('sncp.tesouraria.mapas.diario.resumo')

            linhas_ids = db_sncp_tesouraria_mapas_diario_linhas.search(cr, uid, [('mapa_id', '=', nid)])
            resumo_ids = db_sncp_tesouraria_mapas_diario_resumo.search(cr, uid, [('mapa_id', '=', nid)])

            if len(linhas_ids) != 0:
                db_sncp_tesouraria_mapas_diario_linhas.unlink(cr, uid, linhas_ids, context)

            if len(resumo_ids) != 0:
                db_sncp_tesouraria_mapas_diario_resumo.unlink(cr, uid, resumo_ids, context)

        return super(sncp_tesouraria_mapas_diario, self).unlink(cr, uid, ids, context=context)

sncp_tesouraria_mapas_diario()
# ________________________________________________DIARIOS DOS MAPAS (LINHAS)____________________________________________


class sncp_tesouraria_mapas_diario_linhas(osv.Model):
    _name = 'sncp.tesouraria.mapas.diario.linhas'
    _description = u"Mapas Diários Linhas"

    _columns = {
        'mapa_id': fields.many2one('sncp.tesouraria.mapas.diario'),
        'pagina': fields.integer(u'Página'),
        'linha': fields.integer(u'Linha'),
        'name': fields.char(u'Documento', size=12),
        'cod_sncp': fields.char(u'Código SNCP', size=12),
        'montante_col01': fields.float(u'Receita\norçamental', digits=(12, 2)),
        'montante_col02': fields.float(u'Rep.Abat.\nPagamentos', digits=(12, 2),
                                       help=u'Reposições abatidas nos pagamentos'),
        'montante_col03': fields.float(u'Op.Tes.\n(receb.)', digits=(12, 2),
                                       help=u'Operações tesouraria (recebimentos'),
        'montante_col04': fields.float(u'Bancos\n(levant.)', digits=(12, 2)),
        'montante_col05': fields.float(u'F.maneio\n(levant)', digits=(12, 2)),
        'montante_col06': fields.float(u'Doc.de\u0020Cobr.\n(entrada)', digits=(12, 2),
                                       help=u'Documentos de Cobrança (entrada)'),
        'montante_col11': fields.float(u'Despesa\norçamental', digits=(12, 2)),
        'montante_col12': fields.float(u'Op.\u0020Tes.\n(pagam.)', digits=(12, 2),
                                       help=u'Operações tesouraria (pagamentos)'),
        'montante_col13': fields.float(u'Bancos\n(depósitos)', digits=(12, 2)),
        'montante_col14': fields.float(u'F.Maneio\n(const/reconstr)', digits=(12, 2)),
        'montante_col15': fields.float(u'Doc.de\u0020Cobr.\n(saída)', digits=(12, 2)),
    }

    _order = 'mapa_id,pagina,linha'

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_tesouraria_mapas_diario_linhas, self).unlink(cr, uid, ids, context=context)

sncp_tesouraria_mapas_diario_linhas()
# ________________________________________________DIARIOS DOS MAPAS (RESUMO)____________________________________________


class sncp_tesouraria_mapas_diario_resumo(osv.Model):
    _name = 'sncp.tesouraria.mapas.diario.resumo'
    _description = u"Mapas Diários Resumo"

    _columns = {
        'mapa_id': fields.many2one('sncp.tesouraria.mapas.diario', u'Mapa_diário'),
        'cap': fields.selection([('01Disp', u'Disponibilidades'), ('02Docs', u'Documentos'),
                                 ('03Oporc', u'Operações Orçamentais')], u'Capítulo'),
        'art': fields.selection([('01cx', u'Caixa'), ('02fm', u'Fundos de Maneio'),
                                 ('03bn', u'Bancos'), ('04at', u'Aplicações de Tesouraria')], u'Artigo'),
        'num': fields.selection([('0101num', u'Numerário'), ('0102chq', u'Cheques e Vales Postais'),
                                 ('0301ord', u'À ordem'), ('0302prz', u'A prazo'),
                                 ('0401tit', u'Títulos Negociáveis'), ('0402out', u'Outros')], u'Número'),
        'codigo': fields.char(u'Código', size=5),
        'desc': fields.char(u'Descrição', size=64),
        'conta': fields.char(u'Conta', size=21),
        'saldo_ant': fields.float(u'Saldo do dia anterior', digits=(12, 2)),
        'entrada': fields.float(u'Entrada do dia', digits=(12, 2)),
        'saida': fields.float(u'Saída do dia', digits=(12, 2)),
    }

    _order = 'mapa_id,cap,art,num,codigo'

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_tesouraria_mapas_diario_resumo, self).unlink(cr, uid, ids, context=context)

sncp_tesouraria_mapas_diario_resumo()
# ________________________________________________FOLHA DA CAIXA)____________________________________________


class sncp_tesouraria_folha_caixa(osv.Model):
    _name = 'sncp.tesouraria.folha.caixa'
    _description = u"Folha de Caixa"

    def on_change_encerrar_apenas(self, cr, uid, ids, encerrar_apenas):
        if encerrar_apenas:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'imprimir_fc': False,
                                          'imprimir_rd': False,
                                          'encerrar_fc': False,
                                          'encerrar_apenas': True})
            return {
                'value': {'imprimir_rd': False,
                          'imprimir_fc': False,
                          'encerrar_fc': False,
                          'encerrar_apenas': True, }
            }
        else:
            return {}

    def on_change_imprimir(self, cr, uid, ids, fc, rd):
        if fc is False and rd is False:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'encerrar_fc': False})
            return {
                'value': {'encerrar_fc': False, }
            }
        if fc is True:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'encerrar_apenas': False, 'imprimir_fc': True, 'imprimir_rd': False})
            return {
                'value': {'encerrar_apenas': False, 'imprimir_fc': True, 'imprimir_rd': False}
            }
        if rd is True:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'encerrar_apenas': False, 'imprimir_fc': False, 'imprimir_rd': True})
            return {
                'value': {'encerrar_apenas': False, 'imprimir_fc': False, 'imprimir_rd': True}
            }

        return {}

    def select_date(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        obj_id = self.search(cr, uid, [('name', '=', obj.name)])

        if len(obj_id) > 1:
            res_id = obj_id[1]
            result = self.folha_caixa_fechada(cr, uid, ids, obj.name)
            if result:
                self.write(cr, uid, ids, {'state': 'closed'})
            else:
                self.write(cr, uid, ids, {'state': 'created'})
                res_id = ids[0]
        else:
            self.write(cr, uid, ids, {'state': 'created'})
            res_id = ids[0]

        cr.execute("""
                DELETE FROM sncp_tesouraria_folha_caixa
                WHERE id < %d and name = '%s' and state IN ('created','closed')
                """ % (obj.id, obj.name))

        cr.execute("""DELETE FROM sncp_tesouraria_folha_caixa
                WHERE state = 'new'""")

        return {'name': 'name',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'sncp.tesouraria.folha.caixa',
                'nodestroy': True,
                'res_id': res_id,
                }

    def imprimir_fechar(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        report = {'caixa': 0, 'diario': 0}
        dados_carregados = False

        # Processamento da caixa
        if obj.imprimir_fc:
            [caixa, diario, dados_carregados] = self.imprime_folha_caixa(cr, uid, ids, obj.name)
            report['caixa'] += caixa
            report['diario'] += diario
        if obj.imprimir_rd:
            [caixa, diario, dados_carregados] = self.imprime_resumo_diario(cr, uid, ids, obj.name, dados_carregados)
            report['caixa'] += caixa
            report['diario'] += diario
        if obj.encerrar_fc or obj.encerrar_apenas:
            self.encerra_folha(cr, uid, ids, obj.name, dados_carregados)

        if obj.imprimir_fc is False and obj.imprimir_rd is False and \
           obj.encerrar_fc is False and obj.encerrar_apenas is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Têm que seleccionar pelo menos uma opção.'))

        # Impressão de relatorio
        if report['caixa'] > 0 and report['diario'] == 0:
            return self.imprimir_report_caixa(cr, uid, ids, context)
        if report['diario'] > 0 and report['caixa'] == 0:
            return self.imprimir_report_diario(cr, uid, ids, context)
        if report['caixa'] > 0 and report['diario'] > 0:
            return [self.imprimir_report_caixa(cr, uid, ids, context),
                    self.imprimir_report_diario(cr, uid, ids, context)]

        return True

    def folha_caixa_fechada(self, cr, uid, ids, data):
        cr.execute("""
                SELECT fechado FROM sncp_tesouraria_mapas_diario
                WHERE name = '%s'
            """ % data)
        result = cr.fetchone()
        if result is None:
            return False
        return result[0]

    def imprime_folha_caixa(self, cr, uid, ids, data):
        result = self.folha_caixa_fechada(cr, uid, ids, data)
        if result:
            return [1, 0, False]
        else:
            dados_carregados = self.carrega_dados_folha_caixa(cr, uid, ids, data)
            return [1, 0, dados_carregados]

    def imprime_resumo_diario(self, cr, uid, ids, data, dados_carregados):
        result = self.folha_caixa_fechada(cr, uid, ids, data)
        if result:
            return [0, 1, dados_carregados]
        else:
            if dados_carregados is False:
                dados_carregados = self.carrega_dados_folha_caixa(cr, uid, ids, data)
            return [0, 1, dados_carregados]

    def encerra_folha(self, cr, uid, ids, data, dados_carregados):
        db_sncp_tesouraria_mapas_diario = self.pool.get('sncp.tesouraria.mapas.diario')
        if dados_carregados is False:
            dados_carregados = self.carrega_dados_folha_caixa(cr, uid, ids, data)

        diario_id = db_sncp_tesouraria_mapas_diario.search(cr, uid, [('name', '=', data)])
        db_sncp_tesouraria_mapas_diario.write(cr, uid, diario_id, {'fechado': True})
        # Percorrer os movimentos e fecha-los para 6
        cr.execute("""SELECT id from sncp_tesouraria_movim_fundos_maneio
                      WHERE data_mov::DATE = '%s'""" % data)
        res_id = cr.fetchall()
        if len(res_id) != 0:
            cr.execute("""UPDATE sncp_tesouraria_movim_fundos_maneio SET estado=6
                          WHERE id IN (SELECT id from sncp_tesouraria_movim_fundos_maneio
                                       WHERE data_mov::DATE = '%s')""" % data)

        return dados_carregados

    def imprimir_report_diario(self, cr, uid, ids, context):
        if 'mapa' in context:
            mp_ids = ids[0]
        else:
            obj = self.browse(cr, uid, ids[0])
            cr.execute("""
             SELECT id FROM sncp_tesouraria_mapas_diario WHERE name='%s'
            """ % obj.name)
            mp_ids = cr.fetchone()
            if mp_ids is not None:
                mp_ids = mp_ids[0]

        if mp_ids is not None:

            datas = {'ids': [mp_ids],
                     'model': 'sncp.tesouraria.mapas.diario', }
            return {
                'type': 'ir.actions.report.xml',
                'nodestroy': True,
                'report_name': 'sncp.tesouraria.mapas.diario.resumo.report',
                'datas': datas,
            }
        return True

    def imprimir_report_caixa(self, cr, uid, ids, context):
        if 'mapa' in context:
            mp_ids = ids[0]
        else:
            obj = self.browse(cr, uid, ids[0])
            cr.execute("""
             SELECT id FROM sncp_tesouraria_mapas_diario WHERE name='%s'
            """ % obj.name)
            mp_ids = cr.fetchone()
            if mp_ids is not None:
                mp_ids = mp_ids[0]

        if mp_ids is not None:
            cr.execute("""
            SELECT id FROM sncp_tesouraria_mapas_diario_linhas
            WHERE mapa_id = %d
            """ % mp_ids)

            mapas_linhas_ids = cr.fetchall()

            if len(mapas_linhas_ids) == 0:
                return True

            datas = {'ids': [mp_ids],
                     'model': 'sncp.tesouraria.mapas.diario', }
            return {
                'type': 'ir.actions.report.xml',
                'nodestroy': True,
                'report_name': 'sncp.tesouraria.folha.caixa.report',
                'datas': datas,
            }
        return True

    def procura_ultima_data(self, cr, uid, ids, ultima_data):
        db_sncp_comum_feriados = self.pool.get('sncp.comum.feriados')
        db_sncp_tesouraria_mapas_diario = self.pool.get('sncp.tesouraria.mapas.diario')
        contador_feriados = 0
        ultimo_mapas_diario_id = []
        data_imprimir = date(1900, 1, 1)
        cr.execute(""" SELECT count(*),max(name),min(name)
                       FROM sncp_tesouraria_mapas_diario
        """)
        record = cr.fetchone()
        if record[1] is None or record[0] in [0, 1]:
            return [contador_feriados, data_imprimir, 0, data_imprimir]

        if record[2] is not None:
            menor_data = datetime.strptime(record[2], "%Y-%m-%d").date()
            if ultima_data <= menor_data:
                return [contador_feriados, data_imprimir, 0, data_imprimir]

        while len(ultimo_mapas_diario_id) == 0:
            ultima_data = ultima_data - timedelta(days=1)
            if ultima_data.weekday() >= 5 or \
               len(db_sncp_comum_feriados.search(cr, uid, [('data', '=', unicode(ultima_data))])) != 0:
                contador_feriados += 1
            else:
                data_imprimir = ultima_data
            ultimo_mapas_diario_id = db_sncp_tesouraria_mapas_diario.search(cr, uid,
                                                                            [('name', '=', unicode(ultima_data))])

        return [contador_feriados, ultima_data, ultimo_mapas_diario_id[0], data_imprimir]

    def cria_resumo(self, cr, uid, ids, ultimo_mapa_diario_id, mapas_diario_id, cap, art, num, codigo, desc, conta):
        db_sncp_tesouraria_mapas_diario_resumo = self.pool.get('sncp.tesouraria.mapas.diario.resumo')
        if cap == '02Docs' or ultimo_mapa_diario_id == 0:
            saldo_ant = 0.00
        elif art is None:
            cr.execute("""SELECT COALESCE(saldo_ant,0.0) + COALESCE(entrada,0.0) - COALESCE(saida,0.0)
                          FROM sncp_tesouraria_mapas_diario_resumo
                          WHERE mapa_id =%d AND cap = '%s'
                       """ % (ultimo_mapa_diario_id, cap))
            saldo_ant = cr.fetchone()
        elif num is None:
            cr.execute("""SELECT COALESCE(saldo_ant,0.0) + COALESCE(entrada,0.0) - COALESCE(saida,0.0)
                          FROM sncp_tesouraria_mapas_diario_resumo
                          WHERE mapa_id =%d AND cap = '%s' AND art = '%s' AND codigo = '%s'
                       """ % (ultimo_mapa_diario_id, cap, art, codigo))
            saldo_ant = cr.fetchone()
        elif codigo is None:
            cr.execute("""SELECT COALESCE(saldo_ant,0.0) + COALESCE(entrada,0.0) - COALESCE(saida,0.0)
                          FROM sncp_tesouraria_mapas_diario_resumo
                          WHERE mapa_id =%d AND cap = '%s' AND art = '%s' AND num = '%s'
                       """ % (ultimo_mapa_diario_id, cap, art, num))
            saldo_ant = cr.fetchone()
        else:
            cr.execute("""SELECT COALESCE(saldo_ant,0.0) + COALESCE(entrada,0.0) - COALESCE(saida,0.0)
                          FROM sncp_tesouraria_mapas_diario_resumo
                          WHERE mapa_id =%d AND cap = '%s' AND art = '%s' AND num = '%s' AND codigo = '%s'
                       """ % (ultimo_mapa_diario_id, cap, art, num, codigo))
            saldo_ant = cr.fetchone()

        if saldo_ant is None or cap == '02Docs' or ultimo_mapa_diario_id == 0:
            saldo_ant = 0.00
        else:
            saldo_ant = saldo_ant[0]

        aux = decimal.Decimal(unicode(saldo_ant))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        saldo_ant = float(aux)

        values_resumo = {
            'mapa_id': mapas_diario_id,
            'cap': cap,
            'art':  art,
            'num': num,
            'codigo': codigo,
            'desc': desc,
            'conta': conta,
            'saldo_ant': saldo_ant,
        }
        return db_sncp_tesouraria_mapas_diario_resumo.create(cr, uid, values_resumo)

    def processa_resumos(self, cr, uid, ids, mapas_diario_id, data_date):
        [contador_feriados, ultima_data, ultimo_mapas_diario_id, data_imprimir] = self.procura_ultima_data(cr, uid, ids,
                                                                                                           data_date)

        # Numerario
        # # CAPITULO ARTIGO NUMERO CODIGO
        self.cria_resumo(cr, uid, ids, ultimo_mapas_diario_id, mapas_diario_id,
                         '01Disp', '01cx', '0101num', None, None, None)

        # Cheques e Vales Postais
        self.cria_resumo(cr, uid, ids, ultimo_mapas_diario_id, mapas_diario_id,
                         '01Disp', '01cx', '0102chq', None, None, None)

        # Fundo de Maneio
        cr.execute("""SELECT codigo FROM sncp_tesouraria_fundos_maneio
                      WHERE ativo = TRUE OR saldo <> 0.00""")
        codigo = cr.fetchall()
        for code in codigo:
            self.cria_resumo(cr, uid, ids, ultimo_mapas_diario_id, mapas_diario_id,
                             '01Disp', '02fm', None, code[0], None, None)

        # Bancos
        cr.execute("""SELECT (CASE
                                  WHEN tipo = 'ord' THEN '0301ord'
                                  WHEN tipo = 'prz' THEN '0302prz'
                                  WHEN tipo = 'tit' THEN '0401tit'
                                  ELSE '0402out' END),
                              codigo, name, conta
                      FROM sncp_tesouraria_contas_bancarias
                      WHERE state = 'act' OR saldo <> 0.00""")
        result = cr.fetchall()
        for res in result:
            if res[0] == '0401tit' or res[0] == '0402out':
                self.cria_resumo(cr, uid, ids, ultimo_mapas_diario_id, mapas_diario_id,
                                 '01Disp', '04at', res[0], res[1], res[1]+' - '+res[2], None)
            else:
                self.cria_resumo(cr, uid, ids, ultimo_mapas_diario_id, mapas_diario_id,
                                 '01Disp', '03bn', res[0], res[1], res[1]+' - '+res[2], res[3])

        # Documentos
        cr.execute("""SELECT id FROM sncp_tesouraria_mapas_diario_resumo
                      WHERE cap = '02Docs' AND mapa_id = %d""" % ultimo_mapas_diario_id)
        result = cr.fetchone()
        if result is None:
            self.cria_resumo(cr, uid, ids, ultimo_mapas_diario_id, mapas_diario_id,
                             '02Docs', None, None, None, None, None)

        # Operações Orçamentais
        self.cria_resumo(cr, uid, ids, ultimo_mapas_diario_id, mapas_diario_id, '03Oporc', None, None, None,
                         None, None)
        return True

    def processa_movimentos(self, cr, uid, ids, data):
        # data em formato datetime
        db_sncp_tesouraria_mapas_diario_linhas = self.pool.get('sncp.tesouraria.mapas.diario.linhas')
        db_sncp_tesouraria_mapas_diario_resumo = self.pool.get('sncp.tesouraria.mapas.diario.resumo')
        db_sncp_tesouraria_mapas_diario = self.pool.get('sncp.tesouraria.mapas.diario')

        db_sncp_tesouraria_caixas = self.pool.get('sncp.tesouraria.caixas')
        db_sncp_tesouraria_contas_bancarias = self.pool.get('sncp.tesouraria.contas.bancarias')
        db_sncp_tesouraria_fundos_maneio = self.pool.get('sncp.tesouraria.fundos.maneio')

        mapas_diario_id = db_sncp_tesouraria_mapas_diario.search(cr, uid, [('name', '=', data)])

        # Bloco de preenchimento das linhas
        cr.execute(""" SELECT name,meio, COALESCE(montante,0.0),
                    banco_id, caixa_id, fmaneio_id,
                    (CASE
                        WHEN coluna = '01rece' THEN 'montante_col01'
                        WHEN coluna = '02rpag' THEN 'montante_col02'
                        WHEN coluna = '03otsr' THEN 'montante_col03'
                        WHEN coluna = '04bncl' THEN 'montante_col04'
                        WHEN coluna = '05fmnl' THEN 'montante_col05'
                        WHEN coluna = '06cobr' THEN 'montante_col06'
                        WHEN coluna = '11desp' THEN 'montante_col11'
                        WHEN coluna = '12otsp' THEN 'montante_col12'
                        WHEN coluna = '13bncd' THEN 'montante_col13'
                        WHEN coluna = '14fmnp' THEN 'montante_col14'
                        WHEN coluna = '15cobp' THEN 'montante_col15'
                    END)

            FROM sncp_tesouraria_movimentos
            WHERE data = '%s'
            ORDER BY hora, name, sequencia""" % (unicode(data)))
        movimentos = cr.fetchall()
        if len(movimentos) == 0:
            pass
        for movim in movimentos:
            linhas_criadas = []
            cr.execute("""SELECT id FROM sncp_tesouraria_mapas_diario_linhas
                WHERE mapa_id = %d AND name = '%s' """ % (mapas_diario_id[0], movim[0]))
            linha_id = cr.fetchone()
            if linha_id is None:

                # Codigo SNCP
                if movim[1] in ['do', 'dp']:
                    banco = db_sncp_tesouraria_contas_bancarias.browse(cr, uid, movim[3])
                    codigo = banco.conta_id.code
                elif movim[1] == 'cx':
                    caixa = db_sncp_tesouraria_caixas.browse(cr, uid, movim[4])
                    codigo = caixa.conta_id.code
                elif movim[1] == 'fm':
                    fmaneio = db_sncp_tesouraria_fundos_maneio.browse(cr, uid, movim[5])
                    codigo = fmaneio.conta_id.code
                else:
                    codigo = ''  # Aguarda futuras alterações

                values_create = {
                    'mapa_id': mapas_diario_id[0],
                    'name': movim[0],
                    'cod_sncp': codigo,
                    movim[6]: movim[2],
                }
                linhas_criadas.append(db_sncp_tesouraria_mapas_diario_linhas.create(cr, uid, values_create))
            else:
                values_write = {
                    movim[6]: movim[2],
                }
                db_sncp_tesouraria_mapas_diario_linhas.write(cr, uid, linha_id[0], values_write)

            # Bloco de Numeração de linhas e páginas
            pagina = 1
            linha = 1
            for lin_id in linhas_criadas:
                db_sncp_tesouraria_mapas_diario_linhas.write(
                    cr, uid, lin_id, {'pagina': pagina, 'linha': linha})
                if linha == 28:
                    linha = 1
                    pagina += 1
                else:
                    linha += 1
        # Bloco de preenchimento de resumo
        cr.execute("""SELECT COALESCE(montante,0.0),coluna
            FROM sncp_tesouraria_movimentos
            WHERE data = '%s' AND origem = 'recpag'
            """ % unicode(data))

        movimentos = cr.fetchall()

        total_entradas = 0.0
        total_saidas = 0.0

        for movimento in movimentos:
            if movimento[1] in ['01rece', '02rpag']:
                total_entradas += movimento[0]
            elif movimento[1] == '11desp':
                total_saidas += movimento[0]

        diario_resumo_id = db_sncp_tesouraria_mapas_diario_resumo.search(cr, uid,
                                                                         [('mapa_id', '=', mapas_diario_id),
                                                                          ('cap', '=', '03Oporc')])
        if len(diario_resumo_id) != 0:
            db_sncp_tesouraria_mapas_diario_resumo.write(cr, uid, diario_resumo_id,
                                                         {'entrada': total_entradas, 'saida': total_saidas})

        return True

    def carrega_dados_folha_caixa(self, cr, uid, ids, data):
        dados_carregados = False
        db_sncp_comum_feriados = self.pool.get('sncp.comum.feriados')
        db_sncp_tesouraria_mapas_diario = self.pool.get('sncp.tesouraria.mapas.diario')
        mapas_diario_id = db_sncp_tesouraria_mapas_diario.search(cr, uid, [('name', '=', data)])
        data_date = datetime.strptime(data, "%Y-%m-%d").date()
        # data de registo (vai ser criada)
        if len(mapas_diario_id) == 0:
            data_anterior = data_date - timedelta(days=1)
            diario_anterior_id = db_sncp_tesouraria_mapas_diario.search(cr, uid,
                                                                        [('name', '=', unicode(data_anterior))])
            # Data imediatamente anterior
            if len(diario_anterior_id) == 0:
                # A procura de ultima data
                [contador_feriados, ultima_data, ultimo_mapas_diario_id, data_imprimir] = \
                    self.procura_ultima_data(cr, uid, ids, data_date)
                dias_entre_datas = data_date - ultima_data
                if ultimo_mapas_diario_id != 0:
                    if dias_entre_datas != contador_feriados:
                        data_imprimir = data_imprimir + timedelta(days=1)
                        raise osv.except_osv(_(u'Aviso'), _(u'Imprima primeiro a folha de '
                                                            u''+unicode(data_imprimir)+u'.'))
            # Cria registo relativo a data
            data_test = date(data_date.year, 1, 1)
            numero = 0
            while data_test < data_date:
                if data_test.weekday() >= 5 or \
                        len(db_sncp_comum_feriados.search(cr, uid, [('data', '=', unicode(data_test))])) != 0:
                    pass
                else:
                    numero += 1
                data_test = data_test+timedelta(days=1)
            values_mapas_diario = {
                'name': data,
                'ano': data_date.year,
                'numero': numero,
                'folha_linhas': 0,
                'folha_pagina': 0,
                'fechado': False,
            }
            mapas_diario_id = db_sncp_tesouraria_mapas_diario.create(cr, uid, values_mapas_diario)
        # Data de registo já existe
        else:
            mapas_diario_id = mapas_diario_id[0]
            values_mapas_diario = {
                'folha_linhas': 0,
                'folha_pagina': 0,
                'fechado': False,
            }
            db_sncp_tesouraria_mapas_diario.write(cr, uid, mapas_diario_id, values_mapas_diario)

            # Eliminar as linhas
            cr.execute("""DELETE FROM sncp_tesouraria_mapas_diario_linhas
                WHERE mapa_id =%d""" % mapas_diario_id)
            cr.execute("""DELETE FROM sncp_tesouraria_mapas_diario_resumo
                WHERE mapa_id =%d""" % mapas_diario_id)

        # Bloco de Processamento
        obj = db_sncp_tesouraria_mapas_diario.browse(cr, uid, mapas_diario_id)
        if obj.fechado:
            dados_carregados = True
        else:
            self.processa_resumos(cr, uid, ids, mapas_diario_id, data_date)
            self.processa_movimentos(cr, uid, ids, data_date)

        return dados_carregados

    _columns = {
        'name': fields.date(u'Data'),
        'imprimir_fc': fields.boolean(u'Imprimir Folha de Caixa'),
        'imprimir_rd': fields.boolean(u'Imprimir Resumo Diário'),
        'encerrar_fc': fields.boolean(u'Encerrar Folha de Caixa'),
        'encerrar_apenas': fields.boolean(u'Não listar, encerrar apenas'),
        'state': fields.selection([('new', u'Novo'), ('created', u'Ja existe'), ('closed', u'Fechado'), ]),
    }

    _defaults = {
        'name': unicode(date.today()),
        'state': 'new', }

sncp_tesouraria_folha_caixa()