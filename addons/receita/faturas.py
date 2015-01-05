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
from dateutil.relativedelta import relativedelta
import decimal
from decimal import *

from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools.translate import _
import receita


def test_partner_id_2(self, cr, uid, partner_id):
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


def calcula_data_real(self, cr, uid, data_venc, descanso):
    if isinstance(data_venc, (str, unicode)):
        if data_venc.find(' ') != -1:
            data_venc = data_venc[:data_venc.find(' ')]

    if isinstance(data_venc, (str, unicode)):
        data_venc = datetime.strptime(data_venc, "%Y-%m-%d")
    if descanso != 'mant':
        # Teste dos feriados e fim de semana
        db_sncp_comum_feriados = self.pool.get('sncp.comum.feriados')
        feriados_id = db_sncp_comum_feriados.search(cr, uid, [('data', '=', unicode(data_venc.date()))])
        while data_venc.weekday() >= 5 or len(feriados_id) != 0:
            if descanso == 'ante':
                data_venc = data_venc-timedelta(days=1)
            elif descanso == 'adia':
                data_venc = data_venc+timedelta(days=1)
            feriados_id = db_sncp_comum_feriados.search(cr, uid, [('data', '=', unicode(data_venc.date()))])
    return data_venc


def get_next_date(self, cr, uid, ids, vals):
    # vals = {
    #   'iter': parent_iteracoes,
    #   'data': in datetime,
    #   'quantidade': Quantidade de Intervalo,
    #   'unidade': dias\semanas\meses,
    #   'descanso': mantem\antecipa\adia,
    #   'passo': 1/-1,
    data = vals['data']
    if vals['unidade'] == 'days':
        data += relativedelta(days=vals['quantidade'] * vals['passo'])
    elif vals['unidade'] == 'weeks':
        data += relativedelta(weeks=vals['quantidade'] * vals['passo'])
    else:
        data += relativedelta(months=vals['quantidade'] * vals['passo'])
    return data


def sql_get_first_date(self, cr):
    cr.execute("""
    CREATE OR REPLACE FUNCTION get_first_date( integer[], varchar) RETURNS date AS
    $$
        DECLARE
            first_date date;
            act_date date;
            list_of_date date[];
            list_ids integer[] = $1;
            date_invoice date = $2::date;
            cond_pag integer;
            curr_date date;
            x integer;
        BEGIN
            FOREACH x IN ARRAY list_ids
                LOOP
                cond_pag = (SELECT cond_pag_id FROM sncp_comum_codigos_contab WHERE id = x );
                list_of_date = array_append(list_of_date, (SELECT da_data_vencimento(cond_pag, date_invoice)));
                END LOOP;

            first_date =  list_of_date[1];
            FOREACH curr_date IN ARRAY list_of_date
                LOOP
                IF curr_date < first_date THEN first_date = curr_date;
                END IF;
                END LOOP;
        RETURN first_date;
        END;
    $$
    LANGUAGE plpgsql;
        """)
    return True


def sql_days_in_month(self, cr):
    cr.execute("""
    CREATE OR REPLACE FUNCTION days_in_month(date) RETURNS integer AS
    $$
        DECLARE
            data_date_trunc date;
        BEGIN
            data_date_trunc = (select date_trunc('months', (date_trunc('months', $1) + '45 days'::interval))
            - '1 day'::interval);
            RETURN  extract(day from data_date_trunc);
        END;
    $$
    LANGUAGE plpgsql;
    """)
    return True


def sql_da_data_vencimento(self, cr):
    cr.execute("""
    CREATE OR REPLACE FUNCTION da_data_vencimento( integer, date) RETURNS date AS
    $$
        DECLARE
            cond_pagam_id integer = $1;
            date_invoice date = $2;
            date_due date;
            linha sncp_comum_cond_pagam%ROWTYPE;
            data_linha_date date;
            data_contagem_date date;
        BEGIN
            FOR linha IN
                SELECT * FROM sncp_comum_cond_pagam WHERE id = cond_pagam_id
            LOOP

                IF linha.anual = TRUE THEN
                    data_linha_date = (extract(year from $2)::text||'-'||linha.mes::text||'-'||linha.dia::text)::date;
                    IF data_linha_date < $2
                        THEN date_due = ((extract(year from $2)+1)::text||'-'||linha.mes::text||'-'
                        ||linha.dia::text)::date;
                    ELSE date_due = data_linha_date;
                    END IF;
                ELSE
                    CASE linha.contagem
                        WHEN 'imed' THEN data_contagem_date = $2;
                        WHEN 'imes' THEN
                            data_contagem_date = (extract(year from $2)::text||'-'||extract(month from $2)::text
                            ||'-'||'1')::date;
                            IF linha.tipo = 'dia' THEN data_contagem_date = data_contagem_date - '1 day'::interval;
                            END IF;
                        WHEN 'fmes' THEN
                            data_contagem_date = (extract(year from $2)::text||'-'||extract(month from $2)::text||'-'
                            ||(SELECT days_in_month($2))::text)::date;
                        ELSE raise exception 'Dados incorretos';
                    END CASE;
                    CASE linha.tipo
                        WHEN 'dia' THEN date_due = data_contagem_date +
                        (COALESCE(linha.quantidade,0)::text ||' day')::interval;
                        WHEN 'mes' THEN date_due = data_contagem_date +
                        (COALESCE(linha.quantidade,0)::text ||' month')::interval;
                        ELSE raise exception 'Dados incorretos';
                    END CASE;
                END IF;
            END LOOP;

        RETURN date_due::date;
        END;
    $$
    LANGUAGE plpgsql;
    """)
    return True


def primeira_data_vencimento(self, cr, uid, ids, data, context=None):

    # Bloco de teste de existencia das funções
    cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_first_date'""")
    result = cr.fetchone()
    if result is None:
        sql_get_first_date(self, cr)
    cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'days_in_month'""")
    result = cr.fetchone()
    if result is None:
        sql_days_in_month(self, cr)
    cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'da_data_vencimento'""")
    result = cr.fetchone()
    if result is None:
        sql_da_data_vencimento(self, cr)

    cr.execute("""SELECT get_first_date(%s, '%s')""" % ('ARRAY'+unicode(ids), unicode(data)))
    data_vencimento = cr.fetchone()[0]
    return data_vencimento


