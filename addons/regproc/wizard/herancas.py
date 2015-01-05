# -*- coding: utf-8 -*-
##############################################################################
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

from openerp.osv import osv
from openerp.tools.translate import _


class hr_employee(osv.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    # Chefes dos utilizadores
    # def get_manager_list_js(self, cr, uid):
    #     cr.execute("""SELECT id FROM hr_employee WHERE resource_id in(
    #                   SELECT id FROM resource_resource WHERE user_id = %d)""" % uid)
    #     emp_ids = cr.fetchall()
    #     hr_employee = self.browse(cr, uid, emp_ids[0])
    #     lista_users = []
    #     manager = hr_employee.parent_id or False
    #     while manager:
    #         if manager.resource_id.user_id.id:
    #             lista_users.append(manager.resource_id.user_id.id)
    #         obj_manager = self.browse(cr, uid, manager.id)
    #         manager = obj_manager.parent_id or False
    #
    #     return lista_users

    def recursive_child(self, lista_user, employee):
        if len(employee.child_ids) > 0:
            for child_employee in employee.child_ids:
                if child_employee.resource_id.user_id.id in lista_user:
                    raise osv.except_osv(_(u'Aviso'),
                                         _(u'A hierarquia da dependência dos empregados está em ciclo.'))
                lista_user.append(child_employee.resource_id.user_id.id)
                lista_user = self.recursive_child(lista_user, child_employee)
        return lista_user

    def get_child_ids_js(self, cr, uid):
        cr.execute("""SELECT id FROM hr_employee WHERE resource_id in(
                      SELECT id FROM resource_resource WHERE user_id = %d)""" % uid)
        emp_ids = cr.fetchone()
        lista_emp = list()
        lista_emp.append(emp_ids[0])
        employee = self.browse(cr, uid, emp_ids[0])
        lista_user = []
        lista_user = self.recursive_child(lista_user, employee)
        for employee in self.browse(cr, uid, lista_emp):
            lista_user.append(employee.resource_id.user_id.id)

        lista_user = list(set(lista_user))
        return lista_user

    _sql_constraints = [
        ('employee_resource_id_unique', 'unique (resource_id)', u'Um utilizador - um funcionário!'),

    ]

hr_employee()


class ir_attachment(osv.osv):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    def create(self, cr, uid, vals, context):
        if 'active_model' in context:
            vals['res_model'] = context['active_model']
            if 'active_id' in context:
                vals['res_id'] = context['active_id']
                db_model = self.pool.get(context['active_model'])
                obj = db_model.browse(cr, uid, context['active_id'])
                vals['res_name'] = obj.name or ''
        return super(ir_attachment, self).create(cr, uid, vals, context)

ir_attachment()