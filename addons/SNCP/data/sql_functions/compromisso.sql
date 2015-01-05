CREATE OR REPLACE FUNCTION valida_montantes_agenda(comp_id integer) RETURNS varchar AS 
$$
DECLARE
    mensagem varchar='';
    compromisso_ano sncp_despesa_compromisso_ano%ROWTYPE;
    compromisso_linha sncp_despesa_compromisso_linha%ROWTYPE;
    montante_agenda numeric;
BEGIN
     FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano WHERE compromisso_id=$1) LOOP
	FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha WHERE compromisso_ano_id=compromisso_ano.id) LOOP
            montante_agenda=(SELECT COALESCE(SUM(montante),0.0) FROM sncp_despesa_compromisso_agenda  
                             WHERE compromisso_linha_id=compromisso_linha.id);
            IF montante_agenda!=compromisso_linha.anual_prev THEN
		mensagem='A soma total dos montantes da agenda têm de ser igual ao anual 
		          previsto para aquela linha do compromisso';
	    END IF;
            IF LENGTH(mensagem)>0 THEN
		    RETURN mensagem;
	    END IF;	    
	END LOOP;
     END LOOP;	
     RETURN mensagem;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION da_valor_comprometido_mes(dt timestamp,comp_id integer) RETURNS numeric AS 
$$
DECLARE
    data_ini timestamp;
BEGIN
   data_ini=(EXTRACT(YEAR FROM $1) ||'-' || EXTRACT(MONTH FROM $1) || '-' ||1 || ' ' || 0 || ':' 
       || 0 || ':' || 1)::TIMESTAMP; 
RETURN (SELECT COALESCE(SUM(MONTANTE),0.0)
       FROM sncp_orcamento_historico
       WHERE datahora >= data_ini AND datahora < $1 AND categoria = '05compr' AND compromisso_id <> $2);	
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION da_valor_elegivel(linha_id integer,mes_atual integer) RETURNS numeric AS 
$$
BEGIN
   IF $2<11 THEN
	RETURN (SELECT COALESCE(SUM(montante),0.0)
		FROM sncp_despesa_compromisso_agenda AS AGENDA
		WHERE (AGENDA.name BETWEEN $2 AND $2 + 2) AND compromisso_linha_id=$1
	       );
   ELSIF $2 = 11 THEN
       RETURN (SELECT COALESCE(SUM(montante),0.0)
		FROM sncp_despesa_compromisso_agenda AS AGENDA
		WHERE (AGENDA.name BETWEEN $2 AND $2 + 1) AND compromisso_linha_id=$1
	      );
	      	
   ELSE
      RETURN (  SELECT COALESCE(montante,0.0)
		FROM sncp_despesa_compromisso_agenda AS AGENDA
		WHERE AGENDA.name = $2 AND compromisso_linha_id=$1
	      );	
   END IF;	
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fundo_da_valor_disponivel(ano_atual integer,mes_atual integer) RETURNS numeric AS 
$$
BEGIN
   RETURN (SELECT COALESCE(FUNDO.montante-FUNDO.reservado,0.0)
           FROM sncp_despesa_fundos_disponiveis AS FUNDO
           WHERE FUNDO.name=$1 and FUNDO.mes = $2 
	  );	
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION ultima_atualizacao(tipo varchar,mes_atual integer,compromisso_id integer,
ano integer,nmove_id integer) RETURNS boolean AS 
$$
DECLARE 
  compromisso_ano sncp_despesa_compromisso_ano%ROWTYPE;
  compromisso_linha sncp_despesa_compromisso_linha%ROWTYPE;
