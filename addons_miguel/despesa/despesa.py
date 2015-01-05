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
from openerp.osv import fields, osv
from openerp.tools.translate import _


def get_sequence(self, cr, uid, context, text, value):
    # tipos de sequencia
    # Sequencia de linhas da requisição 'req_lin' +prop_id

    seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_' + text + '_code_'+unicode(value))
    if seq is False:
        sequence_type = self.pool.get('ir.sequence.type')
        values_type = {
            'name': 'type_' + text + '_name_'+unicode(value),
            'code':  'seq_' + text + '_code_'+unicode(value), }
        sequence_type.create(cr, uid, values_type, context=context)
        sequence = self.pool.get('ir.sequence')
        values = {
            'name': 'seq_' + text + '_name_'+unicode(value),
            'code':  'seq_' + text + '_code_'+unicode(value),
            'number_next': 1,
            'number_increment': 1, }
        sequence.create(cr, uid, values, context=context)
        seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_' + text + '_code_'+unicode(value))
    return seq


def test_item_id(self, cr, uid, item_id):
    db_product_product = self.pool.get('product.product')
    obj_product = db_product_product.browse(cr, uid, item_id)
    message = ''

    if hasattr(obj_product.product_tmpl_id, 'property_account_expense'):
        if obj_product.product_tmpl_id.property_account_expense.id is False:
            message += u'Contabilidade/Conta de Despesa associada ao fornecedor\n'
    else:
        message += u'Contabilidade/Conta de Despesa associada ao fornecedor\n'

    if hasattr(obj_product.product_tmpl_id, 'property_account_income'):
        if obj_product.product_tmpl_id.property_account_income.id is False:
            message += u'Contabilidade/Conta de Despesa associada ao cliente\n'
    else:
        message += u'Contabilidade/Conta de Despesa associada ao cliente\n'

    if obj_product.product_tmpl_id.standard_price <= 0:
        message += u'Procurements/Preço de Custo\n'

    if obj_product.default_code is False:
        message += u'Informação/Referência Interna\n'

    if len(obj_product.product_tmpl_id.taxes_id) == 0:
        message += u'Contabilidade/Impostos a Cliente\n'

    if len(obj_product.product_tmpl_id.supplier_taxes_id) == 0:
        message += u'Contabilidade/Impostos do Fornecedor\n'

    if obj_product.product_tmpl_id.categ_id.id is False:
        x = obj_product.product_tmpl_id.categ_id.property_stock_valuation_account_id.id

        if x is False:
            message += u' Para as categorias dos artigos defina a '\
                       u' Conta de avaliação de stock'

    if len(message) != 0:
        raise osv.except_osv(_(u'Aviso'), _(u'Para evitar futuros erros na execução do programa '
                                            u'deverá preencher os seguintes campos do artigo:\n'+message))
    return True

# _______________________________________________FUNDOS DISPONIVEIS______________________________________


