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

from datetime import date, timedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _


class sncp_despesa_requisicoes_converter_wizard(osv.Model):
    _name = 'sncp.despesa.requisicoes.converter.wizard'
    _description = u"Formulário das Requisições"

    def wizard(self, cr, uid, ids, context=None):
        db_sncp_despesa_requisicoes_ordem_compra = self.pool.get('sncp.despesa.requisicoes.ordem.compra')
        obj_req_ord_comp = db_sncp_despesa_requisicoes_ordem_compra.browse(cr, uid, ids[0])
        db_sncp_despesa_requisicoes = self.pool.get('sncp.despesa.requisicoes')
        db_formulario_sncp_despesa_requisicoes_select = self.pool.get('formulario.sncp.despesa.requisicoes.select')

        # ___SUB-QUERYS___
        cr.execute("""
                    SELECT DRL.id
                    FROM sncp_despesa_requisicoes_linhas AS DRL
                    LEFT JOIN sncp_despesa_requisicoes AS DR ON DR.id = DRL.req_id
                    WHERE DRL.state='aprovd' AND (DR.name BETWEEN '%s' AND '%s')
                  """ % (obj_req_ord_comp.req_de_id.name, obj_req_ord_comp.req_ate_id.name))

        result1 = cr.fetchall()

        if len(result1) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existem linhas da requisição no estado aprovada.'))

        cr.execute("""
                SELECT DRL.id
                FROM sncp_despesa_requisicoes_linhas AS DRL
                LEFT JOIN sncp_despesa_requisicoes AS DR ON DR.id = DRL.req_id
                WHERE DRL.state='aprovd' AND (DR.name BETWEEN '%s' AND '%s') AND
                (DR.datahora BETWEEN '%s' AND '%s')
            """ % (obj_req_ord_comp.req_de_id.name, obj_req_ord_comp.req_ate_id.name,
                   obj_req_ord_comp.name, obj_req_ord_comp.data_ate))

        result3 = cr.fetchall()

        if len(result3) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não há requisições cuja data e hora esteja'
                                                u' dentro do intervalo selecionado.'))

        cr.execute("""
            SELECT DRL.id
            FROM sncp_despesa_requisicoes_linhas AS DRL
            LEFT JOIN sncp_despesa_requisicoes AS DR ON DR.id = DRL.req_id
            WHERE DRL.state='aprovd' AND (DR.name BETWEEN '%s' AND '%s') AND
            (DR.datahora BETWEEN '%s' AND '%s') AND
            (DR.requisitante_dep_id IN (SELECT id FROM hr_department AS HD WHERE compara_strings(HD.name,'%s')>=0
            AND compara_strings(HD.name,'%s')<=0))
                  """ % (obj_req_ord_comp.req_de_id.name, obj_req_ord_comp.req_ate_id.name,
                         obj_req_ord_comp.name, obj_req_ord_comp.data_ate,
                         obj_req_ord_comp.depart_de_id.name, obj_req_ord_comp.depart_ate_id.name))

        result4 = cr.fetchall()

        if len(result4) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Os departamentos das requisições não estão alfabeticamente '
                                                u'entre os nomes dos departamentos selecionados.'))

        cr.execute("""
            SELECT DRL.id
            FROM sncp_despesa_requisicoes_linhas AS DRL
            LEFT JOIN sncp_despesa_requisicoes AS DR ON DR.id = DRL.req_id
            WHERE DRL.state='aprovd' AND (DR.name BETWEEN '%s' AND '%s') AND
            (DR.datahora BETWEEN '%s' AND '%s') AND
            (DR.requisitante_dep_id IN (SELECT id FROM hr_department AS HD WHERE compara_strings(HD.name,'%s')>=0
            AND compara_strings(HD.name,'%s')<=0))
            AND DR.armazem_req_id=%d
                  """ % (obj_req_ord_comp.req_de_id.name, obj_req_ord_comp.req_ate_id.name,
                         obj_req_ord_comp.name, obj_req_ord_comp.data_ate,
                         obj_req_ord_comp.depart_de_id.name, obj_req_ord_comp.depart_ate_id.name,
                         obj_req_ord_comp.armazem_id.id))

        result5 = cr.fetchall()

        if len(result5) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existem requisições com o armazém selecionado.'))

        cr.execute("""
            SELECT DRL.req_id,DRL.name,DRL.item_id,DRL.uom_id,
                   COALESCE(DRL.quant_req,0.0)-COALESCE(DRL.quant_sat,0.0)
            FROM sncp_despesa_requisicoes_linhas AS DRL
            LEFT JOIN sncp_despesa_requisicoes AS DR ON DR.id = DRL.req_id
            WHERE DRL.state='aprovd' AND (DR.name BETWEEN '%s' AND '%s') AND
            (DR.datahora BETWEEN '%s' AND '%s') AND
            (DR.requisitante_dep_id IN (SELECT id FROM hr_department AS HD WHERE compara_strings(HD.name,'%s')>=0
            AND compara_strings(HD.name,'%s')<=0))
            AND DR.armazem_req_id=%d AND (DRL.item_id IN
            (SELECT product_id FROM product_supplierinfo WHERE name=%d))
                  """ % (obj_req_ord_comp.req_de_id.name, obj_req_ord_comp.req_ate_id.name,
                         obj_req_ord_comp.name, obj_req_ord_comp.data_ate,
                         obj_req_ord_comp.depart_de_id.name, obj_req_ord_comp.depart_ate_id.name,
                         obj_req_ord_comp.armazem_id.id, obj_req_ord_comp.fornecedor_id.id, ))

        requisicoes_linhas = cr.fetchall()

        if len(requisicoes_linhas) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Os artigos das linhas das requisições '
                                                u'não estão associados ao '
                                                u'fornecedor escolhido.\n'
                                                u'Sugestão: nos artigos crie a associação ao '
                                                u'fornecedor selecionado (separador Procurements).'))

        cr.execute("""
            SELECT DRL.req_id,DRL.name,DRL.item_id,DRL.uom_id,
                   COALESCE(DRL.quant_req,0.0)-COALESCE(DRL.quant_sat,0.0)
            FROM sncp_despesa_requisicoes_linhas AS DRL
            LEFT JOIN sncp_despesa_requisicoes AS DR ON DR.id = DRL.req_id
            WHERE DRL.state='aprovd' AND (DR.name BETWEEN '%s' AND '%s') AND
            (DR.datahora BETWEEN '%s' AND '%s') AND
            (DR.requisitante_dep_id IN (SELECT id FROM hr_department AS HD WHERE compara_strings(HD.name,'%s')>=0
            AND compara_strings(HD.name,'%s')<=0))
            AND DR.armazem_req_id=%d AND (DRL.item_id IN
            (SELECT product_id FROM product_supplierinfo WHERE name=%d))
                  """ % (obj_req_ord_comp.req_de_id.name, obj_req_ord_comp.req_ate_id.name,
                         obj_req_ord_comp.name, obj_req_ord_comp.data_ate,
                         obj_req_ord_comp.depart_de_id.name, obj_req_ord_comp.depart_ate_id.name,
                         obj_req_ord_comp.armazem_id.id, obj_req_ord_comp.fornecedor_id.id, ))

        requisicoes_linhas = cr.fetchall()

        nid = self.create(cr, uid, {'goc_id': ids[0]})

        for requisicao_linha in requisicoes_linhas:
            obj_requisicao = db_sncp_despesa_requisicoes.browse(cr, uid, requisicao_linha[0])
            vals = {'form_id': nid,
                    'requisicao_id': requisicao_linha[0],
                    'name': requisicao_linha[1],
                    'departamento_id': obj_requisicao.requisitante_dep_id.id,
                    'item_id': requisicao_linha[2],
                    'uom_id': requisicao_linha[3],
                    'quant_req': requisicao_linha[4], }

            db_formulario_sncp_despesa_requisicoes_select.create(cr, uid, vals)

        return {'name': u'<div style="width:500px;">Seleciona as Linhas\'s pretendidas</div>',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'sncp.despesa.requisicoes.converter.wizard',
                'nodestroy': True,
                'target': 'new',
                'res_id': nid, }

    def descartar(self, cr, uid, ids, context=None):
        db_formulario_requisicoes_despesa_select = self.pool.get('formulario.sncp.despesa.requisicoes.select')
        select_ids = db_formulario_requisicoes_despesa_select.search(cr, uid, [('form_id', '=', ids[0])])

        if len(select_ids) != 0:
            db_formulario_requisicoes_despesa_select.unlink(cr, uid, select_ids, context)

        self.unlink(cr, uid, ids)
        return True

    def continuar(self, cr, uid, ids, context=None):
        db_purchase_order = self.pool.get('purchase.order')
        db_purchase_order_line = self.pool.get('purchase.order.line')
        db_sncp_despesa_requisicoes_linha = self.pool.get('sncp.despesa.requisicoes.linhas')
        db_sncp_despesa_requisicoes = self.pool.get('sncp.despesa.requisicoes')
        db_ir_sequence = self.pool.get('ir.sequence')
        db_product_product = self.pool.get('product.product')

        obj = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT id FROM formulario_sncp_despesa_requisicoes_select AS DRS
             WHERE DRS.form_id=%d AND DRS.selecionada = TRUE
        """ % obj.id)

        linhas = cr.fetchall()

        if len(linhas) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Selecione pelo menos uma linha.'))

        # PREENCHIMENTO DO CABEÇALHO DA ORDEM DE COMPRA

        # 1. PREENCHIMENTO DA ORIGEM COM O NUMERO DAS REQUISIÇÕES
        cr.execute("""
            SELECT DR.name
            FROM sncp_despesa_requisicoes AS DR WHERE id IN
            (SELECT DISTINCT DRS.requisicao_id FROM formulario_sncp_despesa_requisicoes_select AS DRS
             WHERE DRS.form_id=%d AND DRS.selecionada = TRUE )
        """ % obj.id)

        nomes_req = cr.fetchall()
        origem = u''

        for nome in nomes_req:
            if len(origem+nome[0]+u'/') < 64:
                origem += nome[0]+u'/'
            else:
                break

        if len(origem) == 0:
            origem = None

        # 2. PREENCHIMENTO DO DIÁRIO DE COMPRA
        cr.execute("""
            SELECT id
            FROM account_journal
            WHERE type ='purchase'
            LIMIT 1
        """)

        diario_id = cr.fetchone()
        if diario_id is not None:
            diario_id = diario_id[0]
        else:
            diario_id = False

        # 3. DATA DO SISTEMA
        data = date.today()

        # 4. PARCEIRO DE NEGÓCIOS
        parceiro_id = obj.goc_id.fornecedor_id.id

        # 5. ENDEREÇO DESTINO
        endereco_destino = obj.goc_id.armazem_id.partner_id.id

        # 6. LOCALIZAÇÃO
        localizacao_id = obj.goc_id.armazem_id.lot_input_id.id

        # 7. COMPANHIA
        companhia_id = obj.goc_id.fornecedor_id.company_id.id

        if companhia_id is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina companhia para o fornecedor '
                                                + unicode(obj.goc_id.fornecedor_id.name)
                                                + u'.'))

        # 8. ESTADO
        estado = 'draft'

        # 9. ARMAZÉM
        armazem_id = obj.goc_id.armazem_id.id

        # 10. TERMOS DE PAGAMENTO
        termo_pagamento_id = obj.goc_id.fornecedor_id.property_payment_term.id

        # 11. NOME
        cr.execute("""
            SELECT res_id
            FROM ir_model_data
            WHERE name='seq_purchase_order'
        """)

        sequencia_id = cr.fetchone()

        if sequencia_id is not None:
            nome = db_ir_sequence.next_by_id(cr, uid, sequencia_id)
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existe sequência de nome "seq_purchase_order" '
                                                u'no dados do modelo (ir_model_data).'))

        # 12. NOTAS
        cr.execute("""
            SELECT string_agg(justificacao,' ')
            FROM sncp_despesa_requisicoes
            WHERE id IN (SELECT DISTINCT DRS.requisicao_id FROM formulario_sncp_despesa_requisicoes_select AS DRS
             WHERE DRS.form_id=%d AND DRS.selecionada = TRUE )
            """ % obj.id)

        notas = cr.fetchone()

        if notas is not None:
            notas = notas[0]
        else:
            notas = None

        # 16. MÉTODO DA FATURA
        metodo_fatura = 'picking'

        # 17. EMBARCADO
        embarcado = False

        cr.execute("""
                SELECT id
                FROM product_pricelist
                WHERE type='purchase'
        """)

        lista_preco_id = cr.fetchone()

        if lista_preco_id is not None:
            lista_preco_id = lista_preco_id[0]
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existe lista de preços de artigo de tipo "purchase" '
                                                u'na lista de preços de artigo (product_pricelist).'))

        cabecalho = {'origin': origem,
                     'journal_id': diario_id,
                     'date_order': data,
                     'partner_id': parceiro_id,
                     'dest_address_id': endereco_destino,
                     'location_id': localizacao_id,
                     'company_id': companhia_id,
                     'state': estado,
                     'warehouse_id': armazem_id,
                     'payment_term_id': termo_pagamento_id,
                     'name': nome,
                     'notes': notas,
                     'invoice_method': metodo_fatura,
                     'shipped': embarcado,
                     'pricelist_id': lista_preco_id, }

        ordem_compra_id = db_purchase_order.create(cr, uid, cabecalho)

        # PREENCHIMENTO DAS LINHAS DA ORDEM DE COMPRA
        cr.execute("""
            SELECT item_id,SUM(quant_req)
            FROM formulario_sncp_despesa_requisicoes_select AS DRS
            WHERE DRS.form_id=%d AND DRS.selecionada=TRUE
            GROUP BY item_id
        """ % obj.id)

        linhas = cr.fetchall()

        for linha in linhas:
            produto = db_product_product.browse(cr, uid, linha[0])

            cr.execute("""
            SELECT MAX(delay)
            FROM product_supplierinfo
            WHERE name=%d AND product_id=%d
            """ % (obj.goc_id.fornecedor_id.id, produto.id))

            dias_de_atraso = cr.fetchone()

            if dias_de_atraso is None:
                data_planeada = data
            else:
                data_planeada = data + timedelta(days=dias_de_atraso[0])

            rodape = {'product_uom': produto.product_tmpl_id.uom_id.id,
                      'order_id': ordem_compra_id,
                      'price_unit': produto.product_tmpl_id.standard_price,
                      'product_qty': linha[1],
                      'partner_id': parceiro_id,
                      'invoiced': False,
                      'name': u'['+unicode(produto.default_code)+u'] '+unicode(produto.name_template),
                      'date_planned': data_planeada,
                      'state': 'draft',
                      'product_id': produto.id, }

            ordem_compra_linha_id = db_purchase_order_line.create(cr, uid, rodape)

            cr.execute("""SELECT tax_id FROM product_taxes_rel WHERE prod_id = %d""" % produto.id)
            taxa_id = cr.fetchone()

            if taxa_id is not None:
                taxa_id = taxa_id[0]

                cr.execute("""
                INSERT INTO purchase_order_taxe(ord_id,tax_id)
                VALUES (%d,%d)
                """ % (ordem_compra_linha_id, taxa_id))
                db_purchase_order_line.write(cr, uid, ordem_compra_linha_id, {'taxes_id': [(6, 0, [taxa_id])]})

        # ____LINHAS CONVERTIDAS____

        cr.execute("""
            SELECT DRS.requisicao_id,DRS.name
            FROM formulario_sncp_despesa_requisicoes_select AS DRS
            WHERE DRS.form_id=%d AND DRS.selecionada=TRUE
        """ % obj.id)

        linhas = cr.fetchall()

        for linha in linhas:
            req_linhas_id = db_sncp_despesa_requisicoes_linha.search(cr, uid, [('req_id', '=', linha[0]),
                                                                               ('name', '=', linha[1])])
            db_sncp_despesa_requisicoes_linha.write(cr, uid, req_linhas_id[0], {'state': 'convrt'})

        # ____REQUISIÇÃO COMPLETA_____
        cr.execute("""
        SELECT DISTINCT DRS.requisicao_id
        FROM formulario_sncp_despesa_requisicoes_select AS DRS
        WHERE DRS.form_id=%d AND DRS.selecionada=TRUE
        """ % obj.id)

        req_ids = cr.fetchall()

        for req_id in req_ids:
            db_sncp_despesa_requisicoes.completar(cr, uid, [req_id[0]], context=context)

        ###############################################################################
        cr.execute("""
        DELETE FROM formulario_sncp_despesa_requisicoes_select
        WHERE form_id=%d
        """ % obj.id)

        cr.execute("""
        DELETE FROM sncp_despesa_requisicoes_converter_wizard
        WHERE id=%d
        """ % obj.id)

        return self.pool.get('formulario.mensagem.despesa').wizard(cr, uid, ids,
                                                                   u'Criada a Ordem de Compra '+unicode(nome))

    _columns = {
        'goc_id': fields.many2one('sncp.despesa.requisicoes.ordem.compra', u''),
        'select_ids': fields.one2many('formulario.sncp.despesa.requisicoes.select', 'form_id'),
    }

sncp_despesa_requisicoes_converter_wizard()


class formulario_sncp_despesa_requisicoes_select(osv.Model):
    _name = 'formulario.sncp.despesa.requisicoes.select'
    _description = u"Linhas do Formulário de Requisições"

    _columns = {'form_id': fields.many2one('sncp.despesa.requisicoes.converter.wizard'),
                'requisicao_id': fields.many2one('sncp.despesa.requisicoes', u'Requisição'),
                'name': fields.integer(u'Linha'),
                'departamento_id': fields.many2one('hr.department', u'Departamento'),
                'item_id': fields.many2one('product.product', u'Item'),
                'quant_req': fields.float(u'Quantidade requisitada', digits=(12, 3)),
                'uom_id': fields.many2one('product.uom', u'Unidade'),
                'selecionada': fields.boolean(u'Selecionada'), }

    def unlink(self, cr, uid, ids, context=None):
        return super(formulario_sncp_despesa_requisicoes_select, self).unlink(cr, uid, ids)

    _order = 'departamento_id,requisicao_id,name'

formulario_sncp_despesa_requisicoes_select()