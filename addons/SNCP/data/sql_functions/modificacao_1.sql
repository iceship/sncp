CREATE OR REPLACE FUNCTION insere_modificacao_imprimir_receita(tipo varchar,ano integer,id integer) RETURNS BOOLEAN AS $$
DECLARE
  dados RECORD;
  BEGIN
    IF $1='alt' THEN
	FOR dados in (SELECT COALESCE(AAA.code,'') AS cd,COALESCE(AAA.name,'') AS nm,COALESCE(SUM(OL.reforco),0.0) AS reforco,
	    CAST('artigo' AS varchar) AS linha,COALESCE(SUM(OL.anulacao),0.0) AS anulacao,OL.economica_id AS eco_id 
            FROM sncp_orcamento_linha AS OL
            LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
            WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO WHERE SO.ano=$2 AND SO.tipo_orc='alt' and SO.alt_principal=$3 AND SO.titulo='rece') 
            GROUP BY AAA.code,AAA.name,linha,OL.economica_id) 
            LOOP
		INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,linha,reforco,abate,economica_id) 
		VALUES (dados.cd,dados.nm,dados.linha,dados.reforco,dados.anulacao,dados.eco_id);
            END LOOP;	
        ELSIF $1='rev' THEN
           FOR dados in (SELECT COALESCE(AAA.code,'') AS cd,COALESCE(AAA.name,'') AS nm,COALESCE(SUM(OL.reforco),0.0) AS reforco,
	       CAST('artigo' AS varchar) AS linha,COALESCE(SUM(OL.anulacao),0.0) AS anulacao,OL.economica_id AS eco_id 
               FROM sncp_orcamento_linha AS OL
               LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
               WHERE OL.orcamento_id IN (SELECT SO.id FROM sncp_orcamento AS SO WHERE SO.ano=$2 AND SO.tipo_orc='rev' and SO.numero=$3 AND SO.titulo='rece')  
	       GROUP BY AAA.code,AAA.name,linha,OL.economica_id)
               LOOP
		INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,linha,reforco,abate,economica_id) 
                VALUES (dados.cd,dados.nm,dados.linha,dados.reforco,dados.anulacao,dados.eco_id);
           END LOOP;
        END IF; 
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;