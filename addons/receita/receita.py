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

from openerp.osv import fields, osv


def get_sequence(self, cr, uid, context, text, value):
    # tipos de sequencia
    # Sequencia de linhas da requisição 'req_lin' +prop_id

    seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_' + text + '_code_'+unicode(value))
    if seq is False:
        sequence_type = self.pool.get('ir.sequence.type')
        values_type = {
            'name': 'type_' + text + '_name_'+unicode(value),
            'code':  'seq_' + text + '_code_'+unicode(value), }
        sequence_type.create(cr, uid, values_type, context=context)
        sequence = self.pool.get('ir.sequence')
        values = {
            'name': 'seq_' + text + '_name_'+unicode(value),
            'code':  'seq_' + text + '_code_'+unicode(value),
            'number_next': 1,
            'number_increment': 1, }
        sequence.create(cr, uid, values, context=context)
        seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_' + text + '_code_'+unicode(value))
    return seq

# _____________________________________________ITENS DEPARTAMENTO______________________________________


class sncp_receita_itens_dept(osv.Model):
    _name = 'sncp.receita.itens.dept'
    _description = u"Itens por departamento"

    def get_departamento_list_js(self, cr, uid):
        db_hr_department = self.pool.get('hr.department')
        cr.execute("""
        SELECT DISTINCT department_id
        FROM sncp_receita_itens_dept
        """)
        deps_ids = cr.fetchall()
        deps_ids = [elem[0] for elem in deps_ids]

        return db_hr_department.name_get(cr, uid, deps_ids)

    def on_change_department(self, cr, uid, ids):
        lista = []
        cr.execute(""" SELECT item_id FROM sncp_comum_codigos_contab
                       WHERE natureza IN ('rec','ots')""")
        result = cr.fetchall()
        for res in result:
            lista.append(res[0])

        lista = list(set(lista))
        return {'domain': {'item_id': [('id', 'in', lista)]}}

    _columns = {
        'department_id': fields.many2one('hr.department', u'Departamento'),
        'item_id': fields.many2one('product.product', u'Item'),
        'name': fields.char(u'Código'),
        'muda_preco': fields.boolean(u'Pode mudar o preço'),
    }

    def create(self, cr, uid, vals, context=None):
        return super(sncp_receita_itens_dept, self).create(cr, uid, vals, context=context)

    _order = 'department_id,name'

    _sql_constraints = [
        ('department_item_unique', 'unique (department_id, item_id)', u'Este artigo já está incluído no departamento.'),
    ]

sncp_receita_itens_dept()


# _____________________________________________ITENS UTILIZADOR______________________________________
class sncp_receita_itens_user(osv.Model):
    _name = 'sncp.receita.itens.user'
    _description = u"Itens por utilizador"

    def on_change_regra(self, cr, uid, ids, regra, user_id):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'get_item_autorizado'""")
        result = cr.fetchone()
        if result is None:
            self.sql_get_item_autorizado(cr)

        cr.execute(""" SELECT get_item_autorizado(%d)
        """ % user_id)

        result = cr.fetchall()
        lista = []
        for res in result:
            lista.append(res[0])

        lista = list(set(lista))
        if regra == 'inc':
            return {'domain': {'item_id': [('id', 'not in', lista)]}}
        else:
            return {'domain': {'item_id': [('id', 'in', lista)]}}

    def on_change_item_id(self, cr, uid, ids, item_id, regra, user_id):
        if regra == 'mod':
            if item_id is not False:
                cr.execute(""" SELECT muda_preco FROM sncp_receita_itens_dept
                           WHERE item_id = %d AND
                                 department_id = (SELECT department_id FROM hr_employee
                                                  WHERE resource_id =(
                                                        SELECT id FROM resource_resource
                                                        WHERE user_id = %d LIMIT 1))""" % (item_id, user_id))
                result = cr.fetchone()
                if result is not None or result[0] is not None:
                    if len(ids) != 0:
                        self.write(cr, uid, ids, {'muda_preco': not result[0]})
                    return {'value': {'muda_preco': not result[0]}}
        return {}

    _columns = {
        'regra': fields.selection([('inc', u'Incluir'), ('exc', u'Excluir'), ('mod', u'Modificar')], u'Regra'),
        'user_id': fields.many2one('res.users', u'Utilizador'),
        'item_id': fields.many2one('product.product', u'Item'),
        'name': fields.char(u'Código'),
        'muda_preco': fields.boolean(u'Pode mudar o preço'),
    }

    def sql_get_item_autorizado(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION get_item_autorizado(integer)
        RETURNS TABLE(rec_ids integer) AS

        $$
        DECLARE
            dep_id integer;
            lista RECORD;
        BEGIN
            dep_id = (SELECT department_id FROM hr_employee WHERE resource_id =(
                SELECT id FROM resource_resource WHERE user_id = $1 LIMIT 1));
            RETURN QUERY SELECT id FROM product_product WHERE id IN
                    (SELECT item_id FROM sncp_receita_itens_dept WHERE department_id=dep_id AND
                    item_id NOT IN (SELECT item_id FROM sncp_receita_itens_user WHERE user_id=$1 AND
                    regra='exc') UNION (SELECT item_id FROM sncp_receita_itens_user WHERE user_id = $1 AND
                    regra='inc'));
        END;
        $$ LANGUAGE PLPGSQL;
        """)

    def create(self, cr, user, vals, context=None):
        if vals['regra'] == 'mod':
            cr.execute(""" SELECT muda_preco FROM sncp_receita_itens_dept
                            WHERE item_id = %d AND
                                 department_id = (SELECT department_id FROM hr_employee
                                                  WHERE resource_id =(
                                                        SELECT id FROM resource_resource
                                                        WHERE user_id = %d LIMIT 1))"""
                       % (vals['item_id'], vals['user_id']))
            result = cr.fetchone()
            if result is not None or result[0] is not None:
                vals['muda_preco'] = not result[0]
        return super(sncp_receita_itens_user, self).create(cr, user, vals, context=context)

    _order = 'user_id,name'

    _sql_constraints = [
        ('user_item_unique', 'unique (user_id, item_id)', u'Este artigo já tem a regra associada.'),
    ]

