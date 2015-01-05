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

from openerp.osv import osv, orm
from openerp.tools.translate import _


class account_payment_term(osv.osv):
    _inherit = "account.payment.term"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_comum_cond_pagam
            WHERE payment_term_id = %d
            """ % obj.id)

            res_cond_pagam = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_fatura_modelo
            WHERE payment_term_id = %d
            """ % obj.id)

            res_fat_modelo = cr.fetchall()

            if len(res_cond_pagam) != 0 or len(res_fat_modelo) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o termo de pagamento ' + obj.name +
                                                    u' têm associação em:\n'
                                                    u'1. Condições  de Pagamento.\n'
                                                    u'2. Modelos de Faturas.\n'))

            cr.execute("""
            DELETE FROM account_payment_term_line
            WHERE payment_id = %d
            """ % obj.id)

            cr.execute("""
            DELETE FROM account_payment_term
            WHERE id = %d
            """ % obj.id)

        return True

account_payment_term()


class product_product(osv.osv):
    _inherit = "product.product"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_comum_codigos_contab
            WHERE item_id = %d
            """ % obj.id)

            res_cod_contab = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_requisicoes_linhas
            WHERE item_id = %d AND parent_state IN ('aprovd','complt')
            """ % obj.id)

            res_req_linhas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_juros
            WHERE item_id = %d
            """ % obj.id)

            res_juros = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_itens_dept
            WHERE item_id = %d
            """ % obj.id)

            res_itens_dept = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_itens_user
            WHERE item_id = %d
            """ % obj.id)

            res_itens_user = cr.fetchall()

            if len(res_cod_contab) != 0 or len(res_req_linhas) != 0 or len(res_juros) != 0 \
                    or len(res_itens_dept) or len(res_itens_user) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o item [' + obj.default_code + u'] '
                                                    + obj.name_template
                                                    + u' têm associação em:\n '
                                                      u'1. Códigos de Contabilização.\n'
                                                      u'2. Requisições Internas.\n'
                                                      u'3. Juros.\n'
                                                      u'4. Itens por Departamento.\n'
                                                      u'5. Excepções.'))

        return super(product_product, self).unlink(cr, uid, ids, context=context)

product_product()


class account_account(osv.osv):
    _inherit = "account.account"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_comum_codigos_contab
            WHERE conta_id = %d
            """ % obj.id)

            res_cod_contab = cr.fetchall()

            cr.execute("""
            SELECT OLI.id
            FROM sncp_despesa_pagamentos_ordem_linhas_imprimir AS OLI
            WHERE conta_contabil_id = %d
            """ % obj.id)

            res_ordem_imprimir = cr.fetchall()

            cr.execute("""
            SELECT GRL.id
            FROM sncp_receita_guia_rec_linhas AS GRL
            WHERE conta_id = %d
            """ % obj.id)

            res_guia_rec_linhas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_fundos_maneio
            WHERE conta_id = %d
            """ % obj.id)

            res_fmaneio = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_tipo_mov
            WHERE conta_id = %d
            """ % obj.id)

            res_tes_tipo_mov = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_movimentos
            WHERE conta_id = %d
            """ % obj.id)

            res_tes_mov = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_caixas
            WHERE conta_id = %d
            """ % obj.id)

            res_tes_caixas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_contas_bancarias
            WHERE conta_id = %d
            """ % obj.id)

            res_tes_bancos = cr.fetchall()

            if len(res_cod_contab) != 0 or len(res_ordem_imprimir) != 0 or len(res_guia_rec_linhas) != 0 or \
               len(res_fmaneio) != 0 or len(res_tes_tipo_mov) != 0 or len(res_tes_mov) != 0 or \
                    len(res_tes_caixas) != 0 or len(res_tes_bancos) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a conta ' + obj.code + u' '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Códigos de Contabilização.\n'
                                                    u'2. Ordens de Pagamento.\n'
                                                    u'3. Guias de Receita.\n'
                                                    u'4. Fundos de Maneio.\n'
                                                    u'5. Movimentos.\n'
                                                    u'6. Tipos de Movimento.\n'
                                                    u'7. Caixas.\n'
                                                    u'8. Contas Bancárias.\n'))

        return super(account_account, self).unlink(cr, uid, ids, context=context)

account_account()


class account_analytic_account(osv.osv):
    _inherit = "account.analytic.account"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_comum_codigos_contab
            WHERE organica_id = %d OR economica_id = %d OR funcional_id = %d
            """ % (obj.id, obj.id, obj.id))

            res_cod_contab = cr.fetchall()

            cr.execute("""
            SELECT CABL.id
            FROM sncp_despesa_cabimento_linha AS CABL
            WHERE organica_id = %d OR economica_id = %d OR funcional_id = %d
            """ % (obj.id, obj.id, obj.id))

            res_cab_linhas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso_linha
            WHERE organica_id = %d OR economica_id = %d OR funcional_id = %d
            """ % (obj.id, obj.id, obj.id))

            res_comp_linhas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_ordem_linhas_imprimir
            WHERE organica_id = %d OR economica_id = %d OR funcional_id = %d
            """ % (obj.id, obj.id, obj.id))

            res_ordem_imp_linhas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_historico
            WHERE organica_id = %d OR economica_id = %d OR funcional_id = %d
            """ % (obj.id, obj.id, obj.id))

            res_orc_hist = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_acumulados
            WHERE organica_id = %d OR economica_id = %d OR funcional_id = %d
            """ % (obj.id, obj.id, obj.id))

            res_orc_acum = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_linha
            WHERE organica_id = %d OR economica_id = %d OR funcional_id = %d
            """ % (obj.id, obj.id, obj.id))

            res_orc_linhas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_ppi_accoes
            WHERE funcional_id = %d OR organica_id = %d
            """ % (obj.id, obj.id))

            res_ppi_accoes = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_ppi_dotacoes
            WHERE name = %d
            """ % obj.id)

            res_ppi_dotacoes = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_guia_rec_linhas
            WHERE economica_id = %d
            """ % obj.id)

            res_rec_linhas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM account_invoice_line
            WHERE organica_id = %d OR economica_id = %d OR funcional_id = %d
            """ % (obj.id, obj.id, obj.id))

            res_inv_line = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM account_move_line
            WHERE organica_id = %d OR economica_id = %d OR funcional_id = %d
            """ % (obj.id, obj.id, obj.id))

            res_mov_line = cr.fetchall()

            if len(res_cod_contab) != 0 or len(res_cab_linhas) != 0 or len(res_comp_linhas) or \
               len(res_ordem_imp_linhas) != 0 or len(res_orc_hist) != 0 or len(res_orc_acum) != 0 or \
               len(res_orc_linhas) != 0 or len(res_ppi_accoes) != 0 or len(res_ppi_dotacoes) != 0 or \
               len(res_rec_linhas) != 0 or len(res_inv_line) != 0 or len(res_mov_line) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a conta analítica '
                                                    + obj.code + u' ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Códigos de Contabilização.\n'
                                                    u'2. Cabimentos.\n'
                                                    u'3. Compromissos.\n'
                                                    u'4. Ordens de Pagamento.\n'
                                                    u'5. Histórico.\n'
                                                    u'6. Acumulados.\n'
                                                    u'7. Orçamento e Modificações.\n'
                                                    u'8. Acções e Dotações do PPI.\n'
                                                    u'9. Guias de Receita.\n'
                                                    u'10. Movimentos Contabilísticos.\n'
                                                    u'11. Faturas a Clientes e a Fornecedores.'))

            cr.execute("""
            DELETE FROM account_analytic_account
            WHERE id = %d
            """ % obj.id)

        return True

