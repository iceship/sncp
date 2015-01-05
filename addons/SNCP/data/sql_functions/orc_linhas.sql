CREATE OR REPLACE FUNCTION linhas_orcamento_mm_dimensoes(orcamento_id integer,tipo varchar) RETURNS varchar AS $$
DECLARE
  linha_orc RECORD;
  mensagem varchar='';
  num_linhas integer;
BEGIN
    FOR linha_orc IN (SELECT * FROM sncp_orcamento_linha AS SOL WHERE SOL.orcamento_id=$1) LOOP
	IF $2='rece' THEN
		num_linhas=(SELECT COUNT(id) 
		    FROM sncp_orcamento_linha AS OL
		    WHERE OL.orcamento_id=$1 AND OL.economica_id=linha_orc.economica_id
		    );
	ELSIF $2='desp' THEN
	      num_linhas=(SELECT COUNT(id)
			  FROM sncp_orcamento_linha AS OL
			  WHERE OL.orcamento_id=$1 AND OL.economica_id=linha_orc.economica_id AND OL.organica_id=linha_orc.organica_id
			  AND ( (OL.funcional_id IS NULL AND linha_orc.funcional_id IS NULL) OR
               			(OL.funcional_id IS NOT NULL AND linha_orc.funcional_id = OL.funcional_id))
			    );
	END IF;

	IF num_linhas > 1 THEN
	   IF $2='rece' THEN
		mensagem='A combinação  Orgânica()/Económica(' || 
			 (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_orc.economica_id) 
			 || ')/Funcional() encontra-se repetida';
	   ELSIF $2='desp' THEN
	   	mensagem='A combinação  Orgânica('
	   	         || (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_orc.organica_id) ||
	   	         ')/Económica(' || 
			 (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_orc.economica_id);
		IF linha_orc.funcional_id IS NULL THEN
		   mensagem= mensagem || ')/Funcional() encontra-se repetida';
		ELSE
		   mensagem=mensagem || ')/Funcional(' || 
		   (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_orc.funcional_id) ||') encontra-se repetida';
		END IF;
	   
	  END IF;    
	RETURN mensagem;
	END IF;
    END LOOP;	
RETURN mensagem; 
END
$$ LANGUAGE plpgsql;