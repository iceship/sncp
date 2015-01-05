CREATE OR REPLACE function get_parents_economica(codigo_org varchar,codigo_eco varchar,orcamento_id integer) RETURNS boolean AS $$
DECLARE 
	ok boolean=TRUE;
	codigo_atual varchar;
	parent_atual integer;
	linha varchar;
	dados RECORD;
BEGIN 
 FOR dados IN (SELECT AAA.code,AAA.name,AAA.parent_id FROM account_analytic_account AS AAA WHERE code=$2
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
	      linha='capitulo';
	   ELSIF LENGTH(codigo_atual) = 4 THEN
	      linha='grupo';
	   ELSE
	      linha='';
	   END IF;        

	   IF dados.code NOT IN (SELECT PO.codigo_eco FROM sncp_orcamento_imprimir_despesa AS PO WHERE PO.codigo_eco=dados.code 
	   AND PO.codigo_org=$1) THEN
		INSERT INTO sncp_orcamento_imprimir_despesa(codigo_eco,codigo_org,name,linha,orcamento_id) VALUES (dados.code,$1,dados.name,linha,$3);
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
