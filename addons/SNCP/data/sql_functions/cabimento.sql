CREATE OR REPLACE FUNCTION montante_consolidado_cabimento_associado(cab_id integer,linha integer) RETURNS numeric AS 
$$	
BEGIN
    RETURN (SELECT COALESCE(SUM(CABLINHA.montante),0.0)
	    FROM sncp_despesa_cabimento_linha AS CABLINHA
	    WHERE CABLINHA.cabimento_id IN (SELECT id FROM sncp_despesa_cabimento WHERE origem_id=$1 OR cabimento_id=$1) 
	    AND CABLINHA.linha=$2 
           ); 		
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION montante_consolidado_compromisso_ano_linha_associado(cab_id integer,linha integer,ano_atual integer) RETURNS numeric AS 
$$
BEGIN
    RETURN (SELECT COALESCE(SUM(COMPLINHA.montante),0.0)
	    FROM sncp_despesa_compromisso_linha AS COMPLINHA
	    WHERE COMPLINHA.compromisso_ano_id IN (SELECT id FROM sncp_despesa_compromisso_ano WHERE cabimento_id=$1 AND ano=$3) 
	    AND COMPLINHA.linha=$2  
           ); 		
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION atualizar_estado(cab_id integer,ano_atual integer) RETURNS boolean AS 
$$
DECLARE
    linha_cabimento sncp_despesa_cabimento_linha%ROWTYPE;
    montante_cabimento_consolidado numeric;
    montante_compromisso_consolidado numeric;
    num_linhas integer;
    num_linhas_cons integer;
    estado varchar;	
BEGIN
     FOR linha_cabimento IN (SELECT * FROM sncp_despesa_cabimento_linha WHERE cabimento_id=$1) LOOP
	montante_cabimento_consolidado=montante_consolidado_cabimento_associado($1,linha_cabimento.linha);
	montante_compromisso_consolidado=montante_consolidado_compromisso_ano_linha_associado($1,linha_cabimento.linha,$2);
	IF montante_cabimento_consolidado=montante_compromisso_consolidado THEN
	   UPDATE sncp_despesa_cabimento_linha SET state_line='cons' WHERE id=linha_cabimento.id;
	ELSIF linha_cabimento.state_line='cons' THEN
	   UPDATE sncp_despesa_cabimento_linha SET state_line='cont' WHERE id=linha_cabimento.id;	
        END IF;
     END LOOP;

     estado=(SELECT state FROM sncp_despesa_cabimento WHERE id=$1);
     num_linhas=(SELECT COUNT(id) FROM sncp_despesa_cabimento_linha WHERE cabimento_id=$1);
     num_linhas_cons=(SELECT COUNT(id) FROM sncp_despesa_cabimento_linha WHERE cabimento_id=$1 AND state_line='cons');
     IF num_linhas=num_linhas_cons THEN
	UPDATE sncp_despesa_cabimento SET state='cons' 
	WHERE id =$1;
     ELSIF estado='cons' THEN
        UPDATE sncp_despesa_cabimento SET state_line='cont' 
	WHERE id=$1;
     END IF;
     RETURN TRUE;   		
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION contabiliza_cabimento(cab_id integer,user_id integer,journal_id integer,dh varchar,ref varchar) RETURNS varchar AS 
$$
DECLARE
	caldata date;
	datahora timestamp;
	novadatahora timestamp;
	ano integer;
	disp_orc integer;
	mensagem varchar='';
	conta_credito integer;
	conta_debito integer;
	disporc numeric;
	move_id integer;
	move_line_id integer;
	ok boolean;
	origem_id integer;
	linha_cabimento sncp_despesa_cabimento_linha%ROWTYPE;
	
BEGIN
     caldata=$4::date;
     datahora=$4::timestamp;	
     ano=EXTRACT(YEAR FROM caldata);	
     move_id=insere_movimento_contabilistico($2,$3,caldata,$5,ano);
     UPDATE sncp_despesa_cabimento SET data = caldata WHERE id = $1;

     conta_debito=(SELECT default_debit_account_id FROM account_journal WHERE id=$3);
     conta_credito=(SELECT default_credit_account_id FROM account_journal WHERE id=$3);

     FOR linha_cabimento in SELECT * FROM sncp_despesa_cabimento_linha WHERE cabimento_id=$1 LOOP	
	disporc=da_disponibilidade_orcamental(ano,linha_cabimento.organica_id,linha_cabimento.economica_id,linha_cabimento.funcional_id);
	IF disporc<linha_cabimento.montante THEN
		mensagem='A disponibilidade orçamental é de ' || disporc;
	END IF;
	IF LENGTH(mensagem)>0 THEN
        RETURN mensagem;
        END IF;	

	IF linha_cabimento.montante<0 THEN
	
		move_line_id=insere_linha_movimento_contabilistico(conta_credito,$3,caldata,$5,
		move_id,abs(linha_cabimento.montante),linha_cabimento.organica_id,linha_cabimento.economica_id,
		linha_cabimento.funcional_id,'debit');

		move_line_id=insere_linha_movimento_contabilistico(conta_debito,$3,caldata,$5,
		move_id,abs(linha_cabimento.montante),linha_cabimento.organica_id,linha_cabimento.economica_id,
		linha_cabimento.funcional_id,'credit');
	ELSE
	    move_line_id=insere_linha_movimento_contabilistico(conta_debito,$3,caldata,$5,
	    move_id,linha_cabimento.montante,linha_cabimento.organica_id,linha_cabimento.economica_id,
	    linha_cabimento.funcional_id,'debit');

	    move_line_id=insere_linha_movimento_contabilistico(conta_credito,$3,caldata,$5,
            move_id,linha_cabimento.montante,linha_cabimento.organica_id,linha_cabimento.economica_id,
	    linha_cabimento.funcional_id,'credit');
        END IF;
        	
        novadatahora=insere_linha_historico(ano,'04cabim',datahora,
        linha_cabimento.organica_id,linha_cabimento.economica_id,linha_cabimento.funcional_id,
        linha_cabimento.montante,move_id,move_line_id,NULL,linha_cabimento.cabimento_id,linha_cabimento.id,NULL,NULL);

        ok=insere_linha_acumulados(ano,'04cabim',linha_cabimento.organica_id,
        linha_cabimento.economica_id,linha_cabimento.funcional_id,linha_cabimento.montante);

        UPDATE sncp_despesa_cabimento_linha SET state_line='cont' WHERE id=linha_cabimento.id;	
     END LOOP;
     UPDATE sncp_despesa_cabimento SET state = 'cont',doc_contab_id=move_id WHERE id = $1;
     origem_id=(SELECT CAB.origem_id FROM sncp_despesa_cabimento AS CAB WHERE id=$1);
     IF origem_id IS NOT NULL THEN
	ok=atualizar_estado($1,ano);
     END IF;
     		
