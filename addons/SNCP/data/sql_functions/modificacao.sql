CREATE OR REPLACE FUNCTION abate_possivel(integer) RETURNS varchar AS $$
DECLARE
    lin sncp_orcamento_linha%ROWTYPE;
    mensagem varchar='';
    ano integer;
BEGIN
    ano=(SELECT SO.ano FROM sncp_orcamento AS SO WHERE id=$1);	
    FOR lin in SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=$1 LOOP
	      IF lin.anulacao>0 THEN
		IF verifica_abate(ano,lin.organica_id,lin.economica_id,lin.funcional_id,lin.anulacao)=FALSE THEN
		   mensagem='Para a combinação ' || '[' || COALESCE((SELECT CONCAT(code,' ',name) FROM account_analytic_account WHERE id=lin.organica_id),'') || '/ '
		   || COALESCE((SELECT CONCAT(code,' ',name) FROM account_analytic_account WHERE id=lin.economica_id),'') || '/ '
		   || COALESCE((SELECT CONCAT(code,' ',name) FROM account_analytic_account WHERE id=lin.funcional_id),'') || ']' 
		   || ' o abate de ' || lin.anulacao ||' não é possível'; 
		   RETURN mensagem; 
                END IF;
              END IF;
   END LOOP;
   RETURN mensagem;
END;$$ LANGUAGE plpgsql;


CREATE or REPLACE FUNCTION da_valor_acumulado(ano integer,categoria varchar,organica_id integer,economica_id integer,funcional_id integer) RETURNS NUMERIC AS $$
BEGIN 

RETURN (SELECT COALESCE(SUM(montante), 0.0)
FROM sncp_orcamento_acumulados AS SOA
WHERE SOA.name = $1 AND
 SOA.categoria = $2 AND
 SOA.economica_id = $4 AND 
(
 (($3 IS NULL AND $5 IS NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id IS NULL)) OR
 (($3 IS NULL AND $5 IS NOT NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id = $5)) OR
 (($3 IS NOT NULL AND $5 IS NULL) AND (SOA.organica_id =$3 AND SOA.funcional_id IS NULL)) OR
 (($3 IS NOT NULL AND $5 IS NOT NULL) AND (SOA.organica_id = $3 and SOA.funcional_id = $5))
));
END;$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION da_disponibilidade_orcamental(ano integer,organica_id integer,economica_id integer,funcional_id integer) RETURNS NUMERIC AS $$
DECLARE
	somadotacao numeric;
        somareforcos numeric;
        somaabates numeric;
        somacabimentos numeric;
BEGIN
    somadotacao=da_valor_acumulado($1,'01ddota',$2,$3,$4);
    somareforcos=da_valor_acumulado($1,'02drefo',$2,$3,$4);
    somaabates=da_valor_acumulado($1,'03dabat',$2,$3,$4);
    somacabimentos=da_valor_acumulado($1,'04cabim',$2,$3,$4);
    RETURN somadotacao+somareforcos-somaabates-somacabimentos;	
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION verifica_abate(ano integer,organica_id integer,economica_id integer,funcional_id integer,anulacao numeric) RETURNS BOOLEAN AS
$$
DECLARE
 disporc numeric;
BEGIN
    disporc=da_disponibilidade_orcamental($1,$2,$3,$4);
    IF disporc < $5 THEN
	RETURN FALSE;
    ELSE
	RETURN TRUE;
    END IF;
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_dados_alteracao_revisao(orc_id integer,out ano integer,out tipo_mod varchar,
out titulo varchar) AS $$
DECLARE
 modificacao sncp_orcamento%ROWTYPE;
BEGIN
SELECT * INTO modificacao FROM sncp_orcamento WHERE id=$1;
ano=modificacao.ano;
tipo_mod=modificacao.tipo_mod;
titulo=modificacao.titulo;
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION contabiliza_modificacao(orc_id integer,user_id integer,journal_id integer,varchar,ref varchar) RETURNS varchar AS 
$$
DECLARE
	ok boolean;
        datahora timestamp;
	move_line_id integer;
	move_id integer;
	dados RECORD;
	deb1 integer;
	cred1 integer;
	deb2 integer;
	cred2 integer;
	categoria varchar;
	mensagem varchar;
	linha_orcamento sncp_orcamento_linha%ROWTYPE;
        novadatahora timestamp;