class sncp_despesa_fundos_disponiveis(osv.Model):
    _name = 'sncp.despesa.fundos.disponiveis'
    _description = u"Fundos Disponíveis"

    def da_valor_total(self, cr, uid, ids, vals):
        obj_id = self.search(cr, uid, [('name', '=', vals['name']), ('mes', '=', vals['mes'])])
        obj = self.browse(cr, uid, obj_id[0])
        return obj.montante

    _columns = {
        'name': fields.integer(u'Ano', size=4),
        'mes': fields.integer(u'Mês', size=2),
        'montante': fields.float(u'Valor', digits=(12, 2)),
        'reservado': fields.float(u'Reservado', digits=(12, 2)),
        'dummy': fields.char(u'\n \n \n \n \n \n \n \n \n ')
    }

    _order = 'name, mes'

    _defaults = {
        'name': datetime.now().year,
    }

    def _reservado_valido(self, cr, uid, ids):
        record = self.browse(cr, uid, ids[0])
        if record.reservado > record.montante:
            raise osv.except_osv(_(u'Aviso'), _(u'O valor reservado não pode ser superior ao montante.'))
        else:
            return True

    def _mes_limit(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.mes in range(1, 13):
            return True
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Mês deve ser entre 1 e 12.'))

    def _ano_limitado(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.name <= 0:
            raise osv.except_osv(_(u'Aviso'), _(u'O ano deve ser superior a 0.'))
        return True

    def _restrict_montante(self, cr, uid, ids):
        record = self.browse(cr, uid, ids[0])
        if record.montante < 0:
            raise osv.except_osv(_(u'Aviso'), _(u'O montante não pode ser negativo.'))
        else:
            return True

    _constraints = [
        (_reservado_valido, u'', ['reservado']),
        (_mes_limit, u'', ['mes']),
        (_ano_limitado, u'', ['name']),
        (_restrict_montante, u'', ['montante']),
    ]

    _sql_constraints = [
        ('ano_mes_uniq', 'unique (name, mes)',
            u'Este mês já existe !'), ]

sncp_despesa_fundos_disponiveis()

# ________________________________________________COFINANCIAMENTOS______________________________________


class sncp_despesa_cofinanciamentos(osv.Model):
    _name = 'sncp.despesa.cofinanciamentos'
    _description = u"Cofinanciamentos"
    _rec_name = 'codigo'

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso_dados_adic
            WHERE cofinanciamento_id = %d
            """ % obj.id)

            res_dados = cr.fetchall()

            if len(res_dados) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o cofinanciamento ' + obj.codigo
                                                    + u' têm associação em:\n'
                                                    u'1. Compromissos.'))

        return super(sncp_despesa_cofinanciamentos, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'codigo': fields.char(u'Programa', size=9),
        'name': fields.char(u'Descrição'),
        'encerramento': fields.date(u'Data de encerramento'),
        'state': fields.integer(u'1 se data é definida')
    }

    _defaults = {'state': 0}

    _order = 'codigo'

    _sql_constraints = [
        ('codigo_natureza_unique', 'unique (codigo)', u'Este programa já existe'),
    ]

sncp_despesa_cofinanciamentos()

# _________________________________________________CRIAR CAB/COMP__________________________________


class sncp_despesa_cria_cab_com(osv.Model):
    _name = 'sncp.despesa.cria.cab.com'
    _description = u"Criar Cabimentos e Compromissos"

    def on_change_to_message(self, cr, uid, ids, ordem_id, cabim_id):
        db_purchase_order = self.pool.get('purchase.order')

        if ordem_id is not False:
            op = db_purchase_order.browse(cr, uid, ordem_id)
            cr.execute("""SELECT string_agg('-- Artigo: ' || default_code,E'\n')
                          FROM product_product
                          WHERE id IN (SELECT product_id FROM purchase_order_line
                                    WHERE order_id = %d) AND
                            id NOT IN (SELECT item_id FROM sncp_comum_codigos_contab
                                        WHERE natureza = 'des' AND
                                              organica_id IS NOT NULL AND
                                              economica_id IS NOT NULL)""" % ordem_id)
            lista_items = cr.fetchone()

            if lista_items[0] is not None:
                message = u'Os produtos contidos na ordem de compra '+unicode(op.name)+u' não têm códigos de ' \
                                                                                       u'contabilização de ' \
                          u'natureza "Despesa Orçamental" definidos corretamente: \n'+lista_items[0]

                return {'value': {'message': message}}

        if ordem_id is not False and cabim_id is False:
            return {'value': {'message': u'Se não indicar o cabimento, vai ser criado um novo.'}}
        elif ordem_id is not False and cabim_id is not False:
            return {'value': {'message': u'Vai ser criado o compromisso na base deste cabimento.'}}
        elif ordem_id is False and cabim_id is not False:
            return {'value': {'message': u'Têm que indicar a Ordem de Compra obrigatoriamente.'}}
        else:
            return {'value': {'message': U'Indique Ordem de compra.'}}

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name'], context=context)
        res = []
        for record in reads:
            result = u'Criar Cabimento e Compromisso'
            res.append((record['id'], result))
        return res

    def check_cod_contab(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        cr.execute("""SELECT string_agg('-- Artigo: ' || default_code,E'\n')
                          FROM product_product
                          WHERE id IN (SELECT product_id FROM purchase_order_line
                                    WHERE order_id = %d) AND
                            id NOT IN (SELECT item_id FROM sncp_comum_codigos_contab
                                        WHERE natureza = 'des' AND
                                              organica_id IS NOT NULL AND
                                              economica_id IS NOT NULL)""" % obj.ordem_compra_id.id)
        lista_items = cr.fetchone()

        if lista_items[0] is not None:
            raise osv.except_osv(_(u'Aviso'), _(u'Os produtos contidos na ordem de compra '
                                                + unicode(obj.ordem_compra_id.name)
                                                + u' não têm códigos de contabilização de ' \
                                                u'natureza "Despesa Orçamental" definidos corretamente: \n'
                                                + unicode(lista_items[0])))
        return True

    def continuar(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        # Atualizar estado da ordem
        self.check_cod_contab(cr, uid, ids, context=context)
        cr.execute("""UPDATE purchase_order SET state = 'draft'
                        WHERE id = %d""" % obj.ordem_compra_id.id)
        if obj.state == 'draft':
            if obj.cabimento_id.id is not False:
                self.write(cr, uid, ids, {'state': 'cab_contab'})
                return self.criar_compromisso(cr, uid, ids, context)
            else:
                return self.criar_cabimento(cr, uid, ids, context)
        elif obj.state == 'cab':
            return self.contabilizar_cabimento(cr, uid, ids, context)
        elif obj.state == 'cab_contab':
            return self.criar_compromisso(cr, uid, ids, context)
        elif obj.state == 'comp':
            return self.contabilizar_compromisso(cr, uid, ids, context)
        else:
            pass

    def criar_cabimento(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        db_sncp_despesa_cabimento = self.pool.get('sncp.despesa.cabimento')

        # Cabeçalho do Cabimento
        values_cabim = {
            'cabimento': '',
            'name': obj.name,
            'desc2': obj.desc2,
            'data': unicode(date.today()),
            'observ': u'Cabimento criado automaticamente para satisfazer a ordem de compra ' +
                      obj.ordem_compra_id.name,
            'state': 'draft',
            'origem_id': False, }
        cabimento_id = db_sncp_despesa_cabimento.create(cr, uid, values_cabim)

        # Criar linhas de cabimento
        cr.execute("""SELECT linhas_ordem_compra_cabimento( %d, %d)""" % (obj.ordem_compra_id.id, cabimento_id))
        result = cr.fetchone()[0]
        if result is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Existem artigos que não têm associado código de contabilização'
                                                u' de natureza "Despesa Orçamental".'))

        self.write(cr, uid, ids, {'cabimento_id': cabimento_id, 'state': 'cab',
                                  'message': u'Cabimento criado com sucesso.\n'
                                             u'Procede com a contabilização de cabimento.'})
        return self.contabilizar_cabimento(cr, uid, ids, context)

    def contabilizar_cabimento(self, cr, uid, ids, context):
        db_sncp_despesa_cabimento = self.pool.get('sncp.despesa.cabimento')
        obj = self.browse(cr, uid, ids[0])
        context['criar_compromisso'] = ids[0]
        return db_sncp_despesa_cabimento.call_param(cr, uid, [obj.cabimento_id.id], context)

    def finalizar_cabimento(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state': 'cab_contab', 'message': u'Cabimento criado e contabilizado com sucesso.\n'
                                                                    u'Procede com a criação de compromisso'})
        return self.criar_compromisso(cr, uid, ids, context)

    def usar_cabimento(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        cr.execute("""SELECT valida_soma_totais_oc_cab(%d,%d)"""
                   % (obj.ordem_compra_id.id, obj.cabimento_id.id))
        result = cr.fetchone()[0]
        if len(result) > 0:
            self.write(cr, uid, ids, {'message': result})
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        context['criar_compromisso'] = ids[0]
        return True

    def criar_compromisso(self, cr, uid, ids, context):
        self.usar_cabimento(cr, uid, ids, context)
        obj = self.browse(cr, uid, ids[0])
        db_sncp_despesa_compromisso = self.pool.get('sncp.despesa.compromisso')
        db_sncp_despesa_compromisso_ano = self.pool.get('sncp.despesa.compromisso.ano')

        values_compromisso = {
            'compromisso': '',
            'name': obj.name,
            'desc2': obj.desc2,
            'tipo': 'com',
            'ano_ini': unicode(date.today().year),
            'ano_fim': unicode(date.today().year),
            'partner_id': obj.ordem_compra_id.partner_id.id,
            'obsv': u'Compromisso criado automaticamente para satisfazer a ordem de compra ' +
                    obj.ordem_compra_id.name,
            'state': 'draft',
            'next': 2, }
        compromisso_id = db_sncp_despesa_compromisso.create(cr, uid, values_compromisso)
        values_ano = {
            'compromisso_id': compromisso_id,
            'ano': unicode(date.today().year),
            'cabimento_id': obj.cabimento_id.id,
            'name': '',
        }
        compromisso_ano_id = db_sncp_despesa_compromisso_ano.create(cr, uid, values_ano)

        # Criar linhas/ agenda
        cr.execute("""SELECT linhas_ordem_compra_compromisso(%d, %d)
        """ % (obj.ordem_compra_id.id, compromisso_ano_id))

        result = cr.fetchone()[0]
        if result is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Existem artigos que não têm associado código de contabilização'
                                                u' de natureza "Despesa Orçamental".'))

        cr.execute("""
        SELECT COALESCE(COUNT(COMP_LINHA.id),0)
        FROM sncp_despesa_compromisso AS COMP
        LEFT JOIN sncp_despesa_compromisso_ano AS COMP_ANO ON COMP_ANO.compromisso_id=%d
        LEFT JOIN sncp_despesa_compromisso_linha AS COMP_LINHA ON COMP_LINHA.compromisso_ano_id=COMP_ANO.id
        """ % compromisso_id)

        nlinhas = cr.fetchone()

        if nlinhas[0] == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'O compromisso não tem linhas.'))

        self.write(cr, uid, ids, {'state': 'comp', 'compromisso_id': compromisso_id,
                                  'message': u'Compromisso criado com sucesso.\n'
                                             u'Procede com a contabilização de compromisso.'})

        return self.contabilizar_compromisso(cr, uid, ids, context)

    def contabilizar_compromisso(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        db_sncp_despesa_compromisso = self.pool.get('sncp.despesa.compromisso')
        context['criar_compromisso'] = ids[0]
        return db_sncp_despesa_compromisso.call_diario(cr, uid, [obj.compromisso_id.id], context)

    def insere_relacao(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'comp_contab',
                                  'message': u'Ordem de compra '+obj.ordem_compra_id.name +
                                             u' vinculada ao compromisso '+obj.compromisso_id.compromisso +
                                             u'.'})
        db_sncp_despesa_compromisso_relacoes = self.pool.get('sncp.despesa.compromisso.relacoes')
        db_sncp_despesa_compromisso_relacoes.create(cr, uid, {
            'name': obj.compromisso_id.id,
            'purchase_order_id': obj.ordem_compra_id.id, })

        cr.execute("""UPDATE purchase_order SET compromisso_id = %d, state = 'vinc'
                      WHERE id = %d""" % (obj.compromisso_id.id, obj.ordem_compra_id.id))
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    _columns = {
        'ordem_compra_id': fields.many2one('purchase.order', u'Ordem de Compra'),
        'cabimento_id': fields.many2one('sncp.despesa.cabimento', u'Cabimento'),
        'compromisso_id': fields.many2one('sncp.despesa.compromisso', u'Compromisso'),
        'name': fields.char(u'Descrição', size=80),
        'desc2': fields.char(u'', size=80),
        'message': fields.text(u''),
        'state': fields.selection([('draft', u'Ordem de compra definida'),
                                   ('cab', u'Cabimento Criado'),
                                   ('cab_contab', u'Cabimento contabilizado'),
                                   ('comp', u'Compromisso Criado'),
                                   ('comp_contab', u'Compromisso Contabilizado')], u'Situação'),
    }

    def unlink(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        cr.execute("""UPDATE purchase_order SET state = 'draft'
                      WHERE id = %d""" % obj.ordem_compra_id.id)
        return super(sncp_despesa_cria_cab_com, self).unlink(cr, uid, ids)

    def create(self, cr, uid, vals, context=None):
        # Atualizar estado da ordem
        cr.execute("""UPDATE purchase_order SET state = 'selec'
                        WHERE id = %d""" % vals['ordem_compra_id'])
        return super(sncp_despesa_cria_cab_com, self).create(cr, uid, vals)

    _defaults = {
        'cabimento_id': False,
        'message': u'Indique Ordem de compra.',
        'state': 'draft',
    }

sncp_despesa_cria_cab_com()

# _________________________________________________Autorizações__________________________________


class sncp_despesa_autorizacoes(osv.Model):
    _name = 'sncp.despesa.autorizacoes'
    _description = u"Autorizações"

    def get_user_list_js(self, cr, uid):
        db_res_users = self.pool.get('res.users')
        cr.execute("""
        SELECT DISTINCT user_id
        FROM sncp_despesa_autorizacoes
        """)

        user_ids = cr.fetchall()
        user_ids = [elem[0] for elem in user_ids]
        return db_res_users.name_get(cr, uid, user_ids)

    _columns = {
        'user_id': fields.many2one('res.users', u'Utilizador'),
        'datahora': fields.datetime(u'Data e hora'),
        'tipo_doc': fields.selection([('reqi', u'Requisição Interna'),
                                      ('cabi', u'Cabimento'),
                                      ('comp', u'Compromisso'),
                                      ('ocmp', u'Ordem de Compra'),
                                      ('fact', u'Fatura de Compra'),
                                      ('ppag', u'Proposta de Pagamento'),
                                      ('opag', u'Ordem de Pagamento')], u'Tipo de documento'),
        'name': fields.char(u'Número de Documento', size=12),
        'RSA_signature': fields.char(u'Assinatura RSA', size=256),
        'doc_signature': fields.char(u'Assinatura do documento', size=256), }

sncp_despesa_autorizacoes()