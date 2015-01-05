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

import re
import decimal
from decimal import *
from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _


# _______________________________________________ CONFIGURAÇÃO DE RESUMO __________________
class sncp_orcamento_resumo_config(osv.Model):
    _name = 'sncp.orcamento.resumo.config'
    _description = u'Configuração do Resumo'

    def cons_mont_pal_ss(self, dit, x):

        palavra = x
        pos = 0
        montante_palavra = ''
        xx = palavra.find('+')
        yy = palavra.find('-')

        if xx == -1:
            if yy == -1:
                return unicode(dit[palavra])
            else:
                pos = yy
        elif yy == -1:
            if xx == -1:
                return unicode(dit[palavra])
            else:
                pos = xx

        elif xx > yy:
            pos = yy
        elif yy > xx:
            pos = xx

        pos_inicial = 0
        while pos != -1:
            pal_aux = palavra[pos_inicial:pos]
            pos_inicial = pos + 1
            montante_palavra += unicode(dit[pal_aux])
            montante_palavra += palavra[pos]
            xx = palavra.find('+', pos_inicial)
            yy = palavra.find('-', pos_inicial)
            if xx == -1:
                if yy == -1:
                    pos = -1
                else:
                    pos = yy
            elif yy == -1:
                if xx == -1:
                    pos = -1
                else:
                    pos = xx

            elif xx > yy:
                pos = yy
            elif yy > xx:
                pos = xx

        if pos_inicial != len(x):
            pal_aux = palavra[pos_inicial:]
            montante_palavra += unicode(dit[pal_aux])

        return montante_palavra

    def da_contas(self, x):
        palavra = x
        pos = 0
        montante_palavra = ''
        xx = palavra.find('+')
        yy = palavra.find('-')

        if xx == -1:
            if yy == -1:
                return palavra
            else:
                pos = yy
        elif yy == -1:
            if xx == -1:
                return palavra
            else:
                pos = xx

        elif xx > yy:
            pos = yy
        elif yy > xx:
            pos = xx

        pos_inicial = 0
        while pos != -1:
            pal_aux = palavra[pos_inicial:pos]
            pos_inicial = pos + 1
            montante_palavra += pal_aux
            montante_palavra += ' '
            xx = palavra.find('+', pos_inicial)
            yy = palavra.find('-', pos_inicial)
            if xx == -1:
                if yy == -1:
                    pos = -1
                else:
                    pos = yy
            elif yy == -1:
                if xx == -1:
                    pos = -1
                else:
                    pos = xx

            elif xx > yy:
                pos = yy
            elif yy > xx:
                pos = xx

        if pos_inicial != len(x):
            pal_aux = palavra[pos_inicial:]
            montante_palavra += pal_aux

        return montante_palavra

    def prepara_listagem(self, cr, uid, ids, ano, context=None):

        cr.execute("""
        SELECT id
        FROM sncp_orcamento
        WHERE ano=%d AND titulo='rece' AND tipo_orc='orc'
        """ % ano)

        orc_receita_id = cr.fetchone()

        if orc_receita_id is not None:
            orc_receita_id = orc_receita_id[0]

        cr.execute("""
        SELECT id
        FROM sncp_orcamento
        WHERE ano=%d AND titulo='desp' AND tipo_orc='orc'
        """ % ano)

        orc_despesa_id = cr.fetchone()

        if orc_despesa_id is not None:
            orc_despesa_id = orc_despesa_id[0]

        res_conf_ids = self.search(cr, uid, [])
        mont_linhas_receita = {}
        mont_linhas_despesa = {}

        mont_final_linhas_receita = {}
        mont_final_linhas_despesa = {}

        # OBTENÇÃO DE CÓDIGOS DAS CONTAS
        for res_conf in self.browse(cr, uid, res_conf_ids):
            if res_conf.coluna == 'rec':
                mont_final_linhas_receita[res_conf.id] = 0.0
            else:
                mont_final_linhas_despesa[res_conf.id] = 0.0
            valor = res_conf.valor
            if valor:
                str_codigos = self.da_contas(valor)
                lista_codigos = str_codigos.split(" ")
                for elem in lista_codigos:
                    if res_conf.coluna == 'rec':
                        if elem not in mont_linhas_receita.keys():
                            mont_linhas_receita[elem] = 0.00
                    elif res_conf.coluna == 'dsp':
                        if elem not in mont_linhas_despesa.keys():
                            mont_linhas_despesa[elem] = 0.00

        # CÁLCULO DOS MONTANTES POR CÓDIGO
        for chave in mont_linhas_receita.keys():
            if orc_receita_id is not None:
                cr.execute("""
                SELECT ROUND(reforco,2)
                FROM sncp_orcamento_linha AS OL
                LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                WHERE AAA.code='%s' AND OL.orcamento_id=%d
                """ % (chave, orc_receita_id))

                montante = cr.fetchone()

                if montante is None:
                    cr.execute("""
                    SELECT ROUND(SUM(reforco),2)
                    FROM sncp_orcamento_linha AS OL
                    LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                    WHERE AAA.code LIKE '%s' AND OL.orcamento_id=%d
                    """ % (chave + '%', orc_receita_id))

                    montante_filhos = cr.fetchone()

                    if montante_filhos[0] is None:
                        pass
                    else:
                        mont_linhas_receita[chave] = montante_filhos[0]

                else:
                    mont_linhas_receita[chave] = montante[0]

        # CÁLCULO DOS MONTANTES POR CÓDIGO
        for chave in mont_linhas_despesa.keys():
            if orc_despesa_id is not None:
                cr.execute("""
                SELECT ROUND(SUM(reforco),2)
                FROM sncp_orcamento_linha AS OL
                LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                WHERE AAA.code='%s' AND OL.orcamento_id=%d
                """ % (chave, orc_despesa_id))

                montante = cr.fetchone()

                if montante[0] is None:
                    cr.execute("""
                    SELECT ROUND(SUM(reforco),2)
                    FROM sncp_orcamento_linha AS OL
                    LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
                    WHERE AAA.code LIKE '%s' AND OL.orcamento_id=%d
                    """ % (chave + '%', orc_despesa_id))

                    montante_filhos = cr.fetchone()

                    if montante_filhos[0] is None:
                        pass
                    else:
                        mont_linhas_despesa[chave] = montante_filhos[0]
                else:
                    mont_linhas_despesa[chave] = montante[0]

        res_conf_ids = self.search(cr, uid, [])

        for res_conf in self.browse(cr, uid, res_conf_ids):
            valor = res_conf.valor
            if valor:
                if res_conf.coluna == 'rec':
                    string_mont_final_rec = self.cons_mont_pal_ss(mont_linhas_receita, valor)
                    mont_final_linhas_receita[res_conf.id] = eval(string_mont_final_rec)
                elif res_conf.coluna == 'dsp':
                    string_mont_final_dsp = self.cons_mont_pal_ss(mont_linhas_despesa, valor)
                    mont_final_linhas_despesa[res_conf.id] = eval(string_mont_final_dsp)

        total_receitas = 0.0
        total_despesas = 0.0
        # CALCULO DO TOTAL DAS RECEITAS
        for res_conf_id in mont_final_linhas_receita.keys():
            obj = self.browse(cr, uid, res_conf_id)
            if obj.depend is False and obj.coluna == 'rec':
                total_receitas += mont_final_linhas_receita[res_conf_id]
                aux = decimal.Decimal(unicode(total_receitas))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                total_receitas = float(aux)

        # CALCULO DO TOTAL DAS DESPESAS
        for res_conf_id in mont_final_linhas_despesa.keys():
            obj = self.browse(cr, uid, res_conf_id)
            if obj.depend is False and obj.coluna == 'dsp':
                total_despesas += mont_final_linhas_despesa[res_conf_id]
                aux = decimal.Decimal(unicode(total_despesas))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                total_despesas = float(aux)

        # CALCULAR A PERCENTAGEM BASEADO NOS MONTANTES ATUALIZADOS DA RECEITA
        if total_receitas != 0.0:
            for conf_id in mont_final_linhas_receita.keys():
                aux = decimal.Decimal(unicode((mont_final_linhas_receita[conf_id] / total_receitas) * 100))
                aux = aux.quantize(Decimal('0.1'), ROUND_HALF_UP)
                perc_rec = float(aux)
                self.write(cr, uid, [conf_id], {'montante': mont_final_linhas_receita[conf_id],
                                                'perc': perc_rec})

        # CALCULAR A PERCENTAGEM BASEADO NOS MONTANTES ATUALIZADOS DA DESPESA
        if total_despesas != 0.0:
            for conf_id in mont_final_linhas_despesa.keys():
                aux = decimal.Decimal(unicode((mont_final_linhas_despesa[conf_id] / total_despesas) * 100))
                aux = aux.quantize(Decimal('0.1'), ROUND_HALF_UP)
                perc_des = float(aux)
                self.write(cr, uid, [conf_id], {'montante': mont_final_linhas_despesa[conf_id],
                                                'perc': perc_des})

        datas = {
            'ids': ids,
            'model': 'sncp.orcamento.resumo.config',
        }

        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.orcamento.resumo.config.report',
            'datas': datas,
        }

    _columns = {
        'coluna': fields.selection([('rec', u'Receitas'),
                                    ('dsp', u'Despesas')], u'Coluna'),
        'ordem': fields.integer(u'Ordem'),
        'name': fields.char(u'Descrição', size=64),
        'align': fields.selection([('left', u'Esquerda'),
                                   ('center', u'Centro'),
                                   ('right', u'Direita')], u'Alinhamento'),
        'bold': fields.boolean(u'Negrito'),
        'depend': fields.boolean(u'Dependente'),
        'valor': fields.char(u'Valor', size=64),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'perc': fields.float(u'Percentagem', digits=(3, 1)),
    }

    def _valor_valido(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        valor = obj.valor
        if valor:
            valor = valor.replace(" ", "")
            valor = valor.replace("\t", "")
            valor = valor.replace("\r", "")
            valor = valor.replace("\n", "")

            re_name = re.compile('^[a-zA-Z0-9]+([+-][a-zA-Z0-9]+)*$')

            if re_name.match(valor):

                str_codigos = self.da_contas(valor)
                lista_codigos = str_codigos.split(" ")

                for codigo in lista_codigos:
                    cr.execute("""SELECT id FROM account_analytic_account WHERE code='%s' AND tipo_dim='ce'""" % codigo)

                    aaa_eco = cr.fetchone()

                    if aaa_eco is None:
                        raise osv.except_osv(_(u'Aviso'), _(u'Não existe conta analítica de tipo económica'
                                                            u' com o código ' + unicode(codigo) + u'.'))
        return True

    _defaults = {
        'coluna': 'rec',
        'align': 'left',
    }

    _constraints = [
        (_valor_valido, u'', ['valor']),
    ]

    _sql_constraints = [
        ('orcamento_resumo_config_unique', 'unique(coluna,ordem)', u'Coluna+Ordem já existe.'),
    ]
sncp_orcamento_resumo_config()


# ________________________________________________________IMPRESSÃO________________________
class sncp_orcamento_imprimir_resumo_config(osv.Model):
    _name = 'sncp.orcamento.imprimir.resumo.config'
    _description = u'Imprimir Configuração do Resumo'

    def _get_lista(self, cr, uid, context=None):

        cr.execute("""
        SELECT ano
        FROM sncp_orcamento
        WHERE tipo_orc='orc' and titulo='desp'
        """)

        anos_despesa = cr.fetchall()
        if len(anos_despesa) == 0:
            lista_desp = []
        else:
            lista_desp = [ano[0] for ano in anos_despesa]

        cr.execute("""
        SELECT ano
        FROM sncp_orcamento
        WHERE tipo_orc='orc' and titulo='rece'
        """)

        anos_receita = cr.fetchall()
        if len(anos_receita) == 0:
            lista_rec = []
        else:
            lista_rec = [ano[0] for ano in anos_receita]

        lista_conjunto = list(set(lista_desp + lista_rec))
        lista = [(unicode(ano), unicode(ano)) for ano in lista_conjunto]
        return lista

    def imprimir_report(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        ano = int(obj.name)
        cr.execute("""
        DELETE FROM sncp_orcamento_imprimir_resumo_config WHERE id<%d
        """ % obj.id)

        cr.execute("""
        UPDATE sncp_orcamento_resumo_config SET montante=0.0,perc=0.0
        """)

        return self.pool.get('sncp.orcamento.resumo.config').prepara_listagem(cr, uid, [], ano)

    _columns = {
        'name': fields.selection(_get_lista, u'Ano'),
    }


sncp_orcamento_imprimir_resumo_config()


class sncp_orcamento_imprimir_ano_receita(osv.Model):
    _name = 'sncp.orcamento.imprimir.ano.receita'
    _description = u'Imprimir ano de receita'

    def _get_lista(self, cr, uid, context=None):
        cr.execute("""
        SELECT ano
        FROM sncp_orcamento
        WHERE tipo_orc='orc' and titulo='rece'
        """)

        anos = cr.fetchall()
        if len(anos) == 0:
            lista = []
        else:
            lista = [(unicode(ano[0]), unicode(ano[0])) for ano in anos]

        return lista

    def imprimir_report(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        ano = int(obj.name)
        cr.execute("""
        SELECT id
        FROM sncp_orcamento
        WHERE ano=%d AND tipo_orc='orc' and titulo='rece'
        """ % ano)

        orc_id = cr.fetchone()

        cr.execute("""
        DELETE FROM sncp_orcamento_imprimir_ano_receita WHERE id<%d
        """ % obj.id)

        if orc_id is None:
            return True
        else:
            orc_id = orc_id[0]
            return self.pool.get('sncp.orcamento').imprimir_report_receita(cr, uid, [orc_id], context=None)

    _columns = {
        'name': fields.selection(_get_lista, u'Ano'),
    }


sncp_orcamento_imprimir_ano_receita()


class sncp_orcamento_imprimir_ano_despesa(osv.Model):
    _name = 'sncp.orcamento.imprimir.ano.despesa'
    _description = u'Imprimir ano Despesa'

    def _get_lista(self, cr, uid, context=None):

        cr.execute("""SELECT ano FROM sncp_orcamento WHERE tipo_orc='orc' and titulo='desp'""")

        anos = cr.fetchall()
        if len(anos) == 0:
            lista = []
        else:
            lista = [(unicode(ano[0]), unicode(ano[0])) for ano in anos]

        return lista

    def imprimir_report(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        ano = int(obj.name)
        cr.execute("""
        SELECT id
        FROM sncp_orcamento
        WHERE ano=%d AND tipo_orc='orc' and titulo='desp'
        """ % ano)

        orc_id = cr.fetchone()

        cr.execute("""
        DELETE FROM sncp_orcamento_imprimir_ano_despesa WHERE id<%d
        """ % obj.id)

        if orc_id is None:
            return True
        else:
            orc_id = orc_id[0]
            return self.pool.get('sncp.orcamento').imprimir_report_despesa(cr, uid, [orc_id], context=None)

    _columns = {
        'name': fields.selection(_get_lista, u'Ano'),
    }


sncp_orcamento_imprimir_ano_despesa()


# _______________________________________________________ORÇAMENTO IMPRESSÃO RECEITA_____________________________
class sncp_orcamento_imprimir_receita(osv.Model):
    _name = 'sncp.orcamento.imprimir.receita'
    _description = u'Imprimir orçamento receita'

    _columns = {
        'orcamento_id': fields.many2one('sncp.orcamento', u'Orçamento'),
        'name': fields.char(u'Descrição'),
        'codigo': fields.char(u'Código económica'),
        'linha': fields.char(u'Secção'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
    }

    _sql_constraints = [
        ('orcamento_imprimir_receita_unique', 'unique (codigo)', u'Código já existe.'),
    ]


sncp_orcamento_imprimir_receita()


# _______________________________________________________ORÇAMENTO IMPRESSÃO DESPESA_____________________________
class sncp_orcamento_imprimir_despesa(osv.Model):
    _name = 'sncp.orcamento.imprimir.despesa'
    _description = u'Imprimir orçamento despesa'

    _columns = {
        'orcamento_id': fields.many2one('sncp.orcamento', u'Orçamento'),
        'name': fields.char(u'Descrição'),
        'codigo_eco': fields.char(u'Económica'),
        'codigo_org': fields.char(u'Orgânica'),
        'linha': fields.char(u'Secção'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
    }

    _sql_constraints = [
        ('orcamento_imprimir_despesa_unique', 'unique(codigo_eco,codigo_org)', u'Orgânica+Económica já existe.'),
    ]


sncp_orcamento_imprimir_despesa()


# _______________________________________________________MODIFICAÇÃO IMPRESSÃO ANO RECEITA____________________________
class sncp_modificacao_imprimir_ano_receita(osv.Model):
    _name = 'sncp.modificacao.imprimir.ano.receita'
    _description = u'Imprimir Ano Receita modificação'

    def imprimir_report_mod_receita(self, cr, uid, vals, context=None):
        datahora = ""
        db_sncp_orcamento = self.pool.get('sncp.orcamento')
        cr.execute("""DELETE FROM sncp_modificacao_imprimir_receita """)
        cr.execute("""SELECT insere_modificacao_imprimir_receita('%s',%d,%d);"""
                   % (vals['tipo'], vals['ano'], vals['id']))

        if vals['tipo'] == 'rev':
            orc = db_sncp_orcamento.browse(cr, uid, vals['mod_id'])
            if orc.contab is True:
                cr.execute("""
                SELECT MAX(datahora)
                FROM sncp_orcamento_historico
                WHERE doc_contab_id=%d
                """ % orc.doc_contab_id.id)
                datahora = cr.fetchone()[0]
            else:
                datahora = unicode(datetime.now())
                if datahora.find('.') != -1:
                    datahora = datahora[:datahora.find('.')]

        elif vals['tipo'] == 'alt':
            cr.execute("""SELECT id
                           FROM sncp_orcamento
                           WHERE ano=%d AND tipo_orc='%s' and alt_principal=%d AND contab=FALSE
                       """ % (vals['ano'], vals['tipo'], vals['id']))
            result = cr.fetchall()
            if len(result) != 0:
                datahora = unicode(datetime.now())
                if datahora.find('.') != -1:
                    datahora = datahora[:datahora.find('.')]
            else:
                cr.execute("""
                SELECT MAX(datahora)
                FROM sncp_orcamento_historico
                WHERE doc_contab_id IN (SELECT doc_contab_id FROM sncp_orcamento
                WHERE id IN (SELECT id FROM sncp_orcamento WHERE ano=%d AND tipo_orc='%s' and alt_principal=%d))
                """ % (vals['ano'], vals['tipo'], vals['id']))
                datahora = cr.fetchone()[0]

        cr.execute("""SELECT obtem_previsao_atual('%s',%d);""" % (datahora, vals['ano']))

        cr.execute("""SELECT mod_get_parents(AAA.code)
                      FROM sncp_modificacao_imprimir_receita AS MIR
                      LEFT JOIN account_analytic_account AS AAA ON AAA.id=MIR.economica_id
                      WHERE MIR.economica_id IS NOT NULL
                      """)

        cr.execute("""SELECT atualiza_print_modificacao();""")
        cr.execute("""UPDATE sncp_modificacao_imprimir_receita SET linha='artigo' WHERE linha='';""")
        cr.execute("""SELECT insere_titulos_mod(false);""")

        datas = {'ids': [], 'model': 'sncp.modificacao.imprimir.receita', }

        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.modificacao.receita.report',
            'datas': datas,
        }

    def _get_lista(self, cr, uid, context=None):
        cr.execute("""
        SELECT ano
        FROM sncp_orcamento
        WHERE tipo_orc IN ('rev','alt') and titulo='rece'
        """)

        anos = cr.fetchall()
        if len(anos) == 0:
            lista = []
        else:
            lista = [(unicode(ano[0]), unicode(ano[0])) for ano in anos]

        lista = list(set(lista))
        return lista

    def imprimir_report(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        vals = {}
        cr.execute("""DELETE FROM sncp_modificacao_imprimir_ano_receita WHERE id<%d""" % obj.id)
        if obj.tipo_mod == 'rev':

            cr.execute("""
            SELECT id
            FROM sncp_orcamento
            WHERE ano=%d AND tipo_orc='%s' AND numero=%d and titulo='rece'
            """ % (int(obj.name), obj.tipo_mod, obj.numero))
            result = cr.fetchone()
            if result is not None:
                vals['tipo'] = obj.tipo_mod
                vals['ano'] = int(obj.name)
                vals['id'] = obj.numero
                vals['mod_id'] = result[0]
                return self.imprimir_report_mod_receita(cr, uid, vals)

        elif obj.tipo_mod == 'alt':
            cr.execute("""
            SELECT id
            FROM sncp_orcamento
            WHERE ano=%d AND tipo_orc='%s' AND alt_principal=%d and titulo='rece'
            """ % (int(obj.name), obj.tipo_mod, obj.numero))
            result = cr.fetchall()
            if len(result) != 0:
                vals['tipo'] = obj.tipo_mod
                vals['ano'] = int(obj.name)
                vals['id'] = obj.numero
                return self.imprimir_report_mod_receita(cr, uid, vals)

        return True

    _columns = {
        'name': fields.selection(_get_lista, u'Ano'),
        'numero': fields.integer(u'Número da Alteração/Revisão'),
        'tipo_mod': fields.selection([('rev', u'Revisão'),
                                      ('alt', u'Alteração')], u'Modificação'),
    }


sncp_modificacao_imprimir_ano_receita()


# _______________________________________________________MODIFICAÇÂO IMPRESSÂO ANO DESPESA____________________________
class sncp_modificacao_imprimir_ano_despesa(osv.Model):
    _name = 'sncp.modificacao.imprimir.ano.despesa'
    _description = u'Imprimir Ano Despesa Modificação'

    def imprimir_report_mod_despesa(self, cr, uid, vals, context=None):
        datahora = ""
        db_sncp_orcamento = self.pool.get('sncp.orcamento')
        cr.execute("""DELETE FROM sncp_modificacao_imprimir_despesa """)
        cr.execute("""SELECT insere_modificacao_imprimir_despesa('%s',%d,%d);"""
                   % (vals['tipo'], vals['ano'], vals['id']))

        if vals['tipo'] == 'rev':
            orc = db_sncp_orcamento.browse(cr, uid, vals['mod_id'])
            if orc.contab is True:
                cr.execute("""
                SELECT MAX(datahora)
                FROM sncp_orcamento_historico
                WHERE doc_contab_id=%d
                """ % orc.doc_contab_id.id)
                datahora = cr.fetchone()[0]
            else:
                datahora = unicode(datetime.now())
                if datahora.find('.') != -1:
                    datahora = datahora[:datahora.find('.')]

        elif vals['tipo'] == 'alt':
            cr.execute("""SELECT id
                           FROM sncp_orcamento
                           WHERE ano=%d AND tipo_orc='%s' and alt_principal=%d AND contab=FALSE
                       """ % (vals['ano'], vals['tipo'], vals['id']))
            result = cr.fetchall()
            if len(result) != 0:
                datahora = unicode(datetime.now())
                if datahora.find('.') != -1:
                    datahora = datahora[:datahora.find('.')]
            else:
                cr.execute("""
                SELECT MAX(datahora)
                FROM sncp_orcamento_historico
                WHERE doc_contab_id IN (SELECT doc_contab_id FROM sncp_orcamento
                WHERE id IN (SELECT id FROM sncp_orcamento WHERE ano=%d AND tipo_orc='%s' and alt_principal=%d))
                """ % (vals['ano'], vals['tipo'], vals['id']))
                datahora = cr.fetchone()[0]

        cr.execute("""SELECT obtem_mod_desp_previsao_atual('%s',%d);""" % (datahora, vals['ano']))

        cr.execute("""SELECT get_mod_desp_parents_economica(AAA2.code,AAA.code)
                      FROM sncp_modificacao_imprimir_despesa AS MID
                      LEFT JOIN account_analytic_account AS AAA ON AAA.id=MID.economica_id
                      LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=MID.organica_id
                      WHERE MID.economica_id IS NOT NULL
                      """)

        cr.execute("""
        SELECT get_mod_desp_parents_organica(AAA2.code)
        FROM sncp_modificacao_imprimir_despesa AS MID
        LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=MID.organica_id
        WHERE MID.organica_id IS NOT NULL
        """)

        cr.execute("""        SELECT atualiza_print_modificacao_despesa();        """)
        cr.execute("""        SELECT mod_desp_check_cab_organica();        """)
        cr.execute("""UPDATE sncp_modificacao_imprimir_despesa SET linha='artigo' WHERE linha='';""")

        datas = {'ids': [], 'model': 'sncp.modificacao.imprimir.despesa', }

        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.modificacao.despesa.report',
            'datas': datas,
        }

    def _get_lista(self, cr, uid, context=None):
        cr.execute("""
        SELECT ano
        FROM sncp_orcamento
        WHERE tipo_orc IN ('rev','alt') and titulo='desp'
        """)

        anos = cr.fetchall()
        if len(anos) == 0:
            lista = []
        else:
            lista = [(unicode(ano[0]), unicode(ano[0])) for ano in anos]

        lista = list(set(lista))
        return lista

    def imprimir_report(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        vals = {}
        cr.execute("""DELETE FROM sncp_modificacao_imprimir_ano_despesa WHERE id<%d""" % obj.id)
        if obj.tipo_mod == 'rev':

            cr.execute("""
            SELECT id
            FROM sncp_orcamento
            WHERE ano=%d AND tipo_orc='%s' AND numero=%d and titulo='desp'
            """ % (int(obj.name), obj.tipo_mod, obj.numero))
            result = cr.fetchone()
            if result is not None:
                vals['tipo'] = obj.tipo_mod
                vals['ano'] = int(obj.name)
                vals['id'] = obj.numero
                vals['mod_id'] = result[0]
                return self.imprimir_report_mod_despesa(cr, uid, vals)

        elif obj.tipo_mod == 'alt':
            cr.execute("""
            SELECT id
            FROM sncp_orcamento
            WHERE ano=%d AND tipo_orc='%s' AND alt_principal=%d and titulo='desp'
            """ % (int(obj.name), obj.tipo_mod, obj.numero))
            result = cr.fetchall()
            if len(result) != 0:
                vals['tipo'] = obj.tipo_mod
                vals['ano'] = int(obj.name)
                vals['id'] = obj.numero
                return self.imprimir_report_mod_despesa(cr, uid, vals)

        return True

    _columns = {
        'name': fields.selection(_get_lista, u'Ano'),
        'numero': fields.integer(u'Número da Alteração/Revisão'),
        'tipo_mod': fields.selection([('rev', u'Revisão'),
                                      ('alt', u'Alteração')], u'Modificação'),
    }


sncp_modificacao_imprimir_ano_despesa()


# _______________________________________________________MODIFICAÇÃO IMPRESSÃO RECEITA____________________________
class sncp_modificacao_imprimir_receita(osv.Model):
    _name = 'sncp.modificacao.imprimir.receita'
    _description = u'Modificação Imprimir Receita'

    _columns = {
        'economica_id': fields.integer(u'economica_id'),
        'name': fields.char(u'Descrição'),
        'codigo': fields.char(u'Código económica'),
        'linha': fields.char(u'Secção'),
        'reforco': fields.float(u'Reforços e Inscrições', digits=(12, 2)),
        'abate': fields.float(u'Abates e Anulações', digits=(12, 2)),
        'previsao_atual': fields.float(u'Previsão Corrigida', digits=(12, 2)),
        'previsao_corrigida': fields.float(u'Previsão Corrigida', digits=(12, 2))
    }

    _sql_constraints = [
        ('modificacao_imprimir_receita_unique', 'unique (codigo)', u'Código já existe.'),
    ]


sncp_modificacao_imprimir_receita()


# _______________________________________________________MODIFICAÇÂO IMPRESSÂO DESPESA________________________________
class sncp_modificacao_imprimir_despesa(osv.Model):
    _name = 'sncp.modificacao.imprimir.despesa'
    _description = u'Imprimir Modificação Despesa'

    _columns = {
        'economica_id': fields.integer(u'economica_id'),
        'organica_id': fields.integer(u'organica_id'),
        'name': fields.char(u'Descrição'),
        'codigo_eco': fields.char(u'Código Económica'),
        'codigo_org': fields.char(u'Código Orgânica'),
        'linha': fields.char(u'Secção'),
        'reforco': fields.float(u'Reforços e Inscrições', digits=(12, 2)),
        'abate': fields.float(u'Abates e Anulações', digits=(12, 2)),
        'previsao_atual': fields.float(u'Previsão Corrigida', digits=(12, 2)),
        'previsao_corrigida': fields.float(u'Previsão Corrigida', digits=(12, 2))
    }

    _sql_constraints = [
        ('modificacao_imprimir_despesa_unique', 'unique(codigo_eco,codigo_org)', u'Orgânica+Económica já existe.'),
    ]
sncp_modificacao_imprimir_despesa()