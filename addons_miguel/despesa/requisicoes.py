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

from datetime import datetime
import decimal
from decimal import *
from openerp.osv import fields, osv
from openerp.tools.translate import _
import despesa

# ___________________________________________________________ REQUISIÇÕES_____________________________________________


class sncp_despesa_requisicoes(osv.Model):
    _name = 'sncp.despesa.requisicoes'
    _description = u"Requisições"

    def anular(self, cr, uid, ids, context):
        cr.execute("""
        DELETE FROM sncp_despesa_requisicoes_linhas
        WHERE req_id=%d
        """ % ids[0])

        cr.execute("""
        DELETE FROM sncp_despesa_requisicoes_historico
        WHERE req_id=%d
        """ % ids[0])

        return self.unlink(cr, uid, ids)

    def continuar(self, cr, uid, ids, context):
        db_sncp_despesa_requisicoes_historico = self.pool.get('sncp.despesa.requisicoes.historico')
        db_sncp_despesa_requisicoes_historico.create(cr, uid, {'req_id': ids[0]})
        self.write(cr, uid, ids, {'estado': 1})
        return True

    def para_aprovar(self, cr, uid, ids, context):
        db_sncp_despesa_requisicoes_historico = self.pool.get('sncp.despesa.requisicoes.historico')
        obj = self.browse(cr, uid, ids[0])

        # O valor total da requisição
        cr.execute("""SELECT SUM(quant_req * preco_unit  * (1 + taxa_iva))
                      FROM sncp_despesa_requisicoes_linhas
                      WHERE req_id = %d""" % ids[0])
        montante = cr.fetchone()
        if montante[0] is None:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode Remeter para Aprovação a requisição sem linhas.'))

        # Verificar se é aprovador
        cr.execute("""SELECT id  FROM sncp_despesa_aprovadores
                      WHERE aprovador_id = %d AND
                            departamento_id = %d AND
                            requisicoes = TRUE AND
                            limite_req >= %d AND
                            '%s' BETWEEN name AND fim
                            """
                   % (obj.requisitante_emp_id.id,
                      obj.requisitante_dep_id.id,
                      montante[0], obj.datahora))
        result = cr.fetchone()

        # Para aprovação
        if result is None:
            db_sncp_despesa_requisicoes_historico.create(cr, uid, {
                'req_id': ids[0], 'accao': 'remetd'})
            self.write(cr, uid, ids, {'state': 'remetd'})
            cr.execute("""
            UPDATE sncp_despesa_requisicoes_linhas SET parent_state='remetd'
            WHERE req_id=%d
            """ % ids[0])
        # Aprovado
        else:
            self.aprovar(cr, uid, ids, context)
        return True

    def aprovar(self, cr, uid, ids, context):
        # Atribuir o número
        cr.execute("""SELECT ri_sequence_id FROM sncp_comum_param
                      WHERE state = 'draft'""")
        result = cr.fetchone()
        if result is None:
            raise osv.except_osv(_(u'Aviso'), _(u'Considere definir os parâmetros em Comum/Parâmetros.'))

        db_ir_sequence = self.pool.get('ir.sequence')
        name = db_ir_sequence.next_by_id(cr, uid, result[0])
        self.write(cr, uid, ids, {'name': name})

        db_sncp_despesa_requisicoes_historico = self.pool.get('sncp.despesa.requisicoes.historico')
        db_sncp_despesa_requisicoes_historico.create(cr, uid, {
            'req_id': ids[0], 'accao': 'aprovd'})
        self.write(cr, uid, ids, {'state': 'aprovd', 'estado': 2})
        # linhas

        cr.execute("""UPDATE sncp_despesa_requisicoes_linhas SET state = 'aprovd',parent_state='aprovd'
                      WHERE req_id = %d AND state = 'draft'""" % ids[0])
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def rejeitar(self, cr, uid, ids, context):
        db_sncp_despesa_requisicoes_historico = self.pool.get('sncp.despesa.requisicoes.historico')
        db_sncp_despesa_requisicoes_historico.create(cr, uid, {
            'req_id': ids[0], 'accao': 'rejeit'})
        self.write(cr, uid, ids, {'state': 'rejeit'})
        # linhas
        cr.execute("""UPDATE sncp_despesa_requisicoes_linhas SET state = 'rejeit',parent_state='rejeit'
                      WHERE req_id = %d""" % ids[0])
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def recuperar(self, cr, uid, ids, context):
        db_sncp_despesa_requisicoes_historico = self.pool.get('sncp.despesa.requisicoes.historico')
        db_sncp_despesa_requisicoes_historico.create(cr, uid, {
            'req_id': ids[0], 'accao': 'recupe'})
        self.write(cr, uid, ids, {'state': 'draft', 'name': None, 'estado': 1})
        # linhas
        cr.execute("""UPDATE sncp_despesa_requisicoes_linhas SET state = 'draft',parent_state='draft'
                      WHERE req_id = %d""" % ids[0])
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def completar(self, cr, uid, ids, context):
        # linhas
        cr.execute("""
                      SELECT id
                      FROM sncp_despesa_requisicoes_linhas
                      WHERE req_id = %d""" % ids[0])
        total = cr.fetchall()
        cr.execute("""
                      SELECT id
                      FROM sncp_despesa_requisicoes_linhas
                      WHERE req_id = %d AND state IN ('satisf','convrt') """ % ids[0])
        linha_estado = cr.fetchall()

        if len(total) == len(linha_estado):
            self.write(cr, uid, ids, {'state': 'complt'})
            cr.execute("""
            UPDATE sncp_despesa_requisicoes_linhas SET parent_state='complt'
            WHERE req_id=%d
            """ % ids[0])
            db_sncp_despesa_requisicoes_historico = self.pool.get('sncp.despesa.requisicoes.historico')
            db_sncp_despesa_requisicoes_historico.create(cr, uid, {
                'req_id': ids[0], 'accao': 'complt'})

        return True

    def criar_entrega(self, cr, uid, ids, context):
        db_product_product = self.pool.get('product.product')
        db_sncp_despesa_requisicoes_linhas = self.pool.get('sncp.despesa.requisicoes.linhas')
        db_stock_move = self.pool.get('stock.move')
        obj = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'estado': 3})

        # Carregar as linhas de requisição
        cr.execute("""SELECT uom_id, preco_unit, item_id,id FROM sncp_despesa_requisicoes_linhas
                      WHERE req_id = %d""" % ids[0])
        linhas = cr.fetchall()
        datahora = unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                                    datetime.now().minute, datetime.now().second))

        for linha in linhas:
            req_linha = db_sncp_despesa_requisicoes_linhas.browse(cr, uid, linha[3])
            obj_product = db_product_product.browse(cr, uid, linha[2])
            obj_user = self.pool.get('res.users').browse(cr, uid, uid)
            qt_dif_req_sat = req_linha.quant_req - req_linha.quant_sat
            aux = decimal.Decimal(unicode(qt_dif_req_sat))
            aux = aux.quantize(Decimal('0.001'), ROUND_HALF_UP)
            qt_dif_req_sat = float(aux)

            if not obj.requisitante_dep_id.location_id.id:
                raise osv.except_osv(_(u'Aviso'), _(u'O/A ' + unicode(obj.requisitante_dep_id.name) +
                                                    u' não tem a localização definida.'))

            values = {
                'req_id': ids[0],
                'req_linha_id': linha[3],
                'name': '[' + obj_product.default_code + '] ' + obj_product.name_template,
                'priority': '1',
                'date': datahora,
                'date_expected': datahora,
                'product_id': linha[2],
                'product_uom': linha[0],
                'product_qty': qt_dif_req_sat,
                'product_uos': None,
                'location_id': obj.armazem_req_id.lot_output_id.id,
                'location_dest_id': obj.requisitante_dep_id.location_id.id,
                'partner_id': obj_user.company_id.partner_id.id,
                'auto_validate': False,
                'state': 'draft',
                'price_unit': linha[1],
                'price_currency_id': obj_user.company_id.currency_id.id,
                'origin': obj.name,
            }
            db_stock_move.create(cr, uid, values)
        return True

    def entregar(self, cr, uid, ids, context=None):
        db_sncp_despesa_requisicoes_linhas = self.pool.get('sncp.despesa.requisicoes.linhas')
        db_stock_picking = self.pool.get('stock.picking')
        db_ir_sequence = self.pool.get('ir.sequence')
        db_stock_move = self.pool.get('stock.move')
        obj = self.browse(cr, uid, ids[0])

        cr.execute("""SELECT ri_diario_id FROM sncp_comum_param
                      WHERE state = 'draft'""")
        result = cr.fetchone()
        if result is None:
            raise osv.except_osv(_(u'Aviso'), _(u'Considere definir os parâmetros em Comum/Parâmetros.'))

        datahora = unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                                    datetime.now().minute, datetime.now().second))

        linhas_ids = db_sncp_despesa_requisicoes_linhas.search(cr, uid, [('req_id', '=', obj.id)])
        obj_user = self.pool.get('res.users').browse(cr, uid, uid)
        cr.execute("""
            SELECT res_id
            FROM ir_model_data
            WHERE name='seq_picking_internal'
            """)

        sequencia_id = cr.fetchone()

        if sequencia_id is not None:
            nome = db_ir_sequence.next_by_id(cr, uid, sequencia_id)
        else:
            nome = None

        values = {
            'origin': obj.name,
            'date': datahora,
            'partner_id': obj_user.company_id.partner_id.id,
            'name': nome,
            'type': 'internal',
            'stock_journal_id': result[0],
            'location_id': obj.armazem_req_id.lot_output_id.id,
            'location_dest_id': obj.requisitante_dep_id.location_id.id,
            'move_type': 'direct',
            'state': 'draft',
            'auto_picking': False,
            'invoice_state': 'none',
        }
        pick_id = db_stock_picking.create(cr, uid, values)

        stock_move_ids = db_stock_move.search(cr, uid, [('req_linha_id', 'in', linhas_ids)])

        for stock_move in db_stock_move.browse(cr, uid, stock_move_ids):

            qt_dif_req_sat = stock_move.req_linha_id.quant_req - stock_move.req_linha_id.quant_sat
            aux = decimal.Decimal(unicode(qt_dif_req_sat))
            aux = aux.quantize(Decimal('0.001'), ROUND_HALF_UP)
            qt_dif_req_sat = float(aux)

            if stock_move.product_qty > qt_dif_req_sat:
                raise osv.except_osv(_(u'Aviso'), _(u' A quantidade do movimento de stock deve ser inferior ou igual'
                                                    u' à diferença entre a quantidade requirida e a '
                                                    u' quantidade satisfeita da linha da requisição associada.'))

        db_stock_move.write(cr, uid, stock_move_ids, {'picking_id': pick_id})

        # _Confirmar e Transferir
        db_stock_picking.draft_validate(cr, uid, [pick_id], context=context)
        for linha_id in linhas_ids:
            stock_move_id = db_stock_move.search(cr, uid, [('req_linha_id', '=', linha_id)])
            stock_move = db_stock_move.browse(cr, uid, stock_move_id[0])
            linha = db_sncp_despesa_requisicoes_linhas.browse(cr, uid, linha_id)

            quant_satis = linha.quant_sat + stock_move.product_qty
            aux = decimal.Decimal(unicode(quant_satis))
            aux = aux.quantize(Decimal('0.001'), ROUND_HALF_UP)
            quant_satis = float(aux)

            if linha.quant_req == quant_satis:
                db_sncp_despesa_requisicoes_linhas.write(cr, uid, linha.id, {'quant_sat': quant_satis,
                                                                             'state': 'satisf'})
            else:
                db_sncp_despesa_requisicoes_linhas.write(cr, uid, linha.id, {'quant_sat': quant_satis})

        self.completar(cr, uid, ids, context)
        self.write(cr, uid, ids, {'estado': 4})
        return self.imprimir(cr, uid, ids, context)

    def imprimir(self, cr, uid, ids, context=None):
        datas = {
            'ids': ids,
            'model': 'sncp.despesa.requisicoes',
        }
        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.despesa.requisicoes.report',
            'datas': datas,
        }

    def get_lista_requisicoes_js(self, cr, uid, context):
        # Seleccionar aprovadores
        cr.execute("""SELECT departamento_id, name, fim, limite_req
                    FROM sncp_despesa_aprovadores
                    WHERE requisicoes = TRUE AND
                    aprovador_id IN (SELECT id FROM hr_employee
                    WHERE resource_id IN (SELECT id FROM resource_resource WHERE user_id = %d ))
                    """ % uid)
        aprovadores = cr.fetchall()
        lista_req = []

        # Lista de requisições
        for aprovador in aprovadores:
            cr.execute("""SELECT R.id
                          FROM sncp_despesa_requisicoes AS R
                          WHERE R.datahora BETWEEN '%s' AND '%s' AND
                            R.requisitante_dep_id = %d AND
                            R.state = '%s' AND
                            (SELECT SUM(quant_req * preco_unit  * (1 + taxa_iva))
                                FROM sncp_despesa_requisicoes_linhas
                                WHERE req_id = R.id) <= %d
            """ % (aprovador[1], aprovador[2], aprovador[0], context['state'], aprovador[3]))
            lista = cr.fetchall()

            for line in lista:
                lista_req.append(line[0])

        if len(lista_req) == 0:
            if context['text'] == u'aprovar':
                text = u'aprovar'
            else:
                text = u'recuperar'
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Para este aprovador não há nenhuma requisição para ' + text +
                                   u' entre as datas, departamentos e valores máximos definidos'
                                   u' em Despesa/Dados Gerais/Aprovadores.'))

        return lista_req

    def get_requisicao_pesquisa_list_js(self, cr, uid):
        lista = self.search(cr, uid, [])
        lista = list(set(lista))
        return self.name_get(cr, uid, lista)

    def get_user_list_js(self, cr, uid):
        res_users = self.pool.get('res.users')
        lista = res_users.search(cr, uid, [])
        lista = list(set(lista))
        return res_users.name_get(cr, uid, lista)

    _columns = {
        'name': fields.char(u'Número', size=12),
        'datahora': fields.datetime(u'Data e Hora'),
        'armazem_req_id': fields.many2one('stock.warehouse', u'Armazém Requisitado'),
        'requisitante_dep_id': fields.many2one('hr.department', u'Departamento Requisitante'),
        'requisitante_emp_id': fields.many2one('hr.employee', u'Nome do Requisitante'),
        'justificacao': fields.text(u'Justificação'),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('remetd', u'Remetida a aprovação'),
                                   ('aprovd', u'Aprovada'),
                                   ('rejeit', u'Rejeitada'),
                                   ('complt', u'Completa')], u'Estado'),
        'linhas_ids': fields.one2many('sncp.despesa.requisicoes.linhas', 'req_id', u'Linhas das requisições'),
        'historico_ids': fields.one2many('sncp.despesa.requisicoes.historico', 'req_id', u'Historico'),
        'movim_stock_ids': fields.one2many('stock.move', 'req_id', u'Linhas de Stock'),
        'estado': fields.integer(u'campo de controlo'),
        # 0 -- notebook invisivel, botão continuar visivel
        # 1 -- notebook visivel , botão para aprovação visivel
        # 2 -- "Criar Entrega" visivel
        # 3 -- Entregas do armazem Visivel
    }

    _order = 'name'

    def get_employee(self, cr, uid, context):
        cr.execute("""SELECT id FROM hr_employee WHERE resource_id IN (
                            SELECT id FROM resource_resource WHERE user_id = %d )""" % uid)
        res = cr.fetchone()
        if res[0] is None:
            raise osv.except_osv(_(u'Aviso'), _(u'O utilizador corrente não é empregado.'))
        else:
            return res[0]

    _defaults = {
        'state': 'draft',
        'datahora': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                                     datetime.now().minute, datetime.now().second)),
        'requisitante_emp_id': lambda self, cr, uid, ctx: self.get_employee(cr, uid, ctx),
    }

    _sql_constraints = [
        ('numero_requisicao_unique', 'unique (name)',
         u'Requisição com este número já está registada ou número de digitos na sequência é superior a 12')
    ]


