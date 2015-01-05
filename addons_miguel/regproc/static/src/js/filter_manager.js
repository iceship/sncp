/**
 * Created by exeq on 20-10-2014.
 */

openerp.regproc.filter_manager = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.regproc = instance.web.regproc || {};



    instance.web.views.add('filter_manager_tree', 'instance.web.regproc.FilterManagerListView');
    instance.web.regproc.FilterManagerListView = instance.web.ListView.extend({
        init:function(){
            this._super.apply(this, arguments);
            this.current_user_id = null;
            this.domain_user_lista = [];
            this.autorized_user_lista = [];

        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            this.$el.parent().prepend(QWeb.render("Parametros", {widget: this}));

            // Carregar as variaveis locais com os valores seleccionados
            this.$el.parent().find('.oe_regproc_select_user').change(function() {
                self.current_user_id = this.value ==='' ? null : parseInt(this.value);
                    console.log("curr_user_id", self.current_user_id);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });



            //Tratamento dos atributos
            this.on('edit:after', this, function () {
                self.$el.parent().find('.oe_regproc_select_user').attr('disabled', 'disabled');

            });
            this.on('save:after cancel:after', this, function () {
                self.$el.parent().find('.oe_regproc_select_user').removeAttr('disabled');

            });

            //Chamada a função Python
            var mod_employee = new instance.web.Model("hr.employee", self.dataset.context, self.dataset.domain);
            defs.push(mod_employee.call("get_child_ids_js", []).then(function(result) {
                    self.domain_user_lista = result;
                    console.log("domain_user_lista ", self.domain_user_lista);
            }));
            var mod_aquis_alien = new instance.web.Model("sncp.regproc.aquis.alien", self.dataset.context, self.dataset.domain);
            defs.push(mod_aquis_alien.call("get_autorized_user_js", []).then(function(result) {
                    self.autorized_user_lista = result;
                    console.log("autorized_user_lista ", self.autorized_user_lista);
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
            self.$el.parent().find('.oe_regproc_select_user').children().remove().end();
            self.$el.parent().find('.oe_regproc_select_user').append(new Option('', ''));
            for (var i = 0; i < self.autorized_user_lista.length; i++) {
                //console.log("Ciclo: ", i);
                for (var k = 0; k < self.domain_user_lista.length; k++) {
                    if (self.autorized_user_lista[i][0] == self.domain_user_lista[k]) {
                        console.log("True");
                        o = new Option(self.autorized_user_lista[i][1], self.autorized_user_lista[i][0]);
                        self.$el.parent().find('.oe_regproc_select_user').append(o);
                    }
                }
            }
            self.$el.parent().find('.oe_regproc_select_user').val(self.current_user_id).attr('selected',true);



            return self.search();
        },
        search: function(){
            var self = this;
            var domain = [];
            var defs = [];

            // Atribuição de valor ao domain
            if (self.current_user_id !== null) {domain.push(["user_id","=", self.current_user_id]);}
            else {domain.push(["user_id","in", self.domain_user_lista]);}
            console.log("self.domain_user_lista: ", self.domain_user_lista);
            console.log("self.current_user_id: ", self.current_user_id);
            console.log("domain: ", domain);


            self.last_context["user_id"] = self.current_user_id === null ? false : self.current_user_id;
            delete self.last_context["id"];
            self.last_context["id"] =  self.id_lista;

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            console.log("CompoundDomain: ", compound_domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        }
    });
};