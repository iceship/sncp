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
from openerp.tools.translate import _


class formulario_tesouraria_series(osv.Model):
    _name = 'formulario.tesouraria.series'
    _description = u"Formulário Séries"

    send = {}

    def wizard(self, cr, uid, ids, context):
        self.send['banco_id'] = ids
        return {
            'name': u'<div style="width:500px;">Parâmetros de criação de séries</div>',
            'id': 'ccc',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.tesouraria.series',
            'nodestroy': True,
            'target': 'new', }

    def criar_serie(self, cr, uid, ids, context):
        record = self.browse(cr, uid, ids[0])
        db_sncp_tesouraria_series = self.pool.get('sncp.tesouraria.series')

        series_id = db_sncp_tesouraria_series.search(cr, uid, [('name', '=', record.nome_serie),
                                                               ('banco_id', '=', self.send['banco_id'][0])])

        if len(series_id) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A série já existe.'))

        if record.nome_serie.isalnum() is False:
            raise osv.except_osv(_(u'Aviso'), _(u'O nome da série contêm carateres não alfanuméricos.'))
        db_sncp_tesouraria_series.create(cr, uid, {'name': record.nome_serie, 'banco_id': self.send['banco_id'][0]})
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    _columns = {
        'nome_serie': fields.char(u'Nome da série', size=5), }

formulario_tesouraria_series()