def test_partner_id(self, cr, uid, partner_id):
    db_res_partner = self.pool.get('res.partner')
    obj_partner = db_res_partner.browse(cr, uid, partner_id)
    message = ''

    if hasattr(obj_partner, 'property_account_position'):
        if obj_partner.property_account_position.id is False:
            message += u'Contabilidade/Posição Fiscal\n'
    else:
        message += u'Contabilidade/Posição Fiscal\n'

    if obj_partner.property_account_receivable.id is False:
            message += u'Contabilidade/Conta a receber (Cliente)\n'

    if obj_partner.property_account_payable.id is False:
        message += u'Contabilidade/Conta a receber (Fornecedor)\n'

    if len(message) != 0:
        raise osv.except_osv(_(u'Aviso'), _(u'Para evitar futuros erros na execução do programa '
                                            u'deverá preencher os seguintes campos do parceiro de negócio:\n'+message
                                            + u'.'))
    return True

# _____________________________________________________________FATURAS SIMPLIFICADAS___________________


class sncp_receita_fatura_wizard(osv.Model):
    _name = 'sncp.receita.fatura.wizard'
    _description = u"Fatura da Receita"

    def sql_preenche_item_aut(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION preenche_item_aut(departamento_id integer, user_id integer)
        RETURNS boolean AS $$
        DECLARE
            linha RECORD;
        BEGIN
            FOR linha IN (SELECT  RID.item_id, RID.muda_preco FROM sncp_receita_itens_dept AS RID
                            WHERE RID.department_id = $1)
            LOOP
                INSERT INTO sncp_receita_fatura_item_aut (item_id, muda_preco)
                                  VALUES (linha.item_id, linha.muda_preco);
                END LOOP;
                FOR linha IN (SELECT  RIU.item_id, RIU.muda_preco, regra FROM sncp_receita_itens_user RIU
                        WHERE RIU.user_id = $2)
            LOOP
                IF linha.regra = 'mod'
                    THEN UPDATE sncp_receita_fatura_item_aut SET muda_preco = NOT muda_preco
                    WHERE item_id = linha.item_id;
                ELSIF linha.regra = 'exc'
                    THEN DELETE FROM sncp_receita_fatura_item_aut
                    WHERE item_id = linha.item_id;
                ELSE
                    INSERT INTO sncp_receita_fatura_item_aut (item_id, muda_preco)
                                 VALUES (linha.item_id, linha.muda_preco);
                        END IF;
            END LOOP;
            RETURN TRUE;

        END;
        $$ LANGUAGE PLPGSQL;
        """)
        return True

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        lista = []
        db_res_partner = self.pool.get('res.partner')
        obj_partner = db_res_partner.browse(cr, uid, partner_id)
        if hasattr(obj_partner, 'property_payment_term'):
            if obj_partner.property_payment_term.id is False:
                message = u'Considere em definir o Termo de pagamento para o Parceiro.\n'
                return {'domain': {'payment_term_id': [('id', 'in', lista)]},
                        'warning': {'title': 'Aviso', 'message': message}}
            else:
                lista.append(int(obj_partner.property_payment_term.id))
        else:
            message = u'Considere em definir o Termo de pagamento para o Parceiro.\n'
            return {'domain': {'payment_term_id': [('id', 'in', lista)]},
                    'warning': {'title': 'Aviso', 'message': message}}

        lista = list(set(lista))
        return {'domain': {'payment_term_id': [('id', 'in', lista)]}}

    def on_change_department_id(self, cr, uid, ids, department_id):
        message = u''

        lista_item = []
        cr.execute("""SELECT item_id FROM sncp_receita_itens_dept
                      WHERE department_id = %d""" % department_id)
        result_item = cr.fetchall()
        for res_item in result_item:
            lista_item.append(res_item[0])

        lista_journal = []
        cr.execute("""SELECT journal_id FROM sncp_receita_diarios_dept
                      WHERE department_id = %d""" % department_id)
        result_journal = cr.fetchall()
        for res_journal in result_journal:
            lista_journal.append(res_journal[0])

        linhas_ids = []
        if len(lista_journal) == 0:
            message += u'Considere em definir o diário padrão.\n'
        if len(lista_item) == 0:
            message += u'Considere em definir os artigos autorizados.\n'
        else:
            self.sql_preenche_item_aut(cr)
            cr.execute("""DELETE FROM sncp_receita_fatura_item_aut""")
            cr.execute("""SELECT preenche_item_aut(%d, %d)""" % (department_id, uid))

        if len(message) > 1:
            return {'domain': {'journal_id': [('id', 'in', lista_journal)]},
                    'warning': {'title': u'Erro de Departamento.',
                                'message': message + u'\n Receita/Dados Gerais'}}
        else:
            lista_journal = list(set(lista_journal))
            return {
                'value': {'linhas_ids': linhas_ids},
                'domain': {'journal_id': [('id', 'in', lista_journal)]}}

    def on_change_payment_term_id(self, cr, uid, ids, payment_term_id):
        db_sncp_comum_cond_pagam = self.pool.get('sncp.comum.cond.pagam')
        lista_ids = db_sncp_comum_cond_pagam.search(cr, uid, [('payment_term_id', '=', payment_term_id)])
        if len(lista_ids) == 0:
            return {'warning': {'title': u'Aviso',
                                'message': u'Este Termo de Pagamento não tem Condição de pagamento associada '
                                           u'no módulo Comum.'}}
        else:
            return {}

    def get_amount_tax(self, cr, uid, ids):
        cr.execute("""
        SELECT SUM(valor_iva) AS montante_iva
        FROM (
        SELECT SUM(untaxed) AS soma_sem_taxa,IVA,round(SUM(untaxed)*IVA,2) AS valor_iva
        FROM
        (SELECT untaxed,IVA
        FROM
        (SELECT round(RFLW.quantidade*RFLW.preco_unit,2) AS untaxed,RFLW.item_aut_id AS item,
            (SELECT T.amount FROM account_tax AS T
             WHERE id = (SELECT PTR.tax_id FROM product_taxes_rel AS PTR
                     WHERE prod_id=
                    (SELECT RFI.item_id FROM sncp_receita_fatura_item_aut AS RFI WHERE id=item_aut_id))) AS IVA
            FROM sncp_receita_fatura_linha_wizard AS RFLW
            WHERE fatura_id=%d) AS X) AS K
        GROUP BY IVA) AS H
        """ % ids[0])
        amount_tax = cr.fetchone()[0]
        if amount_tax is False or amount_tax is None:
            amount_tax = 0.00
        return amount_tax

    def get_amount_untaxed(self, cr, uid, ids):
        cr.execute("""
        SELECT SUM(preco_unit * quantidade) FROM sncp_receita_fatura_linha_wizard
        WHERE fatura_id = %d """ % ids[0])
        amount_untaxed = cr.fetchone()[0]
        if amount_untaxed is False or amount_untaxed is None:
            amount_untaxed = 0.00
        return amount_untaxed

    def atualizar(self, cr, uid, ids, context=None):

        amount_tax = self.get_amount_tax(cr, uid, ids)
        amount_untaxed = self.get_amount_untaxed(cr, uid, ids)

        aux = decimal.Decimal(unicode(amount_tax+amount_untaxed))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_original = float(aux)

        self.write(cr, uid, ids, {
            'amount_tax': amount_tax,
            'amount_untaxed': amount_untaxed,
            'amount_total': montante_original,
        })
        return True

    def processar(self, cr, uid, ids, context=None):
        db_account_invoice = self.pool.get('account.invoice')
        db_account_invoice_line = self.pool.get('account.invoice.line')
        db_sncp_comum_cond_pagam = self.pool.get('sncp.comum.cond.pagam')
        db_sncp_receita_fatura_linha_wizard = self.pool.get('sncp.receita.fatura.linha.wizard')
        self.atualizar(cr, uid, ids, context=context)
        obj = self.browse(cr, uid, ids[0])

        cr.execute("""SELECT id FROM sncp_comum_cond_pagam
                      WHERE payment_term_id = %d""" % obj.payment_term_id.id)
        cond_pagam = cr.fetchone()
        if cond_pagam is None:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Este Termo de Pagamento não tem Condição de pagamento associada '
                                   u'no módulo Comum.'))
        vals_da_data_v = {'cond_pagam_id': cond_pagam[0],
                          'dataemissao': datetime.strptime(obj.name, "%Y-%m-%d"), }

        # Bloco de cabeçalho de fatura
        vals_account_invoice = {
            'name': '',
            'origin': '',
            'type': 'out_invoice',
            'reference_type': 'none',
            'comment': obj.note,
            'state': 'draft',
            'sent': False,
            'date_invoice': obj.name,
            'date_due': db_sncp_comum_cond_pagam.da_data_vencimento(cr, uid, ids, vals_da_data_v, context),
            'period_id': self.get_period(cr, uid, ids),
            'account_id': obj.partner_id.property_account_receivable.id,
            'partner_id': obj.partner_id.id,
            'currency_id': obj.currency_id.id,
            'journal_id': obj.journal_id.id,
            'company_id': self.get_company(cr, uid, ids),
            'user_id': uid,
            'fiscal_position': obj.partner_id.property_account_position.id,
            'payment_term': obj.payment_term_id.id,
            'department_id': obj.department_id.id,
        }
        invoice_id = db_account_invoice.create(cr, uid, vals_account_invoice)

        # Bloco de linhas de fatura
        linhas_ids = db_sncp_receita_fatura_linha_wizard.search(cr, uid, [('fatura_id', '=', ids[0])])
        for obj_linha in db_sncp_receita_fatura_linha_wizard.browse(cr, uid, linhas_ids):

            cr.execute("""SELECT natureza, organica_id, economica_id, funcional_id, conta_id
                          FROM sncp_comum_codigos_contab
                          WHERE item_id = %d AND natureza IN ('rec','ots')
                          """ % obj_linha.item_aut_id.item_id.id)
            cod_contab = cr.fetchone()
            if cod_contab is None:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Defina código de contabilização de natureza receita orçamental '
                                       u'ou operações de tesouraria'
                                       u'para o artigo ' + u'[' +
                                       unicode(obj_linha.item_aut_id.item_id.default_code)+u'] ' +
                                       unicode(obj_linha.item_aut_id.item_id.name_template)))
            conta_id = obj_linha.item_aut_id.item_id.product_tmpl_id.property_account_income.id
            if cod_contab[4] is not False:
                conta_id = cod_contab[4]
            lll = obj_linha.item_aut_id.item_id.product_tmpl_id.taxes_id
            nova_lista = [elem.id for elem in lll]
            vals_account_invoice_line = {
                'origin': '',
                'uos_id': obj_linha.item_aut_id.item_id.product_tmpl_id.uos_id.id,
                'account_id': conta_id,
                'name': '[' + obj_linha.item_aut_id.item_id.default_code + '] ' +
                        obj_linha.item_aut_id.item_id.product_tmpl_id.name,
                'sequence': '',
                'invoice_id': invoice_id,
                'price_unit': obj_linha.preco_unit,
                'company_id': self.get_company(cr, uid, ids),
                'quantity': obj_linha.quantidade,
                'partner_id': obj.partner_id.id,
                'product_id': obj_linha.item_aut_id.item_id.id,
                'natureza': cod_contab[0],
                'organica_id': cod_contab[1],
                'economica_id': cod_contab[2],
                'funcional_id': cod_contab[3],
                'invoice_line_tax_id':  [(6, 0, nova_lista)],
            }
            db_account_invoice_line.create(cr, uid, vals_account_invoice_line)

        # Responsável por passar o estado da fatura para "open"
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)

        fatura = db_account_invoice.browse(cr, uid, invoice_id)

        amount_total = unicode(fatura.amount_total).replace(u'.', u',')
        ###############################
        ids_wizard = self.search(cr, uid, [('id', '<', ids[0])])
        ids_linhas = db_sncp_receita_fatura_linha_wizard.search(cr, uid, [('fatura_id', 'in', ids_wizard)])
        db_sncp_receita_fatura_linha_wizard.unlink(cr, uid, ids_linhas)
        self.unlink(cr, uid, ids_wizard)
        ######################
        return self.pool.get('formulario.mensagem.receita').wizard(cr, uid, u'Criada a Fatura nº '+
                                                                   fatura.internal_number + u' no valor de ' +
                                                                   amount_total+u'€')

    _columns = {
        'name': fields.date(u'Data'),
        'department_id': fields.many2one('hr.department', u'Departamento'),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios',
                                      domain=[('customer', '=', True)]),
        'currency_id': fields.many2one('res.currency', u'Moeda'),
        'note': fields.text(u'Notas'),
        'payment_term_id': fields.many2one('account.payment.term', u'Termos de Pagamento'),
        'journal_id': fields.many2one('account.journal', u'Diário'),
        'linhas_ids': fields.one2many('sncp.receita.fatura.linha.wizard', 'fatura_id', u'Linhas'),
        'amount_tax': fields.float(u'Imposto', digits=(12, 2)),
        'amount_untaxed': fields.float(u'Subtotal', digits=(12, 2)),
        'amount_total': fields.float(u'Total', digits=(12, 2)),
    }

    def get_department(self, cr, uid, context):
        cr.execute("""SELECT department_id FROM hr_employee WHERE resource_id IN (
                            SELECT id FROM resource_resource WHERE user_id = %d )""" % uid)
        res = cr.fetchone()
        if res[0] is None:
            raise osv.except_osv(_(u'Aviso'), _(u'O utilizador corrente não têm departamento definido.\n'
                                                u'Recursos Humanos/Funcionarios.'))
        else:
            return res[0]

    def get_currency(self, cr, uid, context):
        cr.execute("""SELECT currency_id FROM res_company WHERE id IN (
                            SELECT company_id FROM res_users WHERE id = %d )""" % uid)
        res = cr.fetchone()
        if res[0] is None:
            raise osv.except_osv(_(u'Aviso'), _(u'A moeda não está definida corretamente.'))
        else:
            return res[0]

    def get_company(self, cr, uid, ids):
        cr.execute("""SELECT company_id FROM res_users
                      WHERE id = %d""" % uid)
        company_id = cr.fetchone()[0]
        return company_id

    def get_period(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        cr.execute("""SELECT id, state FROM account_period
                      WHERE special = FALSE AND
                            '%s' BETWEEN date_start AND date_stop """ % obj.name)
        result = cr.fetchone()
        if result is None:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina o período para a data '+unicode(obj.name)+u'.'))
        if result[1] != 'draft':
            raise osv.except_osv(_(u'Aviso'), _(u'O período já se encontra fechado.'))
        return result[0]

    _defaults = {'name': unicode(date(datetime.now().year, datetime.now().month, datetime.now().day)),
                 'department_id': lambda self, cr, uid, ctx: self.get_department(cr, uid, ctx),
                 'currency_id': lambda self, cr, uid, ctx: self.get_currency(cr, uid, ctx), }

    def check_payment_id(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        db_sncp_comum_cond_pagam = self.pool.get('sncp.comum.cond.pagam')
        lista_ids = db_sncp_comum_cond_pagam.search(cr, uid, [('payment_term_id', '=', obj.payment_term_id.id)])
        if len(lista_ids) == 0:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Este Termo de Pagamento não tem Condição de pagamento associada '
                                   u'no módulo Comum.'))
        else:
            return True

    def create(self, cr, uid, vals, context=None):
        test_partner_id_2(self, cr, uid, vals['partner_id'])
        wizard_id = super(sncp_receita_fatura_wizard, self).create(cr, uid, vals, context=context)
        self.atualizar(cr, uid, [wizard_id])
        return wizard_id

    _constraints = [
        (check_payment_id, u'', ['payment_term_id'])
    ]

sncp_receita_fatura_wizard()
# ____________________________________________________________FATURAS LINHAS___________________________


class sncp_receita_fatura_linha_wizard(osv.Model):
    _name = 'sncp.receita.fatura.linha.wizard'
    _description = u"Linha da Fatura de Receita"

    def on_change_item_aut_id(self, cr, uid, ids, item_aut_id):
        value = 0
        db_sncp_receita_fatura_item_aut = self.pool.get('sncp.receita.fatura.item.aut')
        obj_item_aut = db_sncp_receita_fatura_item_aut.browse(cr, uid, item_aut_id)
        if obj_item_aut.muda_preco is True:
            value = 1
        self.write(cr, uid, ids, {'name': value, 'preco_unit': obj_item_aut.item_id.product_tmpl_id.list_price})
        return {'value': {'name': value, 'preco_unit': obj_item_aut.item_id.product_tmpl_id.list_price}}

    _columns = {
        'fatura_id': fields.many2one('sncp.receita.fatura.wizard', u''),
        'item_aut_id': fields.many2one('sncp.receita.fatura.item.aut', u'Item'),
        'quantidade': fields.float(u'Quantidade', digits=(12, 3)),
        'preco_unit': fields.float(u'Preço Unitário', digits=(7, 4)),
        'name': fields.integer(u'Campo de controlo'),

    }

    def create(self, cr, uid, vals, context=None):
        db_sncp_receita_fatura_item_aut = self.pool.get('sncp.receita.fatura.item.aut')
        obj_item_aut = db_sncp_receita_fatura_item_aut.browse(cr, uid, vals['item_aut_id'])
        if 'preco_unit' not in vals:
                if obj_item_aut.item_id.product_tmpl_id.list_price > 0:
                    vals['preco_unit'] = obj_item_aut.item_id.product_tmpl_id.list_price
        return super(sncp_receita_fatura_linha_wizard, self).create(cr, uid, vals, context=context)

    _defaults = {
        'name': 0,
        'preco_unit': 0.0,
    }

    def quantidade_positiva(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.quantidade > 0:
            return True
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'A quantidade  têm que ser positiva.'))

    _constraints = [
        (quantidade_positiva, u'', ['quantidade'])
    ]

sncp_receita_fatura_linha_wizard()
# ____________________________________________________________ARTIGOS AUTORIZADOS_____________________


class sncp_receita_fatura_item_aut(osv.Model):
    _name = 'sncp.receita.fatura.item.aut'
    _description = u"Fatura Itens Autorizados"

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['item_id'], context=context)
        res = []
        for record in reads:
            result = record['item_id'][1]
            res.append((record['id'], result))
        return res

    _columns = {
        'item_id': fields.many2one('product.product', u''),
        'muda_preco': fields.boolean(u''),
    }

sncp_receita_fatura_item_aut()
# ___________________________________________________________FATURAS MODELO______________________


class sncp_receita_fatura_modelo(osv.Model):
    _name = 'sncp.receita.fatura.modelo'
    _description = u"Modelo da Fatura"

    def artigos(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'estado': 1})
        return True

    def atualiza_preco_estado(self, cr, uid, ids, context):
        db_sncp_receita_fatura_modelo_linha = self.pool.get('sncp.receita.fatura.modelo.linha')
        obj = self.browse(cr, uid, ids[0])
        if obj.atualiza_preco is False:
            cr.execute("""UPDATE sncp_receita_fatura_modelo_linha SET estado = 1
                          WHERE fatura_id = %d """ % ids[0])
            self.write(cr, uid, ids, {'atualiza_preco': True})
        else:
            linha_ids = db_sncp_receita_fatura_modelo_linha.search(cr, uid, [('fatura_id', '=', ids[0])])
            for obj_linha in db_sncp_receita_fatura_modelo_linha.browse(cr, uid, linha_ids):
                db_sncp_receita_fatura_modelo_linha.write(cr, uid, obj_linha.id,
                                                          {'estado': 0,
                                                           'preco_unit': obj_linha.item_id.product_tmpl_id.list_price})
            self.write(cr, uid, ids, {'atualiza_preco': False})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    _columns = {
        'name': fields.char(u'Descrição', size=64),
        'journal_id': fields.many2one('account.journal', u'Diário',
                                      domain=[('type', '=', 'sale')]),
        'currency_id': fields.many2one('res.currency', u'Moeda'),
        'note': fields.text(u'Notas'),
        'payment_term_id': fields.many2one('account.payment.term', u'Termos de pagamento'),
        'atualiza_preco': fields.boolean(u'Atualiza preços'),
        'origem': fields.char(u'Referência de origem', size=64),
        'linha_ids': fields.one2many('sncp.receita.fatura.modelo.linha', 'fatura_id', u'Linhas'),
        'estado': fields.integer(u'estado modelo'),
    }

    _order = 'name'

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_receita_recorrente
            WHERE fatura_mod_id = %d
            """ % obj.id)

            res_recorr = cr.fetchall()

            if len(res_recorr) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o modelo de fatura ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Receita\Faturação Recorrente\Agendamentos.'))

            cr.execute("""
            DELETE FROM sncp_receita_fatura_modelo_linha
            WHERE fatura_id = %d
            """ % obj.id)

        return super(sncp_receita_fatura_modelo, self).unlink(cr, uid, ids, context=context)

    def get_currency(self, cr, uid, context):
        cr.execute("""SELECT currency_id FROM res_company WHERE id IN (
                            SELECT company_id FROM res_users WHERE id = %d )""" % uid)
        res = cr.fetchone()
        if res[0] is None:
            raise osv.except_osv(_(u'Aviso'), _(u'A moeda não está definida corretamente.'))
        else:
            return res[0]

    _defaults = {'currency_id': lambda self, cr, uid, ctx: self.get_currency(cr, uid, ctx),
                 'estado': 0, }

