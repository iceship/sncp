CREATE or replace FUNCTION fu_extenso_real(num numeric(20,2)) returns text as $$
begin
  return fu_extenso(num,'Euro','Euros') ;  
end ;
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
m_cen text[] := array['quatrilhão','quatrilhões','trilhão','trilhões','bilhão','bilhões','milhão','milhões','mil','mil'] ;
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
m_uni text[] := array['','um','dois','três','quatro','cinco','seis','sete','oito','nove','dez','onze','doze','treze','quatorze','quinze','dezesseis','dezessete','dezoito','dezenove'] ;
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
