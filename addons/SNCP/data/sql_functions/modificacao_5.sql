CREATE OR REPLACE FUNCTION insere_titulos_mod(despesa boolean)
        RETURNS boolean AS
        $$
        DECLARE
          dados varchar;
          prefixo varchar(1);
          reforco numeric;
          abate numeric;
          prev_atual numeric;
          prev_corr numeric;
        BEGIN
             dados=(SELECT codigo FROM sncp_modificacao_imprimir_receita WHERE linha='artigo' LIMIT 1);
             IF SUBSTRING(dados FROM 1 FOR 1) NOT BETWEEN '0' AND '9' THEN
                prefixo=SUBSTRING(dados FROM 1 FOR 1);
             ELSE
                prefixo='';

             END IF;

             IF $1=FALSE THEN
                reforco=(SELECT calcula_montante_titulo_mod('',prefixo||'08',1));
                abate=(SELECT calcula_montante_titulo_mod('',prefixo||'08',0));
                prev_atual=(SELECT calcula_montante_titulo_mod('',prefixo||'08',2));
                prev_corr=(SELECT calcula_montante_titulo_mod('',prefixo||'08',3));
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,reforco,linha,abate,previsao_atual,previsao_corrigida) 
                VALUES('','RECEITAS CORRENTES',reforco,'titulo',abate,prev_atual,prev_corr);
                reforco=(SELECT calcula_montante_titulo_mod(prefixo||'09',prefixo||'zz',1));
                abate=(SELECT calcula_montante_titulo_mod(prefixo||'09',prefixo||'zz',0));
                prev_atual=(SELECT calcula_montante_titulo_mod(prefixo||'09',prefixo||'zz',2));
                prev_corr=(SELECT calcula_montante_titulo_mod(prefixo||'09',prefixo||'zz',3));
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,reforco,linha,abate,previsao_atual,previsao_corrigida) 
                VALUES(prefixo||'08zzzzzzzzzzzz','RECEITAS DE CAPITAL',reforco,'titulo',abate,prev_atual,prev_corr);
             ELSE
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,linha) VALUES('','DESPESAS CORRENTES','titulo');
                INSERT INTO sncp_modificacao_imprimir_receita(codigo,name,linha) VALUES(prefixo||'06zzzzzzzzzzzz','RECEITAS DE CAPITAL','titulo');
             END IF;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;