sncp_receita_fatura_modelo()
# ___________________________________________________________FATURAS MODELO LINHAS ____________


class sncp_receita_fatura_modelo_linha(osv.Model):
    _name = 'sncp.receita.fatura.modelo.linha'
    _description = u"Linha do Modelo da Fatura"

    def on_change_cod_contab_id(self, cr, uid, ids, cod_contab_id, fatura_id):
        db_sncp_comum_codigos_contab = self.pool.get('sncp.comum.codigos.contab')
        obj_cod_contab = db_sncp_comum_codigos_contab.browse(cr, uid, cod_contab_id)
        obj_fatura = self.pool.get('sncp.receita.fatura.modelo').browse(cr, uid, fatura_id)
        estado = 0
        if obj_fatura.atualiza_preco is True:
            estado = 1
        item_id = obj_cod_contab.item_id.id
        list_price = obj_cod_contab.item_id.product_tmpl_id.list_price
        self.write(cr, uid, ids, {'item_id': item_id, 'preco_unit': list_price, 'estado': estado})
        return {'value': {'item_id': item_id, 'preco_unit': list_price, 'estado': estado}}

    _columns = {
        'fatura_id': fields.many2one('sncp.receita.fatura.modelo'),
        'name': fields.integer(u'Linha'),
        'cod_contab_id': fields.many2one('sncp.comum.codigos.contab', u'Item',
                                         domain=[('natureza', 'in', ['rec', 'ots'])]),
        'item_id': fields.many2one('product.product', u'Item'),
        'quantidade': fields.float(u'Quantidade', digits=(12, 3)),
        'preco_unit': fields.float(u'Preço Unitário', digits=(7, 4)),
        'estado': fields.integer(u'estado linha'), }

    def create(self, cr, uid, vals, context=None):
        db_sncp_comum_codigos_contab = self.pool.get('sncp.comum.codigos.contab')
        vals['name'] = receita.get_sequence(self, cr, uid, context, 'fat_mod', vals['fatura_id'])
        obj_cod_contab = db_sncp_comum_codigos_contab.browse(cr, uid, vals['cod_contab_id'])
        vals['item_id'] = obj_cod_contab.item_id.id
        if 'preco_unit' not in vals:
            vals['preco_unit'] = obj_cod_contab.item_id.product_tmpl_id.list_price
        return super(sncp_receita_fatura_modelo_linha, self).create(cr, uid, vals, context=context)

    _defaults = {
        'quantidade': 1,
        'estado': 0,
    }

