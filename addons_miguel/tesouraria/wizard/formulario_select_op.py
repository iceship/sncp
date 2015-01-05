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
import decimal
from decimal import *


class formulario_sncp_tesouraria_movim_fm(osv.Model):
    _name = 'formulario.sncp.tesouraria.movim.fm'
    _description = u"Formulário Movim FM"

    def wizard(self, cr, uid, ids, result):
        db_formulario_sncp_tesouraria_movim_fm_wizard = self.pool.get('formulario.sncp.tesouraria.movim.fm.wizard')
        """Method is used to show form view in new windows"""
        # Bloco de seleção das OP
        nid = self.create(cr, uid, {})
        for line in result:
                aux = decimal.Decimal(unicode(line[1]-line[2]-line[3]))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante = float(aux)

                db_formulario_sncp_tesouraria_movim_fm_wizard.create(cr, uid, {
                    'form_id': nid,
                    'movim_fm_id': ids[0],
                    'ordem_pag_id': line[0],
                    'name': line[4],
                    'montante': montante,
                    'selec': False,
                })
        return {
            'name': u'<div style="width:500px;">Seleciona as OP\'s pretendidas</div>',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.sncp.tesouraria.movim.fm',
            'nodestroy': True,
            'target': 'new',
            'res_id': nid, }

    def end(self, cr, uid, ids, context=None,):
        db_sncp_tesouraria_movim_fundos_maneio = self.pool.get('sncp.tesouraria.movim.fundos.maneio')
        cr.execute("""
            SELECT movim_fm_id FROM formulario_sncp_tesouraria_movim_fm_wizard
            WHERE selec = True AND form_id = %d
            LIMIT 1
        """ % ids[0])
        movim_fm_id = cr.fetchone()[0]

        cr.execute("""
            SELECT COALESCE (SUM(montante),0.0) FROM formulario_sncp_tesouraria_movim_fm_wizard
            WHERE selec = True AND form_id = %d
        """ % ids[0])
        montante = cr.fetchone()[0]
        if montante is None:
            raise osv.except_osv(_(u'Aviso'), _(u'Têm que seleccionar pelo menos uma OP.'))
        else:
            return db_sncp_tesouraria_movim_fundos_maneio.atualiza_montante(cr, uid, movim_fm_id,
                                                                            {'montante': montante})

    def descartar(self, cr, uid, ids, context):

        cr.execute("""
            DELETE FROM formulario_sncp_tesouraria_movim_fm_wizard
            WHERE form_id=%d
            """ % ids[0])

        # Apagar formulários
        self.unlink(cr, uid, ids)
        #

        return True

    _columns = {
        'op_ids': fields.one2many('formulario.sncp.tesouraria.movim.fm.wizard', 'form_id')
    }


class formulario_sncp_tesouraria_movim_fm_wizard(osv.Model):
    _name = 'formulario.sncp.tesouraria.movim.fm.wizard'
    _description = u"Formulário Movim FM Wizard"

    _columns = {
        'form_id': fields.many2one('formulario.sncp.tesouraria.movim.fm'),
        'movim_fm_id': fields.many2one('sncp.tesouraria.movim.fundos.maneio', u'Movimento FM'),
        'ordem_pag_id': fields.many2one('sncp.despesa.pagamentos.ordem', u'Ordem de Pagamento'),
        'name': fields.char(u'OP'),
        'data': fields.related('ordem_pag_id', 'paga', string=u'Paga em', store=True, type="char"),
        'partner_name': fields.related('ordem_pag_id', 'partner_id', 'name', string=u'Parceiro de Negócios', store=True,
                                       type="char"),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'selec': fields.boolean(u'Seleccionar'),
    }

    _order = 'name'

formulario_sncp_tesouraria_movim_fm_wizard()