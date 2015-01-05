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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _
# _____________________________________________PROCEDIMENTOS______________________________________


class sncp_despesa_procedimentos(osv.Model):
    _name = 'sncp.despesa.procedimentos'
    _description = u"Procedimentos"
    _rec_name = 'codigo_120'

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso_dados_adic
            WHERE procedimento_id = %d
            """ % obj.id)

            res_dados = cr.fetchall()

            if len(res_dados) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o procedimento ' +
                                                    unicode(obj.codigo_120)
                                                    + u' têm associação em:\n'
                                                    u'1. Compromissos.'))

        return super(sncp_despesa_procedimentos, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'name': fields.text(u'Descrição', size=255),
        'codigo_120': fields.integer(u'Código', size=10),
    }
    _order = 'codigo_120'

    _sql_constraints = [
        ('codigo_procedimentos_unique', 'unique (codigo_120)', u'Este código já existe'),
    ]

sncp_despesa_procedimentos()
# _____________________________________________FUNDAMENTOS______________________________________


class sncp_despesa_fundamentos(osv.Model):
    _name = 'sncp.despesa.fundamentos'
    _description = u"Fundamentos"
    _rec_name = 'codigo_120'

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso_dados_adic
            WHERE fundamento_id = %d
            """ % obj.id)

            res_dados = cr.fetchall()

            if len(res_dados) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o fundamento ' +
                                                    unicode(obj.codigo_120)
                                                    + u' têm associação em:\n'
                                                    u'1. Compromissos.'))

        return super(sncp_despesa_fundamentos, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'name': fields.text(u'Norma legal', size=255),
        'codigo_120': fields.char(u'Fundamento', size=9),
    }
    _order = 'codigo_120'

    _sql_constraints = [
        ('codigo_fundamentos_unique', 'unique (codigo_120)', u'Este código já existe'),
    ]

sncp_despesa_fundamentos()
# _____________________________________________NATUREZAS______________________________________


