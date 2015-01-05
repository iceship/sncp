# -*- coding: utf-8 -*-
# #############################################################################
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

from openerp.osv import fields, osv

# _______________________________________________________ dimensões_______________________________________


class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'

    def _mesma_dimensao_mesmo_codigo(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])
        no = self.search(cr, uid, [('tipo_dim', '=', record.tipo_dim), ('code', '=', record.code)])
        if len(no) == 1:
            return True

        return False

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' ' + name
            res.append((record['id'], name))
        return res

    def on_change_tipo_dim(self, cr, uid, ids, tipo_dim):
        if len(ids) != 0:
            self.write(cr, uid, ids, {'estado': tipo_dim, 'tipo_dim': tipo_dim})

        if tipo_dim is not None:
            return {
                'value': {
                    'estado': tipo_dim,
                    'tipo_dim': tipo_dim},
            }
        else:
            return {}

    _columns = {
        'tipo_dim': fields.selection([
            ('uo', u'Orgânica'),
            ('ce', u'Económica'),
            ('cf', u'Funcional'),
            ('cc', u'Centro de Custo')], u'Dimensão', select=True,
            help=u"Analítica multi-dimensão, para servir de base aos classificadores orçamentais"),
        'parent_id': fields.many2one('account.analytic.account', "Parent Analytic Account",
                                     domain="[('tipo_dim','=',tipo_dim),('type','=','view')]"),
        'code': fields.char("Reference", select=True),
        'estado': fields.char(u'Campo de controlo'),
        # 0 Tipo de Dimensão editável
        # 1 Tipo de Dimensão não editável
    }

    def create(self, cr, uid, vals, context=None):
        if 'estado' in vals:
            vals['tipo_dim'] = vals['estado']
        return super(account_analytic_account, self).create(cr, uid, vals, context=context)

    _order = 'code'
    _constraints = [(_mesma_dimensao_mesmo_codigo,
                     u'Aviso: Existem 2 contas'
                     u' com a mesma dimensão e a mesma referência', ['tipo_dim', 'code'])]

account_analytic_account()
# _______________________________________________________ FATURA________________________________


class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'department_id': fields.many2one('hr.department', u'Departamento'),
    }

account_invoice()
# _______________________________________________________ LINHAS DE FATURA________________________________


class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
        'organica_id': fields.many2one('account.analytic.account', u'Orgânica', domain=[('tipo_dim', '=', 'uo')]),
        'economica_id': fields.many2one('account.analytic.account', u'Económica', domain=[('tipo_dim', '=', 'ce')]),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional', domain=[('tipo_dim', '=', 'cf')]),
        'centrocustos_id': fields.many2one('account.analytic.account', u'Centro de Custo',
                                           domain=[('tipo_dim', '=', 'cc')]),
        # Para usar na cobrança
        'natureza': fields.selection([('rec', u'Receita Orçamental'),
                                      ('ots', u'Operações de Tesouraria')], u'Natureza'),
    }

account_invoice_line()
# _______________________________________________________ LINHAS DE MOVIMENTO_________________________


class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    _columns = {
        'organica_id': fields.many2one('account.analytic.account', 'tipo_dim', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo')]),
        'economica_id': fields.many2one('account.analytic.account', 'tipo_dim', u'Económica',
                                        domain=[('tipo_dim', '=', 'ce')]),
        'funcional_id': fields.many2one('account.analytic.account', 'tipo_dim', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf')]),
        'centrocustos_id': fields.many2one('account.analytic.account', 'tipo_dim', u'Centro de Custo',
                                           domain=[('tipo_dim', '=', 'cc')]),
    }

account_move_line()
# _______________________________________________________ MOVIMENTO___________________________________


class account_move(osv.osv):
    _inherit = 'account.move'

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            return []
        res = []
        data_move = self.pool.get('account.move').browse(cr, uid, ids, context=context)
        for move in data_move:
            if move.state == 'draft':
                if move.name and len(move.name) > 0:
                    name = move.name
                else:
                    name = '*' + unicode(move.id)
            else:
                name = move.name
            res.append((move.id, name))
        return res

account_move()