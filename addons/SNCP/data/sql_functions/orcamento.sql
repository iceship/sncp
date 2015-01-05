CREATE OR REPLACE FUNCTION insere_linha_historico(ano integer,categoria varchar,datahora timestamp,
organica_id integer,economica_id integer,funcional_id integer,
montante numeric,move_id integer,linha_move_id integer,centrocustos_id integer,cabimento_id integer,
cabimento_linha_id integer,compromisso_id integer,compromisso_linha_id integer) RETURNS TIMESTAMP AS
$$
BEGIN
 INSERT INTO sncp_orcamento_historico(name,categoria,datahora,organica_id,economica_id,funcional_id,montante,doc_contab_id,
 doc_contab_linha_id,centrocustos_id,cabimento_id,cabimento_linha_id,compromisso_id,compromisso_linha_id)
 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14);
RETURN $3;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insere_linha_acumulados(ano integer,categoria varchar,organica_id integer,
economica_id integer,funcional_id integer,montante numeric) RETURNS boolean AS 
$$
DECLARE 
	linha_acumulados sncp_orcamento_acumulados%ROWTYPE;
	encontrado boolean=FALSE;
BEGIN
FOR linha_acumulados IN SELECT * FROM sncp_orcamento_acumulados AS SOA WHERE SOA.name = $1 AND SOA.categoria = $2 AND SOA.economica_id = $4 AND 
(
 (($3 IS NULL AND $5 IS NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id IS NULL)) OR
 (($3 IS NULL AND $5 IS NOT NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id = $5)) OR
 (($3 IS NOT NULL AND $5 IS NULL) AND (SOA.organica_id =$3 AND SOA.funcional_id IS NULL)) OR
 (($3 IS NOT NULL AND $5 IS NOT NULL) AND (SOA.organica_id = $3 and SOA.funcional_id = $5))
) LOOP
encontrado=TRUE;
UPDATE sncp_orcamento_acumulados SET montante = linha_acumulados.montante+$6 WHERE id = linha_acumulados.id;
END LOOP;

IF encontrado=FALSE THEN
   INSERT INTO sncp_orcamento_acumulados(name,categoria,organica_id,economica_id,funcional_id,montante)
VALUES ($1,$2,$3,$4,$5,$6);   	
END IF;
RETURN TRUE;
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_companhia(user_id integer) RETURNS integer AS
$$
BEGIN
RETURN (SELECT company_id FROM res_users WHERE id=$1);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_periodo(date) RETURNS integer AS
$$
BEGIN
RETURN (SELECT id FROM account_period WHERE $1 BETWEEN date_start AND date_stop);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insere_movimento_contabilistico(user_id integer,journal_id integer,date,ref varchar,ano integer) RETURNS integer AS $$
DECLARE
 periodo_id integer;
 companhia_id integer;
 nome varchar;
BEGIN
periodo_id=get_periodo($3);
companhia_id=get_companhia($1);
nome=$4 || ' ' || $5;
INSERT INTO account_move(name,ref,period_id,journal_id,state,date,company_id)
VALUES (nome,ref,periodo_id,$2,'draft',$3,companhia_id);
RETURN (SELECT currval('account_move_id_seq'));
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_dados_orcamento(orc_id integer,out ano integer,out categoria varchar,
out deb1 integer,out cred1 integer,out deb2 integer,out cred2 integer) AS $$
DECLARE
 orcamento sncp_orcamento%ROWTYPE;
BEGIN
SELECT * INTO orcamento FROM sncp_orcamento WHERE id=$1;
ano=orcamento.ano;
IF orcamento.titulo='rece' THEN
		categoria='51rdota';
		deb1=(SELECT id FROM account_account WHERE code='011');
		cred1=(SELECT id FROM account_account WHERE code='031');
		deb2=cred1;
		cred2=(SELECT id FROM account_account WHERE code='034');
ELSIF orcamento.titulo='desp' THEN
		categoria='01ddota';
		deb1=(SELECT id FROM account_account WHERE code='011');
		cred1=(SELECT id FROM account_account WHERE code='021');
		deb2=cred1;
		cred2=(SELECT id FROM account_account WHERE code='023');
ELSE
		categoria='';
		deb1=0;
		cred1=0;
		deb2=0;
		cred2=0; 
END IF;
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insere_linha_movimento_contabilistico(conta_id integer,journal_id integer,date,ref varchar,
move_id integer,valor numeric,organica_id integer,economica_id integer,funcional_id integer,
deb_creb varchar) RETURNS integer AS $$
DECLARE
	periodo_id integer;
BEGIN
periodo_id = get_periodo($3);
IF $10='credit' THEN
	INSERT INTO account_move_line(account_id,date,journal_id,period_id,name,move_id,credit,organica_id,economica_id,
	funcional_id) VALUES($1,$3,$2,periodo_id,$4,$5,$6,$7,$8,$9);
	RETURN (SELECT currval('account_move_line_id_seq'));
ELSE
	INSERT INTO account_move_line(account_id,date,journal_id,period_id,name,move_id,debit,organica_id,economica_id,
	funcional_id) VALUES($1,$3,$2,periodo_id,$4,$5,$6,$7,$8,$9);
	RETURN (SELECT currval('account_move_line_id_seq'));
END IF;		
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION contabiliza(orc_id integer,user_id integer,journal_id integer,varchar,ref varchar) RETURNS boolean AS 
$$
DECLARE
	ok boolean;
    datahora timestamp;
	move_line_id integer;
	move_id integer;
	dados RECORD;
	linha_orcamento sncp_orcamento_linha%ROWTYPE;
    novadatahora timestamp;
BEGIN
     dados=get_dados_orcamento($1);	
     move_id=insere_movimento_contabilistico($2,$3,$4::date,$5,dados.ano);
     UPDATE sncp_orcamento SET doc_contab_id = move_id WHERE id = $1;
     FOR linha_orcamento in SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=$1 LOOP	
    
	 move_line_id=insere_linha_movimento_contabilistico(dados.deb1,$3,$4::date,$5,move_id,linha_orcamento.reforco,
	 linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,'debit');

         move_line_id=insere_linha_movimento_contabilistico(dados.cred1,$3,$4::date,$5,
         move_id,linha_orcamento.reforco,linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,
         'credit');

         move_line_id=insere_linha_movimento_contabilistico(dados.deb2,$3,$4::date,$5,move_id,linha_orcamento.reforco,
         linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,'debit');

         move_line_id=insere_linha_movimento_contabilistico(dados.cred2,$3,$4::date,$5,move_id,linha_orcamento.reforco,
         linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,'credit');

         novadatahora=insere_linha_historico(dados.ano,dados.categoria,$4::timestamp,
         linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,
         linha_orcamento.reforco,move_id,move_line_id,NULL,NULL,NULL,NULL,NULL);

         ok=insere_linha_acumulados(dados.ano,dados.categoria,linha_orcamento.organica_id,
         linha_orcamento.economica_id,linha_orcamento.funcional_id,linha_orcamento.reforco);	
     END LOOP;
     UPDATE sncp_orcamento SET state = 'accounted',contab=TRUE WHERE id = $1;		
RETURN ok;
END;
$$ LANGUAGE plpgsql;



DELETE FROM sncp_orcamento_historico;
DELETE FROM sncp_orcamento_acumulados;
DELETE FROM account_move_line;
DELETE FROM account_move;
