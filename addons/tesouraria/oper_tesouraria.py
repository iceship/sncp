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

# ________________________________________________________________CONTA CORRENTE________________________


class sncp_tesouraria_conta_corrente(osv.Model):
    _name = 'sncp.tesouraria.conta.corrente'
    _description = u"Conta Corrente"

    def lista_fornecedor(self, cr, uid, context=None):
        cr.execute("""
        SELECT id,name
        FROM res_partner
        WHERE id IN (
        SELECT partner_id
        FROM sncp_despesa_descontos_retencoes)
        """)
        list_tuple = cr.fetchall()

        lista = []
        for res in list_tuple:
            lista.append((unicode(res[0]), unicode(res[1])))
        lista = list(set(lista))  # Elimina duplicados
        return lista

    def on_change_partner(self, cr, uid, ids, partner_ref):
        cr.execute("""DELETE FROM sncp_tesouraria_conta_corrente
                          WHERE  create_date::DATE < '%s' """ % unicode(date.today()))
        cr.execute("""DELETE FROM sncp_tesouraria_conta_corrente_linhas
                          WHERE  create_date::DATE < '%s' """ % unicode(date.today()))
        db_res_partner = self.pool.get('res.partner')
        obj_parceiro = db_res_partner.browse(cr, uid, int(partner_ref))
        test_partner_id(self, cr, uid, obj_parceiro.id)
        conta_id = None
        if obj_parceiro.supplier is True:
            conta_id = obj_parceiro.property_account_payable.id

        return {
            'value': {
                'conta_id': conta_id,
                'partner_id': int(partner_ref),
            }
        }

    def criar_linhas(self, cr, uid, ids, context):
        db_sncp_tesouraria_conta_corrente_linhas = self.pool.get('sncp.tesouraria.conta.corrente.linhas')
        obj = self.browse(cr, uid, ids[0])

        # Caso é uma atualização
        cr.execute("""DELETE FROM sncp_tesouraria_conta_corrente_linhas
                      WHERE conta_corr_id = %d""" % ids[0])

        # Caso não começe a um de janeiro
        data_ini_date = datetime.strptime(obj.data_ini, "%Y-%m-%d").date()
        saldo = 0.00
        if data_ini_date.month == 1:
            if data_ini_date.day == 1:
                pass
            else:
                cr.execute("""SELECT SUM(COALESCE(debit,0.0) - COALESCE(credit,0.0)) FROM account_move_line
                    WHERE partner_id = %d AND account_id = %d AND date < '%s' AND date >= '%s'
                """ % (int(obj.partner_ref), obj.conta_id.id, obj.data_ini, unicode(date(date.today().year, 1, 1))))
                result = cr.fetchone()
                if result[0] is not None:
                    saldo = result[0]
                db_sncp_tesouraria_conta_corrente_linhas.create(cr, uid, {'conta_corr_id': ids[0],
                                                                          'name': 'Saldo anterior',
                                                                          'saldo': saldo})
        else:
            cr.execute("""SELECT SUM(COALESCE(debit,0.0) - COALESCE(credit,0.0)) FROM account_move_line
                WHERE partner_id = %d AND account_id = %d AND date < '%s' AND date >= '%s'
            """ % (int(obj.partner_ref), obj.conta_id.id, obj.data_ini, unicode(date(date.today().year, 1, 1))))
            result = cr.fetchone()
            if result[0] is not None:
                saldo = result[0]
            db_sncp_tesouraria_conta_corrente_linhas.create(cr, uid, {'conta_corr_id': ids[0],
                                                                      'name': 'Saldo anterior',
                                                                      'saldo': saldo})
        # Bloco de processamento
        cr.execute("""SELECT ML.date,ML.name,ML.debit,ML.credit,M.name
                      FROM account_move_line AS ML, account_move AS M
            WHERE ML.partner_id = %d AND ML.account_id = %d AND ML.date <= '%s' AND ML.date >= '%s'
                  AND ML.move_id = M.id
            ORDER BY date """ % (int(obj.partner_ref), obj.conta_id.id, obj.data_fim, obj.data_ini))
        result = cr.fetchall()
        for res in result:
            debito = 0.00
            credito = 0.00
            name = res[4] + ' - ' + res[1]
            if res[2] is not None:
                debito = res[2]
            if res[3] is not None:
                credito = res[3]
            saldo += debito - credito
            aux = decimal.Decimal(unicode(saldo))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            saldo = float(aux)
            db_sncp_tesouraria_conta_corrente_linhas.create(cr, uid, {
                'conta_corr_id': ids[0],
                'data': res[0],                 'name': name,
                'debito': debito,               'credito': credito,
                'saldo': saldo})
        self.write(cr, uid, ids, {'name': 1})
        return True

    def imprimir(self, cr, uid, ids, context):
        datas = {'ids': ids,
                 'model': 'sncp.tesouraria.conta.corrente', }
        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.tesouraria.conta.corrente.report',
            'datas': datas,
        }

    _columns = {
        'name': fields.boolean(u'Criar Conta Corrente de Operações de Tesouraria'),
        'partner_ref': fields.selection(lista_fornecedor, u'Parceiro de Negócios beneficiário'),
        'conta_id': fields.many2one('account.account', u'Conta contábil', domain=[('type', 'not in', ['view'])]),
        'data_ini': fields.date(u'Data de início'),
        'data_fim': fields.date(u'Data do fim'),
        'linhas_ids': fields.one2many('sncp.tesouraria.conta.corrente.linhas', 'conta_corr_id', u''),
        'estado': fields.integer(u'Controlo'),
        # 0 -- So preencher campos
        # 1 -- Aparece o resto/Pronta para eliminar

    }

    _defaults = {
        'estado': 0,
        'data_ini': unicode(date(date.today().year, 1, 1)),
        'data_fim': unicode(date.today()), }

    def _mesmo_ano(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        ano_ini = datetime.strptime(obj.data_ini, "%Y-%m-%d").year
        ano_fim = datetime.strptime(obj.data_fim, "%Y-%m-%d").year
        if ano_fim != ano_ini:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'As datas de início e de fim têm que ser do mesmo ano.'))
        return True

    _constraints = [
        (_mesmo_ano, u'', ['data_ini', 'data_fim'])
    ]

