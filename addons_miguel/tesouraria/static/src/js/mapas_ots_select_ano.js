openerp.web.tesouraria = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.tesouraria  = instance.web.tesouraria || {};
    console.log("Meu objeto", instance.web.tesouraria);

    instance.web.views.add('mapas_ots_view', 'instance.web.tesouraria.MapasOtsSelectAno');

    instance.web.tesouraria.SelectAnoView = instance.web.ListView.extend({
        init: function() {
            console.log("estou aqui no init");
            this._super.apply(this, arguments);

        },
        start:function(){
            console.log("estou aqui no start");
            var self = this;

            _.each(_.range(1900, 2014), function(i) {
                $(".select_ano").append("<option value="+i+">'" + i + "</option>");
            })
        }
    });
};
/*
openerp.tesouraria = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.tesouraria  =  {};
    console.log("Meu objeto", instance.web.tesouraria)

    instance.web.views.add('mapas_ots_view', 'instance.web.tesouraria.SelectAnoView');

    instance.web.tesouraria.SelectAnoView = instance.web.Widget.extend({
        template: "MapasOtsSelectAno",
        start:function(){
            console.log("estou aqui no start");
            var self = this;

            _.each(_.range(1900, 2014), function(i) {
                $(".select_ano").append("<option value="+i+">'" + i + "</option>");
            })
        }
    });

};