class sncp_despesa_naturezas(osv.Model):
    _name = 'sncp.despesa.naturezas'
    _description = u"Naturezas"
    _rec_name = 'codigo_120'

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_despesa_compromisso_dados_adic
            WHERE natureza_id = %d
            """ % obj.id)

            res_dados = cr.fetchall()

            if len(res_dados) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a natureza ' +
                                                    unicode(obj.codigo_120)
                                                    + u' têm associação em:\n'
                                                    u'1. Compromissos.'))

        return super(sncp_despesa_naturezas, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'name': fields.char(u'Descrição', size=255),
        'codigo_120': fields.char(u'Natureza', size=4),
        'empreitada': fields.boolean(u'Empreitada'),
    }
    _order = 'codigo_120'

    _sql_constraints = [
        ('codigo_natureza_unique', 'unique (codigo_120)', u'Este código já existe'),
    ]

sncp_despesa_naturezas()

# _____________________________________________APROVADORES______________________________________


class sncp_despesa_aprovadores(osv.Model):
    _name = 'sncp.despesa.aprovadores'
    _description = u"Aprovadores"

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name'], context=context)
        res = []
        for record in reads:
            result = u'Aprovações'
            res.append((record['id'], result))
        return res

    def on_change_requisicoes(self, cr, uid, ids, requisicao):
        if requisicao is True:
            limite_req = 999999999999.99
        else:
            limite_req = 0.0

        if len(ids) != 0:
            self.write(cr, uid, ids, {'requisicoes': requisicao, 'limite_req': limite_req})

        return {'value': {'requisicoes': requisicao, 'limite_req': limite_req}}

    def on_change_compras(self, cr, uid, ids, compras):
        if compras is True:
            limite_comp = 999999999999.99
        else:
            limite_comp = 0.0

        if len(ids) != 0:
            self.write(cr, uid, ids, {'compras': compras, 'limite_comp': limite_comp})

        return {'value': {'compras': compras, 'limite_comp': limite_comp}}

    def on_change_faturas(self, cr, uid, ids, faturas):
        if faturas is True:
            limite_fat = 999999999999.99
        else:
            limite_fat = 0.0

        if len(ids) != 0:
            self.write(cr, uid, ids, {'faturas': faturas, 'limite_fat': limite_fat})

        return {'value': {'faturas': faturas, 'limite_fat': limite_fat}}

    def on_change_pagamentos(self, cr, uid, ids, pagamentos):
        if pagamentos is True:
            limite_pagam = 999999999999.99
        else:
            limite_pagam = 0.0

        if len(ids) != 0:
            self.write(cr, uid, ids, {'pagamentos': pagamentos, 'limite_pagam': limite_pagam})

        return {'value': {'pagamentos': pagamentos, 'limite_pagam': limite_pagam}}

    def on_change_aprovador(self, cr, uid, ids, aprovador_id):
        db_hr_employee = self.pool.get('hr.employee')
        empregado = db_hr_employee.browse(cr, uid, aprovador_id)

        if empregado.resource_id.user_id.id is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Associe um utilizador ao empregado '
                                                + unicode(empregado.name_related)+u'.'))

        if len(ids) != 0:
            self.write(cr, uid, ids, {'user_id': empregado.resource_id.user_id.id})

        return {'value': {'user_id': empregado.resource_id.user_id.id}}

    def valido(self, cr, uid, ids, context, vals):
        lista_aprovadores_id = self.search(cr, uid, [('user_id', '=', uid),
                                                     ('departamento_id', '=', vals['departamento_id'])])

        db_hr_department = self.pool.get('hr.department')
        departamento = db_hr_department.browse(cr, uid, vals['departamento_id'])
        texto = None
        limite = None
        mensagem = None
        if len(lista_aprovadores_id) == 1:
            obj = self.browse(cr, uid, lista_aprovadores_id[0])

            data_inicial = datetime.strptime(obj.name, "%Y-%m-%d %H:%M:%S")
            data_final = datetime.strptime(obj.fim, "%Y-%m-%d %H:%M:%S")

            if vals['documento'] == 1:
                texto = u'Requisição'
                limite = obj.limite_req
            elif vals['documento'] == 2:
                texto = u'Ordem de Compra'
                limite = obj.limite_comp
            elif vals['documento'] == 3:
                texto = u'Fatura'
                limite = obj.limite_fat
            elif vals['documento'] == 4:
                texto = u'Ordem de Pagamento'
                limite = obj.limite_pagam

            if texto == u'Requisição' and obj.requisicoes is False:
                mensagem = u'Não tem permissão para autorizar ' + texto + \
                           u' do departamento ' + departamento.name

            elif texto == u'Ordem de Compra' and obj.compras is False:
                mensagem = u'Não tem permissão para autorizar ' + texto + \
                           u' do departamento ' + departamento.name

            elif texto == u'Fatura' and obj.faturas is False:
                mensagem = u'Não tem permissão para autorizar ' + texto + \
                           u' do departamento ' + departamento.name

            elif texto == u'Ordem de Pagamento' and obj.pagamentos is False:
                mensagem = u'Não tem permissão para autorizar ' + texto + \
                           u' do departamento ' + departamento.name

            if vals['datahora'] > data_final:
                mensagem = u'As suas permissões para o departamento ' + departamento.name + u' expiraram em '\
                           + unicode(data_final.date())

            elif vals['datahora'] < data_inicial:
                mensagem = u'Só terá permissão para autorizar ' + texto + u' do departamento ' + \
                           departamento.name + u' a partir de ' + unicode(data_inicial.date())

            if vals['montante'] > limite:
                mensagem = u'Só lhe é permitido autorizar ' + texto + u' até ao montante de ' + \
                           unicode(limite)

        if mensagem is not None:
            return [False, mensagem]
        else:
            return [True, mensagem]

    _columns = {
        'aprovador_id': fields.many2one('hr.employee', u'Nome'),
        'departamento_id': fields.many2one('hr.department', u'Departamento'),
        'user_id': fields.many2one('res.users', u'Utilizador'),
        'name': fields.datetime(u'Desde'),
        'fim': fields.datetime(u'Até'),
        'requisicoes': fields.boolean(u'Requisições'),
        'compras': fields.boolean(u'Ordens de compra'),
        'faturas': fields.boolean(u'Faturas'),
        'pagamentos': fields.boolean(u'Ordens de Pagamento'),
        'limite_req': fields.float(u'Limite para as Requisições', digits=(12, 2)),
        'limite_comp': fields.float(u'Limite Ordens de Compra', digits=(12, 2)),
        'limite_fat': fields.float(u'Limite para as Faturas', digits=(12, 2)),
        'limite_pagam': fields.float(u'Limite Ordens Pagamento', digits=(12, 2)),
        'estado': fields.integer(u''),
    }

    _order = 'aprovador_id,departamento_id'

    _defaults = {
        'name': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                        datetime.now().hour, datetime.now().minute, datetime.now().second)),
        'fim': unicode(datetime(datetime.now().year+20, datetime.now().month, datetime.now().day,
                       datetime.now().hour, datetime.now().minute, datetime.now().second)),
        'limite_req': 0.0,
        'limite_comp': 0.0,
        'limite_fat': 0.0,
        'limite_pagam': 0.0,
    }

    def create(self, cr, uid, vals, context=None):
        if 'aprovador_id' in vals and 'user_id' not in vals:
            db_hr_employee = self.pool.get('hr.employee')
            empregado = db_hr_employee.browse(cr, uid, vals['aprovador_id'])
            vals['user_id'] = empregado.resource_id.user_id.id
        return super(sncp_despesa_aprovadores, self).create(cr, uid, vals, context=context)

    def _datas_restrict(self, cr, uid, ids):
        record = self.browse(cr, uid, ids[0])
        if record.name >= record.fim:
            raise osv.except_osv(_(u'Aviso'), _(u' A data inicial deve ser inferior à data final.'))
        return True

    def _montante_positivo(self, cr, uid, ids):
        record = self.browse(cr, uid, ids[0])
        if record.limite_req <= 0.0 and record.requisicoes is True:
            raise osv.except_osv(_(u'Aviso'), _(u'O limite para as requisições têm de ser positivo.'))

        elif record.limite_comp <= 0.0 and record.compras is True:
            raise osv.except_osv(_(u'Aviso'), _(u'O limite para as ordens de compra têm de ser positivo.'))

        if record.limite_fat <= 0.0 and record.faturas is True:
            raise osv.except_osv(_(u'AViso'), _(u'O limite para as faturas têm de ser positivo.'))

        if record.limite_pagam <= 0.0 and record.pagamentos is True:
            raise osv.except_osv(_(u'Aviso'), _(u'O limite para as ordens de pagamento têm de ser positivo.'))

        return True

    _constraints = [
        (_datas_restrict, u'', ['name', 'fim']),
        (_montante_positivo, u'', ['limite_req', 'limite_comp', 'limite_fat', 'limite_pagam']),
    ]

    _sql_constraints = [
        ('aprovador_departamento_unique', 'unique (aprovador_id,departamento_id)',
         u'Duplicação de aprovador e departamento!'), ]

sncp_despesa_aprovadores()