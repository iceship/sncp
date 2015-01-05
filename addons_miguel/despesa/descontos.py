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

import re
from openerp.osv import fields, osv
from openerp.tools.translate import _
import decimal
from decimal import *
# __________________________________________________________DESCONTOS RETENÇÕES___________________________________


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


class sncp_despesa_descontos_retencoes(osv.Model):
    _name = 'sncp.despesa.descontos.retencoes'
    _description = u"Descontos e Retenções"

    def on_change_codigo(self, cr, uid, ids, codigo):
        if len(ids) != 0:
            self.write(cr, uid, ids, {'codigo': codigo.upper()})
        return {'value': {'codigo': codigo.upper()}}

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'codigo'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['codigo']:
                name = record['codigo'] + ' ' + name
            res.append((record['id'], name))
        return res

    _columns = {
        'codigo': fields.char(u'Código', size=3),
        'name': fields.char(u'Descrição', size=30),
        'cod_contab_id': fields.many2one('sncp.comum.codigos.contab', u'Código de Contabilização',
                                         domain=[('natureza', 'in', ['ots'])],),
        # ----------------------------CAMPOS DE DEMONSTRAÇÃO--------------
        'ean': fields.related('cod_contab_id', 'ean13', type="char", string=u'EAN', store=True),
        'conta_code': fields.related('cod_contab_id', 'conta_id', 'code',
                                     type="char", string=u'Patrimonial', store=True),
        'conta_name': fields.related('cod_contab_id', 'conta_id', 'name', type="char", store=True),
        'organica_code': fields.related('cod_contab_id', 'organica_id', 'code', type="char", string=u'Orgânica',
                                        store=True),
        'organica_name': fields.related('cod_contab_id', 'organica_id', 'name', type="char", string=u'Orgânica',
                                        store=True),
        'economica_code': fields.related('cod_contab_id', 'economica_id', 'code', type="char", string=u'Económica',
                                         store=True),
        'economica_name': fields.related('cod_contab_id', 'economica_id', 'name', type="char", string=u'Económica',
                                         store=True),
        # -----------------------------FIM------------------------------
        'natureza': fields.selection([
                                    ('desc', u'Desconto'),
                                    ('rete', u'Retenção')], u'Natureza'),
        'perc': fields.float(u'Percentagem', digits=(3, 2)),
        'montante_min': fields.float(u'Montante mínimo', digits=(12, 2)),
        'montante_max': fields.float(u'Montante máximo', digits=(12, 2)),
        'montante_fix': fields.float(u'Montante fixo', digits=(12, 2)),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios',
                                      domain=[('supplier', '=', True)],),
        'opag_imediata': fields.boolean(u'Ordem de Pagamento Imediata'),
    }

    _order = 'codigo'

    _sql_constraints = [
        ('name_uniq', 'unique (codigo)',
            u'O codigo têm que ser único !'), ]

    def _codigo_limit(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        re_name = re.compile('^([A-Z0-9]){1,3}$')
        if re_name.match(obj.codigo):
            return True
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'O campo Código é composto por três maiúsculas ou algarismos'
                                                u' no máximo de 3 carateres.'))

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_despesa_descontos_retencoes_rel_grec
            WHERE ret_desc_id = %d
            """ % obj.id)

            res_ret_desc_rel = cr.fetchall()

            if len(res_ret_desc_rel) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o desconto/retenção ' +
                                                    obj.codigo + u' ' + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Ordens de Pagamento.'))
        return super(sncp_despesa_descontos_retencoes, self).unlink(cr, uid, ids)

    def create(self, cr, uid, vals, context=None):
        test_partner_id(self, cr, uid, vals['partner_id'])
        return super(sncp_despesa_descontos_retencoes, self).create(cr, uid, vals, context=None)

    _constraints = [
        (_codigo_limit, u'', ['codigo']),
    ]

sncp_despesa_descontos_retencoes()

# __________________________________________________________RELAÇÃO A GUIA DE RECEITA____________________________


class sncp_despesa_descontos_retencoes_rel_grec(osv.Model):
    _name = 'sncp.despesa.descontos.retencoes.rel.grec'
    _description = u"Ord. de Pag., Desc. e Ret. e Guia de Receita"

    def unique_ordem_desconto_rel(self, lista_ids, ret_desc_id):
        lista = []
        for lista_id in lista_ids:
            lista.append(lista_id[2]['ret_desc_id'])
        if ret_desc_id in lista:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Em cada ordem de pagamento um dado Desconto/Retenção não pode estar repetido.'))
        else:
            return True

    def on_change_ret_desc_id(self, cr, uid, ids, opag_id, ret_desc_id):
        montante = 0
        db_sncp_despesa_descontos_retencoes = self.pool.get('sncp.despesa.descontos.retencoes')
        db_sncp_despesa_pagamentos_ordem = self.pool.get('sncp.despesa.pagamentos.ordem')
        obj_desc = db_sncp_despesa_descontos_retencoes.browse(cr, uid, ret_desc_id)
        obj_ordem = db_sncp_despesa_pagamentos_ordem.browse(cr, uid, opag_id)
        cr.execute("""
                    SELECT ret_desc_id
                    FROM sncp_despesa_descontos_retencoes_rel_grec
                    WHERE opag_id=%d""" % opag_id)
        lista = cr.fetchall()
        for line in lista:
            if ret_desc_id == line[0]:
                raise osv.except_osv(_(u'Aviso'), _(u'Este Desconto/Retenção já existe.'))
        # Atribuição do DR fixo
        if obj_desc.montante_fix != 0:
            montante = obj_desc.montante_fix
            if montante > obj_ordem.montante_iliq:
                raise osv.except_osv(_(u'Aviso'), _(u'Desconto/Retenção não pode ser superior ao montante ilíquido.'))
        # Atribuição do montante DR %
        elif obj_desc.perc != 0:
            value = obj_ordem.montante_iliq * obj_desc.perc / 100
            if value < obj_desc.montante_min and obj_desc.montante_min:
                montante = 0
            elif (obj_desc.montante_min <= value <= obj_desc.montante_max and
                  obj_desc.montante_min != 0 and
                  obj_desc.montante_max != 0) or \
                 (obj_desc.montante_min == 0 and value <= obj_desc.montante_max) or \
                 (obj_desc.montante_max == 0 and value >= obj_desc.montante_min):
                montante = value
            elif value > obj_desc.montante_max and obj_desc.montante_max:
                montante = obj_desc.montante_max
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'O Desconto/Retenção escolhido está mal definido.'))
        # Se o montante DR esta nos limites
        if obj_ordem.montante_iliq < obj_ordem.montante_desc + obj_ordem.montante_ret + montante:
            montante = montante - (obj_ordem.montante_desc + obj_ordem.montante_ret - obj_ordem.montante_iliq)
            if obj_desc.natureza == 'desc':
                montante_desc = obj_ordem.montante_desc+montante
                aux = decimal.Decimal(unicode(montante_desc))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante_desc = float(aux)
                db_sncp_despesa_pagamentos_ordem.write(cr, uid, opag_id, {'montante_desc': montante_desc})
            else:
                montante_ret = obj_ordem.montante_ret+montante
                aux = decimal.Decimal(unicode(montante_ret))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante_ret = float(aux)

                db_sncp_despesa_pagamentos_ordem.write(cr, uid, opag_id, {'montante_ret': montante_ret})

            aux = decimal.Decimal(unicode(montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante = float(aux)
            if len(ids) != 0:
                self.write(cr, uid, ids, {'montante': montante})
            return {'value': {'montante': montante},
                    'warning': {'title': u'Limite de Descontos/Retenções',
                                'message': u'Chegou ao limite dos Descontos/Retenções.'}}

        if obj_desc.natureza == 'desc':
            aux = decimal.Decimal(unicode(obj_ordem.montante_desc+montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_desc = float(aux)
            db_sncp_despesa_pagamentos_ordem.write(cr, uid, opag_id,
                                                   {'montante_desc': montante_desc})
        else:
            aux = decimal.Decimal(unicode(obj_ordem.montante_ret+montante))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_ret = float(aux)
            db_sncp_despesa_pagamentos_ordem.write(cr, uid, opag_id,
                                                   {'montante_ret': montante_ret})
        if len(ids) != 0:
            self.write(cr, uid, ids, {'montante': montante})
        return {'value': {'montante': montante}}

    def on_change_ret_desc_montante(self, cr, uid, ids, opag_id, ret_desc_id, montante):
        db_sncp_despesa_descontos_retencoes = self.pool.get('sncp.despesa.descontos.retencoes')
        db_sncp_despesa_pagamentos_ordem = self.pool.get('sncp.despesa.pagamentos.ordem')
        if len(ids) == 0:
            return {}

        obj = self.browse(cr, uid, ids[0])
        obj_op = db_sncp_despesa_pagamentos_ordem.browse(cr, uid, opag_id)
        obj_dr = db_sncp_despesa_descontos_retencoes.browse(cr, uid, ret_desc_id)

        resultado = montante - obj.montante
        # Atualizar OrPag
        if obj_dr.natureza == 'desc':
            aux = decimal.Decimal(unicode(obj_op.montante_desc+resultado))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_desc = float(aux)
            db_sncp_despesa_pagamentos_ordem.write(cr, uid, opag_id,
                                                   {'montante_desc': montante_desc})

        else:
            aux = decimal.Decimal(unicode(obj_op.montante_ret+resultado))
            aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
            montante_ret = float(aux)
            db_sncp_despesa_pagamentos_ordem.write(cr, uid, opag_id,
                                                   {'montante_ret': montante_ret})

        return {'value': {'montante': montante}}

    _columns = {
        'opag_id': fields.many2one('sncp.despesa.pagamentos.ordem', u'Ordem de pagamento'),
        'ret_desc_id': fields.many2one('sncp.despesa.descontos.retencoes', u'Desconto/Retenção'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'guia_rec_id': fields.many2one('sncp.receita.guia.rec', u'Guia de Recebimento'),
    }

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_despesa_pagamentos_ordem = self.pool.get('sncp.despesa.pagamentos.ordem')
        for obj_rel in self.browse(cr, uid, ids):
            if obj_rel.ret_desc_id.natureza == 'desc':
                aux = decimal.Decimal(unicode(obj_rel.opag_id.montante_desc-obj_rel.montante))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante_dif_desc = float(aux)
                db_sncp_despesa_pagamentos_ordem.write(cr, uid,
                                                       obj_rel.opag_id.id, {'montante_desc': montante_dif_desc})
            else:
                aux = decimal.Decimal(unicode(obj_rel.opag_id.montante_ret-obj_rel.montante))
                aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
                montante_dif_ret = float(aux)

                db_sncp_despesa_pagamentos_ordem.write(cr, uid, obj_rel.opag_id.id, {'montante_ret': montante_dif_ret})

        return super(sncp_despesa_descontos_retencoes_rel_grec, self).unlink(cr, uid, ids)

    def montantes_validos(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        rel_grec_ids = self.search(cr, uid, [('opag_id', '=', obj.opag_id.id)])
        total = 0
        for obj_rel_grec in self.browse(cr, uid, rel_grec_ids):
            total += obj_rel_grec.montante

        aux = decimal.Decimal(unicode(total))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        total = float(aux)

        if total > obj.opag_id.montante_iliq:
            raise osv.except_osv(_(u'Aviso'), _(u'A soma dos montantes dos Descontos/Retenções não pode ultrapassar'
                                                u' o montante ilíquido.'))
        return True

    _constraints = [
        (montantes_validos, u'', ['montante'])]

    _sql_constraints = [
        ('opag_desc_uniq', 'unique (opag_id, ret_desc_id)',
            u'Em cada ordem de pagamento um dado Desconto/Retenção não pode estar repetido '),
    ]

sncp_despesa_descontos_retencoes_rel_grec()

# __________________________________________________________RELAÇÃO A ORDEM DE PAGAMENTO_________________________


class sncp_despesa_descontos_retencoes_rel_opag(osv.Model):
    _name = 'sncp.despesa.descontos.retencoes.rel.opag'
    _description = u"Relação entre Ordem de Pagamento e Ordem de Pagamento OT"

    _columns = {
        'opag_id': fields.many2one('sncp.despesa.pagamentos.ordem', u'Ordem de pagamento'),
        'opag_tes_id': fields.many2one('sncp.despesa.pagamentos.ordem', u'Ordem de pagamento OT'),
    }

sncp_despesa_descontos_retencoes_rel_opag()