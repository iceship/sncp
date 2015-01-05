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


class formulario_mensagem_tesouraria(osv.Model):
    _name = 'formulario.mensagem.tesouraria'
    _description = u"Mensagem Tesouraria"

    send = {}

    def wizard(self, cr, uid, ids, text):
        """Method is used to show form view in new windows"""
        nid = self.create(cr, uid, {'name': text})

        self.send['opag_id'] = ids

        return {
            'name': u'<div style="width:500px;">Aviso</div>',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.mensagem.tesouraria',
            'nodestroy': True,
            'target': 'new',
            'res_id': nid, }

    def sim(self, cr, uid, ids, context=None):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return self.pool.get('sncp.despesa.pagamentos.ordem').anular_pagar(cr, uid, self.send['opag_id'])

    def nao(self, cr, uid, ids, context=None):
        self.unlink(cr, uid, ids)
        return True

    _columns = {
        'name': fields.char(u''), }

formulario_mensagem_tesouraria()