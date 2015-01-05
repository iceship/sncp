CREATE OR REPLACE FUNCTION insere_linha_historico(ano integer,categoria varchar,datahora timestamp,
organica_id integer,economica_id integer,funcional_id integer,montante numeric,move_id integer,linha_move_id integer,centrocustos_id integer,cabimento_id integer,
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

CREATE or replace FUNCTION fu_extenso_euro(num numeric(20,2)) returns text as $$
begin
  return fu_extenso(num,'Euro','Euros') ;
end;
$$ LANGUAGE plpgsql
   IMMUTABLE
   RETURNS NULL ON NULL INPUT ;                                        

CREATE or replace FUNCTION fu_extenso(num numeric(20,2) , moeda text , moedas text) returns text as $$
declare
w_int char(21) ;
x integer ;
v integer ;
w_ret text ;
w_ext text ;
w_apoio text ;
m_cen text[] := array['quatrilião','quatriliões','trilião','triliões','bilião','biliões','milhão','milhões','mil','mil'] ;
begin
  w_ret := '' ;
  w_int := to_char(num * 100 , 'fm000000000000000000 00') ;
  for x in 1..5 loop
      v := cast(substr(w_int,(x-1)*3 + 1,3) as integer) ;
      if v > 0 then
         if v > 1 then
            w_ext := m_cen[(x-1)*2+2] ;
           else
            w_ext := m_cen[(x-1)*2+1] ;
         end if ;
         w_ret := w_ret || fu_extenso_blk(substr(w_int,(x-1)*3 + 1,3)) || ' ' || w_ext ||' ' ;
      end if ;
  end loop ;
  v := cast(substr(w_int,16,3) as integer) ;
  if v > 0 then
     if v > 1 then
        w_ext := moedas ;
       else
        if w_ret = '' then
           w_ext := moeda ;
          else
           w_ext := moedas ;
        end if ;
     end if ;
     w_apoio := fu_extenso_blk(substr(w_int,16,3)) || ' ' || w_ext ;
     if w_ret = '' then
        w_ret := w_apoio ;
       else
        if v > 100 then
           if w_ret = '' then
              w_ret := w_apoio ;
             else
              w_ret := w_ret || w_apoio ;
           end if ;
          else
           w_ret := btrim(w_ret,', ') || ' e ' || w_apoio ;
        end if ;
     end if ;
    else
     if w_ret <> '' then
        if substr(w_int,13,6) = '000000' then
           w_ret := btrim(w_ret,', ') || ' de ' || moedas ;
          else
           w_ret := btrim(w_ret,', ') || ' ' || moedas ;
        end if ;
     end if ;
  end if ;
  v := cast(substr(w_int,20,2) as integer) ;
  if v > 0 then
     if v > 1 then
        w_ext := 'cêntimos' ;
       else
        w_ext := 'cêntimo' ;
     end if ;
     w_apoio := fu_extenso_blk('0'||substr(w_int,20,2)) || ' ' || w_ext ;
     if w_ret = '' then
        w_ret := w_apoio  || ' de ' || moeda;
       else
        w_ret := w_ret || ' e ' || w_apoio ;
     end if ;
  end if ;
  return w_ret ;
end ;
$$ LANGUAGE plpgsql
   IMMUTABLE
   RETURNS NULL ON NULL INPUT ;

CREATE or replace FUNCTION fu_extenso_blk(num char(3)) returns text as $$
declare
w_cen integer ;
w_dez integer ;
w_dez2 integer ;
w_uni integer ;
w_tcen text ;
w_tdez text ;
w_tuni text ;
w_ext text ;
m_cen text[] := array['','cento','duzentos','trezentos','quatrocentos','quinhentos','seiscentos','setecentos','oitocentos','novecentos'];
m_dez text[] := array['','dez','vinte','trinta','quarenta','cinquenta','sessenta','setenta','oitenta','noventa'] ;
m_uni text[] := array['','um','dois','três','quatro','cinco','seis','sete','oito','nove','dez','onze','doze','treze','catorze','quinze','dezasseis','dezassete','dezoito','dezanove'] ;
begin
  w_cen := cast(substr(num,1,1) as integer) ;
  w_dez := cast(substr(num,2,1) as integer) ;
  w_dez2 := cast(substr(num,2,2) as integer) ;
  w_uni := cast(substr(num,3,1) as integer) ;
  if w_cen = 1 and w_dez2 = 0 then
     w_tcen := 'Cem' ;
     w_tdez := '' ;
     w_tuni := '' ;
    else
     if w_dez2 < 20 then
        w_tcen := m_cen[w_cen + 1] ;
        w_tdez := m_uni[w_dez2 + 1] ;
        w_tuni := '' ;
       else
        w_tcen := m_cen[w_cen + 1] ;
        w_tdez := m_dez[w_dez + 1] ;
        w_tuni := m_uni[w_uni + 1] ;
     end if ;
  end if ;
  w_ext := w_tcen ;
  if w_tdez <> '' then
     if w_ext = '' then
        w_ext := w_tdez ;
       else
        w_ext := w_ext || ' e ' || w_tdez ;
     end if ;
  end if ;
  if w_tuni <> '' then
     if w_ext = '' then
        w_ext := w_tuni ;
       else
        w_ext := w_ext || ' e ' || w_tuni ;
     end if ;
  end if ;
  return w_ext ;
end ;
$$ LANGUAGE plpgsql
   IMMUTABLE
   RETURNS NULL ON NULL INPUT ;

CREATE OR REPLACE FUNCTION meios_pagamento(guia_rec_id integer) RETURNS varchar
AS
$$
DECLARE
  conta integer;
  meio_pag varchar='';
  guia_rec_meios sncp_receita_guia_rec_meios%ROWTYPE;
BEGIN
   conta=(SELECT COUNT(*) FROM sncp_receita_guia_rec_meios AS GRM WHERE GRM.guia_rec_id=$1);
   FOR guia_rec_meios IN (SELECT * FROM sncp_receita_guia_rec_meios AS GRM WHERE GRM.guia_rec_id=$1) LOOP
       IF guia_rec_meios.meio_rec='num' THEN
          meio_pag=CONCAT(meio_pag,'Numerário ');
       ELSIF guia_rec_meios.meio_rec='chq' THEN
          meio_pag=CONCAT(meio_pag,'Cheque ');
       ELSIF guia_rec_meios.meio_rec='dep' THEN
          meio_pag=CONCAT(meio_pag,'Talão de Depósito ');
       ELSIF guia_rec_meios.meio_rec='trf' THEN
          meio_pag=CONCAT(meio_pag,'Transferência Bancária ');
       ELSIF guia_rec_meios.meio_rec='cdc' THEN
          meio_pag=CONCAT(meio_pag,'Crédito em conta ');
       ELSE
          meio_pag=CONCAT(meio_pag,'Outros ');
       END IF;
       meio_pag=CONCAT(meio_pag,guia_rec_meios.obs);
       IF conta=1 THEN
          RETURN meio_pag;
       ELSE
          meio_pag=CONCAT(meio_pag,' ',guia_rec_meios.montante,'; ');
       END IF;
   END LOOP;
   RETURN meio_pag;
END;$$  LANGUAGE plpgsql;

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

CREATE OR REPLACE FUNCTION insere_linha_movimento_contabilistico_compromisso(conta_id integer, journal_id integer, date, ref character varying, move_id integer, valor numeric, organica_id integer, economica_id integer, funcional_id integer, deb_creb character varying, partner_id integer)
  RETURNS integer AS
$$
DECLARE
    periodo_id integer;
BEGIN
periodo_id = get_periodo($3);
IF $10='credit' THEN
    INSERT INTO account_move_line(account_id,date,journal_id,period_id,name,move_id,credit,organica_id,economica_id,
    funcional_id,partner_id) VALUES($1,$3,$2,periodo_id,$4,$5,$6,$7,$8,$9,$11);
    RETURN (SELECT currval('account_move_line_id_seq'));
ELSE
    INSERT INTO account_move_line(account_id,date,journal_id,period_id,name,move_id,debit,organica_id,economica_id,
    funcional_id,partner_id) VALUES($1,$3,$2,periodo_id,$4,$5,$6,$7,$8,$9,$11);
    RETURN (SELECT currval('account_move_line_id_seq'));
END IF;
END;
$$  LANGUAGE plpgsql;

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
          move_line_id=insere_linha_movimento_contabilistico_compromisso(conta_debito,$3,caldata,$5,
          move_id,compromisso_linha.montante,compromisso_linha.organica_id,compromisso_linha.economica_id,compromisso_linha.funcional_id,
          'debit',compromisso.partner_id);
          move_line_id=insere_linha_movimento_contabilistico_compromisso(conta_credito,$3,caldata,$5,
          move_id,compromisso_linha.montante,compromisso_linha.organica_id,compromisso_linha.economica_id,compromisso_linha.funcional_id,
          'credit',compromisso.partner_id);
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
        move_id=insere_movimento_contabilistico_compromisso($2,$6,caldata,$5,compromisso.partner_id);
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
           move_line_id=insere_linha_movimento_contabilistico_compromisso(conta_debito,$6,caldata,$5,
            move_id,compromisso_linha_futuro.montante,compromisso_linha_futuro.organica_id,
            compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,
          'debit',compromisso.partner_id);
            move_line_id=insere_linha_movimento_contabilistico_compromisso(conta_credito,$6,caldata,$5,
            move_id,compromisso_linha_futuro.montante,compromisso_linha_futuro.organica_id,
            compromisso_linha_futuro.economica_id,compromisso_linha_futuro.funcional_id,
          'credit',compromisso.partner_id);
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

