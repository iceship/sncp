/* Declarações a fazer

*/
openerp.receita = function (instance) {

    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.receita = instance.web.receita || {};


   

    instance.web.views.add('tree_pesquisa_departamento', 'instance.web.receita.PesquisaPorDepartamentoListView');
    instance.web.receita.PesquisaPorDepartamentoListView = instance.web.ListView.extend({
        init:function(){
            this._super.apply(this, arguments);
            this.departamento_lista = [];
            this.current_departamento_id = null;

        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            this.$el.parent().prepend(QWeb.render("PesquisaPorDepartamento", {widget: this}));

            // Carregar as variaveis locais com os valores seleccionados
            this.$el.parent().find('.oe_receita_select_departamento').change(function() {
                self.current_departamento_id = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });



            //Tratamento dos atributos
            this.on('edit:after', this, function () {
                self.$el.parent().find('.oe_receita_select_departamento').attr('disabled', 'disabled');
                });
            this.on('save:after cancel:after', this, function () {
                self.$el.parent().find('.oe_receita_select_departamento').removeAttr('disabled');
                });

            //Chamada a função Python
            var mod_itens_dept = new instance.web.Model("sncp.receita.itens.dept", self.dataset.context, self.dataset.domain);
            defs.push(mod_itens_dept.call("get_departamento_list_js", []).then(function(result) {
                    self.departamento_lista = result;
            }));


            return $.when(tmp, defs);
        },
        do_search: function(domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            var defs = [];
            var o;

            // Bloco de construção da lista dos objetos
            self.$el.parent().find('.oe_receita_select_departamento').children().remove().end();
            self.$el.parent().find('.oe_receita_select_departamento').append(new Option('', ''));
            for (var i = 0; i < self.departamento_lista.length; i++) {
                o = new Option(self.departamento_lista[i][1], self.departamento_lista[i][0]);
                self.$el.parent().find('.oe_receita_select_departamento').append(o);
            }
            self.$el.parent().find('.oe_receita_select_departamento').val(self.current_departamento_id).attr('selected',true);

            return self.search();
        },
        search: function(){
            var self = this;
            var domain = [];
            var defs = [];

            // Atribuição de valor ao domain
            if (self.current_departamento_id !== null) domain.push(["department_id","=", self.current_departamento_id]);

            self.last_context["department_id"] = self.current_departamento_id === null ? false : self.current_departamento_id;
            delete self.last_context["id"];
            self.last_context["id"] =  self.id_lista;

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        }
    });
};
