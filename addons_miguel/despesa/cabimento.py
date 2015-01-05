# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    vals program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    vals program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with vals program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from openerp.osv import fields, osv
import pytz
from openerp.tools.translate import _

# ____________________________________________________CABIMENTO________________________________________________


class sncp_despesa_cabimento(osv.Model):
    _name = 'sncp.despesa.cabimento'
    _description = u"Cabimento"

    _rec_name = 'cabimento'

    def call_param(self, cr, uid, ids, context=None):
        cr.execute(""" SELECT * FROM sncp_despesa_cabimento_linha WHERE cabimento_id=%d""" % (ids[0]))
        ha_linhas = cr.fetchall()

        if len(ha_linhas) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não há linhas para processar.'))

        cr.execute("""
        SELECT id
        FROM sncp_despesa_cabimento_linha
        WHERE cabimento_id = %d AND (economica_id IS NULL OR organica_id IS NULL)
        """ % ids[0])

        linhas = cr.fetchall()

        if len(linhas) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Linhas do cabimento mal configuradas.'))

        return self.pool.get('formulario.sncp.despesa.cabimento.diario').wizard(cr, uid, ids, context)

    def cabimento_cont(self, cr, uid, ids, context, vals):
        self.verifica_contabilizado(cr, uid, ids, vals)

        db_ir_sequence = self.pool.get('ir.sequence')
        db_account_journal = self.pool.get('account.journal')

        jornal = db_account_journal.browse(cr, uid, vals['diario_id'])
        if jornal.sequence_id.id:
            name = db_ir_sequence.next_by_id(cr, uid, jornal.sequence_id.id)
            self.write(cr, uid, ids, {'cabimento': name})
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'O diário '+unicode(jornal.name) +
                                                u' não têm sequência de movimentos associada.'))
        if 'criar_compromisso' in context:
            return self.pool.get('sncp.despesa.cria.cab.com').finalizar_cabimento(cr, uid,
                                                                                  [context['criar_compromisso']],
                                                                                  context)
        else:
            return self.imprimir_report(cr, uid, ids, context)

    def cabimento_cons(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'cons'})
        return True

    def cabimento_anul(self, cr, uid, ids, context=None):
        return self.anula_contabilizado(cr, uid, ids)

    def teste_existencia_cabimento(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'anula_cabimento'""")
        result = cr.fetchone()
        if result is None:
            self.sql_anula_cabimento(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'atualizar_estado'""")
        result = cr.fetchone()
        if result is None:
            self.sql_atualizar_estado(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'contabiliza_cabimento'""")
        result = cr.fetchone()
        if result is None:
            self.sql_contabiliza_cabimento(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'da_valor_disponivel'""")
        result = cr.fetchone()
        if result is None:
            self.sql_da_valor_disponivel(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc
                      WHERE proname = 'montante_consolidado_cabimento_associado'""")
        result = cr.fetchone()
        if result is None:
            self.sql_montante_consolidado_cabimento_associado(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc
                      WHERE proname = 'montante_consolidado_compromisso_ano_linha_associado'""")
        result = cr.fetchone()
        if result is None:
            self.sql_montante_consolidado_compromisso_ano_linha_associado(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc WHERE proname = 'linhas_cabimento_mm_dimensoes'""")
        result = cr.fetchone()
        if result is None:
            self.sql_linhas_cabimento_mm_dimensoes(cr)

        return True

    def verifica_contabilizado(self, cr, uid, ids, vals, context=None):
        cabim = self.browse(cr, uid, ids[0])

        datahora = datetime.strptime(vals['datahora'], "%Y-%m-%d %H:%M:%S")
        datahora = datahora.replace(tzinfo=pytz.utc)

        cr.execute("""
           SELECT contabiliza_cabimento(%d,%d,%d,'%s','%s')
        """ % (cabim.id, uid, vals['diario_id'], unicode(datahora), vals['ref']))
        mensagem = cr.fetchone()[0]
        if len(mensagem) > 0:
            raise osv.except_osv(_(mensagem), _(u''))

        return True

    def anula_contabilizado(self, cr, uid, ids, context=None):
        cabimento = self.browse(cr, uid, ids[0])
        cr.execute("""
                   SELECT anula_cabimento(%d)""" % cabimento.id)
        mensagem = cr.fetchone()[0]
        if len(mensagem) > 0:
            raise osv.except_osv(_(mensagem), _(u''))
        return True

    def criar_linha_cabimento(self, cr, uid, ids, context):
        db_sncp_despesa_cabimento_linha = self.pool.get('sncp.despesa.cabimento.linha')
        self.write(cr, uid, ids[0], {'estado': 1})
        linhas_ids = db_sncp_despesa_cabimento_linha.search(cr, uid, [('cabimento_id', '=', context['origem_id'])])
        linhas = db_sncp_despesa_cabimento_linha.browse(cr, uid, linhas_ids)
        for lin in linhas:
            db_sncp_despesa_cabimento_linha.create(cr, uid, {
                'estado': 1,
                'linha': lin.linha,
                'cabimento_id': ids[0],
                'organica_id': lin.organica_id.id,
                'economica_id': lin.economica_id.id,
                'funcional_id': lin.funcional_id.id}, context=context)
        return True

    def imprimir_report(self, cr, uid, ids, context=None):
        # Bloco de limpeza de formulario
        # Transient Model
        # Bloco de verificação de existencia de serviço
        cr.execute("""SELECT report_name FROM ir_act_report_xml WHERE model = 'sncp.despesa.cabimento'""")
        result = cr.fetchone()

        if result is None or result[0] is None:
            return self.pool.get('formulario.mensagem.despesa').wizard(cr, uid, ids, u'O relatório do cabimento não '
                                                                                     u'está definido. \n'
                                                                                     u'Contacte o Administrador do '
                                                                                     u'sistema.')
        else:
            datas = {'ids': ids,
                     'model': 'sncp.despesa.cabimento', }
            return {
                'type': 'ir.actions.report.xml',
                'nodestroy': True,
                'report_name': result[0],
                'datas': datas,
            }

    _columns = {
        'cabimento': fields.char(u'Cabimento', size=12),
        'name': fields.char(u'Descrição', size=80),
        'desc2': fields.char(u'', size=80),
        'data': fields.date(u'Data de cabimento',),
        'observ': fields.text(u'Observações'),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('cont', u'Contabilizado'),
                                   ('cons', u'Consumido'),
                                   ('anul', u'Anulado')], u'Status',),
        'origem_id': fields.many2one('sncp.despesa.cabimento', u'Cabimento original',
                                     domain=[('origem_id', '=', None), ('state', 'in', ['cont', 'cons'])]),
        'doc_contab_id': fields.many2one('account.move', u'Documento de contabilização'),
        'cab_linhas_id': fields.one2many('sncp.despesa.cabimento.linha', 'cabimento_id', u'Linhas'),
        'estado': fields.integer(u''),
    }

    def sql_montante_consolidado_cabimento_associado(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION montante_consolidado_cabimento_associado(cab_id integer,linha integer)
        RETURNS numeric AS
        $$
        BEGIN
            RETURN (SELECT COALESCE(SUM(CABLINHA.montante),0.0)
                FROM sncp_despesa_cabimento_linha AS CABLINHA
                WHERE CABLINHA.cabimento_id IN (SELECT id FROM sncp_despesa_cabimento WHERE origem_id=$1
                OR cabimento_id=$1) AND CABLINHA.linha=$2 AND CABLINHA.state_line = 'cont');
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_montante_consolidado_compromisso_ano_linha_associado(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION montante_consolidado_compromisso_ano_linha_associado(cab_id integer,linha integer,
        ano_atual integer) RETURNS numeric AS
        $$
        BEGIN
            RETURN (SELECT COALESCE(SUM(COMPLINHA.montante),0.0)
                FROM sncp_despesa_compromisso_linha AS COMPLINHA
                WHERE COMPLINHA.compromisso_ano_id IN (SELECT id FROM sncp_despesa_compromisso_ano WHERE cabimento_id=$1
                 AND ano=$3) AND COMPLINHA.linha=$2 AND COMPLINHA.state_line = 'proc');
        END;
        $$ LANGUAGE plpgsql;

        """)
        return True

    def sql_atualizar_estado(self, cr):
        cr.execute("""
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
            montante_compromisso_consolidado=montante_consolidado_compromisso_ano_linha_associado($1,
            linha_cabimento.linha,$2);
            IF montante_cabimento_consolidado=montante_compromisso_consolidado THEN
               UPDATE sncp_despesa_cabimento_linha SET state_line='cons' WHERE id=linha_cabimento.id;
            ELSE
               UPDATE sncp_despesa_cabimento_linha SET state_line='cont' WHERE id=linha_cabimento.id;
            END IF;
             END LOOP;

             estado=(SELECT state FROM sncp_despesa_cabimento WHERE id=$1);
             num_linhas=(SELECT COUNT(id) FROM sncp_despesa_cabimento_linha WHERE cabimento_id=$1);
             num_linhas_cons=(SELECT COUNT(id) FROM sncp_despesa_cabimento_linha WHERE cabimento_id=$1 AND
             state_line='cons');
             IF num_linhas=num_linhas_cons THEN
                UPDATE sncp_despesa_cabimento SET state='cons' WHERE id=$1;
             ELSE
                UPDATE sncp_despesa_cabimento SET state='cont' WHERE id=$1;
             END IF;
             RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_contabiliza_cabimento(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION contabiliza_cabimento(cab_id integer,user_id integer,journal_id integer,dh varchar,
        ref varchar) RETURNS varchar AS
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
            dim1 varchar;
            dim2 varchar;
            dim3 varchar;
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
            disporc=da_disponibilidade_orcamental(ano,linha_cabimento.organica_id,linha_cabimento.economica_id,
            linha_cabimento.funcional_id);
            IF disporc<linha_cabimento.montante THEN
                dim1=(SELECT code FROM account_analytic_account WHERE id=linha_cabimento.organica_id);
                dim2=(SELECT code FROM account_analytic_account WHERE id=linha_cabimento.economica_id);
                dim3=(SELECT code FROM account_analytic_account WHERE id=linha_cabimento.funcional_id);

                mensagem='Para as classificações Orgânica(' ||
                COALESCE(dim1,'')||')/ Económica(' || COALESCE(dim2,'') ||')/ Funcional('||
                COALESCE(dim3,'')||')' || ' o valor disponível não cobre o montante de '
                || to_char(linha_cabimento.montante,'999G999G999G9990D00');

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
                linha_cabimento.montante,move_id,move_line_id,NULL,linha_cabimento.cabimento_id,linha_cabimento.id,NULL,
                NULL);

                ok=insere_linha_acumulados(ano,'04cabim',linha_cabimento.organica_id,
                linha_cabimento.economica_id,linha_cabimento.funcional_id,linha_cabimento.montante);

                UPDATE sncp_despesa_cabimento_linha SET state_line='cont' WHERE id=linha_cabimento.id;
             END LOOP;
             UPDATE sncp_despesa_cabimento SET state = 'cont',doc_contab_id=move_id WHERE id = $1;
             origem_id=(SELECT CAB.origem_id FROM sncp_despesa_cabimento AS CAB WHERE id=$1);
             IF origem_id IS NOT NULL THEN
            ok=atualizar_estado(origem_id,ano);
             END IF;

        RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_anula_cabimento(self, cr):
        cr.execute("""
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
            FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano AS COMPANO WHERE COMPANO.ano=nano
            AND cabimento_id =$1) LOOP
                mensagem='Não é possível anular pois existe compromissos associados';
                IF LENGTH(mensagem) > 0 THEN
                    RETURN mensagem;
                    END IF;
            END LOOP;
             ELSE
            FOR linha_cabimento IN (SELECT * FROM sncp_despesa_cabimento_linha AS CABLINHA
            WHERE CABLINHA.cabimento_id=$1) LOOP
             IF linha_cabimento.montante>0.0 THEN
                FOR compromisso_ano IN (SELECT * FROM sncp_despesa_compromisso_ano  AS COMPANO WHERE COMPANO.ano=nano
                AND cabimento_id=origem) LOOP
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
             UPDATE sncp_despesa_cabimento SET state = 'anul',cabimento=NULL,doc_contab_id=NULL,origem_id=NULL,data=NULL
             WHERE id = $1;
        RETURN mensagem;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_da_valor_disponivel(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION da_valor_disponivel(cab_id integer,linha integer,ano integer) RETURNS numeric AS
        $$
        DECLARE
            mensagem varchar='';
            cabimento_linha sncp_despesa_cabimento_linha%ROWTYPE;
            montante_cab numeric;
            montante_comp numeric;
        BEGIN
             FOR cabimento_linha IN (SELECT * FROM sncp_despesa_cabimento_linha AS CABLINHA
             WHERE CABLINHA.cabimento_id=$1 and CABLINHA.linha=$2) LOOP
                 IF cabimento_linha.state_line <> 'cont' THEN
                RETURN 0.0;
             END IF;
             montante_cab=montante_consolidado_cabimento_associado($1,$2);
             montante_comp=montante_consolidado_compromisso_ano_linha_associado($1,$2,$3);
             RETURN montante_cab - montante_comp;
             END LOOP;
        END;
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_linhas_cabimento_mm_dimensoes(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION linhas_cabimento_mm_dimensoes(cabimento_id integer) RETURNS varchar AS $$
        DECLARE
          linha_cab RECORD;
          mensagem varchar='';
          num_linhas integer;
        BEGIN
            FOR linha_cab IN (SELECT * FROM sncp_despesa_cabimento_linha AS CL WHERE CL.cabimento_id=$1) LOOP
            num_linhas=(SELECT COUNT(id)
                      FROM sncp_despesa_cabimento_linha AS CL
                      WHERE CL.cabimento_id=$1 AND CL.economica_id=linha_cab.economica_id AND
                      CL.organica_id=linha_cab.organica_id
                      AND ( (CL.funcional_id IS NULL AND linha_cab.funcional_id IS NULL) OR
                                (CL.funcional_id IS NOT NULL AND CL.funcional_id=linha_cab.funcional_id))
                        );
            IF num_linhas > 1 THEN
               mensagem='A combinação  Orgânica('
                         || (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_cab.organica_id) ||
                         ')/Económica(' ||
                     (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_cab.economica_id);
                IF linha_cab.funcional_id IS NULL THEN
                   mensagem= mensagem || ')/Funcional() encontra-se repetida';
                ELSE
                   mensagem=mensagem || ')/Funcional(' ||
                   (SELECT AAA.code FROM account_analytic_account AS AAA WHERE id= linha_cab.funcional_id) ||')
                   encontra-se repetida';
                END IF;

            RETURN mensagem;
            END IF;
            END LOOP;
        RETURN mensagem;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def create(self, cr, uid, vals, context=None):
        self.teste_existencia_cabimento(cr)
        cabimento_id = super(sncp_despesa_cabimento, self).create(cr, uid, vals, context=context)
        sequence_type = self.pool.get('ir.sequence.type')
        seq_type_ids = sequence_type.search(cr, uid, [('name', '=', 'type_cab_name_'+unicode(cabimento_id))])
        if len(seq_type_ids) == 0:
            values_type = {
                'name': 'type_cab_name_'+unicode(cabimento_id),
                'code':  'seq_cab_code_'+unicode(cabimento_id), }
            sequence_type.create(cr, uid, values_type, context=context)
        sequence = self.pool.get('ir.sequence')
        seq_ids = sequence.search(cr, uid, [('name', '=', 'seq_cab_name_'+unicode(cabimento_id))])
        if len(seq_ids) == 0:
            values = {
                'name': 'seq_cab_name_'+unicode(cabimento_id),
                'code':  'seq_cab_code_'+unicode(cabimento_id),
                'number_next': 1,
                'number_increment': 1, }
            sequence.create(cr, uid, values, context=context)

        return cabimento_id

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_despesa_cabimento_linhas = self.pool.get('sncp.despesa.cabimento.linha')
        linhas_ids = db_sncp_despesa_cabimento_linhas.search(cr, uid, [('cabimento_id', '=', ids[0])])

        if len(linhas_ids) != 0:
            db_sncp_despesa_cabimento_linhas.unlink(cr, uid, linhas_ids)
        return super(sncp_despesa_cabimento, self).unlink(cr, uid, ids, context=context)

    _order = 'cabimento'

    _defaults = {'state': 'draft',
                 'estado': 0, }

    def _mesmo_id_organica_economica_funcional(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT linhas_cabimento_mm_dimensoes(%d)
        """ % obj.id)

        mensagem = cr.fetchone()[0]
        if len(mensagem) != 0:
            raise osv.except_osv(_(mensagem), _(u''))

        return True

    _constraints = [
        (_mesmo_id_organica_economica_funcional, u'', ['cab_linhas_id.montante']), ]

sncp_despesa_cabimento()

# _______________________________________________________LINHAS________________________________________________


class sncp_despesa_cabimento_linha(osv.Model):
    _name = 'sncp.despesa.cabimento.linha'
    _description = u"Linhas do Cabimento"

    _columns = {
        'cabimento_id': fields.many2one('sncp.despesa.cabimento', u'Cabimento'),
        'linha': fields.integer(u'Linha'),
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')]),
        'economica_id': fields.many2one('account.analytic.account', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')]),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')],),
        'montante': fields.float(u'Despesa emergente', digits=(12, 2)),
        'name': fields.char(u'Observações'),
        'state_line': fields.selection([('draft', u'Rascunho'),
                                        ('cont', u'Contabilizado'),
                                        ('cons', u'Consumido'),
                                        ('anul', u'Anulado')], u'Status'),
        'estado': fields.integer(u''),
        # 0 -- Criar Linhas disponivel
        # 1 -- Criar linhas invisivel
    }

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            record = self.browse(cr, uid, ids)
        else:
            record = self.browse(cr, uid, ids[0])

        if record.cabimento_id.origem_id.id is False:
            if record.montante > 0.0 or ('montante' in vals is True and vals['montante'] > 0.0):
                return super(sncp_despesa_cabimento_linha, self).write(cr, uid, ids, vals, context=context)

            else:
                raise osv.except_osv(_(u'Aviso'), _(u'Montante deve ser positivo se cabimento original.'))
        else:
            return super(sncp_despesa_cabimento_linha, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        return super(sncp_despesa_cabimento_linha, self).unlink(cr, uid, ids, context=context)

    def create(self, cr, uid, vals, context=None):
        cr.execute("""
        SELECT COALESCE(origem_id,0)
        FROM sncp_despesa_cabimento
        WHERE id=%d
        """ % vals['cabimento_id'])

        result = cr.fetchone()

        if result[0] == 0 or 'linha' not in vals:
            sequence_type = self.pool.get('ir.sequence.type')
            seq_type_ids = sequence_type.search(cr, uid,
                                                [('name', '=', 'type_cab_name_'+unicode(vals['cabimento_id']))])
            if len(seq_type_ids) == 0:
                values_type = {
                    'name': 'type_cab_name_'+unicode(vals['cabimento_id']),
                    'code':  'seq_cab_code_'+unicode(vals['cabimento_id']), }
                sequence_type.create(cr, uid, values_type, context=context)
            sequence = self.pool.get('ir.sequence')
            seq_ids = sequence.search(cr, uid, [('name', '=', 'seq_cab_name_'+unicode(vals['cabimento_id']))])
            if len(seq_ids) == 0:
                values = {
                    'name': 'seq_cab_name_'+unicode(vals['cabimento_id']),
                    'code':  'seq_cab_code_'+unicode(vals['cabimento_id']),
                    'number_next': 1,
                    'number_increment': 1, }
                sequence.create(cr, uid, values, context=context)

            if result[0] > 0:
                cr.execute("""
                SELECT MAX(linha)
                FROM sncp_despesa_cabimento_linha
                WHERE cabimento_id=%d
                """ % vals['cabimento_id'])

                linha = cr.fetchone()

                if linha[0] is not None:
                    vals['linha'] = linha[0]+1
                else:
                    raise osv.except_osv(_(u'Aviso'), _(u'Efetue o carregamento das linhas.'))
            else:
                vals['linha'] = self.pool.get('ir.sequence').get(cr, uid, 'seq_cab_code_'+unicode(vals['cabimento_id']))

        return super(sncp_despesa_cabimento_linha, self).create(cr, uid, vals, context=context)

    def _montante_valido(self, cr, uid, ids):
        record = self.browse(cr, uid, ids[0])
        if record.montante <= 0.0 and record.cabimento_id.origem_id.id is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Montante deve ser positivo se cabimento original.'))

        return True

    _defaults = {'state_line': 'draft',
                 'estado': 0, }

    _constraints = [(_montante_valido, u'', ['montante']), ]

sncp_despesa_cabimento_linha()