BEGIN
     dados=get_dados_alteracao_revisao($1);
     mensagem=abate_possivel($1);
     IF LENGTH(mensagem)>0 THEN
	RETURN mensagem;
     END IF;
     move_id=insere_movimento_contabilistico($2,$3,$4::date,$5,dados.ano);
     UPDATE sncp_orcamento SET doc_contab_id = move_id WHERE id = $1;
     FOR linha_orcamento in SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=$1 LOOP
	 IF linha_orcamento.reforco>0.0 THEN
		IF dados.titulo='rece' THEN
			deb1=(SELECT id FROM account_account WHERE code='03211');
			cred1=(SELECT id FROM account_account WHERE code='031');
			deb2=(SELECT id FROM account_account WHERE code='034');
			cred2=deb1;
			categoria='52rrefo';
	        ELSE
		    deb1=(SELECT id FROM account_account WHERE code='011');
		    cred1=(SELECT id FROM account_account WHERE code='02211');
		    deb2=cred1;
		    cred2=(SELECT id FROM account_account WHERE code='023');
		    categoria='02drefo';
		END IF;
	ELSE
		IF dados.titulo='rece' THEN
			deb1=(SELECT id FROM account_account WHERE code='031');
			cred1=(SELECT id FROM account_account WHERE code='0322');
			deb2=cred1;
			cred2=(SELECT id FROM account_account WHERE code='034');
			categoria='53rabat';
	        ELSE
		    deb1=(SELECT id FROM account_account WHERE code='02212');
		    cred1=(SELECT id FROM account_account WHERE code='011');
		    deb2=(SELECT id FROM account_account WHERE code='023');
		    cred2=deb1;
		    categoria='03dabat';
		END IF;
	END IF;		
    
	 move_line_id=insere_linha_movimento_contabilistico(deb1,$3,$4::date,$5,move_id,COALESCE(linha_orcamento.reforco,0.0)
         +COALESCE(linha_orcamento.anulacao,0.0),
	 linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,'debit');

         move_line_id=insere_linha_movimento_contabilistico(cred1,$3,$4::date,$5,
         move_id,COALESCE(linha_orcamento.reforco,0.0)
         +COALESCE(linha_orcamento.anulacao,0.0),linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,
         'credit');

         move_line_id=insere_linha_movimento_contabilistico(deb2,$3,$4::date,$5,move_id,COALESCE(linha_orcamento.reforco,0.0)
         +COALESCE(linha_orcamento.anulacao,0.0),
         linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,'debit');

         move_line_id=insere_linha_movimento_contabilistico(cred2,$3,$4::date,$5,move_id,COALESCE(linha_orcamento.reforco,0.0)
         +COALESCE(linha_orcamento.anulacao,0.0),
         linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,'credit');

         datahora=(SELECT ($4::date + INTERVAL '1 second' - INTERVAL '1 hour'));

         novadatahora=insere_linha_historico(dados.ano,categoria,datahora,
         linha_orcamento.organica_id,linha_orcamento.economica_id,linha_orcamento.funcional_id,
         COALESCE(linha_orcamento.reforco,0.0)
         +COALESCE(linha_orcamento.anulacao,0.0),move_id,move_line_id,NULL,NULL,NULL,NULL,NULL);
		
         ok=insere_linha_acumulados(dados.ano,categoria,linha_orcamento.organica_id,
         linha_orcamento.economica_id,linha_orcamento.funcional_id,COALESCE(linha_orcamento.reforco,0.0)
         +COALESCE(linha_orcamento.anulacao,0.0));	
     END LOOP;
     UPDATE sncp_orcamento SET state = 'accounted',contab=TRUE WHERE id = $1;		
RETURN mensagem;
END;
$$ LANGUAGE plpgsql;
