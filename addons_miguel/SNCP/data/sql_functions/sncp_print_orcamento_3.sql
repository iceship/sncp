CREATE OR REPLACE function get_parents(codigo varchar,orcamento_id integer) RETURNS boolean AS $$
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
	      linha='capitulo';
	   ELSIF LENGTH(codigo_atual) = 4 THEN
	      linha='grupo';
	   ELSE
	      linha='';
	   END IF;        

	   IF dados.code NOT IN (SELECT PO.codigo FROM sncp_orcamento_imprimir AS PO WHERE PO.codigo=dados.code) THEN
		INSERT INTO sncp_orcamento_imprimir(codigo,name,linha,orcamento_id) VALUES (dados.code,dados.name,linha,$2);
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
