from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssessmentSheet(models.Model):
    _name = 'pt.application.assessment.sheet'
    _description = 'Assessment Sheet'

    application_id = fields.Many2one(
        'pt.place.application', string="PT Application", required=True, ondelete='cascade'
    )
    name = fields.Char(
        string="Student Name", compute='_compute_name', store=True
    )
    student_id = fields.Many2one(
        'student.student', string="Student", related='application_id.student_id', store=True
    )
    supervisor_id = fields.Many2one(
        'res.users', string="Supervisor", required=True
    )
    date = fields.Date(string="Assessment Date", required=True)

    # Marks Fields
    training_officer = fields.Integer(string="Training Officer (10)", default=0)
    logbook_content = fields.Integer(string="Content relevance (5)", default=0)
    logbook_neatness = fields.Integer(string="Drawing Precision and neatness (5)", default=0)
    logbook_relevance = fields.Integer(string="Relevance of the task/rolls according to a student's level (year of study) (5)", default=0)
    logbook_organization = fields.Integer(string="Overall organization & neatness (5)", default=0)
    academic_supervisor = fields.Integer(string="Academic Supervisor (10)", default=0)
    report_intro = fields.Integer(string="Introduction and Organisation Chart (5)", default=0)
    report_safety = fields.Integer(string="Comments on the practice of Safety Regulations and General Welfare (5)", default=0)
    report_job_desc = fields.Integer(string="Job Descriptions based on Professionalism (5)", default=0)
    report_recruitment = fields.Integer(string="Outline (description) of Recruitment and Training Policy (5)", default=0)
    task_diagram = fields.Integer(string="Diagrammatic Presentation (5)", default=0)
    task_problem = fields.Integer(string="Problem Identification and Assumptions made (5)", default=0)
    task_solution = fields.Integer(string="Choice and Justification of the chosen Solution (5)", default=0)
    task_comparison = fields.Integer(string="Discussion and Comparison of Alternative Solutions (5)", default=0)
    task_technical = fields.Integer(string="Functional and Technical Requirements (5)", default=0)
    task_conclusion = fields.Integer(string="Conclusion & Recommendations (5)", default=0)
    task_references = fields.Integer(string="References (5)", default=0)
    task_formatting = fields.Integer(string="Neatness and Precision of writing, Arrangement, Formatting & Drawing (5)", default=0)

    # Computed total
    total = fields.Integer(string="GRAND TOTAL MARKS", compute="_compute_total_marks", store=True)

    is_final = fields.Boolean(string="Final PT?")

    @api.depends('application_id.student_id')
    def _compute_name(self):
        for record in self:
            record.name = record.student_id.name or ''

    @api.depends(
        'training_officer', 'logbook_content', 'logbook_neatness', 'logbook_relevance',
        'logbook_organization', 'academic_supervisor', 'report_intro', 'report_safety',
        'report_job_desc', 'report_recruitment', 'task_diagram', 'task_problem',
        'task_solution', 'task_comparison', 'task_technical', 'task_conclusion',
        'task_references', 'task_formatting'
    )
    def _compute_total_marks(self):
        for record in self:
            record.total = sum([
                record.training_officer,
                record.logbook_content,
                record.logbook_neatness,
                record.logbook_relevance,
                record.logbook_organization,
                record.academic_supervisor,
                record.report_intro,
                record.report_safety,
                record.report_job_desc,
                record.report_recruitment,
                record.task_diagram,
                record.task_problem,
                record.task_solution,
                record.task_comparison,
                record.task_technical,
                record.task_conclusion,
                record.task_references,
                record.task_formatting
            ])

    @api.constrains(
        'training_officer', 'logbook_content', 'logbook_neatness', 'logbook_relevance',
        'logbook_organization', 'academic_supervisor', 'report_intro', 'report_safety',
        'report_job_desc', 'report_recruitment', 'task_diagram', 'task_problem',
        'task_solution', 'task_comparison', 'task_technical',
        'task_conclusion', 'task_references', 'task_formatting'
    )
    def _check_marks(self):
        for record in self:
            # Define maximum marks for each field
            max_marks = {
                'training_officer': 10,
                'logbook_content': 5,
                'logbook_neatness': 5,
                'logbook_relevance': 5,
                'logbook_organization': 5,
                'academic_supervisor': 10,
                'report_intro': 5,
                'report_safety': 5,
                'report_job_desc': 5,
                'report_recruitment': 5,
                'task_diagram': 5,
                'task_problem': 5,
                'task_solution': 5,
                'task_comparison': 5,
                'task_technical': 5,
                'task_conclusion': 5,
                'task_references': 5,
                'task_formatting': 5,
            }
            for field, max_mark in max_marks.items():
                value = getattr(record, field)
                if value < 0 or value > max_mark:
                    raise ValidationError(
                        f"{field.replace('_', ' ').title()} must be between 0 and {max_mark}."
                    )
