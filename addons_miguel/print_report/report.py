# -*- encoding: utf-8 -*-
# #############################################################################
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

import time
from openerp.report import report_sxw


"""                                                     Modelo
class print__report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print__report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {'time': time,})

report_sxw.report_sxw('report.sncp__report', 'sncp_',
                      'print_report/sncp_.jrxml',
                      parser=print__report)
"""


# ==================================================  ADDONS ========================================
class print_account_analytic_account_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_account_analytic_account_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.account_analytic_account_report', 'account_analytic_account',
                      'print_report/account_analytic_account.jrxml',
                      parser=print_account_analytic_account_report)


class print_account_invoice_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_account_invoice_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.account_invoice_report', 'account_invoice',
                      'print_report/account_invoice.jrxml',
                      parser=print_account_invoice_report)


class print_account_invoice_line_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_account_invoice_line_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.account_invoice_line_report', 'account_invoice_line',
                      'print_report/account_invoice_line.jrxml',
                      parser=print_account_invoice_line_report)


# ==================================================  COMUM  =========================================
class print_comum_calendario_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_comum_calendario_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_comum_calendario_report', 'sncp_comum_calendario',
                      'print_report/sncp_comum_calendario.jrxml',
                      parser=print_comum_calendario_report)


class print_comum_cond_pagam_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_comum_cond_pagam_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_comum_cond_pagam_report', 'sncp_comum_cond_pagam',
                      'print_report/sncp_comum_cond_pagam.jrxml',
                      parser=print_comum_cond_pagam_report)


class print_comum_cpv_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_comum_cpv_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_comum_cpv_report', 'sncp_comum_cpv',
                      'print_report/sncp_comum_cpv.jrxml',
                      parser=print_comum_cpv_report)


class print_comum_meios_pagamento_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_comum_meios_pagamento_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_comum_meios_pagamento_report', 'sncp_comum_meios_pagamento',
                      'print_report/sncp_comum_meios_pagamento.jrxml',
                      parser=print_comum_meios_pagamento_report)


# ==================================================  ORCAMENTO  =========================================
class print_orcamento_despesa_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_orcamento_despesa_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_orcamento_despesa_report', 'sncp_orcamento_despesa',
                      'print_report/sncp_orcamento_despesa.jrxml',
                      parser=print_orcamento_despesa_report)


class print_orcamento_receita_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_orcamento_receita_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_orcamento_receita_report', 'sncp_orcamento_receita',
                      'print_report/sncp_orcamento_receita.jrxml',
                      parser=print_orcamento_receita_report)


class print_orcamento_resumo_config_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_orcamento_resumo_config_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_orcamento_resumo_config_report', 'sncp_orcamento_resumo_config',
                      'print_report/sncp_orcamento_resumo_config.jrxml',
                      parser=print_orcamento_resumo_config_report)


class print_modificacao_receita_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_modificacao_receita_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_modificacao_receita_report', 'sncp_modificacao_imprimir_receita',
                      'print_report/sncp_modificacao_receita.jrxml',
                      parser=print_modificacao_receita_report)


class print_modificacao_despesa_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_modificacao_despesa_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_modificacao_despesa_report', 'sncp_modificacao_imprimir_despesa',
                      'print_report/sncp_modificacao_despesa.jrxml',
                      parser=print_modificacao_despesa_report)


class print_orcamento_historico_receita_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_orcamento_historico_receita_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_orcamento_historico_cabecalho_receita_report', 'sncp_orcamento_historico_cabecalho',
                      'print_report/sncp_orcamento_historico_receita.jrxml',
                      parser=print_orcamento_historico_receita_report)


class print_orcamento_historico_despesa_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_orcamento_historico_despesa_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_orcamento_historico_cabecalho_despesa_report', 'sncp_orcamento_historico_cabecalho',
                      'print_report/sncp_orcamento_historico_despesa.jrxml',
                      parser=print_orcamento_historico_despesa_report)


class print_orcamento_acumulados_receita_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_orcamento_acumulados_receita_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_orcamento_acumulados_cabecalho_receita_report',
                      'sncp_orcamento_acumulados_cabecalho',
                      'print_report/sncp_orcamento_acumulados_receita.jrxml',
                      parser=print_orcamento_acumulados_receita_report)


class print_orcamento_acumulados_despesa_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_orcamento_acumulados_despesa_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_orcamento_acumulados_cabecalho_despesa_report',
                      'sncp_orcamento_acumulados_cabecalho',
                      'print_report/sncp_orcamento_acumulados_despesa.jrxml',
                      parser=print_orcamento_acumulados_despesa_report)


class print_orcamento_ppi_imprimir_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_orcamento_ppi_imprimir_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_orcamento_ppi_imprimir_report', 'sncp_orcamento_ppi_imprimir',
                      'print_report/sncp_orcamento_ppi_imprimir.jrxml',
                      parser=print_orcamento_ppi_imprimir_report)


