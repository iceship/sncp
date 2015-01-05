# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2012 Tiny SPRL (<http://tiny.be>).
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
from datetime import datetime
from openerp.tools.translate import _


class formulario_sncp_tesouraria_guia_cobrar_diario(osv.Model):
    _name = 'formulario.sncp.tesouraria.guia.cobrar.diario'
    _description = u"Formulário de Cobrança de Guias"

    send = {}

    def wizard(self, cr, uid, ids):
        """Method is used to show form view in new windows"""
        db_sncp_comum_param = self.pool.get('sncp.comum.param')
        param_ids = db_sncp_comum_param.search(cr, uid, [('state', '=', 'draft')])
        if len(param_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                u'Preencha os parâmetros por defeito no menu:\n'
                                                u'Comum/Parâmetros.'))
        parametros = db_sncp_comum_param.browse(cr, uid, param_ids[0])

        if parametros.diario_liq_rec_id.id is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina o diário de liquidação da receita em '
                                                u' Comum/Parâmetros.'))

        if parametros.diario_cob_rec_id.id is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina o diário de cobrança da receita em '
                                                u' Comum/Parâmetros.'))

        db_sncp_tesouraria_caixas = self.pool.get('sncp.tesouraria.caixas')
        caixas_ids = db_sncp_tesouraria_caixas.search(cr, uid, [])
        def_caixa_id = False
        for caixa_id in caixas_ids:
            caixa = db_sncp_tesouraria_caixas.browse(cr, uid, caixa_id)
            lista = caixa.caixa_user

            for elem in lista:
                if elem.name.id == uid and elem.default is True:
                    def_caixa_id = caixa.id
                    break

            if def_caixa_id is not False:
                break

        nid = self.create(cr, uid, {'guia_id': ids[0],
                                    'diario_liq_id': parametros.diario_liq_rec_id.id,
                                    'diario_cobr_id': parametros.diario_cob_rec_id.id,
                                    'caixa_id': def_caixa_id,
                                    'user_id': uid, })

        return {
            'name': u'<div style="width:500px;">Parâmetros de cobrança da Guia</div>',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.sncp.tesouraria.guia.cobrar.diario',
            'nodestroy': True,
            'target': 'new',
            'res_id': nid, }

    def end(self, cr, uid, ids, context=None,):
        obj = self.browse(cr, uid, ids[0])
        return self.pool.get('sncp.receita.guia.rec').cobrar_end(cr, uid, [obj.guia_id.id])

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    _columns = {
        'guia_id': fields.many2one('sncp.receita.guia.rec', u''),
        'name': fields.datetime(u'Data e hora'),
        'diario_liq_id': fields.many2one('account.journal', u'Diário de Liquidação'),
        'diario_cobr_id': fields.many2one('account.journal', u'Diário de Cobrança'),
        'user_id': fields.many2one('res.users', u'utilizador'),
        'caixa_id': fields.many2one('sncp.tesouraria.caixas', u'Caixa'),
    }

    def get_journal_id(self, cr, text):
        cr.execute("""SELECT id FROM account_journal WHERE code = '%s'""" % text)
        return cr.fetchone()

    _defaults = {
        'name': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                        datetime.now().minute, datetime.now().second)),
    }

    def _check_ano(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        data = datetime.strptime(obj.name, "%Y-%m-%d %H:%M:%S")
        if data.year != datetime.now().year:
            raise osv.except_osv(_(u'Aviso'), _(u'A data têm que ser do ano corrente.'))
        else:
            return True

    def _diario_restrict(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.diario_liq_id.id is not False:
            if obj.diario_liq_id.default_credit_account_id.id is False:
                raise osv.except_osv(_(u'Aviso'), _(u'Defina a conta a crédito e/ou a débito do diário '+
                                                    unicode(obj.diario_liq_id.name)+u'.'))
        return True

    def _caixa_restrict(self, cr, uid, ids, context=None):

        db_sncp_tesouraria_caixas = self.pool.get('sncp.tesouraria.caixas')

        obj = self.browse(cr, uid, ids[0])

        caixa = db_sncp_tesouraria_caixas.browse(cr, uid, obj.caixa_id.id)
        lista = caixa.caixa_user

        for elem in lista:
            if elem.name.id == obj.user_id.id and elem.default is True:
                    return True

        db_res_users = self.pool.get('res.users')
        utilizador = db_res_users.browse(cr, uid, obj.user_id.id)
        raise osv.except_osv(_(u'Aviso'), _(u'O utilizador ' + unicode(utilizador.partner_id.name) +
                                            u' não está associado a esta caixa.'))

    _constraints = [(_caixa_restrict, u'', ['user_id', 'caixa_id']),
                    (_check_ano, u'', ['name']),
                    (_diario_restrict, u'', ['diario_liq_id'])]

formulario_sncp_tesouraria_guia_cobrar_diario()