account_analytic_account()


class hr_employee(osv.osv):
    _inherit = "hr.employee"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_comum_param
            WHERE emp_info_cab = %d OR emp_info_com = %d OR emp_tesoureiro = %d AND state = 'draft'
            """ % (obj.id, obj.id, obj.id))

            res_param = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_aprovadores
            WHERE aprovador_id = %d
            """ % obj.id)

            res_aprov = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_requisicoes
            WHERE requisitante_emp_id = %d
            """ % obj.id)

            res_req = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_ppi_accoes
            WHERE responsavel_id = %d
            """ % obj.id)

            res_ppi_accoes = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_regproc_notario_actos_outrg
            WHERE employee_id = %d
            """ % obj.id)

            res_atos_outrg = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_regproc_aquis_alien_notif
            WHERE employee_id = %d
            """ % obj.id)

            res_aliens_notif = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_fundos_maneio
            WHERE empregado_id = %d
            """ % obj.id)

            res_fmaneio = cr.fetchall()

            if len(res_param) != 0 or len(res_aliens_notif) != 0 or len(res_aprov) != 0 or \
               len(res_atos_outrg) != 0 or len(res_req) != 0 or len(res_ppi_accoes) != 0 or \
               len(res_fmaneio) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o empregado ' + obj.name_related
                                                    + u' têm associação em:\n'
                                                    u'1. Parâmetros.\n'
                                                    u'2. Atos Notariais\Registo.\n'
                                                    u'3. Aprovadores.\n'
                                                    u'4. Aquisições e Alienações.\n'
                                                    u'5. Requisições Internas.\n'
                                                    u'6. Acções do PPI.\n'
                                                    u'7. Fundos de Maneio.'))

        return super(hr_employee, self).unlink(cr, uid, ids, context=context)

hr_employee()


class account_journal(osv.osv):
    _inherit = "account.journal"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_comum_param
            WHERE diario_fat_juros = %d OR diario_liq_id = %d OR diario_liq_rec_id = %d
            OR diario_cob_rec_id = %d AND state = 'draft'
            """ % (obj.id, obj.id, obj.id, obj.id))

            res_param = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_fatura_modelo
            WHERE journal_id = %d
            """ % obj.id)

            res_fat_modelo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_diarios_dept
            WHERE journal_id = %d
            """ % obj.id)

            res_diario_dept = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_fundos_maneio
            WHERE diario_id = %d
            """ % obj.id)

            res_fmaneio = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_caixas
            WHERE diario_id = %d
            """ % obj.id)

            res_caixas = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_contas_bancarias
            WHERE diario_id = %d
            """ % obj.id)

            res_contas_bancarias = cr.fetchall()

            if len(res_param) != 0 or len(res_diario_dept) != 0 or len(res_fat_modelo) != 0 or \
               len(res_fmaneio) != 0 or len(res_caixas) != 0 or len(res_contas_bancarias) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o diário ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Parâmetros.\n'
                                                    u'2. Diários.\n'
                                                    u'3. Modelos de Faturas.\n'
                                                    u'4. Fundos de Maneio.\n'
                                                    u'5. Caixas.\n'
                                                    u'6. Contas Bancárias.'))

            cr.execute("""
            DELETE FROM account_journal WHERE id = %d
            """ % obj.id)

        return True

account_journal()


class ir_sequence(osv.osv):
    _inherit = "ir.sequence"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_comum_param
            WHERE ri_sequence_id = %d OR an_sequence_id = %d OR aquis_sequence_id = %d
            OR alien_sequence_id = %d AND state = 'draft'
            """ % (obj.id, obj.id, obj.id, obj.id))

            res_param = cr.fetchall()

            if len(res_param) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a sequência ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Parâmetros.'))

        return super(ir_sequence, self).unlink(cr, uid, ids, context=context)

