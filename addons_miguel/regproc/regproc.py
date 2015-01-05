# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _


def test_partner_id(self, cr, uid, partner_id):
    db_res_partner = self.pool.get('res.partner')
    obj_partner = db_res_partner.browse(cr, uid, partner_id)
    message = u''

    if obj_partner.property_account_receivable.id is False:
            message += u'Contabilidade/Conta a receber (Cliente)\n'

    if obj_partner.property_account_payable.id is False:
        message += u'Contabilidade/Conta a receber (Fornecedor)\n'

    if len(message) != 0:
        raise osv.except_osv(_(u'Aviso'), _(u'Para evitar futuros erros na execução do programa '
                                            u'deverá preencher os seguintes campos do parceiro de negócio:\n'+message
                                            + u'.'))
    return True


def get_sequence(self, cr, uid, context, text, value):
    seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_'+text+'_code_'+unicode(value))
    if seq is False:
        sequence_type = self.pool.get('ir.sequence.type')
        values_type = {
            'name': 'type_'+text+'_name_'+unicode(value),
            'code':  'seq_'+text+'_code_'+unicode(value)}
        sequence_type.create(cr, uid, values_type, context=context)
        sequence = self.pool.get('ir.sequence')
        values = {
            'name': 'seq_'+text+'_name_'+unicode(value),
            'code':  'seq_'+text+'_code_'+unicode(value),
            'number_next': 1,
            'number_increment': 1}
        sequence.create(cr, uid, values, context=context)
        seq = self.pool.get('ir.sequence').get(cr, uid, 'seq_'+text+'_code_'+unicode(value))
    return seq

# ____________________________________________________________  PESQUISA dos registos Notariais________________________


class sncp_regproc_pesquisa_notario_actos(osv.Model):
    _name = 'sncp.regproc.pesquisa.notario.actos'
    _description = u'Registos Notariais'

    def pesquisar(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        where = ''

        # Bloco de pesquisa por texto
        if obj.name is not False:
            if obj.invert is False:
                where = "A.desc LIKE '%" + obj.name + "%' "
            else:
                where = "A.desc NOT LIKE '%" + obj.name + "%'"

        # Bloco de pesquisa pelas datas
        if obj.datahora_ini is not False and obj.datahora_fim is not False:
            if len(where) > 0:
                where += ' AND '
            where = where + "A.datahora BETWEEN '" + unicode(obj.datahora_ini) +\
                "' AND '" + unicode(obj.datahora_fim) + "'"
        if obj.datahora_ini is not False and obj.datahora_fim is False:
            if len(where) > 0:
                where += ' AND '
            where = where + "A.datahora >= '" + unicode(obj.datahora_ini) + "'"
        if obj.datahora_ini is False and obj.datahora_fim is not False:
            if len(where) > 0:
                where += ' AND '
            where = where + "A.datahora <= '" + unicode(obj.datahora_fim)+"'"

        # Bloco de pesquisa por referencias
        if obj.objecto_id.id != 0:
            if len(where) > 0:
                where += ' AND '
            where = where + "A.objecto_id = " + unicode(obj.objecto_id.id)
        # Aquisições/Alienações
        if obj.aquis_alien_id.id != 0:
            if len(where) > 0:
                where += ' AND '
            where = where + "A.id IN (SELECT AA.notario_actos_id FROM sncp_regproc_notario_actos_aquis_alien_rel " \
                            "AS AA  WHERE AA.aquis_alien_id = " + unicode(obj.aquis_alien_id.id) + ")"
        # Outorgantes
        if obj.outrg_id.id != 0:
            if len(where) > 0:
                where += ' AND '
            where = where + "A.id IN (SELECT O.acto_id FROM sncp_regproc_notario_actos_outrg AS O " \
                            "WHERE O.id = " + unicode(obj.outrg_id.id) + ")"

        lista_ids = []
        if len(where) > 0:
            query = unicode('SELECT A.id FROM sncp_regproc_notario_actos AS A WHERE ' + where)
            cr.execute(query)
            lista_tuplo = cr.fetchall()
            for line in lista_tuplo:
                lista_ids.append(line[0])
        else:
            lista_ids = self.pool.get('sncp.regproc.notario.actos').search(cr, uid, [])
        self.write(cr, uid, ids, {'notario_actos_ids': [(6, 0, [])]})
        self.write(cr, uid, ids, {'notario_actos_ids': [(6, 0, lista_ids)]})
        return True

    _columns = {
        'datahora_ini': fields.datetime(u'A partir de'),
        'datahora_fim': fields.datetime(u'Até'),
        'objecto_id': fields.many2one('sncp.regproc.notario.objecto', u'Por objeto'),
        'outrg_id': fields.many2one('sncp.regproc.notario.actos.outrg', u'Por Outorgante'),
        'aquis_alien_id': fields.many2one('sncp.regproc.aquis.alien', u'Por Aquisição/Alienação'),
        'name': fields.text(u'Descrição contém'),
        'invert': fields.boolean(u'Não contém'),
        'notario_actos_ids': fields.many2many('sncp.regproc.notario.actos', 'sncp_regproc_notario_actos_pesquisa_rel',
                                              'pesquisa_id', 'notario_actos_id', u'Lista dos Registos'),

    }

sncp_regproc_pesquisa_notario_actos()

# _____________________________________________Objetos dos Actos Notariais _________________________


class sncp_regproc_notario_objecto(osv.Model):
    _name = 'sncp.regproc.notario.objecto'
    _description = u'Objetos dos Actos Notariais'

    def get_objecto_list_js(self, cr, uid, context=None):
        lista_ids = self.search(cr, uid, [])
        lista_ids = list(set(lista_ids))
        return self.name_get(cr, uid, lista_ids, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            cr.execute("""
            SELECT id
            FROM sncp_regproc_notario_actos
            WHERE objecto_id = %d
            """ % nid)

            res_notario_atos = cr.fetchall()

            if len(res_notario_atos) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o objeto '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Registo de Processos\Atos Notoriais\Registo.'))

        return super(sncp_regproc_notario_objecto, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'name': fields.char(u'Objeto do Acto', size=32),
        'cod_estatistico': fields.char(u'Código estatístico', size=8),

    }

