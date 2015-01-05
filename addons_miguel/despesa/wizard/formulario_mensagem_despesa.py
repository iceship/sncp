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


class formulario_mensagem_despesa(osv.Model):
    _name = 'formulario.mensagem.despesa'
    _description = u"Mensagem Despesa"

    def wizard(self, cr, uid, ids, text):
        """Method is used to show form view in new windows"""
        nid = self.create(cr, uid, {'name': text})
        return {
            'name': u'<div style="width:500px;">Aviso</div>',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.mensagem.despesa',
            'nodestroy': True,
            'target': 'new',
            'res_id': nid, }

    def end(self, cr, uid, ids, context=None):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    _columns = {
        'name': fields.char(u''), }

formulario_mensagem_despesa()