class print_comum_codigos_contab_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_comum_codigos_contab_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_comum_codigos_contab_report', 'sncp_comum_codigos_contab',
                      'print_report/sncp_comum_codigos_contab.jrxml',
                      parser=print_comum_codigos_contab_report)


# ==================================================  DESPESA  =========================================
class print_despesa_cabimento_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_despesa_cabimento_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_despesa_cabimento_report', 'sncp_despesa_cabimento',
                      'print_report/sncp_despesa_cabimento.jrxml',
                      parser=print_despesa_cabimento_report)


class print_despesa_cofinanciamentos_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_despesa_cofinanciamentos_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_despesa_cofinanciamentos_report', 'sncp_despesa_cofinanciamentos',
                      'print_report/sncp_despesa_cofinanciamentos.jrxml',
                      parser=print_despesa_cofinanciamentos_report)


class print_despesa_compromisso_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_despesa_compromisso_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_despesa_compromisso_report', 'sncp_despesa_compromisso',
                      'print_report/sncp_despesa_compromisso.jrxml',
                      parser=print_despesa_compromisso_report)


class print_despesa_fundamentos_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_despesa_fundamentos_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_despesa_fundamentos_report', 'sncp_despesa_fundamentos',
                      'print_report/sncp_despesa_fundamentos.jrxml',
                      parser=print_despesa_fundamentos_report)


class print_despesa_naturezas_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_despesa_naturezas_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_despesa_naturezas_report', 'sncp_despesa_naturezas',
                      'print_report/sncp_despesa_naturezas.jrxml',
                      parser=print_despesa_naturezas_report)


class print_despesa_pagamentos_ordem_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_despesa_pagamentos_ordem_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_despesa_pagamentos_ordem_report', 'sncp_despesa_pagamentos_ordem',
                      'print_report/sncp_despesa_pagamentos_ordem.jrxml',
                      parser=print_despesa_pagamentos_ordem_report)


class print_despesa_pagamentos_reposicoes_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_despesa_pagamentos_reposicoes_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_despesa_pagamentos_reposicoes_report', 'sncp_despesa_pagamentos_reposicoes',
                      'print_report/sncp_despesa_pagamentos_reposicoes.jrxml',
                      parser=print_despesa_pagamentos_reposicoes_report)


class print_despesa_procedimentos_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_despesa_procedimentos_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_despesa_procedimentos_report', 'sncp_despesa_procedimentos',
                      'print_report/sncp_despesa_procedimentos.jrxml',
                      parser=print_despesa_procedimentos_report)


class print_despesa_requisicoes_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_despesa_requisicoes_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_despesa_requisicoes_report', 'sncp_despesa_requisicoes',
                      'print_report/sncp_despesa_requisicoes.jrxml',
                      parser=print_despesa_requisicoes_report)


# ==================================================  RECEITA  =========================================
class print_receita_guia_rec_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_receita_guia_rec_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_receita_guia_rec_report', 'sncp_receita_guia_rec',
                      'print_report/sncp_receita_guia_rec.jrxml',
                      parser=print_receita_guia_rec_report)


class print_receita_print_report_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_receita_print_report_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_receita_print_report_report', 'sncp_receita_print_report',
                      'print_report/sncp_receita_print_report.jrxml',
                      parser=print_receita_print_report_report)


# ==================================================  TESOURARIA  =========================================
class print_tesouraria_conta_corrente_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_tesouraria_conta_corrente_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_tesouraria_conta_corrente_report', 'sncp_tesouraria_conta_corrente',
                      'print_report/sncp_tesouraria_conta_corrente.jrxml',
                      parser=print_tesouraria_conta_corrente_report)


class print_tesouraria_folha_caixa_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_tesouraria_folha_caixa_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_tesouraria_folha_caixa_report', 'sncp_tesouraria_folha_caixa',
                      'print_report/sncp_tesouraria_folha_caixa.jrxml',
                      parser=print_tesouraria_folha_caixa_report)


class print_tesouraria_mapa_ots_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_tesouraria_mapa_ots_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_tesouraria_mapa_ots_report', 'sncp_tesouraria_mapa_ots',
                      'print_report/sncp_tesouraria_mapa_ots.jrxml',
                      parser=print_tesouraria_mapa_ots_report)


class print_tesouraria_mapas_diario_resumo_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_tesouraria_mapas_diario_resumo_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_tesouraria_mapas_diario_resumo_report', 'sncp_tesouraria_mapas_diario_resumo',
                      'print_report/sncp_tesouraria_mapas_diario_resumo.jrxml',
                      parser=print_tesouraria_mapas_diario_resumo_report)


class print_tesouraria_movim_fundos_maneio_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_tesouraria_movim_fundos_maneio_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time})

report_sxw.report_sxw('report.sncp_tesouraria_movim_fundos_maneio_report', 'sncp_tesouraria_movim_fundos_maneio',
                      'print_report/sncp_tesouraria_movim_fundos_maneio.jrxml',
                      parser=print_tesouraria_movim_fundos_maneio_report)