RETURN mensagem;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION anula_cabimento(cab_id integer) RETURNS varchar AS 
$$
DECLARE
    mensagem varchar='';
    compromisso_ano sncp_despesa_compromisso_ano%ROWTYPE;
    linha_cabimento sncp_despesa_cabimento_linha%ROWTYPE;	
    ok boolean;
    origem integer;
    nano integer;
    ndata date;
    nmove_id integer;
    montante_consolidado_linha_cab numeric;
    montante_consolidado_linha_comp_ano numeric;
BEGIN
     origem=(SELECT origem_id FROM sncp_despesa_cabimento WHERE id=$1);
     ndata=(SELECT CAB.data FROM sncp_despesa_cabimento AS CAB WHERE id=$1);
     nano=EXTRACT(YEAR FROM ndata); 	
     nmove_id=(SELECT doc_contab_id FROM sncp_despesa_cabimento WHERE id=$1);	
     IF origem IS NULL THEN
	FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano  AS COMPANO WHERE COMPANO.ano=nano AND cabimento_id =$1) LOOP
		mensagem='Não é possível anular pois existe compromissos associados';
		IF LENGTH(mensagem) > 0 THEN 
			RETURN mensagem;
	        END IF;
	END LOOP;
     ELSE
	FOR linha_cabimento IN (SELECT * FROM sncp_despesa_cabimento_linha AS CABLINHA WHERE CABLINHA.cabimento_id=$1) LOOP
	 IF linha_cabimento.montante>0.0 THEN
	    FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano  AS COMPANO WHERE COMPANO.ano=nano AND cabimento_id=origem) LOOP
	        montante_consolidado_linha_cab=montante_consolidado_cabimento_associado(origem,linha_cabimento.linha)
	        -linha_cabimento.montante;
                montante_consolidado_linha_comp_ano=montante_consolidado_compromisso_ano_linha_associado(origem,
                linha_cabimento.linha,nano);
                IF montante_consolidado_linha_cab < montante_consolidado_linha_comp_ano THEN
		   mensagem='Valor insuficiente para cobrir os compromissos';
		   IF LENGTH(mensagem) > 0 THEN
		      RETURN mensagem;
		   END IF;
	        END IF;
	    END LOOP;
	END IF;
       END LOOP;
     END IF;
     ok=elimina_historico_orc_mod_cab(nano,'04cabim',nmove_id);
     UPDATE sncp_despesa_cabimento_linha SET state_line='anul' WHERE cabimento_id=$1;
     DELETE FROM account_move_line AS AML WHERE AML.move_id=nmove_id;
     DELETE FROM account_move WHERE id=nmove_id;
     UPDATE sncp_despesa_cabimento SET state = 'anul',cabimento=NULL,doc_contab_id=NULL,origem_id=NULL,data=NULL WHERE id = $1;		
RETURN mensagem;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION da_valor_disponivel(cab_id integer,linha integer,ano integer) RETURNS numeric AS 
$$
DECLARE
    mensagem varchar='';
    cabimento_linha sncp_despesa_cabimento_linha%ROWTYPE;
    montante_cab numeric;
    montante_comp numeric;
BEGIN
     FOR cabimento_linha IN (SELECT * FROM sncp_despesa_cabimento_linha AS CABLINHA WHERE CABLINHA.cabimento_id=$1 and CABLINHA.linha=$2) LOOP
         IF cabimento_linha.state_line <> 'cont' THEN
		RETURN 0.0;
	 END IF;
	 montante_cab=montante_consolidado_cabimento_associado($1,$2);
	 montante_comp=montante_consolidado_compromisso_ano_linha_associado($1,$2,$3);
	 RETURN montante_cab - montante_comp; 
     END LOOP;	
END;
$$ LANGUAGE plpgsql;
