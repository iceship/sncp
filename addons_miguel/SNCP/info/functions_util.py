__author__ = 'exeq'


def inserir_estados_no_meio(self):
    estados = [('a', 1), ('c', 3), ('b', 2)]
    estados.insert(estados.index(('c', 3)), ('d', 4))

    # estados = [('a', 1), ('d', 4), ('c', 3), ('b', 2)]


def pesquisa_valores_tabelas(self, cr):
    cr.execute("""
            SELECT IT.table_name
            FROM information_schema.tables AS IT
            """)

    lista = cr.fetchall()
    lista = [elem[0] for elem in lista]

    lista_resultados = []
    for tabela in lista:
        if tabela in ['_pg_foreign_data_wrappers', '_pg_foreign_servers', '_pg_foreign_tables',
                      '_pg_user_mappings', 'administrable_role_authorizations', 'applicable_roles',
                      'attributes', 'character_sets', 'check_constraint_routine_usage',
                      'check_constraints', 'collation_character_set_applicability', 'collations',
                      'column_domain_usage', 'column_privileges', 'column_udt_usage', 'columns',
                      'constraint_column_usage', 'constraint_table_usage', 'data_type_privileges',
                      'domain_constraints', 'domain_udt_usage', 'domains', 'element_types', 'enabled_roles',
                      'foreign_data_wrapper_options', 'foreign_data_wrappers', 'foreign_server_options',
                      'foreign_servers', 'foreign_table_options', 'foreign_tables',
                      'information_schema_catalog_name', 'key_column_usage', 'parameters',
                      'referential_constraints', 'role_column_grants', 'role_routine_grants',
                      'role_table_grants', 'role_usage_grants', 'routine_privileges',
                      'routines', 'schemata', 'sequences', 'sql_features', 'sql_implementation_info',
                      'sql_languages', 'sql_packages', 'sql_parts', 'sql_sizing', 'sql_sizing_profiles',
                      'table_constraints', 'table_privileges', 'tables', 'triggered_update_columns',
                      'triggers', 'usage_privileges', 'user_mapping_options', 'user_mappings',
                      'view_column_usage', 'view_routine_usage', 'view_table_usage', 'views']:
            tabela = 'information_schema.' + tabela

        cr.execute("""
        SELECT IC.column_name FROM information_schema.columns AS IC
        WHERE IC.data_type IN ('character varying','text') AND IC.table_name='%s'
        """ % tabela)
        lista_campos = cr.fetchall()
        lista_campos = [elem[0] for elem in lista_campos]
        for campo in lista_campos:
            alias = "SNCP."+campo
            apelido = " AS SNCP"
            query = str("SELECT "+alias+" FROM "+tabela+apelido+" WHERE SNCP."+campo +" LIKE 'Lock%'")
            if campo == 'RSA_signature':
                pass
            else:
                cr.execute(query)
                result = cr.fetchone()
                if result is not None:
                    lista_resultados.append({'tabela': tabela, 'campo': campo})

    return lista_resultados