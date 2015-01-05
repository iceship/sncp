CREATE OR REPLACE FUNCTION elimina_acumulados(name integer,categoria varchar,organica_id integer,economica_id integer,funcional_id integer,montante numeric) RETURNS boolean AS $$
DECLARE
    lin sncp_orcamento_acumulados%ROWTYPE;
BEGIN
     FOR lin in SELECT * FROM sncp_orcamento_acumulados AS SOA WHERE SOA.name = $1 AND SOA.categoria = $2 AND SOA.economica_id = $4 
     AND 
(
 (($3 IS NULL AND $5 IS NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id IS NULL)) OR
 (($3 IS NULL AND $5 IS NOT NULL) AND (SOA.organica_id IS NULL AND SOA.funcional_id = $5)) OR
 (($3 IS NOT NULL AND $5 IS NULL) AND (SOA.organica_id =$3 AND SOA.funcional_id IS NULL)) OR
 (($3 IS NOT NULL AND $5 IS NOT NULL) AND (SOA.organica_id = $3 and SOA.funcional_id = $5))
) LOOP
    UPDATE sncp_orcamento_acumulados SET montante=lin.montante-$6 WHERE id=lin.id;
END LOOP;
RETURN TRUE;	
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION elimina_historico_orc_mod_cab(name integer,categoria varchar,move_id integer) RETURNS boolean AS $$
DECLARE
    lin sncp_orcamento_historico%ROWTYPE;
    ok boolean;
BEGIN
     FOR lin in SELECT * FROM sncp_orcamento_historico AS SOH WHERE SOH.name = $1 AND SOH.categoria = $2 AND SOH.doc_contab_id=$3
     LOOP
     ok=elimina_acumulados(lin.name,lin.categoria,lin.organica_id,lin.economica_id,lin.funcional_id,lin.montante);
	DELETE FROM sncp_orcamento_historico WHERE id=lin.id;
     END LOOP;
RETURN TRUE;	
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_dados_orcamento_anular(orc_id integer,out ano integer,out categoria varchar,out move_id integer) AS $$
DECLARE
 orcamento sncp_orcamento%ROWTYPE;
BEGIN
SELECT * INTO orcamento FROM sncp_orcamento WHERE id=$1;
ano=orcamento.ano;
move_id=orcamento.doc_contab_id;
IF orcamento.titulo='rece' THEN
		categoria='51rdota';
ELSIF orcamento.titulo='desp' THEN
		categoria='01ddota';
ELSE
		categoria='';
END IF;
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION anula_orcamento(orc_id integer) RETURNS varchar AS 
$$
DECLARE
    mensagem varchar='';
    lin_historico sncp_orcamento_historico%ROWTYPE;
    dados RECORD;
    ok boolean;
BEGIN
     dados=get_dados_orcamento_anular($1);	
     FOR lin_historico IN SELECT * FROM sncp_orcamento_historico AS SOH WHERE SOH.categoria='04cabim' AND SOH.name=dados.ano
     LOOP
	mensagem='Não é possível anular pois existe cabimento para o ano ' || dados.ano;	
     END LOOP;
     IF LENGTH(mensagem)<>0 THEN
	RETURN mensagem;
     END IF;
     ok=elimina_historico_orc_mod_cab(dados.ano,dados.categoria,dados.move_id);
     DELETE FROM account_move_line WHERE move_id=dados.move_id;
     DELETE FROM account_move WHERE id=dados.move_id;
     UPDATE sncp_orcamento SET state = 'approved',contab=FALSE,doc_contab_id=NULL WHERE id = $1;		
RETURN mensagem;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_dados_alteracao_revisao_anular(orc_id integer,out titulo integer,out ano integer,out move_id integer) AS $$
DECLARE
 orcamento sncp_orcamento%ROWTYPE;
BEGIN
SELECT * INTO orcamento FROM sncp_orcamento WHERE id=$1;
ano=orcamento.ano;
titulo=orcamento.titulo;
move_id=orcamento.doc_contab_id;
END;$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION anula_modificacao(orc_id integer) RETURNS varchar AS 
$$
DECLARE
    mensagem varchar='';
    lin_orcamento sncp_orcamento_linha%ROWTYPE;
    dados RECORD;
    ano integer;
    ok boolean;
    categoria varchar;
BEGIN
     dados=get_dados_alteracao_revisao_anular($1);	
     FOR lin_orcamento IN SELECT * FROM sncp_orcamento_linha WHERE orcamento_id=$1
     LOOP
	IF lin_orcamento.reforco>0.0 THEN
	    IF dados.titulo='rece' THEN
		categoria='52rrefo';
	    ELSE
		categoria='02drefo';
	    END IF;

	    IF lin_orcamento.reforco>da_disponibilidade_orcamental(dados.ano,lin_orcamento.organica_id,lin_orcamento.economica_id,
	    lin_orcamento.funcional_id) THEN
		mensagem='Não existe valor suficiente para cobrir os cabimentos';
	    END IF;	
	    IF LENGTH(mensagem)<>0 THEN
	       RETURN mensagem;	
	    END IF;
	ELSE
	    IF dados.titulo='rece' THEN
		categoria='53rabat';
            ELSE
		categoria='03dabat';
	    END IF;
	END IF;	
     END LOOP;
     ok=elimina_historico_orc_mod_cab(dados.ano,categoria,dados.move_id);
     DELETE FROM account_move_line WHERE move_id=dados.move_id;
     DELETE FROM account_move WHERE id=dados.move_id;
     UPDATE sncp_orcamento SET state = 'approved',contab=FALSE,doc_contab_id=NULL WHERE id = $1;		
RETURN mensagem;
END;
$$ LANGUAGE plpgsql;