sncp_tesouraria_conta_corrente()
# ________________________________________________________________CONTA CORRENTE LINHAS__________________


class sncp_tesouraria_conta_corrente_linhas(osv.Model):
    _name = 'sncp.tesouraria.conta.corrente.linhas'
    _description = u"Linhas da Conta Corrente"

    _columns = {
        'conta_corr_id': fields.many2one('sncp.tesouraria.conta.corrente', u''),
        'data': fields.date(u'Data'),
        'name': fields.char(u'Descrição'),
        'debito': fields.float(u'Débito', digits=(12, 2)),
        'credito': fields.float(u'Crédito', digits=(12, 2)),
        'saldo': fields.float(u'Saldo', digits=(12, 2)),
    }

sncp_tesouraria_conta_corrente_linhas()
# ________________________________________________________________Ordem Pagamrnto OTS__________________


class sncp_tesouraria_ordem_pagamento_ot(osv.Model):
    _name = 'sncp.tesouraria.ordem.pagamento.ot'
    _description = u"Ordem de Pagamento OT"

    def calcula_valor(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        result = 0.0
        self.write(cr, uid, ids, {'estado': 2})
        cr.execute("""
           SELECT SUM(COALESCE(credit,0.0)-COALESCE(debit,0.0)),AML.account_id,AML.funcional_id,AML.organica_id,
           AML.economica_id
                       FROM account_move_line AS AML
                       WHERE AML.partner_id=%d AND
                       AML.date BETWEEN '%s' AND '%s' AND AML.account_id=%d
                  GROUP BY AML.account_id,AML.funcional_id,AML.organica_id,AML.economica_id
          """ % (int(obj.partner_ref), obj.data_ini, obj.data_fim, obj.conta_id.id))

        resultado = cr.fetchall()

        if len(resultado) != 0:
            montante_lista = [elem[0] for elem in resultado]

            result_total = sum(montante_lista)

            aux = decimal.Decimal(unicode(result_total))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            result_total = float(aux)

            result = result_total

        self.write(cr, uid, ids, {'resultado': result})
        return True

    def criar_ordem_pagamento_ot(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        db_sncp_despesa_pagamento_ordem = self.pool.get('sncp.despesa.pagamentos.ordem')
        db_sncp_despesa_pagamentos_ordem_linhas_imprimir =\
            self.pool.get('sncp.despesa.pagamentos.ordem.linhas.imprimir')
        montante_iliquido = 0.00
        db_sncp_comum_meios_pagamento = self.pool.get('sncp.comum.meios.pagamento')
        obj_meio = db_sncp_comum_meios_pagamento.browse(cr, uid, obj.meio_pag_id.id)

        cr.execute("""
               SELECT SUM(COALESCE(credit,0.0)-COALESCE(debit,0.0)),AML.account_id,AML.organica_id,AML.economica_id,
               AML.funcional_id
                           FROM account_move_line AS AML
                           WHERE AML.partner_id=%d AND
                           AML.date BETWEEN '%s' AND '%s' AND AML.account_id=%d
                      GROUP BY AML.account_id,AML.funcional_id,AML.organica_id,AML.economica_id
              """ % (int(obj.partner_ref), obj.data_ini, obj.data_fim, obj.conta_id.id))
        lista = cr.fetchall()

        if len(lista) == 0:
            self.unlink(cr, uid, ids)
            menu_obj = self.pool.get('ir.ui.menu')
            menu_ids = menu_obj.search(cr, uid, [('name', '=', 'Gerar Ordem de Pagamento OT')], context=context)
            return {'type': 'ir.actions.client', 'tag': 'reload', 'params': {'menu_id': menu_ids}}

        else:
            montante_lista = [elem[0] for elem in lista]

            result_total = sum(montante_lista)
            aux = decimal.Decimal(unicode(result_total))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            result_total = float(aux)

            if result_total <= 0.0:
                self.unlink(cr, uid, ids)
                menu_obj = self.pool.get('ir.ui.menu')
                menu_ids = menu_obj.search(cr, uid, [('name', '=', 'Gerar Ordem de Pagamento OT')],
                                           context=context)
                return {'type': 'ir.actions.client', 'tag': 'reload', 'params': {'menu_id': menu_ids}}

            values_ordem = {'partner_id': int(obj.partner_ref),
                            'tipo': 'opt',
                            'estado_linhas': 1,
                            'meio_pag_id': obj_meio.id,
                            'ref_meio': obj_meio.meio, }

            ordem_id = db_sncp_despesa_pagamento_ordem.create(cr, uid, values_ordem)

            fator = obj.resultado/result_total
            linha = 1
            for result in lista:
                if result[0] > 0.0:
                    aux = decimal.Decimal(unicode(result[0]*fator))
                    aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                    result_prop = float(aux)
                    values_linhas_imprimir = {
                        'opag_id': ordem_id,
                        'name': linha,
                        'conta_contabil_id': result[1],
                        'organica_id': result[2],
                        'economica_id': result[3],
                        'funcional_id': result[4],
                        'montante': result_prop, }
                    montante_iliquido += result_prop
                    db_sncp_despesa_pagamentos_ordem_linhas_imprimir.create(cr, uid, values_linhas_imprimir)

            aux = decimal.Decimal(unicode(montante_iliquido))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_iliquido = float(aux)

            db_sncp_despesa_pagamento_ordem.write(cr, uid, ordem_id, {'montante_iliq': montante_iliquido})
            self.unlink(cr, uid, ids)
            menu_obj = self.pool.get('ir.ui.menu')
            menu_ids = menu_obj.search(cr, uid, [('name', '=', 'Gerar Ordem de Pagamento OT')], context=context)
            return {'type': 'ir.actions.client', 'tag': 'reload', 'params': {'menu_id': menu_ids}}

    def lista_fornecedor(self, cr, uid, context=None):
        cr.execute("""
        SELECT id,name
        FROM res_partner
        WHERE id IN (
        SELECT partner_id
        FROM sncp_despesa_descontos_retencoes)
        """)
        list_tuple = cr.fetchall()

        lista = []
        for res in list_tuple:
            lista.append((unicode(res[0]), unicode(res[1])))
        lista = list(set(lista))
        return lista

    def on_change_partner(self, cr, uid, ids, partner_ref):
        if partner_ref is False:
            return {}
        db_res_partner = self.pool.get('res.partner')
        obj_parceiro = db_res_partner.browse(cr, uid, int(partner_ref))
        test_partner_id(self, cr, uid, obj_parceiro.id)
        conta_id = None
        if obj_parceiro.supplier is True:
            conta_id = obj_parceiro.property_account_payable.id

        return {'value': {'conta_id': conta_id,
                          'partner_id': partner_ref, }}

    def _get_meio_pagamento(self, cr, uid, context):
        db_sncp_comum_param = self.pool.get('sncp.comum.param')
        param_ids = db_sncp_comum_param.search(cr, uid, [('state', '=', 'draft')])
        if len(param_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                u'Preencha os parâmetros por defeito no menu:\n'
                                                u'Comum/Parâmetros.'))

        obj_param = db_sncp_comum_param.browse(cr, uid, param_ids[0])
        return obj_param.desp_mpag.id

    _columns = {
        'partner_ref': fields.selection(lista_fornecedor, u'Parceiro de Negócios beneficiário'),
        'conta_id': fields.many2one('account.account', u'Conta contábil', domain=[('type', 'not in', ['view'])]),
        'meio_pag_id': fields.many2one('sncp.comum.meios.pagamento', u'Meio de Pagamento',
                                       domain=[('tipo', 'in', ['pag']), ('meio', 'not in', ['dc'])]),
        'data_ini': fields.date(u'Data de início'),
        'data_fim': fields.date(u'Data do fim'),
        'resultado': fields.float(u'Resultado'),
        'estado': fields.integer(u'Controlo'),
        # 0 aparece o campo name
        # 1 aparece o resto dos campos com o parceiro limitado aos que aparecem nos descontos e retenções
    }

    _defaults = {
        'estado': 1,
        'data_ini': unicode(date(date.today().year, 1, 1)),
        'data_fim': unicode(date.today()),
        'meio_pag_id': lambda self, cr, uid, ctx: self._get_meio_pagamento(cr, uid, ctx),
    }

    def _mesmo_ano(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        data_ini = datetime.strptime(obj.data_ini, "%Y-%m-%d").date()
        data_fim = datetime.strptime(obj.data_fim, "%Y-%m-%d").date()
        if data_ini >= data_fim:
            raise osv.except_osv(_(u'Aviso'), _(u'A data inicial têm de ser inferior à data final.'))

        if data_ini.year != data_fim.year:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'As datas de início e de fim têm que ser do mesmo ano.'))
        return True

    _constraints = [
        (_mesmo_ano, u'', ['data_ini', 'data_fim'])
    ]