sncp_receita_fatura_modelo_linha()
# ___________________________________________________________RECORRENTE________________________


class sncp_receita_recorrente(osv.Model):
    _name = 'sncp.receita.recorrente'
    _description = u"Recorrente"

    def parceiros(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'estado': 1})
        return True

    def process(self, cr, uid, ids, context):
        db_ir_cron = self.pool.get('ir.cron')
        db_sncp_receita_recorrente_parceiros = self.pool.get('sncp.receita.recorrente.parceiros')
        parceiros_ids = db_sncp_receita_recorrente_parceiros.search(cr, uid, [('recorrente_id', '=', ids[0])])
        if len(parceiros_ids) == 0:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'O agendamento da geração de faturas terá que ter'
                                   u' no mínimo um parceiro de negócio associado.'))
        obj = self.browse(cr, uid, ids[0])
        values = {
            'name': obj.name,
            'user_id': uid,
            'active': True,
            'interval_number': obj.intervalo_num,
            'interval_type': obj.intervalo_tipo,
            'numbercall': obj.iteracoes - obj.execucoes,
            'doall': True,
            'nextcall': obj.data_inicial,
            'model': 'sncp.receita.recorrente',
            'function': 'cria_faturas',
            'args': unicode([[obj.id]]),
            'priority': 9,
        }
        cron_id = db_ir_cron.create(cr, uid, values)
        self.write(cr, uid, ids, {'state': 'running', 'cron_id': cron_id})
        cr.execute("""UPDATE sncp_receita_recorrente_parceiros SET name = '3'
                      WHERE recorrente_id = %d""" % ids[0])
        return True

    def stop_running(self, cr, uid, ids, context):
        cr.execute("""UPDATE ir_cron SET active = FALSE
                      WHERE args = '[[%d]]' """ % ids[0])
        self.write(cr, uid, ids, {'state': 'done'})
        return True

    def get_company(self, cr, uid, ids):
        cr.execute("""SELECT company_id FROM res_users
                      WHERE id = %d""" % uid)
        company_id = cr.fetchone()[0]
        return company_id

    def get_period(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        cr.execute("""SELECT id, state FROM account_period
                      WHERE special = FALSE AND
                            '%s' BETWEEN date_start AND date_stop """ % obj.cron_id.nextcall)
        result = cr.fetchone()
        if result is None:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Defina o período para a data ' + unicode(obj.cron_id.nextcall)+u'.'))
        if result[1] != 'draft':
            raise osv.except_osv(_(u'Aviso'), _(u'O período já se encontra fechado.'))
        return result[0]

    def criar_faturas(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        db_ir_cron = self.pool.get('ir.cron')
        db_account_invoice = self.pool.get('account.invoice')
        db_account_invoice_line = self.pool.get('account.invoice.line')
        db_sncp_receita_fatura_modelo_linha = self.pool.get('sncp.receita.fatura.modelo.linha')
        db_sncp_receita_recorrente_parceiros = self.pool.get('sncp.receita.recorrente.parceiros')
        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]
        parceiros_ids = db_sncp_receita_recorrente_parceiros.search(cr, uid, [('recorrente_id', '=', ids[0]),
                                                                              ('activo', '=', True),
                                                                              ('data_inicial', '<=', datahora)])

        # Bloco de criação de faturas
        for parceiro in db_sncp_receita_recorrente_parceiros.browse(cr, uid, parceiros_ids):
            values_invoice = {
                'name': '',
                'origin': obj.fatura_mod_id.origem,
                'type': 'out_invoice',
                'reference_type': 'none',
                'comment': obj.fatura_mod_id.note,
                'state': 'draft',
                'sent': False,
                'date_invoice': obj.cron_id.nextcall,
                'period_id': self.get_period(cr, uid, ids),
                'account_id': parceiro.partner_id.property_account_receivable.id,
                'partner_id': parceiro.partner_id.id,
                'currency_id': obj.fatura_mod_id.currency_id.id,
                'journal_id': obj.fatura_mod_id.journal_id.id,
                'company_id': self.get_company(cr, uid, ids),
                'user_id': uid,
                'fiscal_position': parceiro.partner_id.property_account_position.id,
                'payment_term': obj.fatura_mod_id.payment_term_id.id,
            }
            invoice_id = db_account_invoice.create(cr, uid, values_invoice)

            # Bloco fatura Linha
            linhas_modelo_ids = db_sncp_receita_fatura_modelo_linha.search(cr, uid, [('fatura_id', '=',
                                                                                     obj.fatura_mod_id.id)])
            lista_cod_contab = []
            for artigo in db_sncp_receita_fatura_modelo_linha.browse(cr, uid, linhas_modelo_ids):
                cr.execute("""SELECT natureza, organica_id, economica_id, funcional_id, conta_id, id
                              FROM sncp_comum_codigos_contab
                              WHERE item_id = %d AND natureza IN ('rec','ots')""" % artigo.item_id.id)
                cod_contab = cr.fetchone()
                if cod_contab is None:
                    raise osv.except_osv(_(u'Aviso'),
                                         _(u'Defina código de contabilização de natureza receita orçamental '
                                           u'ou operações de tesouraria'
                                           u'para o artigo ' + u'[' + unicode(artigo.item_id.default_code)+u'] '
                                           + unicode(artigo.item_id.name_template)))
                lista_cod_contab.append(cod_contab[5])
                conta_id = artigo.item_id.product_tmpl_id.property_account_income.id
                if cod_contab[4] is not False:
                    conta_id = cod_contab[4]
                lll = artigo.item_id.product_tmpl_id.taxes_id
                nova_lista = [elem.id for elem in lll]
                values_invoice_line = {
                    'origin': '',
                    'uos_id': artigo.item_id.product_tmpl_id.uos_id.id,
                    'account_id': conta_id,
                    'name': '[' + artigo.item_id.default_code + '] ' + artigo.item_id.product_tmpl_id.name,
                    'sequence': '',
                    'invoice_id': invoice_id,
                    'price_unit': artigo.preco_unit,
                    'company_id': self.get_company(cr, uid, ids),
                    'quantity': artigo.quantidade,
                    'partner_id': parceiro.partner_id.id,
                    'product_id': artigo.item_id.id,
                    'natureza': cod_contab[0],
                    'organica_id': cod_contab[1],
                    'economica_id': cod_contab[2],
                    'funcional_id': cod_contab[3],
                    'invoice_line_tax_id': [(6, 0, nova_lista)],
                }
                db_account_invoice_line.create(cr, uid, values_invoice_line)

            date_invoice = datetime.strptime(obj.cron_id.nextcall[0:10], "%Y-%m-%d").date()
            primeira_data = primeira_data_vencimento(self, cr, uid, lista_cod_contab, date_invoice, context)
            date_due = calcula_data_real(self, cr, uid, primeira_data, obj.dias_descanso)
            db_account_invoice.write(cr, uid, invoice_id, {'date_due': date_due})

            # Passar o estado da fatura para open
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)

            # Bloco de atualização de parceiros

            if parceiro.iteracoes == parceiro.execucoes + 1:
                activo = False
            else:
                activo = True
            values_parceiro = {
                'execucoes': parceiro.execucoes + 1,
                'activo': activo,
            }
            db_sncp_receita_recorrente_parceiros.write(cr, uid, parceiro.id, values_parceiro)

        # Bloco de atualização de dados
        self.write(cr, uid, ids, {'execucoes': obj.execucoes + 1})
        if 0 < obj.iteracoes == obj.execucoes+1:
            self.write(cr, uid, ids, {'state': 'done'})

        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]

        vals = {
            'data': datahora,
            'quantidade': obj.intervalo_num,
            'unidade': obj.intervalo_tipo,
            'descanso': obj.dias_descanso,
            'passo': obj.execucoes}

        if obj.cron_id.numbercall != -1:
            if obj.cron_id.numbercall-1 == 0:
                data_frente = obj.cron_id.nextcall
                active = False
                numbercall = 0
            else:
                active = True
                data_frente = get_next_date(self, cr, uid, ids, vals)
                numbercall = (obj.iteracoes-(obj.execucoes+1))
        else:
            active = True
            data_frente = get_next_date(self, cr, uid, ids, vals)
            numbercall = -1
        data_real = calcula_data_real(self, cr, uid, data_frente, obj.dias_descanso)

        data_real = datetime(data_real.year, data_real.month, data_real.day, data_real.hour, data_real.minute,
                             data_real.second)

        db_ir_cron.write(cr, uid, [obj.cron_id.id], {
            'nextcall': data_real,
            'numbercall': numbercall,
            'active': active,
        })

        return True

    _columns = {
        'name': fields.char(u'Descrição', size=64),
        'fatura_mod_id': fields.many2one('sncp.receita.fatura.modelo', u'Fatura Modelo'),
        'iteracoes': fields.integer(u'Iterações'),
        'intervalo_num': fields.integer(u'Quantidade de Intervalo'),
        'intervalo_tipo': fields.selection([('days', u'Dias'),
                                            ('weeks', u'Semanas'),
                                            ('months', u'Meses'), ], u'Unidade de Intervalo'),
        'data_inicial': fields.date(u'Primeira data'),
        'dias_descanso': fields.selection([('mant', u'Mantém'),
                                           ('ante', u'Antecipa'),
                                           ('adia', u'Adia'), ], u'Nos dias de Descanso'),
        'execucoes': fields.integer(u'Execuções'),
        'cron_id': fields.many2one('ir.cron', u'Cron'),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('running', u'Activo'),
                                   ('done', u'Completo'), ], u'Estado'),
        'parceiros_ids': fields.one2many('sncp.receita.recorrente.parceiros', 'recorrente_id'),
        'estado': fields.integer(u'Controlo'),
    }

    _order = 'name'

    _defaults = {
        'state': 'draft',
        'data_inicial': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day)),
        'dias_descanso': 'mant',
        'estado': 0,
    }

    def tell_me_why(self, cr, uid, ids, data):
        text = u''
        if isinstance(data, (str, unicode)):
            data = datetime.strptime(data, "%Y-%m-%d")
        cr.execute("""SELECT name FROM sncp_comum_feriados
                          WHERE data = '%s'""" % unicode(data.date()))
        feriado_nome = cr.fetchone()

        if data.weekday() == 5:
            text = u' com um sabado'
        elif data.weekday() == 6:
            text = u' com um domingo'
        elif feriado_nome is not None:
            text = u' com o feriado ' + feriado_nome[0]

        return text

    def check_iteracoes(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.iteracoes == 0 and obj.state == 'draft':
            raise osv.except_osv(_(u'Aviso'), _(u'O número de iterações não pode ser 0.'))
        if obj.iteracoes < -1 and obj.state == 'draft':
            raise osv.except_osv(_(u'Aviso'), _(u'Para iterações contínuas defina -1.'))
        return True

    def check_intervalo_num(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.intervalo_num == 0 and obj.state == 'draft':
            raise osv.except_osv(_(u'Aviso'), _(u'O intervalo não pode ser 0.'))
        return True

    def check_data_inicial(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.dias_descanso != 'mant':
            data_real = calcula_data_real(self, cr, uid, obj.data_inicial, obj.dias_descanso)

            if unicode(data_real).find(' ') != -1:
                data_real = data_real.date()

            if obj.data_inicial != unicode(data_real):
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Considere de alterar a data ' + unicode(obj.data_inicial) +
                                       u', porque a mesma coincide ' + self.tell_me_why(cr, uid, ids,  obj.data_inicial)
                                       + u'.'))
        return True

    _constraints = [
        (check_iteracoes, u'', ['iteracoes']),
        (check_intervalo_num, u'', ['intervalo']),
        (check_data_inicial, u'', ['data_inicial']),
    ]

    def unlink(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids):
            cr.execute("""
            DELETE FROM sncp_receita_recorrente_parceiros
            WHERE recorrente_id=%d
            """ % obj.id)

            if obj.cron_id.id:
                cr.execute("""
                DELETE FROM ir_cron
                WHERE id=%d
                """ % obj.cron_id.id)

        return super(sncp_receita_recorrente, self).unlink(cr, uid, ids, context=context)

sncp_receita_recorrente()
# ____________________________________________________RECORRENTE PARCEIROS______________________


class sncp_receita_recorrente_parceiros(osv.Model):
    _name = 'sncp.receita.recorrente.parceiros'
    _description = u"Recorrente Parceiros"

    def dicionario_iter_por_data(self, cr, uid, ids, vals):
        # vals = {
        #   'iter': numero de iter,
        #   'data': in datetime,
        #   'quantidade': Quantidade de Intervalo,
        #   'unidade': dias\semanas\meses,
        #   'descanso': mantem\antecipa\adia,
        dicionario = {}
        data = vals['data']
        if vals['unidade'] == 'days':
            for key in range(1, vals['iter']+1):
                data += relativedelta(days=vals['quantidade'])
                dicionario[unicode(date(data.year, data.month, data.day))] = key
        elif vals['unidade'] == 'weeks':
            for key in range(1, vals['iter']+1):
                data += relativedelta(weeks=vals['quantidade'])
                dicionario[unicode(date(data.year, data.month, data.day))] = key
        else:
            for key in range(1, vals['iter']+1):
                data += relativedelta(months=vals['quantidade'])
                dicionario[unicode(date(data.year, data.month, data.day))] = key
        return dicionario

    def get_next_date(self, cr, uid, ids, vals):
        # vals = {
        #   'iter': parent_iteracoes,
        #   'data': in datetime,
        #   'quantidade': Quantidade de Intervalo,
        #   'unidade': dias\semanas\meses,
        #   'descanso': mantem\antecipa\adia,
        #   'passo': 1/-1,
        data = vals['data']
        if vals['unidade'] == 'days':
            data += relativedelta(days=vals['quantidade'] * vals['passo'])
        elif vals['unidade'] == 'weeks':
            data += relativedelta(weeks=vals['quantidade'] * vals['passo'])
        else:
            data += relativedelta(months=vals['quantidade'] * vals['passo'])
        return data

    def on_change_iteracoes(self, cr, uid, ids, iteracoes, parent_iteracoes, data_inicial, parent_data_inicial,
                            intervalo_num, intervalo_tipo, dias_descanso):
        if iteracoes > parent_iteracoes and data_inicial == parent_data_inicial:
            self.write(self, cr, uid, ids, {'iteracoes': parent_iteracoes})
            return {'warning': {'title': u'Aviso',
                                'message': u'As iterações nos parceiros não podem ser superior às '
                                           u'iterações que faltam cumprir para a receita recorrente.'},
                    'value': {'iteracoes': parent_iteracoes}}
        elif data_inicial != parent_data_inicial and parent_iteracoes > 0:
            dicionario = self.dicionario_iter_por_data(cr, uid, ids, {'iter': parent_iteracoes,
                                                                      'data': datetime.strptime(parent_data_inicial,
                                                                                                "%Y-%m-%d"),
                                                                      'quantidade': intervalo_num,
                                                                      'unidade': intervalo_tipo,
                                                                      'descanso': dias_descanso, })
            if iteracoes > dicionario[data_inicial]:
                self.write(self, cr, uid, ids, {'iteracoes': parent_iteracoes - dicionario[data_inicial]})
                return {'warning': {'title': u'Aviso',
                                    'message': u'As iterações nos parceiros não podem ser superior às '
                                               u'iterações que faltam cumprir para a receita recorrente.'},
                        'value': {'iteracoes': parent_iteracoes - dicionario[data_inicial]}}
        else:
            return {}

    def on_change_partner_id(self, cr, uid, ids, data_inicial, iteracoes, descanso):
        data_real = calcula_data_real(self, cr, uid, data_inicial, descanso)
        aux_data_real = unicode(data_real)
        if aux_data_real.find(' ') > 0:
            data_real = data_real.date()
        self.write(cr, uid, ids, {'data_inicial': data_inicial, 'data_real': data_real,
                                  'iteracoes': iteracoes, 'name': '0'})
        return {'value': {'data_inicial': data_inicial, 'data_real': unicode(data_real),
                          'iteracoes': iteracoes, 'name': '0'}}

    def step_forward(self, cr, uid, ids, context):

        db_sncp_receita_recorrente = self.pool.get('sncp.receita.recorrente')
        obj = self.browse(cr, uid, ids[0])
        obj_recorrente = db_sncp_receita_recorrente.browse(cr, uid, obj.recorrente_id.id)
        vals = {
            'data': datetime.strptime(obj.data_inicial, "%Y-%m-%d"),
            'quantidade': obj_recorrente.intervalo_num,
            'unidade': obj_recorrente.intervalo_tipo,
            'descanso': obj_recorrente.dias_descanso,
            'passo': 1, }
        data_frente = get_next_date(self, cr, uid, ids, vals)
        if obj.iteracoes == -1:
            name = 1
            iteracoes = -1
        elif obj.iteracoes == 2:
            name = 2
            iteracoes = obj.iteracoes - 1
        else:
            name = 1
            iteracoes = obj.iteracoes - 1
        data_real = calcula_data_real(self, cr, uid, data_frente, obj_recorrente.dias_descanso)
        vals_parceiro = {'data_inicial': unicode(data_frente), 'data_real': unicode(data_real),
                         'iteracoes': iteracoes, 'name': name}
        self.write(cr, uid, ids, vals_parceiro)
        return True

    def step_back(self, cr, uid, ids, context):
        db_sncp_receita_recorrente = self.pool.get('sncp.receita.recorrente')
        obj = self.browse(cr, uid, ids[0])
        obj_recorrente = db_sncp_receita_recorrente.browse(cr, uid, obj.recorrente_id.id)
        vals = {
            'iter': obj_recorrente.iteracoes,
            'data': datetime.strptime(obj.data_inicial, "%Y-%m-%d"),
            'quantidade': obj_recorrente.intervalo_num,
            'unidade': obj_recorrente.intervalo_tipo,
            'descanso': obj_recorrente.dias_descanso,
            'passo': -1, }
        data_frente = get_next_date(self, cr, uid, ids, vals)

        if data_frente < datetime.now():
            name = '0'
            data_frente = obj_recorrente.data_inicial
            if obj.iteracoes > 0:
                iteracoes = obj.iteracoes + 1
            else:
                iteracoes = obj.iteracoes
        else:
            if obj.iteracoes == -1:
                name = '1'
                iteracoes = -1
            elif obj_recorrente.iteracoes - obj.iteracoes == 1:
                iteracoes = obj.iteracoes + 1
                name = '0'
            else:
                iteracoes = obj.iteracoes + 1
                name = '1'
        data_real = calcula_data_real(self, cr, uid, data_frente, obj_recorrente.dias_descanso)
        vals_parceiro = {'data_inicial': data_frente, 'data_real': data_real,
                         'iteracoes': iteracoes, 'name': name}
        self.write(cr, uid, ids, vals_parceiro)
        return True

    def parar(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'activo': False})
        return True

    def continuar(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'activo': True, 'execucoes': 0})
        return True

    _columns = {
        'recorrente_id': fields.many2one('sncp.receita.recorrente', u'Recorrente'),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios',
                                      domain=[('customer', '=', True)]),
        'iteracoes': fields.integer(u'Iterações'),
        'data_inicial': fields.date(u'Primeira data'),
        'data_real': fields.date(u'Primeira data'),
        'execucoes': fields.integer(u'Execuções'),
        'activo': fields.boolean(u'Activo'),
        'name': fields.char(u'Controlo de botões'),
    }

    def create(self, cr, uid, vals, context=None):
        test_partner_id_2(self, cr, uid, vals['partner_id'])
        db_sncp_receita_recorrente = self.pool.get('sncp.receita.recorrente')
        obj_recorrente = db_sncp_receita_recorrente.browse(cr, uid, vals['recorrente_id'])

        if 'data_inicial' not in vals:
            vals['data_inicial'] = obj_recorrente.data_inicial
            vals['data_real'] = calcula_data_real(self, cr, uid,
                                                  vals['data_inicial'],
                                                  obj_recorrente.dias_descanso)

        if 'data_inicial' in vals and 'data_real' not in vals:
            vals['data_real'] = calcula_data_real(self, cr, uid,
                                                  vals['data_inicial'],
                                                  obj_recorrente.dias_descanso)

        return super(sncp_receita_recorrente_parceiros, self).create(cr, uid, vals, context=context)

    _defaults = {
        'name': '0',
        'activo': True,
    }

    def check_partner_id(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        return test_partner_id(self, cr, uid, obj.partner_id.id)

    _constraints = [
        (check_partner_id, u'', ['partner_id'])
    ]

sncp_receita_recorrente_parceiros()