BEGIN
   FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO WHERE COMPANO.compromisso_id=$3 
   AND COMPANO.ano=$4) LOOP
      FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha AS COMPLINHA 
      WHERE COMPLINHA.compromisso_ano_id=compromisso_ano.id ) LOOP
	IF $1 = 'per' OR $1 = 'cal' THEN
	   IF $2 < 11 THEN
		UPDATE sncp_despesa_compromisso_agenda AS AGENDA SET last_doc_contab_id=$5 
		WHERE AGENDA.compromisso_linha_id=compromisso_linha.id AND (AGENDA.name BETWEEN $2 + 1 AND $2 + 2);
	   ELSIF $2 = 11 THEN
		UPDATE sncp_despesa_compromisso_agenda AS AGENDA SET last_doc_contab_id=$5 
		WHERE AGENDA.compromisso_linha_id=compromisso_linha.id AND (AGENDA.name = $2 + 1);
	   END IF;
	END IF;
	UPDATE sncp_despesa_compromisso_agenda AS AGENDA SET last_doc_contab_id=$5 
		WHERE AGENDA.compromisso_linha_id=compromisso_linha.id AND AGENDA.name = $2;
      END LOOP;
   END LOOP; 	
   RETURN TRUE;	
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insere_movimento_contabilistico_compromisso(user_id integer,journal_id integer,date,ref varchar) RETURNS integer AS $$
DECLARE
 periodo_id integer;
 companhia_id integer;
 nome varchar;
BEGIN
periodo_id=get_periodo($3);
companhia_id=get_companhia($1);
nome=$4 || ' ' || 'futuro';
INSERT INTO account_move(name,ref,period_id,journal_id,state,date,company_id)
VALUES (nome,ref,periodo_id,$2,'draft',$3,companhia_id);
RETURN (SELECT currval('account_move_id_seq'));
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION contabiliza_compromisso(comp_id integer,user_id integer,journal_id integer,dh varchar,ref varchar,
journal_fut_id integer) RETURNS varchar AS 
$$
DECLARE
  compromisso sncp_despesa_compromisso%ROWTYPE; 
  compromisso_ano_atual sncp_despesa_compromisso_ano%ROWTYPE;
  compromisso_ano_futuro sncp_despesa_compromisso_ano%ROWTYPE;
  compromisso_linha sncp_despesa_compromisso_linha%ROWTYPE;
  compromisso_linha_futuro sncp_despesa_compromisso_linha%ROWTYPE;
  mensagem varchar='';
  datahora timestamp;
  nano integer;
  ok boolean;
  move_futuro_ok boolean=FALSE;
  move_id integer;
  move_line_id integer;
  caldata date;	
  val_disp numeric;
  val_comp_mes numeric;
  valor_elegivel numeric=0;
  da_val_eleg numeric;
  fundo_disponivel numeric;
  mes integer;
  dif_anos integer;
  array_mes varchar[]='{"Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro",
  "Outubro","Novembro","Dezembro"}';
  conta_credito integer;
  conta_debito integer;
