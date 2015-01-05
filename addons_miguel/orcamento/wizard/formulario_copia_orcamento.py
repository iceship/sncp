# -*- encoding: utf-8 -*-
# #############################################################################
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


class formulario_sncp_orcamento_copia(osv.Model):
    _name = 'formulario.sncp.orcamento.copia'
    _description = u"Formulário de Cópia do Orçamento"

    send = {}

    def wizard(self, cr, uid, ids, context=None):
        """Method is used to show form view in new windows"""

        db_sncp_orcamento = self.pool.get('sncp.orcamento')

        obj = db_sncp_orcamento.browse(cr, uid, ids[0])

        vals = {'name': obj.tipo_orc, 'ano_origem': obj.ano - 1, 'orc_destino_id': obj.id,
                'ano_destino': obj.ano, 'substitui_valor': True, 'fator': 1.0}

        copia_id = self.create(cr, uid, vals)

        return {
            'name': '<div style="width:500px;">Parâmetros de cópia do orçamento</div>',
            'id': 'dontcare',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': copia_id,
            'res_model': 'formulario.sncp.orcamento.copia',
            'nodestroy': True,
            'target': 'new',
        }

    def end(self, cr, uid, ids, context=None):
        db_sncp_orcamento = self.pool.get('sncp.orcamento')
        obj = self.browse(cr, uid, ids[0])
        obj_orc = db_sncp_orcamento.browse(cr, uid, obj.orc_destino_id)
        orc_origem = None
        if obj.name == u'orc':
            cr.execute("""SELECT id FROM sncp_orcamento WHERE ano=%d AND titulo='%s' AND tipo_orc='%s'
                       """ % (obj.ano_origem, obj_orc.titulo, obj.name))
            orc_origem = cr.fetchone()

        elif obj.name in ['rev', 'alt']:
            cr.execute("""
            SELECT id
            FROM sncp_orcamento
            WHERE ano=%d AND titulo='%s' AND tipo_orc='%s' AND tipo_mod='%s' AND numero=%d
            """ % (obj.ano_origem, obj_orc.titulo, obj.name, obj.tipo_mod, obj.numero))
            orc_origem = cr.fetchone()

        if orc_origem is None:
            self.unlink(cr, uid, ids)
            return True
        else:
            self.send['orc_origem_id'] = orc_origem[0]
            self.send['orc_destino_id'] = obj.orc_destino_id
            self.send['titulo'] = obj_orc.titulo
            self.send['fator'] = obj.fator
            self.send['ad_val'] = obj.adiciona_valor
            self.send['sub_val'] = obj.substitui_valor

        # Apagar formulários
        self.unlink(cr, uid, ids)

        return self.pool.get('sncp.orcamento').copia(cr, uid, ids, self.send)

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        return True

    _columns = {
        'name': fields.char(u'Tipo de orçamento'),
        'ano_origem': fields.integer(u'Ano', size=4),
        'ano_destino': fields.integer(u''),
        'orc_destino_id': fields.integer(u''),
        'numero': fields.integer(u'Número'),
        'tipo_mod': fields.selection([('rev', u'Revisão'),
                                      ('alt', u'Alteração')], u'Tipo de Modificação'),
        'fator': fields.float(u'Fator', digits=(1, 2)),
        'adiciona_valor': fields.boolean(u'Adiciona Montante'),
        'substitui_valor': fields.boolean(u'Substitui Montante'),
    }

    def _escolha_opcao(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.adiciona_valor is False and obj.substitui_valor is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Escolha uma opção.'))

        if obj.adiciona_valor is True and obj.substitui_valor is True:
            raise osv.except_osv(_(u'Aviso'), _(u'Apenas pode escolher uma opção.'))

        return True

    def _ano_origem_valido(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.name == 'orc':
            if obj.ano_origem >= obj.ano_destino:
                raise osv.except_osv(_(u'Aviso'), _(u'Ano de origem deve ser inferior ao ano destino.'))
        elif obj.name in ['rev', 'alt']:
            if obj.ano_origem > obj.ano_destino:
                raise osv.except_osv(_(u'Aviso'), _(u'Ano de origem deve ser inferior ao ano destino.'))
        return True

    def _fator_valido(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.fator <= 0.0:
            raise osv.except_osv(_(u'Aviso'), _(u'Fator deve ser positivo.'))
        return True

    _constraints = [
        (_escolha_opcao, u'', ['adiciona_valor', 'substitui_valor']),
        (_ano_origem_valido, u'', ['ano_origem', 'ano_destino']),
        (_fator_valido, u'', ['fator'])
    ]


formulario_sncp_orcamento_copia()
