/**
 * Created by aksana on 06-02-2014.
 */
openerp.despesa = function(instance){

    openerp.despesa.requisicoes_pesquisa(instance);
    openerp.despesa.autorizacoes_pesquisa(instance);
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.despesa = instance.web.despesa || {};

    // Tratamento de Aprovador Autorizado para as Faturas
    instance.web.views.add('tree_aprovador_autorizado_faturas', 'instance.web.despesa.AprovadorAutorizadoFaturasView');
    instance.web.despesa.AprovadorAutorizadoFaturasView = instance.web.ListView.extend({
        init:function(){
            this._super.apply(this, arguments);
            this.domain_invoice_list = [];
        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            //Chamada a função Python
            var mod_invoice = new instance.web.Model("account.invoice", self.dataset.context, self.dataset.domain);
            defs.push(mod_invoice.call("get_lista_faturas_js", []).then(function(result) {
                    self.domain_invoice_list = result;
            }));
            return $.when(tmp, defs);
        },
        do_search: function(domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);

            return self.search();
        },
        search: function(){
            var self = this;
            var domain = [];

            // Atribuição de valor ao domain
            domain.push(["id","in", self.domain_invoice_list]);


            self.last_context["user_id"] = self.current_user_id === null ? false : self.current_user_id;
            delete self.last_context["id"];
            self.last_context["id"] =  self.id_lista;

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            console.log("CompoundDomainFat: ", compound_domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        }
    });

    // Tratamento de Aprovador Autorizado para as Requisições Aprovar
    instance.web.views.add('tree_aprovador_autorizado_requisicao', 'instance.web.despesa.AprovadorAutorizadoRequisicaoView');
    instance.web.despesa.AprovadorAutorizadoRequisicaoView = instance.web.ListView.extend({
        init:function(){
            this._super.apply(this, arguments);
            this.domain_requisicao_list = [];
        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            //Chamada a função Python
            var mod_requisicao = new instance.web.Model("sncp.despesa.requisicoes", self.dataset.context, self.dataset.domain);
            defs.push(mod_requisicao.call("get_lista_requisicoes_js", [self.dataset.context]).then(function(result) {
                    self.domain_requisicao_list = result;
                    console.log("lista", self.domain_requisicao_list);
            }));
            return $.when(tmp, defs);
        },
        do_search: function(domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);

            return self.search();
        },
        search: function(){
            var self = this;
            var domain = [];

            // Atribuição de valor ao domain
            domain.push(["id","in", self.domain_requisicao_list]);
            console.log("domain", domain);

            self.last_context["user_id"] = self.current_user_id === null ? false : self.current_user_id;
            delete self.last_context["id"];
            self.last_context["id"] =  self.id_lista;

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            console.log("CompoundDomainReq: ", compound_domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        }
    });

    // Tratamento de Aprovador Autorizado para as Ordens de Compra
    instance.web.views.add('tree_aprovador_autorizado_ordem_compra', 'instance.web.despesa.AprovadorAutorizadoOrdemCompraView');
    instance.web.despesa.AprovadorAutorizadoOrdemCompraView = instance.web.ListView.extend({
        init:function(){
            this._super.apply(this, arguments);
            this.domain_ordem_compra_list = [];
        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            //Chamada a função Python
            var mod_order = new instance.web.Model("purchase.order", self.dataset.context, self.dataset.domain);
            defs.push(mod_order.call("get_lista_ordem_compra_js", []).then(function(result) {
                    self.domain_ordem_compra_list = result;
            }));
            return $.when(tmp, defs);
        },
        do_search: function(domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);

            return self.search();
        },
        search: function(){
            var self = this;
            var domain = [];

            // Atribuição de valor ao domain
            domain.push(["id","in", self.domain_ordem_compra_list]);


            self.last_context["user_id"] = self.current_user_id === null ? false : self.current_user_id;
            delete self.last_context["id"];
            self.last_context["id"] =  self.id_lista;

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            console.log("CompoundDomain_ordem_compra: ", compound_domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        }
    });
};