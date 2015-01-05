CREATE OR REPLACE FUNCTION insere_modificacao_imprimir_despesa(tipo varchar,ano integer,id integer) RETURNS BOOLEAN AS $$
            DECLARE
                dados RECORD;
            BEGIN
            IF $1='alt' THEN
		    FOR dados IN (SELECT AAA.name AS nm,AAA2.code AS cod_organica,AAA.code AS cod_economica,
		    COALESCE(SUM(OL.reforco),0.0) AS refo,COALESCE(SUM(OL.anulacao),0.0) AS abate,
		    OL.economica_id AS eco_id,OL.organica_id AS org_id,CAST('artigo' AS varchar) AS linha
		    FROM sncp_orcamento_linha AS OL
			      LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
				  LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
				  WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO WHERE SO.ano=$2 AND SO.tipo_orc='alt' and SO.alt_principal=$3 AND SO.titulo='desp')
				  GROUP BY AAA2.code,AAA.code,AAA.name,OL.economica_id,OL.organica_id) LOOP
				    INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha,reforco,abate,economica_id,organica_id) 
				    VALUES (dados.cod_economica,dados.cod_organica,dados.nm,dados.linha,dados.refo,dados.abate,dados.eco_id,dados.org_id);
		    END LOOP;

		    FOR dados IN (SELECT COALESCE(SUM(OL.reforco),0.0) AS refo,
		    COALESCE(SUM(OL.anulacao),0.0) AS abate,AAA2.name AS nm,AAA2.code AS cod_organica,OL.organica_id AS org_id,
		    CAST('cabecalho2' AS varchar) AS linha
			      FROM sncp_orcamento_linha AS OL
			      LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
				  WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO WHERE SO.ano=$2 AND SO.tipo_orc='alt' AND SO.alt_principal=$3 AND SO.titulo='desp')
				  GROUP BY AAA2.code,AAA2.name,OL.organica_id)
		     LOOP
		      INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha,reforco,abate,organica_id) VALUES ('',dados.cod_organica,dados.nm,dados.linha,dados.refo,dados.abate,dados.org_id);
		    END LOOP;
	    ELSIF $1='rev' THEN
		     FOR dados IN (SELECT AAA.name AS nm,AAA2.code AS cod_organica,AAA.code AS cod_economica,
		    COALESCE(SUM(OL.reforco),0.0) AS refo,COALESCE(SUM(OL.anulacao),0.0) AS abate,
		    OL.economica_id AS eco_id,OL.organica_id AS org_id,CAST('artigo' AS varchar) AS linha
		    FROM sncp_orcamento_linha AS OL
			      LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
				  LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
				  WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO WHERE SO.ano=$2 AND SO.tipo_orc='rev' and SO.numero=$3 AND SO.titulo='desp')
				  GROUP BY AAA2.code,AAA.code,AAA.name,OL.economica_id,OL.organica_id) LOOP
				    INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha,reforco,abate,economica_id,organica_id) 
				    VALUES (dados.cod_economica,dados.cod_organica,dados.nm,dados.linha,dados.refo,dados.abate,dados.eco_id,dados.org_id);
		    END LOOP;

		    FOR dados IN (SELECT COALESCE(SUM(OL.reforco),0.0) AS refo,
		    COALESCE(SUM(OL.anulacao),0.0) AS abate,AAA2.name AS nm,AAA2.code AS cod_organica,OL.organica_id AS org_id,
		    CAST('cabecalho2' AS varchar) AS linha
			      FROM sncp_orcamento_linha AS OL
			      LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
				  WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO WHERE SO.ano=$2 AND SO.tipo_orc='rev' and SO.numero=$3 AND SO.titulo='desp')
				  GROUP BY AAA2.code,AAA2.name,OL.organica_id)
		     LOOP
		      INSERT INTO sncp_modificacao_imprimir_despesa(codigo_eco,codigo_org,name,linha,reforco,abate,organica_id) VALUES ('',dados.cod_organica,dados.nm,dados.linha,dados.refo,dados.abate,dados.org_id);
		    END LOOP;	
	    END IF;	
            RETURN TRUE;
            END
            $$ LANGUAGE plpgsql;