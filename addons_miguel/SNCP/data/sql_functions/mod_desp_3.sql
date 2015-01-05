CREATE OR REPLACE function get_mod_desp_parents_organica(codigo_org varchar) RETURNS boolean AS $$
        DECLARE
            ok boolean=TRUE;
            codigo_atual varchar;
            parent_atual integer;
            linha varchar;
            dados RECORD;
        BEGIN
         FOR dados IN (SELECT AAA.code,AAA.name,AAA.parent_id FROM account_analytic_account AS AAA WHERE code=$1
                LIMIT 1) LOOP

         parent_atual=dados.parent_id;
         IF parent_atual IS NULL
            THEN ok=false;
         END IF;
        END LOOP;
         WHILE (ok=true) LOOP
           FOR dados IN (SELECT code,name,parent_id FROM account_analytic_account WHERE id=parent_atual) LOOP

               codigo_atual=TRIM(dados.code);
               IF LOWER(SUBSTRING(codigo_atual from 1 for 1)) NOT BETWEEN '0' AND '9' THEN
               codigo_atual=SUBSTRING(codigo_atual from 2 for LENGTH(codigo_atual));
               END IF;

               IF LENGTH(codigo_atual) = 2 THEN
                  linha='cabecalho1';
               ELSE
                  linha='cabecalho2';
               END IF;

               IF dados.code NOT IN (SELECT PO.codigo_org FROM sncp_modificacao_imprimir_despesa AS PO WHERE PO.codigo_org=dados.code
               AND PO.codigo_eco='') THEN
                INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha) VALUES ('',dados.code,dados.name,linha);
                parent_atual=dados.parent_id;
                IF parent_atual IS NULL THEN
                    ok=false;
                END IF;
               ELSE
                  ok=false;
               END IF;
          END LOOP;
        END LOOP;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;