BEGIN
   datahora=$4::timestamp;
   caldata=$4::date;
   nano=EXTRACT(YEAR FROM datahora);
   mes=EXTRACT(MONTH FROM datahora);	
   SELECT * INTO compromisso FROM sncp_despesa_compromisso WHERE id=$1;	

   FOR compromisso_ano_atual IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO WHERE COMPANO.ano=nano 
   AND COMPANO.compromisso_id = compromisso.id) LOOP
        move_id=insere_movimento_contabilistico($2,$3,caldata,$5,nano);

   	FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha WHERE compromisso_ano_id=compromisso_ano_atual.id) LOOP
           val_disp=da_valor_disponivel(compromisso_ano_atual.cabimento_id,compromisso_linha.linha,nano);
           IF compromisso_linha.montante>val_disp THEN
		mensagem='O cabimento só têm o valor de ' || ABS(val_disp)|| ' disponível para essa linha';
		IF LENGTH(mensagem)>0 THEN
		   RETURN mensagem;	
		END IF;
	   END IF;
       END LOOP;

       val_comp_mes=da_valor_comprometido_mes(datahora,compromisso.id);

       IF compromisso.tipo='com' or compromisso.tipo='plu' THEN
	  valor_elegivel=(SELECT COALESCE(SUM(montante),0.0) FROM sncp_despesa_compromisso_linha 
	  WHERE compromisso_ano_id=compromisso_ano_atual.id);
       ELSE
	  FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha WHERE compromisso_ano_id=compromisso_ano_atual.id) LOOP
             da_val_eleg= da_valor_elegivel(compromisso_linha.id,mes);
             valor_elegivel=valor_elegivel+da_val_eleg; 
          END LOOP;	
       END IF;

       fundo_disponivel=fundo_da_valor_disponivel(nano,mes);

       IF val_comp_mes+valor_elegivel>fundo_disponivel THEN
	  mensagem='Não há fundos disponíveis suficientes para o mês de '|| array_mes[mes] || ' de ' || nano;
	  IF LENGTH(mensagem)>0 THEN
		RETURN mensagem;
	  END IF;
       END IF;

       FOR compromisso_linha IN (SELECT * FROM sncp_despesa_compromisso_linha WHERE compromisso_ano_id=compromisso_ano_atual.id) LOOP
	  conta_debito=(SELECT default_debit_account_id FROM account_journal WHERE id=$3);
          conta_credito=(SELECT default_credit_account_id FROM account_journal WHERE id=$3);
          move_line_id=insere_linha_movimento_contabilistico(conta_debito,$3,caldata,$5,
          move_id,compromisso_linha.montante,compromisso_linha.organica_id,compromisso_linha.economica_id,compromisso_linha.funcional_id,
          'debit');
          move_line_id=insere_linha_movimento_contabilistico(conta_credito,$3,caldata,$5,
          move_id,compromisso_linha.montante,compromisso_linha.organica_id,compromisso_linha.economica_id,compromisso_linha.funcional_id,
          'credit');
          datahora=insere_linha_historico(nano,'05compr',datahora,compromisso_linha.organica_id,
          compromisso_linha.economica_id,compromisso_linha.funcional_id,compromisso_linha.montante,move_id,move_line_id,
          NULL,NULL,NULL,compromisso.id,compromisso_linha.id);
          ok=insere_linha_acumulados(nano,'05compr',compromisso_linha.organica_id,
         compromisso_linha.economica_id,compromisso_linha.funcional_id,compromisso_linha.montante);
         UPDATE sncp_despesa_compromisso_linha SET state_line='proc' WHERE id=compromisso_linha.id;
       END LOOP;

   UPDATE sncp_despesa_compromisso_ano SET estado = 2 WHERE id=compromisso_ano_atual.id;           
   ok=atualizar_estado(compromisso_ano_atual.cabimento_id,nano);
   ok=ultima_atualizacao(compromisso.tipo,mes,compromisso.id,nano,move_id);
   END LOOP;

   FOR compromisso_ano_futuro IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO WHERE COMPANO.ano>nano 
   AND COMPANO.compromisso_id = compromisso.id) LOOP
	IF move_futuro_ok=FALSE THEN
		move_id=insere_movimento_contabilistico_compromisso($2,$6,caldata,$5);
		move_futuro_ok=TRUE;
        END IF;
        dif_anos=compromisso_ano_futuro.ano-nano;
        FOR compromisso_linha_futuro IN (SELECT * FROM sncp_despesa_compromisso_linha 
        WHERE compromisso_ano_id=compromisso_ano_futuro.id) LOOP
           IF dif_anos=1 THEN
            conta_debito=(SELECT id FROM account_account AS AA WHERE AA.code='041');
            conta_credito=(SELECT id FROM account_account AS AA WHERE AA.code='051');
            ELSIF dif_anos=2 THEN
            conta_debito=(SELECT id FROM account_account AS AA WHERE AA.code='042');
            conta_credito=(SELECT id FROM account_account AS AA WHERE AA.code='052');
            ELSIF dif_anos=3 THEN
            conta_debito=(SELECT id FROM account_account AS AA WHERE AA.code='043');
            conta_credito=(SELECT id FROM account_account AS AA WHERE AA.code='053');
            ELSIF dif_anos>=4 THEN
            conta_debito=(SELECT id FROM account_account AS AA WHERE AA.code='044');
            conta_credito=(SELECT id FROM account_account AS AA WHERE AA.code='054');
          END IF;
           move_line_id=insere_linha_movimento_contabilistico(conta_debito,$6,caldata,$5,
            move_id,compromisso_linha_futuro.montante,compromisso_linha_futuro.organica_id,
            compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,
          'debit');
            move_line_id=insere_linha_movimento_contabilistico(conta_credito,$6,caldata,$5,
            move_id,compromisso_linha_futuro.montante,compromisso_linha_futuro.organica_id,
            compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,
          'credit');
          datahora=insere_linha_historico(compromisso_ano_futuro.ano,'06futur',datahora,compromisso_linha_futuro.organica_id,
          compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,compromisso_linha_futuro.montante,move_id,move_line_id,
          NULL,NULL,NULL,compromisso.id,compromisso_linha_futuro.id);
          ok=insere_linha_acumulados(compromisso_ano_futuro.ano,'06futur',compromisso_linha_futuro.organica_id,
         compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,compromisso_linha_futuro.montante);
         UPDATE sncp_despesa_compromisso_linha SET state_line='proc' WHERE id=compromisso_linha_futuro.id;
        END LOOP;
   UPDATE sncp_despesa_compromisso_ano SET estado = 2 WHERE id=compromisso_ano_futuro.id;
   END LOOP;
   UPDATE sncp_despesa_compromisso SET state='proc' WHERE id=$1;  	
   RETURN mensagem;	
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION elimina_historico_comp(name integer,categoria varchar,compromisso_id integer) RETURNS boolean AS $$
DECLARE
    lin sncp_orcamento_historico%ROWTYPE;
    ok boolean;