sncp_tesouraria_ordem_pagamento_ot()
# ________________________________________________________________CONTAS OP TES ________________________


class sncp_tesouraria_mapa_ots(osv.Model):
    _name = 'sncp.tesouraria.mapa.ots'
    _description = u"Mapas OTS"

    def select_ano(self, cr, uid, context):
        cr.execute("""DELETE FROM sncp_tesouraria_mapa_ots
                          WHERE  create_date::DATE < '%s' """ % unicode(date.today()))
        cr.execute("""DELETE FROM sncp_tesouraria_contas_ots
                          WHERE  create_date::DATE < '%s' """ % unicode(date.today()))
        anos = range(date.today().year, 1900, -1)
        result = []
        for ano in anos:
            result.append(ano)

        result = zip(result, result)
        result = [(unicode(elem[0]), unicode(elem[1])) for elem in result]
        return result

    def on_change_ano(self, cr, uid, ids, ano):
        db_sncp_tesouraria_contas_ots = self.pool.get('sncp.tesouraria.contas.ots')
        if len(ids) != 0:
            self.write(cr, uid, ids, {'state': 1, 'name': ano})
        else:
            ids.append(self.create(cr, uid, {'state': 1, 'name': ano}))

        cr.execute("""
        SELECT id FROM sncp_tesouraria_contas_ots
        WHERE conta_id IN (
           SELECT account_id FROM account_move_line
           WHERE EXTRACT (YEAR FROM date) = '%s')
        OR conta_id IN (
           SELECT account_id FROM account_move_line
           WHERE period_id IN (
              SELECT id FROM account_period
              WHERE special = TRUE AND EXTRACT (YEAR FROM date_start) = '%s')
              )
        """ % (ano, ano))
        result = cr.fetchall()
        lista = []
        state = 0
        for res in result:
            lista.append(res[0])
            db_sncp_tesouraria_contas_ots.write(cr, uid, res[0], {'mapa_id': ids[0]})
            state = 1
        lista = list(set(lista))
        return {
            'value': {'state': state, 'name': ano, 'conta_ots_ids': lista}
        }

    def imprimir(self, cr, uid, ids, context):
        datas = {'ids': ids,
                 'model': 'sncp.tesouraria.mapa.ots', }
        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.tesouraria.mapa.ots.report',
            'datas': datas,
        }

    _columns = {
        'name': fields.selection(select_ano, u'Selecciona o ano'),
        'conta_ots_ids': fields.one2many('sncp.tesouraria.contas.ots', 'mapa_id'),
        'state': fields.integer('Estado'),
        # 0 -- imprimir invisivel
        # 1 -- contas visiveis, imprimir visivel
    }

    _defaults = {
        'state': 0,
        'name': unicode(date.today().year),
    }