sncp_despesa_requisicoes()

# ___________________________________________________________ REQUISIÇÕES LINHAS  ____________________________________


class sncp_despesa_requisicoes_linhas(osv.Model):
    _name = 'sncp.despesa.requisicoes.linhas'
    _description = u"Linhas das Requisições"

    def get_item_details(self, cr, uid, ids, item_id):
        taxa = 0.0
        db_account_tax = self.pool.get('account.tax')
        cr.execute(""" SELECT COALESCE(standard_price,0.0), uom_id FROM product_template
                       WHERE id = %d""" % item_id)
        result = cr.fetchone()
        if result is None:
            result = [0.0, False]
            taxa = 0.0
        elif result[0] is None or result[0] <= 0.0:
            raise osv.except_osv(_(u'Aviso'), _(u'O preço de custo deste artigo não está definido corretamente.'))
        elif result[1] is None or result[1] is False:
            raise osv.except_osv(_(u'Aviso'), _(u'A unidade deste produto não está definida corretamente.'))
        cr.execute(""" SELECT tax_id FROM product_taxes_rel
                       WHERE prod_id = %d""" % item_id)
        tax = cr.fetchone()
        if tax is not None:
            at = db_account_tax.browse(cr, uid, tax[0])
            taxa = at.amount

        return [result[0], result[1], taxa]

    def on_change_item_id(self, cr, uid, ids, item_id):
        [preco, uom, taxa] = self.get_item_details(cr, uid, ids, item_id)

        if len(ids) != 0:
            self.write(cr, uid, ids, {'preco_unit': preco, 'uom_id': uom, 'taxa_iva': taxa, })

        return {'value': {'preco_unit': preco,
                          'uom_id': uom,
                          'taxa_iva': taxa, }}

    def rejeitar_linha(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state': 'rejeit'})
        return True

    _columns = {
        'req_id': fields.many2one('sncp.despesa.requisicoes', u'Requisição'),
        'parent_state': fields.related('req_id', 'state', type="char", store=True),
        'name': fields.integer(u'Linha'),
        'item_id': fields.many2one('product.product', u'Item'),
        'quant_req': fields.float(u'Quantidade requisitada', digits=(12, 3)),
        'preco_unit': fields.float(u'Preço unitário', digits=(12, 3)),
        'uom_id': fields.many2one('product.uom', u'Unidade'),
        'taxa_iva': fields.float(u'Taxa de IVA', digits=(1, 5)),
        'quant_sat': fields.float(u'Quantidade satisfeita', digits=(12, 3)),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('aprovd', u'Aprovada'),
                                   ('rejeit', u'Rejeitada'),
                                   ('satisf', u'Satisfeita'),
                                   ('convrt', u'Convertida'),
                                   ('cancel', u'Cancelada')], u'Estado'),
    }

    def create(self, cr, uid, vals, context=None):
        name = despesa.get_sequence(self, cr, uid, context, 'req_lin', vals['req_id'])
        vals['name'] = name
        [preco, uom, taxa] = self.get_item_details(cr, uid, [], vals['item_id'])
        vals['preco_unit'] = preco
        vals['uom_id'] = uom
        vals['taxa_iva'] = taxa

        return super(sncp_despesa_requisicoes_linhas, self).create(cr, uid, vals, context=context)

    _order = 'name'

    _defaults = {
        'state': 'draft',
    }

    def quantidade_positiva(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.quant_req > 0:
            return True
        else:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'A quantidade requisitada tem que ser positiva.'))

    _constraints = [
        (quantidade_positiva, u'', ['quant_req'])
    ]

    _sql_constraints = [
        ('linha_requisicao_unique', 'unique (req_id, name)', u'Esta linha já está registada!')
    ]