sncp_receita_itens_user()

# _____________________________________________DIARIOS DEPARTAMENTO__________________________________


class sncp_receita_diarios_dept(osv.Model):
    _name = 'sncp.receita.diarios.dept'
    _description = u"Diários por Departamento"

    def on_change_department_id(self, cr, uid, ids):
        self.write(cr, uid, ids, {'padrao': False, 'journal_id': False})
        return {'value': {'padrao': False, 'journal_id': False}}

    def on_change_journal_id(self, cr, uid, ids):
        self.write(cr, uid, ids, {'padrao': False})
        return {'value': {'padrao': False}}

    def on_change_padrao(self, cr, uid, ids, padrao, department_id, journal_id):
        if padrao is True and department_id > 0 and journal_id > 0:
            cr.execute("""SELECT id FROM  sncp_receita_diarios_dept
                          WHERE department_id = %d AND
                                padrao = TRUE""" % department_id)
            registo_id = cr.fetchone()
            if registo_id:
                if len(registo_id) == 1:
                    obj_registo = self.browse(cr, uid, registo_id[0])
                    if len(ids) != 0:
                        self.write(cr, uid, ids, {'padrao': True})
                    return {'warning': {'title': u'Aviso de alteração',
                                        'message': u'Para o '+obj_registo.department_id.name +
                                                   u' já está definido o diário padrão "'+
                                                   obj_registo.journal_id.name+u'".' +
                                                   u'Ao guardar este registo irá alterar o diário padrão para '
                                                   u'o actual.'}}
            else:
                return {}
        else:
            return {'value': {'padrao': False}}

    _columns = {
        'department_id': fields.many2one('hr.department', u'Departamento'),
        'journal_id': fields.many2one('account.journal', u'Diário de Vendas',
                                      domain=[('type', '=', 'sale')]),
        'name': fields.char(u'Nome'),
        'padrao': fields.boolean(u'Padrão'),
    }

    def _diario_padrao_unico(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.padrao is True:
            cr.execute("""UPDATE sncp_receita_diarios_dept SET
                          padrao = FALSE
                          WHERE department_id = %d AND
                                id != %d""" % (obj.department_id.id, ids[0]))
        else:
            cr.execute("""SELECT count(id) FROM sncp_receita_diarios_dept
                          WHERE department_id = %d""" % obj.department_id.id)
            result = cr.fetchone()
            if result[0] == 1:
                self.write(cr, uid, ids, {'padrao': True})
        return True

    _constraints = [
        (_diario_padrao_unico, u'', ['padrao']),
    ]

    _sql_constraints = [
        ('department_journal_unique', 'unique (department_id, journal_id)', u'Este diário já está incluído no '
                                                                            u'departamento.'),
    ]

sncp_receita_diarios_dept()