sncp_tesouraria_mapa_ots()


class sncp_tesouraria_contas_ots(osv.Model):
    _name = 'sncp.tesouraria.contas.ots'
    _description = u"Contas OTS"

    def anterior(self, cr, ano, conta_id):
        cr.execute("""SELECT credit, debit FROM account_move_line
        WHERE EXTRACT (YEAR FROM date) = %d AND
            account_id = %d AND
            period_id IN (
                SELECT id FROM account_period
                WHERE special = TRUE AND EXTRACT (YEAR FROM date_start) = %d)
                """ % (ano, conta_id, ano))
        result = cr.fetchone()
        if result is None:
            devedor = 0
            credor = 0
        else:
            devedor = result[1]
            credor = result[0]
        return [devedor, credor]

    def anual(self, cr, ano, conta_id):
        cr.execute("""SELECT COALESCE(SUM(credit),0.0),COALESCE(SUM(debit),0.0) FROM account_move_line
                WHERE EXTRACT (YEAR FROM date) = %d AND
                    account_id = %d AND
                    period_id IN (
                        SELECT id FROM account_period
                        WHERE special = FALSE AND EXTRACT (YEAR FROM date_start) = %d)
                        """ % (ano, conta_id, ano))
        result = cr.fetchone()
        debito = 0
        credito = 0
        if result[0] is None and result[1] is None:
            pass
        elif result[0] is None:
            credito = 0
            debito = result[1]
        elif result[1] is None:
            debito = 0
            credito = result[0]
        else:
            debito = result[1]
            credito = result[0]
        return [debito, credito]

    def calculo(self, cr, uid, ids, fields, arg, context):
        valor_return = {}
        for conta_ots_id in ids:
            obj = self.browse(cr, uid, conta_ots_id)

            # Os valores escritos no primeiro dia de ano
            if arg in ['deb_ant', 'cre_ant']:
                [devedor, credor] = self.anterior(cr, obj.ano, obj.conta_id.id)

                # Bloco de processamento de resultado
                if arg in ['deb_ant'] and (devedor - credor) < 0:
                    valor_return[conta_ots_id] = 0
                elif arg in ['cre_ant'] and (devedor - credor) < 0:
                    valor_return[conta_ots_id] = abs((devedor - credor))
                elif arg in ['deb_ant'] and (devedor - credor) > 0:
                    valor_return[conta_ots_id] = abs((devedor - credor))
                elif arg in ['cre_ant'] and (devedor - credor) > 0:
                    valor_return[conta_ots_id] = 0
                else:
                    valor_return[conta_ots_id] = 0

            # Movimentos anuais
            elif arg in ['deb_an', 'cre_an']:
                [debito, credito] = self.anual(cr, obj.ano, obj.conta_id.id)

                # Bloco de processamento de resultado
                if arg in ['deb_an']:
                    valor_return[conta_ots_id] = abs(debito)
                elif arg in ['cre_an']:
                    valor_return[conta_ots_id] = abs(credito)

            # Saldo para a gerencia seguinte
            elif arg in ['deb_seg', 'cre_seg']:
                [devedor, credor] = self.anterior(cr, obj.ano, obj.conta_id.id)
                [debito, credito] = self.anual(cr, obj.ano, obj.conta_id.id)

                # Bloco de processamento de resultado
                if arg in ['deb_seg'] and (devedor - credor + debito - credito) < 0:
                    valor_return[conta_ots_id] = 0
                elif arg in ['cre_seg'] and (devedor - credor + debito - credito) < 0:
                    valor_return[conta_ots_id] = abs((devedor - credor + debito - credito))
                elif arg in ['deb_seg'] and (devedor - credor + debito - credito) > 0:
                    valor_return[conta_ots_id] = abs((devedor - credor + debito - credito))
                elif arg in ['cre_seg'] and (devedor - credor + debito - credito) > 0:
                    valor_return[conta_ots_id] = 0
                else:
                    valor_return[conta_ots_id] = 0
            else:
                raise osv.except_osv(_(u'Aviso'), _(u'Argumentos mal definidos.'))

            aux = decimal.Decimal(unicode(valor_return[conta_ots_id]))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            valor_return[conta_ots_id] = float(aux)
        return valor_return

    def on_change_conta(self, cr, uid, ids, conta_id):
        db_account_account = self.pool.get('account.account')
        if conta_id is False:
            return {}
        conta = db_account_account.browse(cr, uid, conta_id)
        if len(ids) != 0:
            self.write(cr, uid, ids, {'name': conta.name})
        return {'value': {'name': conta.name}}

    _columns = {
        'mapa_id': fields.many2one('sncp.tesouraria.mapa.ots'),
        'ano': fields.related('mapa_id', 'name', type="integer", store=True),
        'conta_id': fields.many2one('account.account', u'Conta contábil', domain=[('type', 'not in', ['view'])]),
        'codigo': fields.related('conta_id', 'code', type="char", store=True, string=u'Código'),
        'name': fields.char(u'Designação das contas', size=64),
        'destaque': fields.boolean(u'Destaque'),
        # Esclusivamente para Mapa de Op. Tes.
        'debito_ant': fields.function(calculo,  fields=True, arg='deb_ant', method=False, type="float",
                                      string=u'Devedor (GA)', digits=(12, 2), store=True),
        'credito_ant': fields.function(calculo,  arg='cre_ant', method=False, type="float",
                                       string=u'Credor (GA)', digits=(12, 2), store=True),
        'debito_anual': fields.function(calculo,  arg='deb_an', method=False, type="float",
                                        string=u'Débito (Anual)', digits=(12, 2), store=True),
        'credito_anual': fields.function(calculo,  arg='cre_an', method=False, type="float",
                                         string=u'Crédito (Anual)', digits=(12, 2), store=True),
        'debito_seg': fields.function(calculo,  arg='deb_seg', method=False, type="float",
                                      string=u'Devedor (GF)', digits=(12, 2), store=True),
        'credito_seg': fields.function(calculo,  arg='cre_seg', method=False, type="float",
                                       string=u'Credor (GF)', digits=(12, 2), store=True),

    }

    _sql_constraints = [
        ('conta_ots_unique', 'unique (conta_id)', u'Esta conta já está registada.')
    ]

    _order = 'conta_id'

