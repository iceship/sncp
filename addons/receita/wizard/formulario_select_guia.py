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


class formulario_sncp_receita_select_guia(osv.Model):
    _name = 'formulario.sncp.receita.select.guia'
    _description = u"Seleção de Guias"

    def wizard(self, cr, uid, ids, vals):
        """Method is used to show form view in new windows"""
        nid = self.create(cr, uid, {'controlo': ids[0]})
        if vals['action'] == 'activar':
            self.write(cr, uid, nid, {'name': 1})
        if vals['action'] == 'renovar':
            self.write(cr, uid, nid, {'name': 2})
        # Bloco de pre-seleção das Guias
        cr.execute("""SELECT id  FROM sncp_receita_guia_rec
                      WHERE state = 'rec' AND partner_id = %d AND
                            id IN (SELECT guia_rec_id FROM sncp_receita_guia_rec_linhas
                                   WHERE cod_contab_id = %d) AND
                            id NOT IN (SELECT guia_id FROM sncp_receita_controlo_guias
                                       WHERE controlo_id = %d)
                    """ % (vals['partner_id'], vals['cod_contab_id'], ids[0]))
        result = cr.fetchall()
        for res in result:
            self.pool.get('formulario.sncp.receita.select.guia.linhas').create(cr, uid, {
                'form_id': nid,
                'guia_id': res[0]})
        if len(result) == 0:
            self.write(cr, uid, nid, {'notas': u'Não existe nenhuma Guia.'})
        else:
            self.write(cr, uid, nid, {'notas': u'Selecione somente uma Guia.'})
        return {
            'name': u'<div style="width:500px;">Formulário</div>',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.sncp.receita.select.guia',
            'nodestroy': True,
            'target': 'new',
            'res_id': nid, }

    def end(self, cr, uid, ids, context=None,):
        obj = self.browse(cr, uid, ids[0])
        controlo_ids = [obj.controlo]

        cr.execute("""SELECT guia_id FROM formulario_sncp_receita_select_guia_linhas
                      WHERE form_id = %d AND name = TRUE""" % ids[0])
        result = cr.fetchall()
        if len(result) > 1:
            raise osv.except_osv(_(u'Aviso'), _(u'Selecione apenas uma guia.'))

        if len(result) != 0:
            vals = {'guia_id': result[0][0]}
            if obj.name == 1:
                # Apagar formulários e linhas
                cr.execute("""
                DELETE FROM formulario_sncp_receita_select_guia_linhas
                WHERE form_id=%d
                """ % ids[0])
                self.unlink(cr, uid, ids)
                #
                return self.pool.get('sncp.receita.controlo').activar_termo(cr, uid, controlo_ids, context, vals)
            if obj.name == 2:
                vals['data_reinicio'] = obj.data_reinicio
                vals['data_despacho'] = obj.data_despacho
                # Apagar formulários e linhas
                cr.execute("""
                DELETE FROM formulario_sncp_receita_select_guia_linhas
                WHERE form_id=%d
                """ % ids[0])
                self.unlink(cr, uid, ids)
                #
                return self.pool.get('sncp.receita.controlo').renovar_termo(cr, uid, controlo_ids, context, vals)
        return True

    def descartar(self, cr, uid, ids, context=None):
        # Apagar formulários
        cr.execute("""
        DELETE FROM formulario_sncp_receita_select_guia_linhas
        WHERE form_id=%d
        """ % ids[0])

        self.unlink(cr, uid, ids)
        #
        return True

    _columns = {
        'name': fields.integer(u'1 -- activar, 2 -- renovar'),
        'controlo': fields.integer(u''),
        'guias_ids': fields.one2many('formulario.sncp.receita.select.guia.linhas', 'form_id'),
        'notas': fields.text(u''),
        'data_reinicio': fields.datetime(u'Data de reinício'),
        'data_despacho': fields.datetime(u'Data de Despacho'), }

formulario_sncp_receita_select_guia()


class formulario_sncp_receita_select_guia_linhas(osv.Model):
    _name = 'formulario.sncp.receita.select.guia.linhas'
    _description = u"Linhas de Seleção de Guias"

    _columns = {
        'form_id': fields.many2one('formulario.sncp.receita.select.guia'),
        'guia_id': fields.many2one('sncp.receita.guia.rec', u'Guia de receita'),
        'data': fields.related('guia_id', 'data_emissao', string=u'Emitida', store=True, type="char"),
        'montante': fields.related('guia_id', 'montante', string=u'Montante', store=True, type="float"),
        'name': fields.boolean(u'Seleccionar'),
    }
    _order = 'name'

formulario_sncp_receita_select_guia()