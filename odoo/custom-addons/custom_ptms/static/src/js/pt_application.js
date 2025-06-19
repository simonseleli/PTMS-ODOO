odoo.define('custom_ptms.pt_application_form', function (require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');
    var FormController = require('web.FormController');

    // Extend FormRenderer to handle tab activation
    FormRenderer.include({
        _render: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Check if this is the pt.place.application form view
                if (self.state.model === 'pt.place.application') {
                    var context = self.state.context || {};
                    if (context.default_active_tab) {
                        // Convert default_active_tab to match tab text (e.g., 'final_report' -> 'Final Report')
                        var tabText = context.default_active_tab
                            .replace('_', ' ')
                            .toLowerCase()
                            .replace(/\b\w/g, function (c) { return c.toUpperCase(); }); // Capitalize words
                        // Find and activate the matching tab
                        self.$('.o_notebook .nav-link').each(function () {
                            if ($(this).text().trim() === tabText) {
                                $(this).tab('show');
                                return false; // Break the loop
                            }
                        });
                    }
                }
            });
        }
    });

    // Extend FormController to handle plagiarism check and reload
    FormController.include({
        _executeAction: function (action, options) {
            var self = this;
            var _super = this._super;
            // Check if this is pt.place.application and action_check_plagiarism
            if (this.modelName === 'pt.place.application' && action.name === 'action_check_plagiarism') {
                return _super.apply(this, arguments).then(function (result) {
                    // After action_check_plagiarism, reload form with Final Report tab active
                    self.reload({
                        context: _.extend({}, self.context, {
                            default_active_tab: 'final_report'
                        })
                    });
                    return result;
                });
            }
            return _super.apply(this, arguments);
        }
    });
});