BEGIN
     FOR lin in SELECT * FROM sncp_orcamento_historico AS SOH WHERE SOH.name = $1 AND SOH.categoria = $2 AND SOH.compromisso_id=$3
     LOOP
     ok=elimina_acumulados(lin.name,lin.categoria,lin.organica_id,lin.economica_id,lin.funcional_id,lin.montante);
	DELETE FROM sncp_orcamento_historico WHERE id=lin.id;
     END LOOP;
RETURN TRUE;	
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION anula_compromisso(comp_id integer) RETURNS varchar AS 
$$
DECLARE
  mensagem varchar='';
  ok boolean;
  ano_atual integer;
  compromisso_relacoes sncp_despesa_compromisso_relacoes%ROWTYPE;
  compromisso_ano sncp_despesa_compromisso_ano%ROWTYPE;
  move_ano_atual integer;
  move_ano_futuro integer; 
BEGIN
   FOR compromisso_relacoes in (SELECT * FROM sncp_despesa_compromisso_relacoes COMPREL WHERE COMPREL.name=$1) LOOP
       mensagem='Não é possível anular. Ordem de compra ou fatura associada';
       IF LENGTH(mensagem)>0 THEN
          RETURN mensagem;
       END IF;
   END LOOP;
   ano_atual=(SELECT EXTRACT(YEAR FROM datahora) FROM sncp_orcamento_historico WHERE compromisso_id=$1 LIMIT 1);

   move_ano_atual=(SELECT doc_contab_id FROM sncp_orcamento_historico AS SOH WHERE SOH.name=ano_atual 
                      AND SOH.categoria='05compr' AND compromisso_id=$1
                      LIMIT 1);
   move_ano_futuro=(SELECT doc_contab_id FROM sncp_orcamento_historico AS SOH WHERE SOH.name>ano_atual 
                      AND SOH.categoria='06futur' AND compromisso_id=$1
                      LIMIT 1);
   FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO WHERE COMPANO.compromisso_id=$1) LOOP
     IF compromisso_ano.ano = ano_atual THEN
	ok=elimina_historico_comp(compromisso_ano.ano,'05compr',$1);
	DELETE FROM sncp_despesa_compromisso_agenda WHERE compromisso_linha_id IN 
	(SELECT id FROM sncp_despesa_compromisso_linha WHERE compromisso_ano_id=compromisso_ano.id); 
     ELSE
        ok=elimina_historico_comp(compromisso_ano.ano,'06futur',$1);
     END IF;
     UPDATE sncp_despesa_compromisso_linha SET state_line='anul' WHERE compromisso_ano_id=compromisso_ano.id; 
   END LOOP;
   IF move_ano_atual IS NOT NULL THEN
      DELETE FROM account_move_line AS ML WHERE ML.move_id=move_ano_atual;
      DELETE FROM account_move WHERE id= move_ano_atual;	
   END IF;

   IF move_ano_futuro IS NOT NULL THEN
      DELETE FROM account_move_line AS ML WHERE ML.move_id=move_ano_futuro;
      DELETE FROM account_move WHERE id= move_ano_futuro;
   END IF;
   	
   UPDATE sncp_despesa_compromisso SET state='anul' WHERE id=$1;
RETURN mensagem;   
END;
$$ LANGUAGE plpgsql;