sncp_tesouraria_contas_ots()
# ________________________________________________________________Guias  OP TES ________________________


class sncp_receita_op_tes(osv.Model):
    _inherit = 'sncp.receita.op.tes'
    # receita/cobranca

    def preenche_linhas(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'estado': 1})
        return True

    def continuar(self, cr, uid, ids, context=None):
        cr.execute("""
            SELECT id FROM sncp_receita_op_tes_linhas
            WHERE op_tes_id=%d
            """ % ids[0])

        lista = cr.fetchall()
        if len(lista) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não têm linhas associadas.'))

        self.write(cr, uid, ids, {'estado': 2})
        return True

    def criar_guia_receita(self, cr, uid, ids, context=None):
        if len(ids) != 0:
            obj = self.browse(cr, uid, ids[0])
            db_sncp_receita_guia_rec = self.pool.get('sncp.receita.guia.rec')
            vals = {'natureza': 'ots',
                    'unique_key': obj.name, }
            db_sncp_receita_guia_rec.cria_guia_receita(cr, uid, ids, vals, context)

        menu_obj = self.pool.get('ir.ui.menu')
        menu_ids = menu_obj.search(cr, uid, [('name', '=', 'Criar Guia de Operações de Tesouraria')], context=context)
        return {'type': 'ir.actions.client', 'tag': 'reload', 'params': {'menu_id': menu_ids}}

sncp_receita_op_tes()