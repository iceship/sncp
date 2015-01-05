--__TAX______________________Taxas__________________________________________________
COPY account_tax(id,active,applicable_type,type_tax_use,description,company_id,amount,name,type,sequence)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/account_tax.csv' DELIMITER ',' CSV HEADER;
SELECT setval('account_tax_id_seq',4);


--__PRODUCT__________________Categoria dos Produtos_________________________________
COPY product_category(id,parent_id,type,name) 
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/product_category.csv' DELIMITER ',' CSV HEADER;
SELECT setval('product_category_id_seq',19);

--__PRODUCT__________________Unidades dos Produtos_________________________________
COPY product_uom(id,active,category_id,rounding,factor,uom_type,name)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/product_uom.csv' DELIMITER ',' CSV HEADER;
SELECT setval('product_uom_id_seq',12);

--__PRODUCT__________________Template dos Produtos_________________________________
COPY product_template(id,list_price,uom_id,cost_method,categ_id,name,sale_ok,company_id,uom_po_id,type,supply_method,procure_method,purchase_ok,standard_price)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/product_template.csv' DELIMITER ',' CSV HEADER;
SELECT setval('product_template_id_seq',11936);

--__PRODUCT__________________Produtos_________________________________
COPY product_product(id,default_code,name_template,active,valuation,product_tmpl_id)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/product_product.csv' DELIMITER ',' CSV HEADER;
SELECT setval('product_product_id_seq',11936);

--__PRODUCT/ACCOUNT__________________Relações Produto-Taxa_________________________________
COPY product_taxes_rel(prod_id,tax_id)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/product_supplier_taxes_rel.csv' DELIMITER ',' CSV HEADER;
COPY product_supplier_taxes_rel(prod_id,tax_id)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/product_supplier_taxes_rel.csv' DELIMITER ',' CSV HEADER;

--__ACCOUNT__________________Tipos de Contas_________________________________
COPY account_account_type(id,code,note,close_method,report_type,name)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/account_type.csv' DELIMITER ',' CSV HEADER;
SELECT setval('account_account_type_id_seq',28);

--__ACCOUNT__________________Contas_________________________________
COPY account_account(id,code,user_type,active,name,level,parent_id,currency_mode,type,company_id)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/account_account.csv' DELIMITER ',' CSV HEADER;
SELECT setval('account_account_id_seq',2741);

--__ACCOUNT__________________Dimensões_________________________________
COPY account_analytic_account(id,tipo_dim,code,name,type,parent_id,state,currency_id,company_id,estado)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/account_analytic_account.csv' DELIMITER ',' CSV HEADER;
SELECT setval('account_analytic_account_id_seq',3009);

--__COMUM__________________Meios de Pagamento_________________________________
COPY sncp_comum_meios_pagamento(id,metodo,name,meio,tipo)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_comum_meios_pagamento.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_comum_meios_pagamento_id_seq',11);

--__COMUM__________________Etiquetas___________________________________________
--COPY sncp_comum_etiquetas(id,path,descr,name,model_id)
--FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_comum_etiquetas.csv' DELIMITER ',' CSV HEADER;
--SELECT setval('sncp_comum_etiquetas_id_seq',20);

--__COMUM__________________Condições de Pagamento_________________________________
COPY sncp_comum_cond_pagam(id,contagem,anual,name,descricao,dia,mes,dias_descanso,quantidade,tipo,estado)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_comum_cond_pagam.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_comum_cond_pagam_id_seq',9);

--__COMUM__________________CPV_________________________________
COPY sncp_comum_cpv(id,codigo_120,name)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_comum_cpv.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_comum_cpv_id_seq',9454);

--__DESPESA__________________Co-Financiamentos_________________________________
COPY sncp_despesa_cofinanciamentos(id,name,codigo)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_despesa_cofinanciamentos.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_despesa_cofinanciamentos_id_seq',4);

--__DESPESA__________________Fundamentos_________________________________
COPY sncp_despesa_fundamentos(id,codigo_120,name)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_despesa_fundamentos.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_despesa_fundamentos_id_seq',12);

--__DESPESA__________________Naturezas_________________________________
COPY sncp_despesa_naturezas(id,name,empreitada,codigo_120)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_despesa_naturezas.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_despesa_naturezas_id_seq',40);

--__DESPESA__________________Procedimentos_________________________________
COPY sncp_despesa_procedimentos(id,codigo_120,name)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_despesa_procedimentos.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_despesa_procedimentos_id_seq',9);

