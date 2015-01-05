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


class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    def teste_existencia_account_invoice(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'da_linha_compromisso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_da_linha_compromisso(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'da_dimensoes_codigos_contab'""")
        result = cr.fetchone()
        if result is None:
            self.sql_da_dimensoes_codigos_contab(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'atualiza_linhas_fatura'""")
        result = cr.fetchone()
        if result is None:
            self.sql_atualiza_linhas_fatura(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fu_extenso_euro'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fu_extenso_euro(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fu_extenso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fu_extenso(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fu_extenso_blk'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fu_extenso_blk(cr)

        return True

    def aprovar(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state': 'approved'})
        db_sncp_despesa_faturas_aprovadas = self.pool.get('sncp.despesa.faturas.aprovadas')
        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]
        values_aprovadas = {
            'invoice_id': ids[0],
            'user_id': uid,
            'datahora': datahora,
            'name': obj.origin,
        }
        db_sncp_despesa_faturas_aprovadas.create(cr, uid, values_aprovadas)

        db_sncp_despesa_autorizacoes = self.pool.get('sncp.despesa.autorizacoes')
        values_autorizacoes = {
            'user_id': uid,
            'datahora': datahora,
            'tipo_doc': 'fact',
            'name': obj.internal_number,
        }
        db_sncp_despesa_autorizacoes.create(cr, uid, values_autorizacoes)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def get_lista_faturas_js(self, cr, uid):
        # Seleccionar aprovadores
        cr.execute("""SELECT departamento_id, name, fim, limite_fat
                    FROM sncp_despesa_aprovadores
                    WHERE faturas = TRUE AND
                    aprovador_id IN (SELECT id FROM hr_employee
                    WHERE resource_id IN (SELECT id FROM resource_resource WHERE user_id = %d ))
                    """ % uid)
        aprovadores = cr.fetchall()
        lista_faturas = []

        # Lista de faturas
        for aprovador in aprovadores:
            cr.execute("""SELECT AI.id
                          FROM account_invoice AS AI
                          WHERE AI.date_invoice BETWEEN '%s' AND '%s' AND
                            AI.department_id = %d AND
                            AI.type='in_invoice' AND
                            AI.state = 'open' AND
                            AI.amount_total <= %d AND
                            AI.id NOT IN (SELECT invoice_id FROM sncp_despesa_faturas_aprovadas) AND
                            AI.id IN (SELECT fatura_id FROM sncp_despesa_compromisso_relacoes_faturas)
            """ % (aprovador[1], aprovador[2], aprovador[0], aprovador[3]))
            lista = cr.fetchall()

            for line in lista:
                lista_faturas.append(line[0])

        if len(lista_faturas) == 0:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Não há nenhuma Fatura para aprovar'
                                   u' entre as datas, departamentos e valores máximos definidos'
                                   u' em Despesa/Dados Gerais/Aprovadores.'))

        return lista_faturas

    _columns = {
        'invoice_line_dim': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines', readonly=True,
                                            states={'draft': [('readonly', False)]}),
        'state': fields.selection([
            ('draft', 'Draft'), ('proforma', 'Pro-forma'), ('proforma2', 'Pro-forma'), ('open', 'Open'),
            ('approved', 'Aproved'), ('paid', 'Paid'), ('cancel', 'Cancelled'), ], 'Status', select=True, readonly=True,
            track_visibility='onchange',
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Pro-forma\' when invoice is in Pro-forma status,invoice does not have an invoice number. \
            \n* The \'Open\' status is used when user create invoice,a invoice number is generated.Its in open status '
                 'till user does not pay invoice. \
            \n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or '
                 'may not be reconciled. \
            \n* The \'Cancelled\' status is used when user cancel invoice.'),
    }

    def sql_da_dimensoes_codigos_contab(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION da_dimensoes_codigos_contab(produto integer,out organica integer,
        out economica integer,out funcional integer) AS $$
        BEGIN
        organica=(SELECT organica_id FROM sncp_comum_codigos_contab WHERE natureza='des' and item_id=$1 LIMIT 1);
        economica=(SELECT economica_id FROM sncp_comum_codigos_contab WHERE natureza='des' and item_id=$1 LIMIT 1);
        funcional=(SELECT funcional_id FROM sncp_comum_codigos_contab WHERE natureza='des' and item_id=$1 LIMIT 1);
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_da_linha_compromisso(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION da_linha_compromisso(compromisso_id integer,org integer,eco integer,
        fun integer,ano integer) RETURNS integer AS $$
        DECLARE
          compromisso_ano sncp_despesa_compromisso_ano%ROWTYPE;
          comp_linha_id integer;
        BEGIN
          FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO
          WHERE COMPANO.compromisso_id=$1 AND COMPANO.ano=$5) LOOP
              comp_linha_id=(COALESCE(
              (SELECT id FROM sncp_despesa_compromisso_linha AS COMPLINHA
               WHERE COMPLINHA.compromisso_ano_id=compromisso_ano.id AND economica_id=$3 AND
            (
                 (($2 IS NULL AND $4 IS NULL) AND (COMPLINHA.organica_id IS NULL AND COMPLINHA.funcional_id IS NULL)) OR
                (($2 IS NULL AND $4 IS NOT NULL) AND (COMPLINHA.organica_id IS NULL AND COMPLINHA.funcional_id = $4)) OR
                 (($2 IS NOT NULL AND $4 IS NULL) AND (COMPLINHA.organica_id =$2 AND COMPLINHA.funcional_id IS NULL)) OR
                 (($2 IS NOT NULL AND $4 IS NOT NULL) AND (COMPLINHA.organica_id = $2 and COMPLINHA.funcional_id = $4))
                )
             ),0));
             IF comp_linha_id > 0 THEN
            RETURN comp_linha_id;
             END IF;

          END LOOP;
          RETURN 0;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_atualiza_linhas_fatura(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION atualiza_linhas_fatura(invoice_id integer,ano_atual integer) RETURNS VARCHAR AS $$
        DECLARE
          linha_fatura account_invoice_line%ROWTYPE;
          dados RECORD;
          compromisso_id integer;
          compromisso_linha_id integer;
        BEGIN
          FOR linha_fatura IN (SELECT * FROM account_invoice_line AS AIL WHERE AIL.invoice_id=$1) LOOP
            dados=da_dimensoes_codigos_contab(linha_fatura.product_id);
            IF dados.organica IS NULL AND dados.economica IS NULL AND dados.funcional IS NULL THEN
               RETURN 'Não existe código de contabilização de natureza despesa orçamental
               associado ao produto ' ||
               (SELECT name_template FROM product_product WHERE id=linha_fatura.product_id);
            END IF;
            compromisso_id=(SELECT COMPREL.name FROM sncp_despesa_compromisso_relacoes AS COMPREL
            WHERE id = (SELECT compromisso_relacoes_id FROM sncp_despesa_compromisso_relacoes_faturas
                        WHERE fatura_id=$1));
            compromisso_linha_id=da_linha_compromisso(compromisso_id,
            dados.organica,dados.economica,dados.funcional,ano_atual);
            IF compromisso_linha_id < 1 THEN
              RETURN 'O artigo com o código ' || (SELECT default_code FROM product_product
                       WHERE id=linha_fatura.product_id) || ' com as respetivas classificações
                       não têm correspondência nas linhas do compromisso';
            END IF;

            UPDATE account_invoice_line SET
            organica_id=dados.organica,
            economica_id=dados.economica,
            funcional_id=dados.funcional,
            linha_compromisso_id = compromisso_linha_id
            WHERE id=linha_fatura.id;

          END LOOP;
          RETURN '';
        END;
        $$LANGUAGE plpgsql;
        """)
        return True

    def sql_fu_extenso_euro(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION fu_extenso_euro(num numeric(20,2)) returns text as $$
        DECLARE
           val_extenso text;
           resultado text;
        BEGIN
          val_extenso=fu_extenso($1,'euro','euros');
          resultado=upper(substring( val_extenso from 1 for 1)) || lower(substring( val_extenso from 2 ));
          return resultado;
        END;
        $$ LANGUAGE plpgsql
           IMMUTABLE
           RETURNS NULL ON NULL INPUT ;
        """)
        return True

    def sql_fu_extenso(self, cr):
        cr.execute("""
        CREATE or replace FUNCTION fu_extenso(num numeric(20,2) , moeda text , moedas text) returns text as $$
        declare
        w_int char(21) ;
        x integer ;
        v integer ;
        w_ret text ;
        w_ext text ;
        w_apoio text ;
        m_cen text[] := array['quatrilião','quatriliões','trilião','triliões','bilião','biliões','milhão','milhões',
        'mil','mil'] ;
        begin
          w_ret := '' ;
          w_int := to_char(num * 100 , 'fm000000000000000000 00') ;
          for x in 1..5 loop
              v := cast(substr(w_int,(x-1)*3 + 1,3) as integer) ;
              if v > 0 then
                 if v > 1 then
                    w_ext := m_cen[(x-1)*2+2] ;
                   else
                    w_ext := m_cen[(x-1)*2+1] ;
                 end if ;
                 w_ret := w_ret || fu_extenso_blk(substr(w_int,(x-1)*3 + 1,3)) || ' ' || w_ext ||' ' ;
              end if ;
          end loop ;
          v := cast(substr(w_int,16,3) as integer) ;
          if v > 0 then
             if v > 1 then
                w_ext := moedas ;
               else
                if w_ret = '' then
                   w_ext := moeda ;
                  else
                   w_ext := moedas ;
                end if ;
             end if ;
             w_apoio := fu_extenso_blk(substr(w_int,16,3)) || ' ' || w_ext ;
             if w_ret = '' then
                w_ret := w_apoio ;
               else
                if v > 100 then
                   if w_ret = '' then
                      w_ret := w_apoio ;
                     else
                      w_ret := w_ret || w_apoio ;
                   end if ;
                  else
                   w_ret := btrim(w_ret,', ') || ' e ' || w_apoio ;
                end if ;
             end if ;
            else
             if w_ret <> '' then
                if substr(w_int,13,6) = '000000' then
                   w_ret := btrim(w_ret,', ') || ' de ' || moedas ;
                  else
                   w_ret := btrim(w_ret,', ') || ' ' || moedas ;
                end if ;
             end if ;
          end if ;
          v := cast(substr(w_int,20,2) as integer) ;
          if v > 0 then
             if v > 1 then
                w_ext := 'cêntimos' ;
               else
                w_ext := 'cêntimo' ;
             end if ;
             w_apoio := fu_extenso_blk('0'||substr(w_int,20,2)) || ' ' || w_ext ;
             if w_ret = '' then
                w_ret := w_apoio  || ' de ' || moeda;
               else
                w_ret := w_ret || ' e ' || w_apoio ;
             end if ;
          end if ;
          return w_ret ;
        end ;
        $$ LANGUAGE plpgsql
           IMMUTABLE
           RETURNS NULL ON NULL INPUT ;
        """)
        return True

    def sql_fu_extenso_blk(self, cr):
        cr.execute("""
        CREATE or replace FUNCTION fu_extenso_blk(num char(3)) returns text as $$
        declare
        w_cen integer ;
        w_dez integer ;
        w_dez2 integer ;
        w_uni integer ;
        w_tcen text ;
        w_tdez text ;
        w_tuni text ;
        w_ext text ;
        m_cen text[] := array['','cento','duzentos','trezentos','quatrocentos','quinhentos','seiscentos','setecentos',
        'oitocentos','novecentos'];
        m_dez text[] := array['','dez','vinte','trinta','quarenta','cinquenta','sessenta','setenta','oitenta'
        ,'noventa'] ;
        m_uni text[] := array['','um','dois','três','quatro','cinco','seis','sete','oito','nove','dez','onze','doze',
        'treze','catorze','quinze','dezasseis','dezassete','dezoito','dezanove'] ;
        begin
          w_cen := cast(substr(num,1,1) as integer) ;
          w_dez := cast(substr(num,2,1) as integer) ;
          w_dez2 := cast(substr(num,2,2) as integer) ;
          w_uni := cast(substr(num,3,1) as integer) ;
          if w_cen = 1 and w_dez2 = 0 then
             w_tcen := 'Cem' ;
             w_tdez := '' ;
             w_tuni := '' ;
            else
             if w_dez2 < 20 then
                w_tcen := m_cen[w_cen + 1] ;
                w_tdez := m_uni[w_dez2 + 1] ;
                w_tuni := '' ;
               else
                w_tcen := m_cen[w_cen + 1] ;
                w_tdez := m_dez[w_dez + 1] ;
                w_tuni := m_uni[w_uni + 1] ;
             end if ;
          end if ;
          w_ext := w_tcen ;
          if w_tdez <> '' then
             if w_ext = '' then
                w_ext := w_tdez ;
               else
                w_ext := w_ext || ' e ' || w_tdez ;
             end if ;
          end if ;
          if w_tuni <> '' then
             if w_ext = '' then
                w_ext := w_tuni ;
               else
                w_ext := w_ext || ' e ' || w_tuni ;
             end if ;
          end if ;
          return w_ext ;
        end ;
        $$ LANGUAGE plpgsql
           IMMUTABLE
           RETURNS NULL ON NULL INPUT ;
        """)
        return True

    def create(self, cr, uid, vals, context=None):
        self.teste_existencia_account_invoice(cr)
        return super(account_invoice, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            if obj.state == 'approved':
                raise osv.except_osv(_(u'Aviso'), _(u'Faturas aprovadas não podem ser eliminadas.'))

        return super(account_invoice, self).unlink(cr, uid, ids, context=context)

account_invoice()


class account_invoice_line(osv.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'linha_compromisso_id': fields.many2one('sncp.despesa.compromisso.linha', u'Linha do compromisso')
    }

account_invoice_line()


class stock_move(osv.Model):
    _inherit = 'stock.move'

    _columns = {
        'req_id': fields.many2one('sncp.despesa.requisicoes', u'Requisição'),
        'req_linha_id': fields.many2one('sncp.despesa.requisicoes.linhas', u'Linhas da requisição'),
    }

stock_move()


class hr_department(osv.Model):
    _inherit = 'hr.department'

    _columns = {
        'location_id': fields.many2one('stock.location', u'Localização'),
    }

hr_department()


class purchase_order(osv.Model):
    _inherit = 'purchase.order'

    # From standart 7
    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id):
        if not warehouse_id:
            return {}
        warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id)
        return {'value':{'location_id': warehouse.lot_input_id.id, 'dest_address_id': False}}

    def vincular(self, cr, uid, ids, context):
        return self.pool.get('formulario.ordem.compra.select.compromisso').wizard(cr, uid, ids, context)

    def teste_existencia_purchase_order(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'dados_linha_compromisso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_dados_linha_compromisso(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'calcula_iva'""")
        result = cr.fetchone()
        if result is None:
            self.sql_calcula_iva(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'valida_montante_oc'""")
        result = cr.fetchone()
        if result is None:
            self.sql_valida_montante_oc(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'vincula_ordem_compra'""")
        result = cr.fetchone()
        if result is None:
            self.sql_vincula_ordem_compra(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'linhas_ordem_compra_cabimento'""")
        result = cr.fetchone()
        if result is None:
            self.sql_linhas_ordem_compra_cabimento(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'linhas_ordem_compra_compromisso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_linhas_ordem_compra_compromisso(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'calcula_last_util_mes'""")
        result = cr.fetchone()
        if result is None:
            self.sql_calcula_last_util_mes(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'calcula_iva_purchase_order_line'""")
        result = cr.fetchone()
        if result is None:
            self.sql_calcula_iva_purchase_order_line(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'dados_linha_cabimento'""")
        result = cr.fetchone()
        if result is None:
            self.sql_dados_linha_cabimento(cr)
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'valida_soma_totais_oc_cab'""")
        result = cr.fetchone()
        if result is None:
            self.sql_valida_soma_totais_oc_cab(cr)

        return True

    def verificar_comportamento(self, cr, uid, ids, comp_id):
        ano = date.today().year
        cr.execute("""SELECT valida_montante_oc(%d, %d, %d)""" % (ids[0], comp_id, ano))
        mensagem = cr.fetchone()[0]
        if len(mensagem) != 0:
            raise osv.except_osv(_(u'Aviso'), _(unicode(mensagem)))

        cr.execute("""SELECT vincula_ordem_compra(%d, %d, %d)""" % (ids[0], comp_id, ano))
        mensagem = cr.fetchone()[0]
        if len(mensagem) != 0:
            raise osv.except_osv(_(u'Aviso'), _(unicode(mensagem)))

        self.pool.get('sncp.despesa.compromisso.relacoes').create(cr, uid, {
            'name': comp_id,
            'purchase_order_id':  ids[0]})
        self.write(cr, uid, ids, {'compromisso_id': comp_id, 'state': 'vinc'})
        return True

    def desvincular(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'compromisso_id': False, 'state': 'draft'})
        cr.execute(""" DELETE FROM sncp_despesa_compromisso_relacoes
                    WHERE purchase_order_id = %d""" % ids[0])
        return True

    # Add new value to selection state
    def __init__(self, pool, cr):
        """Add a new state value"""
        super(purchase_order, self).STATE_SELECTION.append(('selec', u'Seleccionada'))
        super(purchase_order, self).STATE_SELECTION.append(('vinc', u'Vinculada'))
        super(purchase_order, self).__init__(pool, cr)

    def cancelar(self, cr, uid, ids, context):
        return self.pool.get('purchase_order').action_cancel(cr, uid, ids)

    def inserir_autorizacao(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        db_sncp_despesa_autorizacoes = self.pool.get('sncp.despesa.autorizacoes')
        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]
        values_autorizacao = {
            'user_id': uid,
            'datahora': datahora,
            'tipo_doc': 'ocmp',
            'name': obj.name,
        }
        db_sncp_despesa_autorizacoes.create(cr, uid, values_autorizacao)
        return True

    def get_lista_ordem_compra_js(self, cr, uid):
        # Seleccionar aprovadores
        cr.execute("""SELECT departamento_id, name, fim, limite_comp
                    FROM sncp_despesa_aprovadores
                    WHERE compras = TRUE AND
                    aprovador_id IN (SELECT id FROM hr_employee
                    WHERE resource_id IN (SELECT id FROM resource_resource WHERE user_id = %d ))
                    """ % uid)
        aprovadores = cr.fetchall()
        lista_oc = []

        # Lista de ordens de compra
        for aprovador in aprovadores:
            cr.execute("""SELECT PO.id
                          FROM purchase_order AS PO
                          LEFT JOIN stock_warehouse AS W ON W.id=PO.warehouse_id
                          WHERE PO.date_order BETWEEN '%s' AND '%s' AND
                            W.department_id = %d AND
                            PO.state = 'vinc' AND
                            (SELECT SUM(product_qty * price_unit  * (1 + calcula_iva_purchase_order_line(id)))
                                FROM purchase_order_line
                                WHERE order_id = PO.id) <= %d
            """ % (aprovador[1], aprovador[2], aprovador[0], aprovador[3]))
            lista = cr.fetchall()

            for line in lista:
                lista_oc.append(line[0])

        if len(lista_oc) == 0:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Para este aprovador não há nenhuma Ordem de Compra para aprovar'
                                   u' entre as datas, departamentos e valores máximos definidos'
                                   u' em Despesa/Dados Gerais/Aprovadores.'))
        return lista_oc

    _columns = {
        'compromisso_id': fields.many2one('sncp.despesa.compromisso', u'Vinculado ao compromisso'),
        'warehouse_id': fields.many2one('stock.warehouse', u'Armazem'),
        }

    def sql_dados_linha_compromisso(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION dados_linha_compromisso(comp_id integer,ano integer,organica_id integer,
        economica_id integer,funcional_id integer,out montante numeric,out linha integer,out comp_linha_id integer)
        AS $$
        DECLARE
            linha_comp sncp_despesa_compromisso_linha%ROWTYPE;
            ano_id integer;
        BEGIN
        ano_id=(SELECT id FROM sncp_despesa_compromisso_ano AS COMP_ANO WHERE COMP_ANO.compromisso_id=$1 AND
        COMP_ANO.ano=$2);
        SELECT * INTO linha_comp FROM sncp_despesa_compromisso_linha AS COMP_LINHA
            WHERE COMP_LINHA.compromisso_ano_id=ano_id AND
               (($3 IS NULL AND COMP_LINHA.organica_id IS NULL) OR ($3 IS NOT NULL AND COMP_LINHA.organica_id=$3)) AND
               (($4 IS NULL AND COMP_LINHA.economica_id IS NULL) OR ($4 IS NOT NULL AND COMP_LINHA.economica_id=$4)) AND
               (($5 IS NULL AND COMP_LINHA.funcional_id IS NULL) OR ($5 IS NOT NULL AND COMP_LINHA.funcional_id=$5));
        montante=COALESCE(linha_comp.montante,0.0);
        linha=COALESCE(linha_comp.linha,0);
        comp_linha_id=COALESCE(linha_comp.id,0);
        END
        $$ LANGUAGE PLPGSQL;
        """)
        return True

    def sql_calcula_iva(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION calcula_iva(prod_id integer) RETURNS numeric AS
        $$
        BEGIN
        RETURN COALESCE((SELECT amount
            FROM account_tax AS AT
            LEFT JOIN product_taxes_rel AS PTR ON PTR.tax_id=AT.id
            WHERE PTR.prod_id=$1
            ),0.0);
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_valida_montante_oc(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION valida_montante_oc(ordem_compra_id integer,compromisso_id integer,ano integer)
        RETURNS varchar AS $$
        DECLARE
            PO_CCC RECORD;
            dados_linha RECORD;
            dim1 varchar;
            dim2 varchar;
            dim3 varchar;
            mensagem varchar='';
        BEGIN
          FOR PO_CCC IN
            (SELECT SUM( linhas.linha_val) AS total,linhas.organica_id,linhas.economica_id,
              linhas.funcional_id
           FROM (SELECT SUM((product_qty*price_unit)*(1+calcula_iva(product_id)))
                        AS linha_val,
                         CCC.organica_id,CCC.economica_id,CCC.funcional_id
                        FROM purchase_order_line AS POL
                        LEFT JOIN sncp_comum_codigos_contab AS CCC
                        ON CCC.item_id=POL.product_id
                        WHERE order_id=$1 and CCC.natureza='des'
                        GROUP BY CCC.organica_id,CCC.economica_id,CCC.funcional_id) AS linhas
             GROUP BY linhas.organica_id,linhas.economica_id,linhas.funcional_id)
             LOOP
            dados_linha=dados_linha_compromisso($2,$3,PO_CCC.organica_id,
        PO_CCC.economica_id,PO_CCC.funcional_id);
            IF dados_linha.linha < 1 THEN
               dim1=(SELECT code FROM account_analytic_account WHERE id=PO_CCC.organica_id);
               dim2=(SELECT code FROM account_analytic_account WHERE id=PO_CCC.economica_id);
               dim3=(SELECT code FROM account_analytic_account WHERE id=PO_CCC.funcional_id);

               mensagem='Não há linha do compromisso com as classificações Orgânica(' ||
                COALESCE(dim1,'')||')/ Económica(' || COALESCE(dim2,'') ||')/ Funcional('||
                COALESCE(dim3,'')||')';
               RETURN mensagem;
            END IF;
            IF dados_linha.montante < PO_CCC.total THEN
              mensagem='A linha ' || dados_linha.linha || ' do compromisso não cobre o valor de '||
              to_char(dados_linha.montante,'999G999G999G9990D00');
              RETURN mensagem;
            END IF;
             END LOOP;
        RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_vincula_ordem_compra(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION vincula_ordem_compra(ordem_compra_id integer,compromisso_id integer,ano integer)
        RETURNS VARCHAR AS $$
        DECLARE
          PO_CCC RECORD;
          produto varchar;
          dados_linha RECORD;
        BEGIN
        FOR PO_CCC IN (SELECT POL.id,POL.product_id,CCC.organica_id,CCC.economica_id,CCC.funcional_id
                   FROM purchase_order_line	AS POL
                   LEFT JOIN sncp_comum_codigos_contab AS CCC ON CCC.item_id=POL.product_id
                   WHERE order_id=$1 and CCC.natureza='des')
             LOOP
            dados_linha=dados_linha_compromisso($2,$3,PO_CCC.organica_id,PO_CCC.economica_id,
            PO_CCC.funcional_id);

            IF dados_linha.comp_linha_id!=0 THEN
               UPDATE purchase_order_line SET compromisso_linha_id=dados_linha.comp_linha_id
               WHERE id=PO_CCC.id;
            ELSE
               produto=(SELECT default_code FROM product_product
               WHERE id=POL.item_id);
               RETURN 'O artigo com o código ' || produto || ' com as respetivas classificações
               não têm correspondência nas linhas do compromisso';
            END IF;
             END LOOP;
        RETURN '';
        END;
        $$ LANGUAGE PLPGSQL;
        """)
        return True

    def sql_linhas_ordem_compra_cabimento(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION linhas_ordem_compra_cabimento(ordem_compra_id integer, cabimento_id integer)
                RETURNS boolean AS $$
                DECLARE
                    PO_LINE RECORD;
                    sequencia integer = 1;
                    result boolean = FALSE;
            BEGIN
                FOR PO_LINE IN
                    (SELECT SUM( linhas.linha_val) AS total,linhas.organica_id,linhas.economica_id, linhas.funcional_id
                    FROM (SELECT SUM((product_qty*price_unit)*(1+calcula_iva(product_id))) AS linha_val,
                            CCC.organica_id,
                            CCC.economica_id,
                            CCC.funcional_id
                        FROM purchase_order_line AS POL
                        LEFT JOIN sncp_comum_codigos_contab AS CCC
                        ON CCC.item_id=POL.product_id
                        WHERE order_id=$1 and CCC.natureza='des'
                        GROUP BY CCC.organica_id,CCC.economica_id,CCC.funcional_id) AS linhas
                    GROUP BY linhas.organica_id,linhas.economica_id,linhas.funcional_id)
                LOOP

                INSERT INTO sncp_despesa_cabimento_linha
                    (estado, linha, cabimento_id, organica_id, economica_id, funcional_id, montante)
                VALUES
                    (1, sequencia, $2, PO_LINE.organica_id, PO_LINE.economica_id, PO_LINE.funcional_id, PO_LINE.total);
                sequencia = sequencia +1;
                result = TRUE;
                END LOOP;
                RETURN result;
            END
            $$ LANGUAGE PLPGSQL;
        """)

    def sql_linhas_ordem_compra_compromisso(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION linhas_ordem_compra_compromisso(ordem_compra_id integer, compromisso_ano_id integer)
                RETURNS boolean AS $$
                DECLARE
                    PO_LINE RECORD;
                    sequencia integer = 1;
                    result boolean = FALSE;
                    linha_id integer;
            BEGIN
                FOR PO_LINE IN
                    (SELECT SUM( linhas.linha_val) AS total,linhas.organica_id,linhas.economica_id, linhas.funcional_id
                    FROM (SELECT SUM((product_qty*price_unit)*(1+calcula_iva(product_id))) AS linha_val,
                            CCC.organica_id,
                            CCC.economica_id,
                            CCC.funcional_id
                        FROM purchase_order_line AS POL
                        LEFT JOIN sncp_comum_codigos_contab AS CCC
                        ON CCC.item_id=POL.product_id
                        WHERE order_id=$1 and CCC.natureza='des'
                        GROUP BY CCC.organica_id,CCC.economica_id,CCC.funcional_id) AS linhas
                    GROUP BY linhas.organica_id,linhas.economica_id,linhas.funcional_id)
                LOOP

                INSERT INTO sncp_despesa_compromisso_linha
                    (linha, compromisso_ano_id, organica_id, economica_id, funcional_id, montante, anual_prev,
                    state_line)
                VALUES
                    (sequencia, $2, PO_LINE.organica_id, PO_LINE.economica_id, PO_LINE.funcional_id, PO_LINE.total,
                    PO_LINE.total, 'draft');
                sequencia = sequencia +1;
                linha_id=(SELECT currval('sncp_despesa_compromisso_linha_id_seq'));

                INSERT INTO sncp_despesa_compromisso_agenda(compromisso_linha_id,name, montante, data_prevista)
                VALUES
                    (linha_id,EXTRACT(MONTH FROM CURRENT_DATE), PO_LINE.total,
                    calcula_last_util_mes(EXTRACT(MONTH FROM CURRENT_DATE)::INT,
                                          EXTRACT(YEAR FROM CURRENT_DATE)::INT));


                result = TRUE;
                END LOOP;
                RETURN result;
            END
            $$ LANGUAGE PLPGSQL;
        """)

    def sql_calcula_last_util_mes(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION calcula_last_util_mes(mes integer, ano integer)
          RETURNS date AS
        $$
            DECLARE
                data_util date;
                BEGIN

                IF mes + 1 > 12 THEN ano = ano + 1; mes = 1; ELSE mes = mes + 1; END IF;

            data_util = (CONCAT(ano, '-', mes, '-', 1)::DATE - INTERVAL '1 DAY')::DATE;

            WHILE EXTRACT(DOW FROM data_util) IN (0,6) OR
                (SELECT id FROM sncp_comum_feriados AS F WHERE F.data = data_util) IS NOT NULL
                LOOP
                data_util = (data_util - INTERVAL '1 DAY'):: DATE;


                END LOOP;
            RETURN data_util;
            END;
         $$   LANGUAGE plpgsql;
        """)

    def sql_calcula_iva_purchase_order_line(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION calcula_iva_purchase_order_line(order_line_id integer) RETURNS numeric AS
        $$
        BEGIN
        RETURN COALESCE((SELECT amount
            FROM account_tax AS AT
            LEFT JOIN purchase_order_taxe AS POT ON POT.tax_id=AT.id
            WHERE POT.ord_id=$1
            ),0.0);
        END
        $$ LANGUAGE plpgsql;
        """)

    def sql_dados_linha_cabimento(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION dados_linha_cabimento(cabimento_id integer,organica_id integer,
        economica_id integer,funcional_id integer,out montante numeric,out linha integer,out cab_linha_id integer) AS $$
        DECLARE
            linha_cab sncp_despesa_cabimento_linha%ROWTYPE;
        BEGIN
        SELECT * INTO linha_cab FROM sncp_despesa_cabimento_linha AS CAB_LINHA
            WHERE CAB_LINHA.cabimento_id=$1 AND
               (($2 IS NULL AND CAB_LINHA.organica_id IS NULL) OR ($2 IS NOT NULL AND CAB_LINHA.organica_id=$2)) AND
               (($3 IS NULL AND CAB_LINHA.economica_id IS NULL) OR ($3 IS NOT NULL AND CAB_LINHA.economica_id=$3)) AND
               (($4 IS NULL AND CAB_LINHA.funcional_id IS NULL) OR ($4 IS NOT NULL AND CAB_LINHA.funcional_id=$4));
        montante=COALESCE(linha_cab.montante,0.0);
        linha=COALESCE(linha_cab.linha,0);
        cab_linha_id=COALESCE(linha_cab.id,0);
        END
        $$ LANGUAGE PLPGSQL;
        """)

    def sql_valida_soma_totais_oc_cab(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION valida_soma_totais_oc_cab(ordem_compra_id integer,cabimento_id integer)
        RETURNS varchar AS $$
        DECLARE
            PO_CCC RECORD;
            dados_linha RECORD;
            ano integer;
            val_disp numeric;
            mensagem varchar='';
        BEGIN
          FOR PO_CCC IN
            (SELECT SUM( linhas.linha_val) AS total,linhas.organica_id,linhas.economica_id,
              linhas.funcional_id
           FROM (SELECT SUM((product_qty*price_unit)*(1+calcula_iva(product_id)))
                        AS linha_val,
                         CCC.organica_id,CCC.economica_id,CCC.funcional_id
                        FROM purchase_order_line AS POL
                        LEFT JOIN sncp_comum_codigos_contab AS CCC
                        ON CCC.item_id=POL.product_id
                        WHERE order_id=$1 and CCC.natureza='des'
                        GROUP BY CCC.organica_id,CCC.economica_id,CCC.funcional_id) AS linhas
             GROUP BY linhas.organica_id,linhas.economica_id,linhas.funcional_id)
             LOOP
            dados_linha=dados_linha_cabimento($2,PO_CCC.organica_id,PO_CCC.economica_id,PO_CCC.funcional_id);
            IF dados_linha.linha > 0 THEN

            ano= COALESCE(EXTRACT(YEAR FROM (SELECT CAB.data FROM sncp_despesa_cabimento AS CAB WHERE id=3)),
                 EXTRACT(YEAR FROM CURRENT_DATE));

            val_disp=da_valor_disponivel($2,dados_linha.linha,ano);

            IF PO_CCC.total>val_disp THEN
                mensagem='A linha ' || dados_linha.linha || ' do Cabimento indicado' ||
                ' não têm disponibilidade para satisfazer o valor de ' ||
                to_char(PO_CCC.total,'999G999G999G9990D00') || ' da Ordem de Compra';
                IF LENGTH(mensagem)>0 THEN
                    RETURN mensagem;
                END IF;
            END IF;
        END IF;
        END LOOP;
        RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)

    def create(self, cr, uid, vals, context=None):
        self.teste_existencia_purchase_order(cr)
        return super(purchase_order, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            if obj.state in ['draft', 'cancel']:
                cr.execute("""
                SELECT id
                FROM sncp_despesa_compromisso_relacoes_faturas AS CRF
                LEFT JOIN sncp_despesa_compromisso_relacoes AS CR ON CR.id = CRF.compromisso_relacoes_id
                WHERE CR.purchase_order_id = %d
                """ % obj.id)

                res_comp_rel_fat = cr.fetchall()

                if len(res_comp_rel_fat) != 0:
                    raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar pois a ordem de compra '
                                                        + obj.name + u' têm faturas associadas.'))

                cr.execute("""
                DELETE FROM sncp_despesa_compromisso_relacoes WHERE purchase_order_id = %d
                """ % obj.id)

        return super(purchase_order, self).unlink(cr, uid, ids, context=context)

    _defaults = {
        'compromisso_id': False,
        'state': 'draft',
    }

purchase_order()


class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'

    _columns = {
        'compromisso_linha_id': fields.many2one('sncp.despesa.compromisso.linha', u'Linha do Compromisso'),
    }

    _sql_constraints = [
        ('compromisso_ordem_linha_unique', 'unique (compromisso_linha_id)', u'Linha de compromisso unica'),
    ]

purchase_order_line()


class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"

    _columns = {
        'department_id': fields.many2one('hr.department', u'Departamento'),
    }

stock_warehouse()


class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def action_invoice_create(self, cr, uid, ids, journal_id=False, group=False, type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings
        """
        if context is None:
            context = {}

        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        partner_obj = self.pool.get('res.partner')
        invoices_group = {}
        res = {}
        inv_type = type
        invoice_vals = []
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.invoice_state != '2binvoiced':
                continue
            partner = self._get_partner_to_invoice(cr, uid, picking, context=context)
            if isinstance(partner, int):
                partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
            if not partner:
                raise osv.except_osv(_('Error, no partner!'),
                                     _('Please put a partner on the picking list if you want to generate invoice.'))

            if not inv_type:
                inv_type = self._get_invoice_type(picking)

            if group and partner.id in invoices_group:
                invoice_id = invoices_group[partner.id]
                invoice = invoice_obj.browse(cr, uid, invoice_id)
                invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
                invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
            else:
                invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
                invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
                invoices_group[partner.id] = invoice_id
            res[picking.id] = invoice_id
            for move_line in picking.move_lines:
                if move_line.state == 'cancel':
                    continue
                if move_line.scrapped:
                    # do no invoice scrapped products
                    continue
                vals = self._prepare_invoice_line(cr, uid, group, picking, move_line,
                                                  invoice_id, invoice_vals, context=context)
                if vals:
                    invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
                    self._invoice_line_hook(cr, uid, move_line, invoice_line_id)

            invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
                                       set_total=(inv_type in ('in_invoice', 'in_refund')))
            self.write(cr, uid, [picking.id], {
                'invoice_state': 'invoiced', }, context=context)
            self._invoice_hook(cr, uid, picking, invoice_id)

            # Bloco exclusivo de sncp
            if 'compromisso' in context:
                db_sncp_despesa_compromisso_relacoes = self.pool.get('sncp.despesa.compromisso.relacoes')
                relacoes_id = db_sncp_despesa_compromisso_relacoes.search(cr, uid, [('purchase_order_id', '=',
                                                                                     picking.purchase_id.id)])

                cr.execute("""INSERT INTO sncp_despesa_compromisso_relacoes_faturas
                              (compromisso_relacoes_id, fatura_id) VALUES (%d, %d)""" % (relacoes_id[0], invoice_id))

                ano = date.today().year
                cr.execute("""
                                SELECT atualiza_linhas_fatura(%d,%d)
                            """ % (invoice_id, ano))

                mensagem = cr.fetchone()[0]

                if len(mensagem) > 0:
                    raise osv.except_osv(_(unicode(mensagem)), _(u''))

        self.write(cr, uid, res.keys(), {
            'invoice_state': 'invoiced', }, context=context)
        return res

    _columns = {
        'account_journal_id': fields.many2one('account.journal', u'Diário de Stock', select=True,
                                              states={'done': [('readonly', True)], 'cancel': [('readonly',True)]}),
    }

stock_picking()