sncp_regproc_notario_objecto()
# _____________________________________________Registo dos Actos Notariais __________________________


class sncp_regproc_notario_actos(osv.Model):
    _name = 'sncp.regproc.notario.actos'
    _description = u'Registo dos Actos Notariais'

    def get_id_list_js(self, cr, uid, vals, context=None):
        if len(vals) == 0:
            lista = self.search(cr, uid, [])
        else:
            cr.execute("""SELECT A.id FROM sncp_regproc_notario_actos AS A
                          WHERE A.desc LIKE '%s'""" % ('%' + unicode(vals) + '%'))
            lista = []
            for res in cr.fetchall():
                lista.append(res[0])
        return lista

    _columns = {
        'name': fields.char(u'Número', size=12),
        'objecto_id': fields.many2one('sncp.regproc.notario.objecto', u'Objecto do Acto'),
        'outorgantes': fields.char(u'Outorgantes', size=64),
        'datahora': fields.datetime(u'Data e Hora'),
        'livro': fields.char(u'Livro', size=12),
        'folhas_ini': fields.char(u'Folhas', size=8),
        'folhas_fim': fields.char(u'a', size=8),
        'desc': fields.text(u'Descrição'),
        'aquis_alien_ids': fields.many2many('sncp.regproc.aquis.alien',
                                            'sncp_regproc_notario_actos_aquis_alien_rel',
                                            'notario_actos_id', 'aquis_alien_id',
                                            u'Aquisição/Alienação'),
        'outrg_ids': fields.one2many('sncp.regproc.notario.actos.outrg', 'acto_id', u'Outorgantes'),
    }

    def create(self, cr, uid, vals, context=None):
        # Bloco de atribuição do Número
        db_comum_param = self.pool.get('sncp.comum.param')
        db_ir_sequence = self.pool.get('ir.sequence')
        param_ids = db_comum_param.search(cr, uid, [('state', '=', 'draft')])
        if len(param_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                u'Preencha os parâmetros por defeito no menu:\n'
                                                u'Comum/Parâmetros.'))
        obj_param = db_comum_param.browse(cr, uid, param_ids[0])
        vals['name'] = db_ir_sequence.next_by_id(cr, uid, obj_param.an_sequence_id.id)
        if vals['name'] is False:
            raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                u'Preencha os parâmetros por defeito no menu:\n'
                                                u'Comum/Parâmetros.'))
        # Bloco de registo dos autorgantes
        db_res_partner = self.pool.get('res.partner')
        db_hr_employee = self.pool.get('hr.employee')
        cont = len(vals['outrg_ids'])
        if cont > 0:
            if vals['outrg_ids'][0][2]['qualidade'] == 'empr':
                vals['outorgantes'] = \
                    db_hr_employee.browse(cr, uid, vals['outrg_ids'][0][2]['employee_id']).name_related
            if vals['outrg_ids'][0][2]['qualidade'] == 'parc':
                vals['outorgantes'] = db_res_partner.browse(cr, uid, vals['outrg_ids'][0][2]['partner_id']).name
        if cont == 2:
            vals['outorgantes'] += ' e Outro'
        elif cont > 3:
            vals['outorgantes'] += ' e Outros'
        return super(sncp_regproc_notario_actos, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        super(sncp_regproc_notario_actos, self).write(cr, uid, ids, vals, context)
        values = {}
        if 'outrg_ids' in vals:
            db_res_partner = self.pool.get('res.partner')
            db_hr_employee = self.pool.get('hr.employee')
            obj = self.browse(cr, uid, ids[0])
            cont = len(obj.outrg_ids)
            if cont > 0:
                if obj.outrg_ids[0].qualidade == 'empr':
                    values['outorgantes'] = db_hr_employee.browse(cr, uid, obj.outrg_ids[0].employee_id.id).name_related
                if obj.outrg_ids[0].qualidade == 'parc':
                    values['outorgantes'] = db_res_partner.browse(cr, uid, obj.outrg_ids[0].partner_id.id).name
            if cont == 2:
                values['outorgantes'] += ' e Outro'
            elif cont >= 3:
                values['outorgantes'] += ' e Outros'
            super(sncp_regproc_notario_actos, self).write(cr, uid, ids, values, context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            cr.execute("""DELETE FROM sncp_regproc_notario_actos_outrg WHERE acto_id = %d""" % nid)
        return super(sncp_regproc_notario_actos, self).unlink(cr, uid, ids, context)

    _defaults = {
        'datahora': unicode(date(datetime.now().year, datetime.now().month, datetime.now().day)),
    }

sncp_regproc_notario_actos()
# ____________________________________________ Outorgantes ______________________________________________


class sncp_regproc_notario_actos_outrg(osv.Model):
    _name = 'sncp.regproc.notario.actos.outrg'
    _description = u'Outorgantes'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['qualidade', 'employee_id', 'partner_id'], context=context)
        res = []
        for record in reads:
            if record['qualidade'] == 'empr':
                name = u'Funcionário ' + record['employee_id'][1]

            else:
                name = u'Parceiro ' + record['partner_id'][1]
            res.append((record['id'], name))
        return res

    def get_outrg_list_js(self, cr, uid, context=None):
        res_partner = self.pool.get('res.partner')
        hr_employee = self.pool.get('hr.employee')
        cr.execute("""
            SELECT DISTINCT qualidade,partner_id,employee_id from sncp_regproc_notario_actos_outrg
        """)
        lista_outrg = cr.fetchall()
        lista_ids = []
        for outrg in lista_outrg:
            if outrg[0] == 'empr':
                employee = hr_employee.browse(cr, uid, outrg[2])
                lista_ids.append(('empr', outrg[2], u'Funcionário ' + employee.name))
            elif outrg[0] == 'parc':
                partner = res_partner.browse(cr, uid, outrg[1])
                lista_ids.append(('parc', outrg[1], u'Parceiro ' + partner.name))
        return lista_ids

    def get_acto_list_js(self, cr, uid, arg):
        lista_actos = []
        val = arg.split(",")
        if val[0] == 'empr':
            cr.execute("""SELECT acto_id FROM sncp_regproc_notario_actos_outrg WHERE qualidade = '%s' AND
                          employee_id = %d""" % (val[0], int(val[1])))
            result = cr.fetchall()
            for res in result:
                lista_actos.append(res[0])
        elif val[0] == 'parc':
            cr.execute("""SELECT acto_id FROM sncp_regproc_notario_actos_outrg WHERE qualidade = '%s' AND
                          partner_id = %d""" % (val[0], int(val[1])))
            result = cr.fetchall()
            for res in result:
                lista_actos.append(res[0])
        return lista_actos

    def on_change_qualidade(self, cr, uid, ids, qualidade):
        if qualidade == 'empr':
            if len(ids) != 0:
                self.write(cr, uid, ids[0], {'qualidade': qualidade, 'partner_id': False})
            return {'value': {'qualidade': qualidade, 'partner_id': False}}
        elif qualidade == 'parc':
            if len(ids) != 0:
                self.write(cr, uid, ids[0], {'qualidade': qualidade, 'employee_id': False})
            return {'value': {'qualidade': qualidade, 'employee_id': False}}

        return {}

    _columns = {
        'acto_id': fields.many2one('sncp.regproc.notario.actos', u'Acto Notarial'),
        'name': fields.integer(u'Sequência'),
        'qualidade': fields.selection([('empr', u'Funcionário'), ('parc', u'Parceiro'), ], u'Qualidade'),
        'employee_id': fields.many2one('hr.employee', u'Funcionário'),
        'partner_id': fields.many2one('res.partner', u'Parceiro'), }

    def create(self, cr, uid, vals, context=None):
        if 'partner_id' in vals:
            test_partner_id(self, cr, uid, vals['partner_id'])
        vals['name'] = get_sequence(self, cr, uid, context, 'act_outrg', vals['acto_id'])
        return super(sncp_regproc_notario_actos_outrg, self).create(cr, uid, vals, context)

    _sql_constraints = [
        ('employee_acto_unique', 'unique (acto_id,employee_id)', u'Este funcionário já está registado para este acto'),
        ('partner_acto_unique', 'unique (acto_id,partner_id)', u'Este parceiro já está registado para este acto'),

    ]

sncp_regproc_notario_actos_outrg()
# ____________________________________________ Aquisições e Alienações ______________________________________________


class sncp_regproc_aquis_alien(osv.Model):
    _name = 'sncp.regproc.aquis.alien'
    _description = u'Aquisições e Alienações'

    def get_autorized_user_js(self, cr, uid, context=None):
        db_res_users = self.pool.get('res.users')
        lista_ids = []
        cr.execute("""SELECT DISTINCT(uid) FROM res_groups_users_rel WHERE gid in (
                    SELECT id FROM res_groups WHERE category_id in (
                        SELECT id FROM ir_module_category WHERE name ILIKE '%regproc%')) """)
        lista = cr.fetchall()
        for line in lista:
            lista_ids.append(line[0])
        return db_res_users.name_get(cr, uid, lista_ids, context=context)

    def get_aquis_alien_list_js(self, cr, uid, context=None):
        lista_ids = self.search(cr, uid, [])
        lista_ids = list(set(lista_ids))
        return self.name_get(cr, uid, lista_ids, context=context)

    def on_change_expro(self, cr, uid, ids, expro):
        if expro is False:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'posse': None})

            return {
                'value': {
                    'posse': u'',
                    'expro': False
                }
            }

        return {}

    _columns = {
        'natureza': fields.selection([('aquis', u'Aquisição'), ('alien', u'Alienação'), ], u'Natureza'),
        'name': fields.char(u'Número'),
        'expro': fields.boolean(u'Expropriação'),
        'desc': fields.text(u'Descrição'),
        'delib_cm_data': fields.date(u'Deliberação da Câmara de'),
        'delib_cm_por': fields.char(u'por', size=64),
        'delib_am_data': fields.date(u'Deliberação da Assembleia de'),
        'delib_am_por': fields.char(u'por', size=64),
        'autorizada': fields.char(u'Autorização', size=64),
        'publicada': fields.char(u'Publicada', size=32),
        'posse': fields.date(u'Posse administrativa'),
        'limite': fields.date(u'Limite de vigência'),
        'caucao_dep': fields.date(u'Depósito até'),
        'caucao_mont': fields.float(u'Montante da caução', digits=(12, 2)),
        'acto_not_ids': fields.many2many('sncp.regproc.notario.actos',
                                         'sncp_regproc_notario_actos_aquis_alien_rel',
                                         'aquis_alien_id', 'notario_actos_id',
                                         u'Acto Notarial'),
        'parcelas_ids': fields.one2many('sncp.regproc.aquis.alien.parcel', 'aquis_alien_id', u'Parcelas'),
        'notific_ids': fields.one2many('sncp.regproc.aquis.alien.notif', 'aquis_alien_id', u'Notificações'), }

    def create(self, cr, uid, vals, context=None):
        # Bloco de atribuição do Número
        db_comum_param = self.pool.get('sncp.comum.param')
        db_ir_sequence = self.pool.get('ir.sequence')
        param_ids = db_comum_param.search(cr, uid, [('state', '=', 'draft')])
        if len(param_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                u'Preenche os parâmetros por defeito no menu:\n'
                                                u'Comum/Parâmetros.'))
        obj_param = db_comum_param.browse(cr, uid, param_ids[0])
        if vals['natureza'] == 'aquis':
            vals['name'] = db_ir_sequence.next_by_id(cr, uid, obj_param.aquis_sequence_id.id)
        if vals['natureza'] == 'alien':
            vals['name'] = db_ir_sequence.next_by_id(cr, uid, obj_param.alien_sequence_id.id)

        return super(sncp_regproc_aquis_alien, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'expro' in vals:
            if vals['expro'] is False:
                vals['posse'] = None
        super(sncp_regproc_aquis_alien, self).write(cr, uid, ids, vals, context)
        if 'delib_cm_data' in vals:
            cr.execute("""UPDATE sncp_regproc_aquis_alien_notif SET done = FALSE
                          WHERE aquis_alien_id = %d AND evento = 'delibcm'""" % ids[0])
        if 'delib_am_data' in vals:
            cr.execute("""UPDATE sncp_regproc_aquis_alien_notif SET done = FALSE
                          WHERE aquis_alien_id = %d AND evento = 'delibam'""" % ids[0])
        if 'autorizada' in vals:
            cr.execute("""UPDATE sncp_regproc_aquis_alien_notif SET done = FALSE
                          WHERE aquis_alien_id = %d AND evento = 'autoriza'""" % ids[0])
        if 'publicada' in vals:
            cr.execute("""UPDATE sncp_regproc_aquis_alien_notif SET done = FALSE
                          WHERE aquis_alien_id = %d AND evento = 'publica'""" % ids[0])
        if 'posse' in vals:
            cr.execute("""UPDATE sncp_regproc_aquis_alien_notif SET done = FALSE
                          WHERE aquis_alien_id = %d AND evento = 'posse'""" % ids[0])
        if 'limite' in vals:
            cr.execute("""UPDATE sncp_regproc_aquis_alien_notif SET done = FALSE
                          WHERE aquis_alien_id = %d AND evento = 'limite'""" % ids[0])
        if 'caucao_dep' in vals:
            cr.execute("""UPDATE sncp_regproc_aquis_alien_notif SET done = FALSE
                          WHERE aquis_alien_id = %d AND evento = 'deposito'""" % ids[0])

        self.pool.get('sncp.regproc.aquis.alien.notif').notificar(cr, uid, context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            cr.execute("""
            DELETE FROM sncp_regproc_aquis_alien_parcel_titls
            WHERE aquis_alien_parcel_id IN (SELECT id FROM sncp_regproc_aquis_alien_parcel
                                            WHERE aquis_alien_id = %d)
            """ % nid)

            cr.execute("""
            DELETE FROM sncp_regproc_aquis_alien_parcel
            WHERE aquis_alien_id = %d
            """ % nid)

            cr.execute("""
            DELETE FROM sncp_regproc_aquis_alien_notif
            WHERE aquis_alien_id = %d
            """ % nid)

        return super(sncp_regproc_aquis_alien, self).unlink(cr, uid, ids, context=context)

    _order = 'natureza,name'

    _sql_constraints = [
        ('natureza_name_unique', 'unique (natureza,name)', u'O conjunto Natureza + Número tem que ser único!')
    ]

sncp_regproc_aquis_alien()
# ______________________________________________________________ Parcela _________________________________


class sncp_regproc_aquis_alien_parcel(osv.Model):
    _name = 'sncp.regproc.aquis.alien.parcel'
    _description = u'Parcelas de Aquisição/Alienação'

    def on_change_natureza(self, cr, uid, ids, natureza):
        if natureza == 'rustico':
            if len(ids) != 0:
                self.write(cr, uid, ids, {'art_matr_urb': None})
            return {
                'value': {
                    'art_matr_urb': u''
                }
            }
        elif natureza == 'urbano':
            if len(ids) != 0:
                self.write(cr, uid, ids, {'art_matr_rust': None})
            return {
                'value': {
                    'art_matr_rust': u''
                }
            }
        elif natureza in ['indef', 'napl']:
            if len(ids) != 0:
                self.write(cr, uid, ids, {'art_matr_urb': None, 'art_matr_rust': None})
            return {
                'value': {
                    'art_matr_rust': u'',
                    'art_matr_urb': u''
                }
            }

        return {}

    _columns = {
        'aquis_alien_id': fields.many2one('sncp.regproc.aquis.alien', u'Aquisição/'),
        'name': fields.char(u'Parcela', size=8),
        'desc': fields.text(u'Descrição'),
        'natureza': fields.selection([('rustico', u'Rústico'),
                                      ('urbano', u'Urbano'),
                                      ('misto', u'Misto'),
                                      ('indef', u'Indefinido'),
                                      ('napl', u'Não aplicável'), ], u'Natureza do Prédio'),
        'freguesia_id': fields.many2one('sncp.comum.freguesias', u'Freguesias'),
        'art_crp': fields.char(u'Artigo na CRP', size=12),
        'art_matr_rust': fields.char(u'Artigo matricial rústico', size=12),
        'art_matr_urb': fields.char(u'Artigo matricial urbano', size=12),
        'area_coberta': fields.char(u'Área Coberta', size=12),
        'area_total': fields.char(u'Área total', size=12),
        'preco': fields.float(u'Preço total', digits=(12, 2)),
        'caucao_forma': fields.selection([('dinheiro', u'Em dinheiro'),
                                          ('bancaria', u'Garantia bancária'),
                                          ('seguro', u'Seguro'),
                                          ('outra', u''),
                                          ('napl', u''), ], u'Forma'),
        'caucao_montante': fields.float(u'Caução/Garantia', digits=(12, 2)),
        'aquis_alien_parcel_titls_ids': fields.one2many('sncp.regproc.aquis.alien.parcel.titls',
                                                        'aquis_alien_parcel_id',
                                                        u'Titulares'),
    }

    def write(self, cr, uid, ids, vals, context=None):
        if 'natureza' in vals:
            if vals['natureza'] == 'rustico':
                vals['art_matr_urb'] = None
            elif vals['natureza'] == 'urbano':
                vals['art_matr_rust'] = None
            elif vals['natureza'] in ['indef', 'napl']:
                vals['art_matr_urb'] = None
                vals['art_matr_rust'] = None
        return super(sncp_regproc_aquis_alien_parcel, self).write(cr, uid, ids, vals, context=context)

sncp_regproc_aquis_alien_parcel()
# _______________________________________________________________ Titulares ____________________________________


class sncp_regproc_aquis_alien_parcel_titls(osv.Model):
    _name = 'sncp.regproc.aquis.alien.parcel.titls'
    _description = 'Titulares das parcelas'

    _columns = {
        'aquis_alien_parcel_id': fields.many2one('sncp.regproc.aquis.alien.parcel', u'Aquisição/Alienação'),
        'name': fields.char(u'NIF', size=9),
        'partner_id': fields.many2one('res.partner', u'Parceiro'),
        'street': fields.related('partner_id', 'street', type="char", store=True, string=u'Endereço'),
        'city': fields.related('partner_id', 'city', type="char", store=True, string=u'Localidade'),
    }

    def create(self, cr, uid, vals, context=None):
        test_partner_id(self, cr, uid, vals['partner_id'])
        db_res_partner = self.pool.get('res.partner')
        partner = db_res_partner.browse(cr, uid, vals['partner_id'])
        vals['name'] = partner.vat or None
        return super(sncp_regproc_aquis_alien_parcel_titls, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'partner_id' in vals:
            db_res_partner = self.pool.get('res.partner')
            partner = db_res_partner.browse(cr, uid, vals['partner_id'])
            vals['name'] = partner.vat or None
        return super(sncp_regproc_aquis_alien_parcel_titls, self).write(cr, uid, ids, vals, context)

sncp_regproc_aquis_alien_parcel_titls()
# _____________________________________________________________________ Notificação __________________________


class sncp_regproc_aquis_alien_notif(osv.Model):
    _name = 'sncp.regproc.aquis.alien.notif'
    _description = u'Notificação'

    def da_data(self, data, unidade, prazo):
        if unidade == 'days':
            data = datetime.strptime(data, "%Y-%m-%d") + relativedelta(days=prazo)
        elif unidade == 'weeks':
            data = datetime.strptime(data, "%Y-%m-%d") + relativedelta(weeks=prazo)
        else:
            data = datetime.strptime(data, "%Y-%m-%d") + relativedelta(month=prazo)
        return data.date()

    def data_valida(self, obj_notif, obj_aquis_alien):
        if obj_notif.evento == 'delibcm':
            data = self.da_data(obj_aquis_alien.delib_cm_data, obj_notif.unidade, obj_notif.prazo)
        elif obj_notif.evento == 'delibam':
            data = self.da_data(obj_aquis_alien.delib_am_data, obj_notif.unidade, obj_notif.prazo)
        elif obj_notif.evento == 'autoriza':
            if len(obj_aquis_alien.autorizada) > 0:
                return True
            else:
                return False
        elif obj_notif.evento == 'publica':
            if len(obj_aquis_alien.publicada) > 0:
                return True
            else:
                return False
        elif obj_notif.evento == 'posse':
            data = self.da_data(obj_aquis_alien.posse, obj_notif.unidade, obj_notif.prazo)
        elif obj_notif.evento == 'limite':
            data = self.da_data(obj_aquis_alien.limite, obj_notif.unidade, obj_notif.prazo)
        elif obj_notif.evento == 'deposito':
            data = self.da_data(obj_aquis_alien.caucao_dep, obj_notif.unidade, obj_notif.prazo)
        else:
            return False
        if data <= date.today():
            return True
        else:
            return False

    def notificar(self, cr, uid, context):
        db_sncp_regproc_aquis_alien = self.pool.get('sncp.regproc.aquis.alien')
        db_res_users = self.pool.get('res.users')
        db_mail_mail = self.pool.get('mail.mail')
        assunto = u''
        lista_nao_enviados = []
        cr.execute("""SELECT id,aquis_alien_id
                      FROM sncp_regproc_aquis_alien_notif
                      WHERE done = FALSE """)
        result = cr.fetchall()
        for res in result:
            papel = False
            obj_aquis_alien = db_sncp_regproc_aquis_alien.browse(cr, uid, res[1])
            obj_notif = self.browse(cr, uid, res[0])
            if obj_aquis_alien.natureza == 'aquis':
                natureza = u'Aquisição'
            else:
                natureza = u'Alienação'

            if obj_notif.evento == 'delibcm':
                evento = u' da Deliberação da Câmara '
            elif obj_notif.evento == 'delibam':
                evento = u' da Deliberação da Assembleia '
            elif obj_notif.evento == 'autoriza':
                evento = u' da Autorização '
            elif obj_notif.evento == 'publica':
                evento = u' da Publicação da autorização '
            elif obj_notif.evento == 'posse':
                evento = u' da Posse administrativa '
            elif obj_notif.evento == 'limite':
                evento = u' do Limite de vigência '
            elif obj_notif.evento == 'deposito':
                evento = u' do Depósito da caução '
            else:
                evento = u' do Evento Desconhecido '

            try:
                if obj_notif.prazo == 0 or self.data_valida(obj_notif, obj_aquis_alien):
                    assunto = u'Notificação ' + evento + unicode(obj_notif.name) + u' referente à ' + \
                              natureza + u' ' + obj_aquis_alien.name
                    if obj_notif.notificar in ['user']:
                        email = obj_notif.user_id.partner_id.email or False
                        body = obj_notif.teor
                        if email:
                            enviado = obj_notif.id
                    elif obj_notif.notificar in ['empr']:
                        if obj_notif.employee_id.resource_id.user_id.id:
                            email = obj_notif.employee_id.resource_id.user_id.partner_id.email
                            body = obj_notif.teor
                        else:
                            email = False
                        if email:
                            enviado = obj_notif.id
                    else:
                        if obj_notif.partner_id.email:
                            email = obj_notif.partner_id.email
                            body = obj_notif.teor
                            enviado = obj_notif.id
                        else:
                            papel = True
                            enviado = obj_notif.id
                            # Impressão em papel
                            vals = {'assunto': assunto, 'partner': obj_notif.partner_id,
                                    'body': unicode(obj_notif.teor)}
                            db_receita_print_report = self.pool.get('sncp.receita.print.report')
                            result = db_receita_print_report.imprime_notificacao_regproc(cr, uid, vals, context)
                            lista_nao_enviados.append(result)

                    if email is False and not papel:
                        email = db_res_users.browse(cr, uid, uid).partner_id.email
                        body = u'Na notificação ' + evento + unicode(obj_notif.name) +\
                               u' o notificado não tem email definido.'

                    # Bloco de envio de email
                    if type(body) in [str, unicode]:
                        body_html = '<html><body>' + body.replace('\n', '<br>') + '</body></html>'
                        datahora = unicode(datetime.now())
                        if datahora.find('.') != -1:
                            datahora = datahora[:datahora.find('.')]
                        values_email = {
                            'attachment_ids': [[6, False, []]],
                            'auto_delete': False,
                            'body_html': unicode(body_html),
                            'email_to': unicode(email),
                            'date': unicode(datahora),
                            'author_id': uid,
                            'type': 'email',
                            'email_from': u'openerp.notification@gmail.com',
                            'subject': unicode(assunto)}
                        mail_id = db_mail_mail.create(cr, uid, values_email)
                        db_mail_mail.send(cr, uid, [mail_id])
                        self.write(cr, uid, enviado, {'done': True})

            except (RuntimeError, TypeError, NameError):
                lista_nao_enviados.append(assunto)
        if len(lista_nao_enviados) > 0:
            if lista_nao_enviados.count(u'') == len(lista_nao_enviados):
                return True

            body = u'Não foi possível enviar email para as seguintes notificações: \n'
            for line in lista_nao_enviados:
                if len(line) > 0:
                    body = body + line + '\n'

            body_html = '<html><body>' + body.replace('\n', '<br>') + '</body></html>'
            datahora = unicode(datetime.now())
            if datahora.find('.') != -1:
                datahora = datahora[:datahora.find('.')]
            values_email = {
                'attachment_ids': [[6, False, []]],
                'auto_delete': False,
                'body_html': unicode(body_html),
                'email_to': unicode(db_res_users.browse(cr, uid, uid).partner_id.email),
                'date': unicode(datahora),
                'author_id': uid,
                'type': 'email',
                'email_from': u'openerp.notification@gmail.com',
                'subject': u'itens não enviados'}
            mail_id = db_mail_mail.create(cr, uid, values_email)
            db_mail_mail.send(cr, uid, [mail_id])

        return True

    def on_change_notificado_id(self, cr, uid, ids, notificado, notificado_id):
        if notificado_id is False:
            return {}
        if notificado == 'user':
            self.write(cr, uid, ids, {'user_id': notificado_id,
                                      'employee_id': False,
                                      'partner_id': False})
            return {'value': {'user_id': notificado_id,
                              'employee_id': False,
                              'partner_id': False}}
        elif notificado == 'empr':
            self.write(cr, uid, ids, {'employee_id': notificado_id,
                                      'user_id': False,
                                      'partner_id': False})
            return {'value': {'employee_id': notificado_id,
                              'user_id': False,
                              'partner_id': False}}
        else:
            self.write(cr, uid, ids, {'partner_id': notificado_id,
                                      'employee_id': False,
                                      'user_id': False})
            return {'value': {'partner_id': notificado_id,
                              'employee_id': False,
                              'user_id': False}}

    _columns = {
        'aquis_alien_id': fields.many2one('sncp.regproc.aquis.alien', u'Aquisição/Alienação'),
        'evento': fields.selection([('delibcm', u'Deliberação da Câmara'),
                                    ('delibam', u'Deliberação da Assembleia'),
                                    ('autoriza', u'Autorização'),
                                    ('publica', u'Publicação da autorização'),
                                    ('posse', u'Posse administrativa'),
                                    ('limite', u'Limite de vigência'),
                                    ('deposito', u'Depósito da caução'), ], u'Evento'),
        'name': fields.integer(u'Sequência'),
        'name_notific': fields.char(u'Nome'),
        'notificar': fields.selection([('user', u'Utilizador'),
                                       ('empr', u'Funcionário'),
                                       ('parc', u'Parceiro'), ], u'Notificar'),
        'employee_id': fields.many2one('hr.employee', u'Funcionário'),
        'user_id': fields.many2one('res.users', u'Utilizador'),
        'partner_id': fields.many2one('res.partner', u'Parceiro'),
        'prazo': fields.integer(u'Até'),
        'unidade': fields.selection([('days', u'Dias'),
                                     ('weeks', u'Semanas'),
                                     ('months', u'Meses'), ], u''),
        'teor': fields.text(u'Teor da notificação'),
        'done': fields.boolean(u'Executada'),
    }

    def create(self, cr, uid, vals, context=None):
        vals['name'] = get_sequence(self, cr, uid, context, vals['evento'], vals['aquis_alien_id'])
        if vals['notificar'] == 'user':
            db_res_users = self.pool.get('res.users')
            user = db_res_users.browse(cr, uid, vals['user_id'])
            vals['name_notific'] = user.partner_id.name
        elif vals['notificar'] == 'empr':
            db_hr_employee = self.pool.get('hr.employee')
            employee = db_hr_employee.browse(cr, uid, vals['employee_id'])
            vals['name_notific'] = employee.name_related
        elif vals['notificar'] == 'parc':
            test_partner_id(self, cr, uid, vals['partner_id'])
            db_res_partner = self.pool.get('res.partner')
            partner = db_res_partner.browse(cr, uid, vals['partner_id'])
            vals['name_notific'] = partner.name

        return super(sncp_regproc_aquis_alien_notif, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'notificar' in vals and vals['notificar'] == 'user':
            db_res_users = self.pool.get('res.users')
            user = db_res_users.browse(cr, uid, vals['user_id'])
            vals['name_notific'] = user.partner_id.name
        elif 'notificar' in vals and vals['notificar'] == 'empr':
            db_hr_employee = self.pool.get('hr.employee')
            employee = db_hr_employee.browse(cr, uid, vals['employee_id'])
            vals['name_notific'] = employee.name_related
        elif 'notificar' in vals and vals['notificar'] == 'parc':
            db_res_partner = self.pool.get('res.partner')
            partner = db_res_partner.browse(cr, uid, vals['partner_id'])
            vals['name_notific'] = partner.name
        super(sncp_regproc_aquis_alien_notif, self).write(cr, uid, ids, vals, context)

        return True

    _order = 'evento,name'

sncp_regproc_aquis_alien_notif()