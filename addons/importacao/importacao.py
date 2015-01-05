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

import os

from openerp.osv import osv


class importacao(osv.Model):
    _name = 'importacao'
    _auto = False

    def parceiros(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM res_partner""")
        x = True
        lista = cr.fetchall()
        for elem in lista:
            if elem[0] in range(5, 8):
                x = False
                break

        if x is True:
            ficheiro = caminho_ficheiro + u'res_partner.csv'
            cr.execute("""COPY res_partner(id,name,lang,company_id,color,active,supplier,employee,customer,is_company,
            display_name,notification_email_send,use_parent_address,opt_out)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)

            cr.execute("""SELECT MAX(id) FROM res_partner""")

            maximo = cr.fetchone()
            cr.execute("""SELECT setval('res_partner_id_seq',%d);""" % maximo[0])
        return True

    def utilizadores(self, cr, caminho_ficheiro):
        db_res_users = self.pool.get('res.users')
        db_res_partner = self.pool.get('res.partner')
        partner_id = False
        for elem in ['funcag', 'secgeral']:
            cr.execute("""SELECT id FROM res_users WHERE login='%s'""" % elem)

            user_id = cr.fetchone()

            if user_id is None:
                if elem == 'funcag':
                    cr.execute("""SELECT id FROM res_partner WHERE name LIKE 'Fun%'""")
                    partner_id = cr.fetchone()
                    if partner_id is None:
                        dict_partner = {
                            'name': elem,
                            'lang': 'pt_PT',
                            'company_id': 1,
                            'color': 0,
                            'active': True,
                            'supplier': False,
                            'employee': False,
                            'customer': False,
                            'is_company': False,
                            'display_name': elem,
                        }
                        partner_id = db_res_partner.create(cr, 1, dict_partner)
                    else:
                        partner_id = partner_id[0]
                elif elem == 'secgeral':
                    cr.execute("""SELECT id FROM res_partner WHERE name LIKE 'Sec%'""")
                    partner_id = cr.fetchone()
                    if partner_id is None:
                        dict_partner = {
                            'name': elem,
                            'lang': 'pt_PT',
                            'company_id': 1,
                            'color': 0,
                            'active': True,
                            'supplier': False,
                            'employee': False,
                            'customer': False,
                            'is_company': False,
                            'display_name': elem,
                        }
                        partner_id = db_res_partner.create(cr, 1, dict_partner)
                    else:
                        partner_id = partner_id[0]

                dict_user = {
                    'active': True,
                    'login': elem,
                    'password': 'xb800',
                    'company_id': 1,
                    'partner_id': partner_id,
                    'menu_id': 1,
                    'share': False
                }

                db_res_users.create(cr, 1, dict_user)

        cr.execute("""SELECT MAX(id) FROM res_users""")

        maximo = cr.fetchone()
        cr.execute("""SELECT setval('res_users_id_seq',%d);""" % maximo[0])
        return True

    def taxas(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM account_tax""")
        x = True
        lista = cr.fetchall()
        for elem in lista:
            if elem[0] in range(1, 5):
                x = False
                break

        if x is True:
            ficheiro = caminho_ficheiro + u'account_tax.csv'
            cr.execute("""COPY account_tax(id,active,applicable_type,type_tax_use,description,company_id,amount,name,
            type,sequence) FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)

            cr.execute("""SELECT MAX(id) FROM account_tax""")

            maximo = cr.fetchone()
            cr.execute("""SELECT setval('account_tax_id_seq',%d);""" % maximo[0])
        return True

    def categorias_produtos(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM product_category""")
        lista = cr.fetchall()
        x = True

        for elem in lista:
            if elem[0] in range(3, 11):
                x = False
                break

        if x is True:
            ficheiro = caminho_ficheiro + u'product_category.csv'
            cr.execute("""COPY product_category(id,parent_id,type,name) FROM '%s' DELIMITER ',' CSV HEADER;"""
                       % ficheiro)

            cr.execute("""SELECT MAX(id) FROM product_category""")

            maximo = cr.fetchone()
            cr.execute("""SELECT setval('product_category_id_seq',%d);""" % maximo[0])
        return True

    def unidades_produtos(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM product_uom""")

        lista = cr.fetchall()

        x = True

        for elem in lista:
            if elem[0] == 12:
                x = False
                break

        if x is True:
            ficheiro = caminho_ficheiro + u'product_uom.csv'
            cr.execute("""COPY product_uom(id,active,category_id,rounding,factor,uom_type,name)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)

            cr.execute("""SELECT MAX(id) FROM product_uom""")

            maximo = cr.fetchone()
            cr.execute("""SELECT setval('product_uom_id_seq',%d);""" % maximo[0])
        return True

    def product_template(self, cr, caminho_ficheiro):
        cr.execute(""" SELECT id FROM product_template """)
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(2, 11937):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'product_template.csv'
            cr.execute("""
            COPY product_template(id,list_price,uom_id,categ_id,name,sale_ok,company_id,uom_po_id,type,
            purchase_ok,active)
            FROM '%s' DELIMITER ',' CSV HEADER;
            """ % ficheiro)

            cr.execute("""SELECT MAX(id) FROM product_template""")

            maximo = cr.fetchone()
            cr.execute("""SELECT setval('product_template_id_seq',%d);""" % maximo[0])
        return True

    def product(self, cr, caminho_ficheiro):
        cr.execute(""" SELECT id FROM product_product """)
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(2, 11937):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'product_product.csv'
            cr.execute("""COPY product_product(id,default_code,name_template,active,product_tmpl_id)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""
            SELECT MAX(id)
            FROM product_product
            """)

            maximo = cr.fetchone()
            cr.execute("""SELECT setval('product_product_id_seq',%d);""" % maximo[0])
        return True

    def product_taxa_rel(self, cr, caminho_ficheiro):
        cr.execute("""SELECT prod_id,tax_id FROM product_taxes_rel""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(2, 11937):
                if elem[1] == 4 or elem[1] == 1:
                    x = False
        cr.execute("""SELECT prod_id,tax_id FROM product_supplier_taxes_rel""")
        lista2 = cr.fetchall()
        x2 = True
        for elem in lista2:
            if elem[0] in range(2, 11937):
                if elem[1] == 4 or elem[1] == 1:
                    x2 = False
        if x is True and x2 is True:
            ficheiro = caminho_ficheiro + u'product_supplier_taxes_rel.csv'
            cr.execute("""
            COPY product_taxes_rel(prod_id,tax_id)
            FROM '%s' DELIMITER ',' CSV HEADER;
            COPY product_supplier_taxes_rel(prod_id,tax_id)
            FROM '%s' DELIMITER ',' CSV HEADER;
            """ % (ficheiro, ficheiro))
        return True

    def tipos_contas(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM account_account_type""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(27, 30):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'account_account_type.csv'
            cr.execute("""COPY account_account_type(id,code,note,close_method,report_type,name)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM account_account_type""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('account_account_type_id_seq',%d);""" % maximo[0])
        return True

    def contas(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM account_account""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 2741):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'account_account.csv'
            cr.execute("""COPY account_account(id,code,user_type,active,name,level,parent_id,currency_mode,type,
            company_id) FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM account_account""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('account_account_id_seq',%d);""" % maximo[0])
        return True

    def contas_analiticas(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM account_analytic_account""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 3088):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'account_analytic_account.csv'
            cr.execute("""COPY account_analytic_account(id,tipo_dim,code,name,type,parent_id,state,currency_id,
            company_id,estado) FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM account_analytic_account""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('account_analytic_account_id_seq',%d);""" % maximo[0])
        return True

    def meios_pagamento(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_comum_meios_pagamento""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 12):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_comum_meios_pagamento.csv'
            cr.execute("""COPY sncp_comum_meios_pagamento(id,metodo,name,meio,tipo)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_comum_meios_pagamento""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_comum_meios_pagamento_id_seq',%d);""" % maximo[0])
        return True

    def cond_pagam(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_comum_cond_pagam""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 10):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_comum_cond_pagam.csv'
            cr.execute("""COPY sncp_comum_cond_pagam(id,contagem,anual,name,descricao,dia,mes,dias_descanso,quantidade,
            tipo,estado) FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_comum_cond_pagam""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_comum_cond_pagam_id_seq',%d);""" % maximo[0])
        return True

    def cpv(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_comum_cpv""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 9455):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_comum_cpv.csv'
            cr.execute("""COPY sncp_comum_cpv(id,codigo_120,name)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_comum_cpv""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_comum_cpv_id_seq',%d);""" % maximo[0])
        return True

    def cofinanciamentos(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_despesa_cofinanciamentos""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 4):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_despesa_cofinanciamentos.csv'
            cr.execute("""COPY sncp_despesa_cofinanciamentos(id,name,codigo)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_despesa_cofinanciamentos""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_despesa_cofinanciamentos_id_seq',%d);""" % maximo[0])
        return True

    def fundamentos(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_despesa_fundamentos""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 13):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_despesa_fundamentos.csv'
            cr.execute("""COPY sncp_despesa_fundamentos(id,codigo_120,name)
                        FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_despesa_fundamentos""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_despesa_fundamentos_id_seq',%d);""" % maximo[0])
        return True

    def naturezas(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_despesa_naturezas""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 40):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_despesa_naturezas.csv'
            cr.execute("""COPY sncp_despesa_naturezas(id,name,empreitada,codigo_120)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_despesa_naturezas""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_despesa_naturezas_id_seq',%d);""" % maximo[0])
        return True

    def procedimentos(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_despesa_procedimentos""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 9):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_despesa_procedimentos.csv'
            cr.execute("""COPY sncp_despesa_procedimentos(id,codigo_120,name)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_despesa_procedimentos""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_despesa_procedimentos_id_seq',%d);""" % maximo[0])
        return True

    def fundos_disponiveis(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_despesa_fundos_disponiveis""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 14):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_despesa_fundos_disponiveis.csv'
            cr.execute("""COPY sncp_despesa_fundos_disponiveis(id,name,mes,reservado,montante)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_despesa_fundos_disponiveis""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_despesa_fundos_disponiveis_id_seq',%d);""" % maximo[0])
        return True

    def juros(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_receita_juros""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 5):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_receita_juros.csv'
            cr.execute("""COPY sncp_receita_juros(id,name,descricao,contagem,periodo,item_id,ignora,aviso)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_receita_juros""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_receita_juros_id_seq',%d);""" % maximo[0])
        return True

    def juros_periodos(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_receita_juros_periodos""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 8):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_receita_juros_periodos.csv'
            cr.execute("""COPY sncp_receita_juros_periodos(id,juros_id,name,data_ini,data_fim)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_receita_juros_periodos""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_receita_juros_periodos_id_seq',%d);""" % maximo[0])
        return True

    def juros_periodos_linhas(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_receita_juros_periodos_linhas""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 9):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_receita_juros_periodos_linhas.csv'
            cr.execute("""COPY sncp_receita_juros_periodos_linhas(id,seq_juros_id,name,taxa_perc,taxa_tipo,substitui)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_receita_juros_periodos_linhas""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_receita_juros_periodos_linhas_id_seq',%d);""" % maximo[0])
        return True

    def cod_contab(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_comum_codigos_contab""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 782):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_comum_codigos_contab.csv'
            cr.execute("""COPY sncp_comum_codigos_contab(id,natureza,conta_id,economica_id,name,item_id,cond_pag_id,
            met_juros_id,code) FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_comum_codigos_contab""")

            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_comum_codigos_contab_id_seq',%d);""" % maximo[0])
        return True

    def sequencias(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM ir_sequence""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(36, 59):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'ir_sequence.csv'
            cr.execute("""COPY ir_sequence(id,number_next,number_increment,implementation,company_id,padding,active,
            prefix,name) FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM ir_sequence""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('ir_sequence_id_seq',%d);""" % maximo[0])
            cr.execute("""SELECT MAX(id) FROM ir_sequence_type""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('ir_sequence_type_id_seq',%d);""" % maximo[0])
        return True

    def diarios(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM account_journal""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(2, 21):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'account_journal.csv'
            cr.execute("""COPY account_journal(id,default_debit_account_id,default_credit_account_id,code,company_id,
            currency,name,type,sequence_id) FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM account_journal""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('account_journal_id_seq',%d);""" % maximo[0])
        return True

    def departamentos(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM hr_department""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 7):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'hr_department.csv'
            cr.execute("""COPY hr_department(id,name,company_id,parent_id,manager_id)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM hr_department""")

            maximo = cr.fetchone()
            cr.execute("""SELECT setval('hr_department_id_seq',%d);""" % maximo[0])
        return True

    def cargos(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM hr_job""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 6):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'hr_job.csv'
            cr.execute("""COPY hr_job(id,name,company_id,state,expected_employees,no_of_employee,department_id)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM hr_job""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('hr_job_id_seq',%d);""" % maximo[0])
        return True

    def tipos_movimento(self, cr, caminho_ficheiro):
        cr.execute(""" SELECT id FROM sncp_tesouraria_tipo_mov""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 8):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_tesouraria_tipo_mov.csv'
            cr.execute("""COPY sncp_tesouraria_tipo_mov(id,conta_id,name,codigo,mov_interno,destino_tipo,origem_tipo)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_tesouraria_tipo_mov""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_tesouraria_tipo_mov_id_seq',%d);""" % maximo[0])
        return True

    def caixas(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_tesouraria_caixas""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 4):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_tesouraria_caixas.csv'
            cr.execute("""COPY sncp_tesouraria_caixas(id,name,codigo,conta_id,diario_id)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_tesouraria_caixas""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_tesouraria_caixas_id_seq',%d);""" % maximo[0])
        return True

    def contas_bancarias(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_tesouraria_contas_bancarias""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 4):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_tesouraria_contas_bancarias.csv'
            cr.execute("""COPY sncp_tesouraria_contas_bancarias(id,conta,name,moeda_id,state,iban,codigo,diario_id,
            conta_id,swift,tipo) FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_tesouraria_contas_bancarias""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_tesouraria_contas_bancarias_id_seq',%d);""" % maximo[0])
        return True

    def fundos_maneio(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_tesouraria_fundos_maneio""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 5):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_tesouraria_fundos_maneio.csv'
            cr.execute("""COPY sncp_tesouraria_fundos_maneio(id,codigo,ativo,name,empregado_id,diario_id,conta_id)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_tesouraria_fundos_maneio""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_tesouraria_fundos_maneio_id_seq',%d);""" % maximo[0])
        return True

    def config_mapas(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_tesouraria_config_mapas""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 36):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_tesouraria_config_mapas.csv'
            cr.execute("""COPY sncp_tesouraria_config_mapas(id,natureza,name,meio,origem,tipo_mov_id,meio_pag_id,coluna)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_tesouraria_config_mapas""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_tesouraria_config_mapas_id_seq',%d);""" % maximo[0])
        return True

    def config_resumo(self, cr, caminho_ficheiro):
        cr.execute("""SELECT id FROM sncp_orcamento_resumo_config""")
        lista = cr.fetchall()
        x = True
        for elem in lista:
            if elem[0] in range(1, 43):
                x = False
                break
        if x is True:
            ficheiro = caminho_ficheiro + u'sncp_orcamento_resumo_config.csv'
            cr.execute("""COPY sncp_orcamento_resumo_config(id,ordem,depend,name,align,coluna,valor,bold)
            FROM '%s' DELIMITER ',' CSV HEADER;""" % ficheiro)
            cr.execute("""SELECT MAX(id) FROM sncp_orcamento_resumo_config""")
            maximo = cr.fetchone()
            cr.execute("""SELECT setval('sncp_orcamento_resumo_config_id_seq',%d);""" % maximo[0])
        return True

    def etiquetas(self, cr, caminho_ficheiro):
        db_sncp_comum_etiquetas = self.pool.get('sncp.comum.etiquetas')
        etiquetas = [
            ('partner_id.title.name', u'Título do Parceiro de Negócios', 'PNTITL', ''),
            ('partner_id.name', u'Nome do Parceiro de Negócios', 'PNNOME', ''),
            ('partner_id.street', u'Morada do Parceiro de Negócios', 'PNMORA', ''),
            ('partner_id.street2', u'Morada do Parceiro de Negócios', 'PNMOR2', ''),
            ('partner_id.zip', u'Código Postal do Parceiro de Negócios', 'PNCODP', ''),
            ('partner_id.city', u'Localidade do Parceiro de Negócios', 'PNLOCA', ''),
            ('partner_id.vat', u'Identificação fiscal do Parceiro de Negócios', 'PNNIFX', ''),
            ('arruamento_id.name', u'Arruamento da Licença', 'LCARRU', 'sncp.receita.controlo'),
            ('cod_contab_id.item_id.name', u'Descrição do Ítem', 'LCITEM', 'sncp.receita.controlo.config'),
            ('numero', u'Número de Polícia da Licença', 'LCNPOL', 'sncp.receita.controlo'),
            ('andar', u'Andar da Licença', 'LCANDA', 'sncp.receita.controlo'),
            ('bairro_id.name', u'Bairro da Licença', 'LCBAIR', 'sncp.comum.bairros'),
            ('freguesia_id.name', u'Freguesia da Licença', 'LCFREG', 'sncp.receita.controlo'),
            ('zona_id.name', u'Zona de Venda Ambulante', 'LCZONA', 'sncp.receita.zonas.venda.amb'),
            ('mercado_id.name', u'Mercado/Feira', 'LCMERC', 'sncp.receita.mercados.feiras'),
            ('finalidade_id.name', u'Finalidade', 'LCFINA', 'sncp.receita.oep.finalidades'),
            ('num_itens', u'Número de Lugares', 'LCNLUG', 'sncp.receita.controlo'),
            ('name', u'Número de Série', 'LCSERI', 'sncp.receita.controlo'),
            ('notas', u'Notas', 'LCNOTA', 'sncp.receita.controlo'),
            ('fim', u'Expira em', 'LCEXPI', 'sncp.receita.controlo'),
        ]
        for line in etiquetas:
            if len(line[3]) > 0:
                cr.execute("""SELECT id FROM ir_model WHERE model = '%s'""" % line[3])
                result = cr.fetchone()
                modelo = result[0]
            else:
                modelo = 0
            # Bloco de gravação
            cr.execute("""
            SELECT id FROM sncp_comum_etiquetas
            WHERE name='%s'
            """ % line[2])

            ha_etiqueta = cr.fetchone()

            if ha_etiqueta is None:
                db_sncp_comum_etiquetas.create(cr, 1, {
                    'path': line[0],
                    'descr': line[1],
                    'name': line[2],
                    'model_id': modelo
                })

        return True

    def init(self, cr):
        caminho = os.getcwd()
        caminho_ficheiro = unicode(caminho) + u'/SNCP/data/sql_import/'

        self.parceiros(cr, caminho_ficheiro)
        self.utilizadores(cr, caminho_ficheiro)
        self.taxas(cr, caminho_ficheiro)
        self.categorias_produtos(cr, caminho_ficheiro)
        self.unidades_produtos(cr, caminho_ficheiro)
        self.product_template(cr, caminho_ficheiro)
        self.product(cr, caminho_ficheiro)
        self.product_taxa_rel(cr, caminho_ficheiro)
        self.tipos_contas(cr, caminho_ficheiro)
        self.contas(cr, caminho_ficheiro)
        self.contas_analiticas(cr, caminho_ficheiro)
        self.meios_pagamento(cr, caminho_ficheiro)
        self.cond_pagam(cr, caminho_ficheiro)
        self.cpv(cr, caminho_ficheiro)
        self.cofinanciamentos(cr, caminho_ficheiro)
        self.fundamentos(cr, caminho_ficheiro)
        self.naturezas(cr, caminho_ficheiro)
        self.procedimentos(cr, caminho_ficheiro)
        self.fundos_disponiveis(cr, caminho_ficheiro)
        self.juros(cr, caminho_ficheiro)
        self.juros_periodos(cr, caminho_ficheiro)
        self.juros_periodos_linhas(cr, caminho_ficheiro)
        self.cod_contab(cr, caminho_ficheiro)
        self.sequencias(cr, caminho_ficheiro)
        self.diarios(cr, caminho_ficheiro)
        self.departamentos(cr, caminho_ficheiro)
        self.cargos(cr, caminho_ficheiro)
        self.tipos_movimento(cr, caminho_ficheiro)
        self.caixas(cr, caminho_ficheiro)
        self.contas_bancarias(cr, caminho_ficheiro)
        self.fundos_maneio(cr, caminho_ficheiro)
        self.config_mapas(cr, caminho_ficheiro)
        self.config_resumo(cr, caminho_ficheiro)
        self.etiquetas(cr, caminho_ficheiro)

