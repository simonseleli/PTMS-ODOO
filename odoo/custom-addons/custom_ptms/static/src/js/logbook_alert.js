odoo.define('custom_ptms.logbook_alert', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var core = require('web.core');
    var _t = core._t;

    FormController.include({
        renderButtons: function () {
            var self = this;
            this._super.apply(this, arguments);
            if (this.modelName === 'pt.application.logbook' && this.mode === 'edit') {
                var isEditable = this.renderer.state.data.is_editable;
                var dateFrom = this.renderer.state.data.date_from;
                var dateTo = this.renderer.state.data.date_to;
                var displayName = this.renderer.state.data.display_name;
                var today = moment().startOf('day');

                if (!isEditable && !this.renderer.state.data.env.user.has_group('school.group_school_administration') &&
                    !this.renderer.state.data.env.user.has_group('custom_ptms.department_coordinator')) {
                    var message = '';
                    if (moment(dateTo).isBefore(today)) {
                        message = _t("This logbook entry ('%s') is read-only because the week ended on %s.").replace('%s', displayName).replace('%s', dateTo);
                    } else if (moment(dateFrom).isAfter(today)) {
                        message = _t("This logbook entry ('%s') is read-only because the week has not yet started (starts on %s).").replace('%s', displayName).replace('%s', dateFrom);
                    }
                    if (message) {
                        this.do_notify({
                            title: _t("Editing Not Allowed"),
                            message: message,
                            type: 'warning',
                            sticky: true,
                        });
                    }
                }
            }
        },
    });
});