--__DESPESA__________________Fundos Disponíveis_________________________________
COPY sncp_despesa_fundos_disponiveis(id,name,mes,reservado,montante)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_despesa_fundos_disponiveis.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_despesa_fundos_disponiveis_id_seq',14);

--__RECEITA__________________Juros_________________________________
COPY sncp_receita_juros(id,name,descricao,contagem,periodo,item_id,ignora,aviso)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_receita_juros.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_receita_juros_id_seq',5);

--__RECEITA__________________Juros Periodos_________________________________
COPY sncp_receita_juros_periodos(id,juros_id,name,data_ini,data_fim)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_receita_juros_periodos.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_receita_juros_periodos_id_seq',8);

--__RECEITA__________________Juros Periodos Linhas_________________________________
COPY sncp_receita_juros_periodos_linhas(id,seq_juros_id,name,taxa_perc,taxa_tipo,substitui)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_receita_juros_periodos_linhas.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_receita_juros_periodos_linhas_id_seq',9);

--__COMUM__________________Códigos de Contabilização_________________________________
COPY sncp_comum_codigos_contab(id,natureza,conta_id,economica_id,name,item_id,cond_pag_id,met_juros_id,code)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_comum_codigos_contab.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_comum_codigos_contab_id_seq',781);

--__SEQUENCE_______________Sequências___________________________________________________
COPY ir_sequence(id,number_next,number_increment,implementation,company_id,padding,active,prefix,name)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/ir_sequence.csv' DELIMITER ',' CSV HEADER;
SELECT setval('ir_sequence_id_seq',51);
SELECT setval('ir_sequence_type_id_seq',20);

--__ACCOUNT__________________Diários_________________________________
COPY account_journal(id,default_debit_account_id,default_credit_account_id,code,company_id,currency,name,type,sequence_id)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/account_journal.csv' DELIMITER ',' CSV HEADER;
SELECT setval('account_journal_id_seq',20);

--__HR_DEPARTMENT__________________Departamentos_________________________________
COPY hr_department(id,name,company_id,parent_id,manager_id)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/hr_department.csv' DELIMITER ',' CSV HEADER;
SELECT setval('hr_department_id_seq',6);

--__HR_JOB_______________________CARGOS____________________________________________
COPY hr_job(id,name,company_id,state,expected_employees,no_of_employee,department_id)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/hr_job.csv' DELIMITER ',' CSV HEADER;
SELECT setval('hr_job_id_seq',5);

--__TESOURARIA__________________Tipos de movimento_________________________________
COPY sncp_tesouraria_tipo_mov(id,conta_id,name,codigo,mov_interno,destino_tipo,origem_tipo)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_tesouraria_tipo_mov.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_tesouraria_tipo_mov_id_seq',7);

--__TESOURARIA___________________CAIXAS_____________________________________________
COPY sncp_tesouraria_caixas(id,name,codigo,conta_id,diario_id)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_tesouraria_caixas.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_tesouraria_caixas_id_seq',3);

--__TESOURARIA___________________CONTAS BANCARIAS_____________________________________________
COPY sncp_tesouraria_contas_bancarias(id,conta,name,moeda_id,state,iban,codigo,diario_id,conta_id,swift,tipo)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_tesouraria_contas_bancarias.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_tesouraria_contas_bancarias_id_seq',3);

--__TESOURARIA___________________FUNDOS DE MANEIO_____________________________________________
COPY sncp_tesouraria_fundos_maneio(id,codigo,ativo,name,empregado_id,diario_id,conta_id)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_tesouraria_fundos_maneio.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_tesouraria_fundos_maneio_id_seq',4);

--__TESOURARIA__________________CONFIGURAÇÃO DE MAPAS_________________________________________
COPY sncp_tesouraria_config_mapas(id,natureza,name,meio,origem,tipo_mov_id,meio_pag_id,coluna)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_tesouraria_config_mapas.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_tesouraria_config_mapas_id_seq',35);

--__ORÇAMENTO___________________ CONFIGURAÇÃO DO RESUMO___________________________________________
COPY sncp_orcamento_resumo_config(id,ordem,depend,name,align,coluna,valor,bold)
FROM '/home/exeq/PycharmProjects/addons/SNCP/data/sql_import/sncp_orcamento_resumo_config.csv' DELIMITER ',' CSV HEADER;
SELECT setval('sncp_orcamento_resumo_config_id_seq',42);
