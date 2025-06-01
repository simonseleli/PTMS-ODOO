# -*- coding: utf-8 -*-
{
    'name': "custom_ptms",

    'summary': """
        Practical Training Management System""",

    'description': """
        AI-integrated PTMS for training and assessment management.
    """,
    'author': "IctPack Solutions Ltd",
    'website': "http://www.ictpack.com",
    'category': 'Ptms',
    'version': '1.0',

    'depends': ['base', 'web', 'school', 'document_management_system', 'sale', 'ks_dashboard_ninja', 'mail', 'portal'],

    'external_dependencies': {
        'python': ['PyPDF2', 'pdfplumber', 'python-docx'],
    },

    'data': [
        'security/ptms_security.xml',
        'security/ir.model.access.csv',
        'data/cron_jobs.xml',
        'views/main_views.xml',
        'views/plagiarism_action_to_all.xml',
        'data/logbook_data.xml',
        'views/pt_application_views.xml',
        'data/pt_application_sequence.xml',
        'views/logbook_views.xml',
        'views/pt_places_views.xml',
        'views/application_views.xml',
        'views/partner_views.xml',
        'views/vacancy_views.xml',
        'views/location_selection_views.xml',
        'views/assessment_sheet_views.xml',
        'views/res_country_views.xml',
        'wizards/confirmation_wizard.xml',
        'wizards/multi_assignment.xml',
        'wizards/move_application_view.xml',
        'wizards/publish_results.xml',
        'views/document.xml',
        'views/student_view.xml',
        'views/teacher_view.xml',
        'views/pt_supervisor_assignment_views.xml',
        'views/login_template.xml',
        'views/division_views.xml',
        'views/school_view.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'custom_ptms/static/src/js/pt_application.js',
        ],
    },

    'qweb': [
        'static/src/xml/user_menu.xml'
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True,
}
