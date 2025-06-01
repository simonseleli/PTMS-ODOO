odoo.define('custom_ptms.pt_application_form', function (require) {
    "use strict";

    var FormController = require('web.FormController');

    FormController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            // Check if this is the pt.place.application form view
            if (this.modelName === 'pt.place.application') {
                var context = this.initialState.context;
                if (context.default_active_tab) {
                    // Find the notebook tab by its string attribute
                    var $tabs = this.$('.o_notebook .nav-link');
                    $tabs.each(function () {
                        if ($(this).text().trim().toLowerCase() === context.default_active_tab.replace('_', ' ')) {
                            $(this).tab('show');
                            return false; // Break the loop
                        }
                    });
                }
            }
        }
    });
});