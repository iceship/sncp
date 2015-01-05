CREATE OR REPLACE FUNCTION insere_orcamento_imprimir(orcamento_id integer) RETURNS BOOLEAN AS $$
DECLARE
    dados RECORD;
BEGIN
FOR dados in (SELECT COALESCE(AAA.code,'') AS cd,COALESCE(AAA.name,'') AS nm,COALESCE(OL.reforco,0.0) AS montante,CAST('artigo' AS varchar) AS linha
	      FROM sncp_orcamento_linha AS OL
              LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id 
	      WHERE OL.orcamento_id=$1) LOOP
                INSERT INTO sncp_orcamento_imprimir(codigo,name,linha,montante,orcamento_id) VALUES (dados.cd,dados.nm,dados.linha,dados.montante,$1); 
END LOOP;
RETURN TRUE;
END
$$ LANGUAGE plpgsql;