sncp_despesa_requisicoes_linhas()

# ___________________________________________________________ REQUISIÇÕES HISTORICO ____________________________________


class sncp_despesa_requisicoes_historico(osv.Model):
    _name = 'sncp.despesa.requisicoes.historico'
    _description = u"Histórico das Requisições"

    _columns = {
        'name': fields.datetime(u'Data e hora'),
        'req_id': fields.many2one('sncp.despesa.requisicoes', u'Requisição'),
        'accao': fields.selection([('draft', u'Abertura'),
                                   ('remetd', u'Remetida a aprovação'),
                                   ('aprovd', u'Aprovada'),
                                   ('rejeit', u'Rejeitada'),
                                   ('recupe', u'Recuperada'),
                                   ('complt', u'Completa')], u'Acção'),
        'user_id': fields.many2one('res.users', u'Utilizador'),
        'parent_id': fields.many2one('sncp.despesa.requisicoes.historico', u'Pai', ),
        'child_ids': fields.one2many('sncp.despesa.requisicoes.historico', 'parent_id', u'Filhos'),

    }

    def create(self, cr, uid, vals, context=None):
        cr.execute("""SELECT id FROM sncp_despesa_requisicoes_historico
                      WHERE req_id= %d AND accao='draft'""" % (vals['req_id']))
        parent_id = cr.fetchone()
        if parent_id is not None:
            vals['parent_id'] = parent_id
        return super(sncp_despesa_requisicoes_historico, self).create(cr, uid, vals, context=context)

    _order = 'name desc'

    _defaults = {
        'accao': 'draft',
        'name': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                                 datetime.now().minute, datetime.now().second)),
        'user_id': lambda self, cr, uid, ctx: uid,
    }


