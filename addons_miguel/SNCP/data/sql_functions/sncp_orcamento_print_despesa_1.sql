CREATE OR REPLACE FUNCTION insere_orcamento_imprimir_despesa(orcamento_id integer) RETURNS BOOLEAN AS $$
DECLARE
    dados RECORD;
BEGIN
FOR dados IN (SELECT SUM(OL.reforco) AS montante,AAA.name AS nm,AAA2.code AS cod_organica,AAA.code AS cod_economica,
              CAST('artigo' AS varchar) AS linha
	      FROM sncp_orcamento_linha AS OL
	      LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
              LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
              WHERE OL.orcamento_id = $1
              GROUP BY AAA2.code,AAA.code,AAA.name) LOOP
                INSERT INTO sncp_orcamento_imprimir_despesa(codigo_eco,codigo_org,name,linha,montante,orcamento_id) VALUES (dados.cod_economica,dados.cod_organica,dados.nm,dados.linha,dados.montante,$1); 
END LOOP;

FOR dados IN (SELECT SUM(OL.reforco) AS montante,AAA2.name AS nm,AAA2.code AS cod_organica,
              CAST('cabecalho2' AS varchar) AS linha
	      FROM sncp_orcamento_linha AS OL
	      LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
              WHERE OL.orcamento_id = $1
              GROUP BY AAA2.code,AAA2.name) 
 LOOP
  INSERT INTO sncp_orcamento_imprimir_despesa(codigo_eco,codigo_org,name,linha,montante,orcamento_id) VALUES ('',dados.cod_organica,dados.nm,dados.linha,dados.montante,$1); 
END LOOP;              

RETURN TRUE;
END
$$ LANGUAGE plpgsql;