ir_sequence()


class stock_journal(osv.osv):
    _inherit = "stock.journal"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_comum_param
            WHERE ri_diario_id = %d AND state = 'draft'
            """ % obj.id)

            res_param = cr.fetchall()

            if len(res_param) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o diário de stock ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Parâmetros.'))
            cr.execute("""
            DELETE FROM stock_journal WHERE id = %d
            """ % obj.id)

        return True

stock_journal()


class printing_printer(orm.Model):
    _inherit = "printing.printer"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_comum_param
            WHERE crr_printer_id = %d AND state = 'draft'
            """ % obj.id)

            res_param = cr.fetchall()

            if len(res_param) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a impressora ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Parâmetros.'))

            cr.execute("""
            DELETE FROM printing_printer WHERE id = %d
            """ % obj.id)

        return True

printing_printer()


class hr_department(osv.osv):
    _inherit = "hr.department"

    def unlink(self, cr, uid, ids, context=None):

        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM account_invoice
            WHERE department_id = %d
            """ % obj.id)

            res_invoice = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_aprovadores
            WHERE departamento_id = %d
            """ % obj.id)

            res_aprovadores = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM stock_warehouse
            WHERE department_id = %d
            """ % obj.id)

            res_armazem = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_reposicoes
            WHERE departamento_id = %d
            """ % obj.id)

            res_repo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_requisicoes
            WHERE requisitante_dep_id = %d
            """ % obj.id)

            res_requi = cr.fetchall()

            if len(res_invoice) != 0 or len(res_aprovadores) != 0 or len(res_armazem) != 0 or \
               len(res_repo) != 0 or len(res_requi) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o departamento ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Contabilidade\Faturas de Clientes e Fornecedores.\n'
                                                    u'2. Aprovadores.\n'
                                                    u'3. Armazém\Configuração\Armazéns.\n'
                                                    u'4. Guias de Reposição.\n'
                                                    u'5. Requisições Internas.'))

            cr.execute("""
            DELETE FROM hr_department
            WHERE id = %d
            """ % obj.id)

        return True

hr_department()


class res_users(osv.osv):
    _inherit = "res.users"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_despesa_aprovadores
            WHERE user_id = %d
            """ % obj.id)

            res_aprov = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_autorizacoes
            WHERE user_id = %d
            """ % obj.id)

            res_auto = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_faturas_aprovadas
            WHERE user_id = %d
            """ % obj.id)

            res_fat_aprov = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_ordem
            WHERE conferida_user_id = %d OR autorizada_user_id = %d
            """ % (obj.id, obj.id))

            res_ordem = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_proposta
            WHERE aprov_user = %d
            """ % obj.id)

            res_proposta = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_reposicoes
            WHERE cobrada_emp = %d
            """ % obj.id)

            res_repo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_requisicoes_historico
            WHERE user_id = %d
            """ % obj.id)

            res_req_hist = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo_config
            WHERE renova_aprov_id = %d OR novo_notif1_id = %d OR novo_notif2_id = %d OR novo_notif3_id = %d
            OR caduc_notif1_id = %d OR caduc_notif2_id = %d OR caduc_notif3_id = %d
            OR renov_notif1_id = %d OR renov_notif2_id = %d OR renov_notif3_id = %d OR last_uid = %d
            """ % (obj.id, obj.id, obj.id, obj.id, obj.id, obj.id, obj.id, obj.id, obj.id, obj.id, obj.id))

            res_rec_controlo_config = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo
            WHERE despacho_user_id = %d
            """ % obj.id)

            res_rec_controlo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_guia_rec
            WHERE user_id = %d
            """ % obj.id)

            res_receita = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_itens_user
            WHERE user_id = %d
            """ % obj.id)

            res_item_user = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_regproc_aquis_alien_notif
            WHERE user_id = %d
            """ % obj.id)

            res_alien_notif = cr.fetchall()

            # NAO APAGAR ESTE COMENTARIO
            # cr.execute("""
            # SELECT id
            # FROM sncp_tesouraria_movimentos
            # WHERE reconsil_user = %d
            # """ % obj.id)
            #
            # res_mov = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_caixas_utilizadores AS CX
            WHERE CX.name = %d
            """ % obj.id)

            res_cx_ut = cr.fetchall()

            if len(res_aprov) != 0 or len(res_repo) != 0 or len(res_alien_notif) != 0 or \
               len(res_auto) != 0 or len(res_cx_ut) != 0 or len(res_fat_aprov) != 0 or \
               len(res_item_user) != 0 or len(res_ordem) != 0 or \
               len(res_proposta) != 0 or len(res_rec_controlo) != 0 or len(res_rec_controlo_config) != 0 or \
               len(res_receita) != 0 or len(res_req_hist) != 0:  # or len(res_mov) != 0
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o utilizador ' + obj.partner_id.name
                                                    + u' têm associação em:\n'
                                                    u'1. Aprovadores.\n'
                                                    u'2. Purchases\Aprovação Ordens de Compra\Autorizações.\n'
                                                    u'3. Faturas Aprovadas.\n'
                                                    u'4. Ordens de Pagamento.\n'
                                                    u'5. Propostas.\n'
                                                    u'6. Guias de Reposição.\n'
                                                    u'7. Histórico das Requisições.\n'
                                                    u'8. Receita\Controlo de Receitas Renováveis\Configurações'
                                                    u'\Configuração Geral.\n'
                                                    u'9. Receita\Controlo de Receitas Renováveis.\n'
                                                    u'10. Guias de Receita.\n'
                                                    u'11. Receita\Dados Gerais\Excepções.\n'
                                                    u'12. Aquisições e Alienações.\n'
                                                    u'13. Caixas.'))

        return super(res_users, self).unlink(cr, uid, ids, context=context)

res_users()


class account_move(osv.osv):
    _inherit = "account.move"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_despesa_cabimento
            WHERE doc_contab_id = %d
            """ % obj.id)

            res_cabim = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso_agenda
            WHERE last_doc_contab_id = %d
            """ % obj.id)

            res_comp_agenda = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_ordem
            WHERE doc_liquida_id = %d OR doc_pagam_id = %d
            """ % (obj.id, obj.id))

            res_ordem = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_reposicoes
            WHERE doc_cobranca_id = %d
            """ % obj.id)

            res_repo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_orcamento
            WHERE doc_contab_id = %d
            """ % obj.id)

            res_orc = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_guia_rec
            WHERE doc_liquida_id = %d OR doc_cobra_id = %d
            """ % (obj.id, obj.id))

            res_guia_rec = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_movim_fundos_maneio
            WHERE movimento_id = %d
            """ % obj.id)

            res_mov_fmaneio = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_movim_internos
            WHERE movimento_id = %d
            """ % obj.id)

            res_movim_internos = cr.fetchall()

            if len(res_repo) != 0 or len(res_ordem) != 0 or len(res_cabim) != 0 or len(res_comp_agenda) or \
               len(res_orc) != 0 or len(res_guia_rec) != 0 or len(res_mov_fmaneio) != 0 or \
               len(res_movim_internos) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o movimento contabilístico '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Guias de Reposição.\n'
                                                    u'2. Ordens de Pagamento.\n'
                                                    u'3. Cabimentos.\n'
                                                    u'4. Compromissos.\n'
                                                    u'5. Orçamento e Modificações.\n'
                                                    u'6. Guias de Receita.\n'
                                                    u'7. Movimentos de Fundo de Maneio.\n'
                                                    u'8. Movimentos Internos.'
                                                    ))
        return super(account_move, self).unlink(cr, uid, ids, context=context)

account_move()


class res_partner(osv.osv):
    _inherit = "res.partner"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:

            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso
            WHERE partner_id = %d
            """ % obj.id)

            res_comp = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_descontos_retencoes
            WHERE partner_id = %d
            """ % obj.id)

            res_desc_ret = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_ordem
            WHERE partner_id = %d
            """ % obj.id)

            res_ordem = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_despesa_pagamentos_proposta
            WHERE res_partner_id = %d
            """ % obj.id)

            res_prop = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo
            WHERE partner_id = %d
            """ % obj.id)

            res_controlo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_recorrente_parceiros
            WHERE partner_id = %d
            """ % obj.id)

            res_recorr_parc = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_receita_guia_rec
            WHERE partner_id = %d
            """ % obj.id)

            res_guia = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_regproc_notario_actos_outrg
            WHERE partner_id = %d
            """ % obj.id)

            res_atos_outrg = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_regproc_aquis_alien_parcel_titls
            WHERE partner_id = %d
            """ % obj.id)

            res_alien_parcel_titls = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_regproc_aquis_alien_notif
            WHERE partner_id = %d
            """ % obj.id)

            res_alien_notif = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_cheques
            WHERE partner_id = %d
            """ % obj.id)

            res_cheques = cr.fetchall()

            if len(res_comp) != 0 or len(res_desc_ret) != 0 or len(res_ordem) != 0 or \
               len(res_prop) != 0 or len(res_controlo) != 0 or len(res_recorr_parc) != 0 or \
               len(res_guia) != 0 or len(res_atos_outrg) != 0 or len(res_alien_parcel_titls) != 0 or \
               len(res_alien_notif) != 0 or len(res_cheques) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o parceiro ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Compromissos.\n'
                                                    u'2. Descontos e Retenções.\n'
                                                    u'3. Ordens de Pagamento.\n'
                                                    u'4. Propostas.\n'
                                                    u'5. Receita\Controlo de Receita Renováveis.\n'
                                                    u'6. Receita\Faturação Recorrente\Agendamentos.\n'
                                                    u'7. Guia de Receita.\n'
                                                    u'8. Registo de Processos\Actos Notoriais\Registo.\n'
                                                    u'9. Aquisições e Alienações.\n'
                                                    u'10. Contas Bancárias.'))

        return super(res_partner, self).unlink(cr, uid, ids, context=context)

res_partner()


class res_currency(osv.osv):
    _inherit = 'res.currency'

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_receita_fatura_modelo
            WHERE currency_id = %d
            """ % obj.id)

            res_fat_modelo = cr.fetchall()

            cr.execute("""
            SELECT id
            FROM sncp_tesouraria_contas_bancarias
            WHERE moeda_id = %d
            """ % obj.id)

            res_conta_bancaria = cr.fetchall()

            if len(res_conta_bancaria) != 0 or len(res_fat_modelo) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a moeda '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Modelos de Faturas.\n'
                                                    u'2. Contas Bancárias.'))
            cr.execute("""
            DELETE FROM res_currency
            WHERE id = %d
            """ % obj.id)

        return True

res_currency()