sncp_despesa_requisicoes_historico()

# ___________________________________________________________ REQUISIÇÕES ORDEM COMPRA ________________________________


class sncp_despesa_requisicoes_ordem_compra(osv.Model):
    _name = 'sncp.despesa.requisicoes.ordem.compra'
    _description = u"Ordem de compra Requisições"

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            result = u'Gerar Ordem de Compra'
            res.append((record['id'], result))
        return res

    def continuar(self, cr, uid, ids, context=None):
        return self.pool.get('sncp.despesa.requisicoes.converter.wizard').wizard(cr, uid, ids, context)

    def on_change_requisicao(self, cr, uid, ids, req_de_id):
        if req_de_id is not False:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'req_de_id': req_de_id, 'req_ate_id': req_de_id})

            return {'value': {'req_de_id': req_de_id, 'req_ate_id': req_de_id}}

        return {}

    def on_change_departamento(self, cr, uid, ids, dep_de_id):
        if dep_de_id is not False:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'depart_de_id': dep_de_id, 'depart_ate_id': dep_de_id})
            return {'value': {'depart_de_id': dep_de_id, 'depart_ate_id': dep_de_id}}

        return {}

    def on_change_data(self, cr, uid, ids, name):
        if len(name) != 0:
            data_aux = datetime.strptime(name, "%Y-%m-%d %H:%M:%S").date()
            nova_data = datetime(data_aux.year, data_aux.month, data_aux.day, 23, 59, 59)
            str_data = unicode(nova_data)

            if len(ids) != 0:
                self.write(cr, uid, ids, {'name': name, 'data_ate': str_data})
            return {'value': {'name': name, 'data_ate': str_data}}

        return {}

    _columns = {
        'fornecedor_id': fields.many2one('res.partner', u'Fornecedor'),
        'armazem_id': fields.many2one('stock.warehouse', u'Armazém'),
        'req_de_id': fields.many2one('sncp.despesa.requisicoes', u'Da requisição',
                                     domain=[('state', 'in', ['aprovd'])]),
        'req_ate_id': fields.many2one('sncp.despesa.requisicoes', u'Até à requisição',
                                      domain=[('state', 'in', ['aprovd'])]),
        'name': fields.datetime(u'Da data'),
        'data_ate': fields.datetime(u'Até à data'),
        'depart_de_id': fields.many2one('hr.department', u'Do departamento'),
        'depart_ate_id': fields.many2one('hr.department', u'Até ao departamento'),

    }

    def _minima_requisicao(self, cr, uid, context):
        cr.execute("""
        SELECT min(name)
        FROM sncp_despesa_requisicoes
        WHERE state='aprovd'
        """)

        nome = cr.fetchone()

        if nome[0] is not None:
            cr.execute("""
            SELECT id
            FROM sncp_despesa_requisicoes
            WHERE name='%s'
            """ % nome[0])

            min_id = cr.fetchone()[0]
            return min_id

        return False

    def _maxima_requisicao(self, cr, uid, context):
        cr.execute("""
        SELECT max(name)
        FROM sncp_despesa_requisicoes
        WHERE state='aprovd'
        """)

        nome = cr.fetchone()

        if nome[0] is not None:
            cr.execute("""
            SELECT id
            FROM sncp_despesa_requisicoes
            WHERE name='%s'
            """ % nome[0])

            max_id = cr.fetchone()[0]
            return max_id

        return False

    def _minimo_departamento(self, cr, uid, context):
        cr.execute("""
        SELECT min(name)
        FROM hr_department
        """)

        nome = cr.fetchone()

        if nome[0] is not None:
            cr.execute("""
            SELECT id
            FROM hr_department
            WHERE name='%s'
            """ % nome[0])

            min_id = cr.fetchone()

            return min_id

        return False

    def _maximo_departamento(self, cr, uid, context):
        cr.execute("""
        SELECT max(name)
        FROM hr_department
        """)

        nome = cr.fetchone()

        if nome[0] is not None:
            cr.execute("""
            SELECT id
            FROM hr_department
            WHERE name='%s'
            """ % nome[0])

            max_id = cr.fetchone()[0]
            return max_id

        return False

    _defaults = {
        'name': unicode(datetime(datetime.now().year, 1, 1, 0, 0, 0)),
        'data_ate': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                                     datetime.now().minute, datetime.now().second)),

        'req_de_id': lambda self, cr, uid, ctx: self._minima_requisicao(cr, uid, ctx),
        'req_ate_id': lambda self, cr, uid, ctx: self._maxima_requisicao(cr, uid, ctx),
        'depart_de_id': lambda self, cr, uid, ctx: self._minimo_departamento(cr, uid, ctx),
        'depart_ate_id': lambda self, cr, uid, ctx: self._maximo_departamento(cr, uid, ctx),
    }

    def data_de_menor(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.name > obj.data_ate:
            raise osv.except_osv(_(u'Aviso'), _(u'A segunda data não deve ser inferior à primeira.'))
        return True

    def depart_de_menor(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.depart_de_id.name > obj.depart_ate_id.name:
            raise osv.except_osv(_(u'Aviso'), _(u'O segundo departamento não deve ser inferior ao primeiro.'))
        return True

    def req_de_menor(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.req_de_id.name > obj.req_ate_id.name:
            raise osv.except_osv(_(u'Aviso'), _(u'A segunda requisição não deve ser inferior à primeira.'))
        return True

    def sql_compara_strings(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION compara_strings(str1 varchar,str2 varchar) RETURNS INTEGER AS $$
        DECLARE
           x int;
           c1 varchar;
           c2 varchar;
        BEGIN
        IF LENGTH($1)>=LENGTH($2) THEN
            FOR x IN 1..LENGTH($1) LOOP
                c1=COALESCE(substring($1 from x for 1),'');
                c2=COALESCE(substring($2 from x for 1),'');
                IF ascii(c1)>ascii(c2) THEN
                RETURN 1;
                ELSIF ascii(c1)<ascii(c2) THEN
                   RETURN -1;
                END IF;
            END LOOP;
        ELSIF LENGTH($2)>=LENGTH($1) THEN
            FOR x in 1..LENGTH($2) LOOP
                c1=COALESCE(substring($1 from x for 1),'');
                c2=COALESCE(substring($2 from x for 1),'');
                IF ascii(c2)>ascii(c1) THEN
                RETURN -1;
                ELSIF ascii(c2)<ascii(c1) THEN
                   RETURN 1;
                END IF;
            END LOOP;
        END IF;
        RETURN 0;
        END;
        $$LANGUAGE plpgsql;
        """)
        return True

    def teste_existencia_requisicoes_ordem_compra(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname='compara_strings'""")
        result = cr.fetchone()
        if result is None:
            self.sql_compara_strings(cr)

        return True

    def create(self, cr, uid, vals, context=None):
        self.teste_existencia_requisicoes_ordem_compra(cr)
        return super(sncp_despesa_requisicoes_ordem_compra, self).create(cr, uid, vals, context=context)

    _constraints = [
        (data_de_menor, u'', ['name', 'data_ate']),
        (depart_de_menor, u'', ['depart_de_id', 'depart_ate_id']),
        (req_de_menor, u'', ['req_de_id', 'req_ate_id'])
    ]


sncp_despesa_requisicoes_ordem_compra()