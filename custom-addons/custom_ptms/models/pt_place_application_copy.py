from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging
import base64
import io
import PyPDF2
import pdfplumber
import re

_logger = logging.getLogger(__name__)


class PTPlaceApplication(models.Model):
    _name = 'pt.place.application'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "PT Application"
    _order = 'create_date desc'

    # ==================== Identification Fields ====================
    name = fields.Char(string="Application Reference", readonly=True, default=lambda self: self._default_reference())
    user_id = fields.Many2one('res.users', string="User", required=True, default=lambda self: self.env.user.id)
    student_id = fields.Many2one('student.student', string="Student", default=lambda self: self._get_student())
    student_name = fields.Char(related="student_id.name", store=True)
    student_gender = fields.Selection(related="student_id.gender", store=True)
    registration_no = fields.Char(related="student_id.registration_no", store=True)
    department_id = fields.Many2one('hr.department', string="Department", related='student_id.department_id',
                                    store=True)
    current_year = fields.Boolean(string='Current Academic Year', default=True)

    # ==================== Application Details ====================
    place_id = fields.Many2one('pt.place', string="PT Place", required=True)
    academic_year = fields.Many2one('academic.year', string="Academic Year", domain="[('current','=',True)]",
                                    default=lambda self: self.env['academic.year'].search([('current', '=', True)],
                                                                                          limit=1).id, required=True)
    date = fields.Date(string="Application Date", default=lambda self: fields.Date.today())
    is_self = fields.Boolean(string="Self-Submitted", default=False)
    is_published = fields.Boolean(string="Results Published", default=False)
    confirmation_letter = fields.Binary(string="Confirmation Letter")
    division_id = fields.Many2one('standard.division', string="Course", related='student_id.standard_id.division_id',
                                  store=True)
    pt_type = fields.Many2one('standard.standard', string="PT Type", related='student_id.standard_id.standard_id',
                              store=True)
    region = fields.Char(related='place_id.region', string="Region", store=True, readonly=True)
    self_company_name = fields.Char(string="Company Name", help="For self-submitted applications")
    self_company_region = fields.Char(string="Company Region")
    self_company_district = fields.Char(string="Company District")

    # ==================== Workflow Fields ====================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string="Status", default='draft', tracking=True)

    # ==================== Supervisor Assignment ====================
    is_assigned = fields.Boolean(string="Assigned", default=False)
    assignment_id = fields.Many2one('pt.supervisor.assignment', string="Assignment")
    assignment_user_id = fields.Many2one('res.users', string="Supervisor",
                                         related='assignment_id.teacher_id.employee_id.user_id', store=True)

    # ==================== Visit Information ====================
    supervisor_id = fields.Many2one('res.users', string="Assessing Supervisor", required=True,
                                    default=lambda self: self.env.user.id)
    arrival_note = fields.Binary(string="Arrival Note")
    date_visit = fields.Date(string="Visiting Date")
    comments = fields.Text(string="Workplace Comments")
    remarks = fields.Text(string="Remarks on Student")
    report_title = fields.Char(string="Final Report Title")

    # ==================== Grading Information ====================
    officer_marks = fields.Float(string="Officer Marks")
    logbook_marks = fields.Float(string="Log Book Marks")
    supervisor_marks = fields.Float(string="Supervisor Marks")
    report_marks = fields.Float(string="Final Report Marks")
    total_marks = fields.Float(string="Total Marks", compute='_compute_total_marks', store=True)
    officer_marks_label = fields.Float(string="Officer Marks", related='student_id.standard_id.officer_marks')
    logbook_marks_label = fields.Float(string="Log Book Marks", related='student_id.standard_id.logbook_marks')
    supervisor_marks_label = fields.Float(string="Supervisor Marks", related='student_id.standard_id.supervisor_marks')
    report_marks_label = fields.Float(string="Final Report Marks", related='student_id.standard_id.report_marks')
    assessment_sheet_ids = fields.One2many('pt.application.assessment.sheet', 'application_id',
                                           string="Assessment Sheets")

    # ==================== Final Report Fields ====================
    final_report = fields.Binary(string="Final Report")
    report_filename = fields.Char(string="Report Filename")
    report_text = fields.Text(string="Extracted Report Text", readonly=True)
    plagiarism_results = fields.Text(string="Plagiarism Check Results", readonly=True)
    plagiarism_percentage = fields.Float(string="Highest Similarity (%)", compute='_compute_plagiarism_fields',
                                         store=True, readonly=True,
                                         groups="school.group_school_administration,school.group_school_teacher,custom_ptms.department_coordinator")
    plagiarism_flagged = fields.Boolean(string="Flagged for Plagiarism", compute='_compute_plagiarism_fields',
                                        store=True, readonly=True,
                                        groups="school.group_school_administration,school.group_school_teacher,custom_ptms.department_coordinator")
    plagiarism_summary = fields.Char(string="Plagiarism Summary", compute='_compute_plagiarism_fields', store=True,
                                     readonly=True,
                                     groups="school.group_school_administration,school.group_school_teacher,custom_ptms.department_coordinator")
    plagiarism_not_checked = fields.Boolean(string="Plagiarism Not Checked", compute='_compute_plagiarism_fields',
                                            store=True, readonly=True,
                                            groups="school.group_school_administration,school.group_school_teacher,custom_ptms.department_coordinator")

    # ==================== Computed Fields for Plagiarism ====================
    @api.depends('plagiarism_results')
    def _compute_plagiarism_fields(self):
        for record in self:
            results = record.plagiarism_results or ""
            percentage = 0.0
            flagged = False
            summary = "No check performed"
            not_checked = True

            if not results or results in ["No text extracted for plagiarism check.",
                                          "No other reports to compare in this academic year."]:
                summary = results if results else "No check performed"
            else:
                not_checked = False
                # Extract percentages from results like "Similarity 100.00% with ..."
                matches = re.findall(r"Similarity (\d+\.\d+)%", results)
                if matches:
                    percentages = [float(p) for p in matches]
                    percentage = max(percentages)
                    flagged = percentage > 80.0
                    # Get the first line for summary
                    first_line = results.split('\n')[0]
                    summary = first_line[:100] + ("..." if len(first_line) > 100 else "")
                else:
                    summary = "No significant similarities detected"

            record.plagiarism_percentage = percentage
            record.plagiarism_flagged = flagged
            record.plagiarism_summary = summary
            record.plagiarism_not_checked = not_checked

    # ==================== Plagiarism Detection Methods ====================
    def _extract_text_from_pdf(self, binary_data):
        try:
            with pdfplumber.open(io.BytesIO(base64.b64decode(binary_data))) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            _logger.error(f"Error extracting text from PDF: {e}")
            try:
                # Fallback to PyPDF2
                pdf_file = io.BytesIO(base64.b64decode(binary_data))
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                return text
            except Exception as e:
                _logger.error(f"Fallback extraction failed: {e}")
                return ""

    def _extract_text(self, binary_data, filename):
        if not binary_data or not filename:
            return ""
        if not filename.lower().endswith('.pdf'):
            _logger.warning(f"Invalid file format: {filename}. Only PDF files are allowed.")
            raise ValidationError("Only PDF files are supported for final reports.")
        return self._extract_text_from_pdf(binary_data)

    def _check_plagiarism(self, text):
        if not text:
            return "No text extracted for plagiarism check."

        # Log current record details
        _logger.info(
            f"Checking plagiarism for application ID {self.id}, academic_year: {self.academic_year.id if self.academic_year else 'None'}")

        # Compare with other reports in the same academic year
        other_reports = self.search([
            ('id', '!=', self.id),
            ('final_report', '!=', False),
            ('academic_year', '=', self.academic_year.id)
        ])

        # Log search results
        _logger.info(
            f"Found {len(other_reports)} other reports for academic_year {self.academic_year.id if self.academic_year else 'None'}: {[r.id for r in other_reports]}")

        if not other_reports:
            return "No other reports to compare in this academic year."

        results = []
        threshold = 0.8  # Similarity threshold (80%)
        min_match_length = 100  # Minimum length for matching substrings

        for report in other_reports:
            other_text = report.report_text or self._extract_text(report.final_report, report.report_filename)
            if not other_text:
                _logger.warning(f"No text extracted for report ID {report.id}")
                continue
            # Log comparison
            _logger.info(f"Comparing with report ID {report.id}, student: {report.student_name}")
            # Find common substrings longer than min_match_length
            max_common_length = 0
            for i in range(len(text) - min_match_length + 1):
                for j in range(len(other_text) - min_match_length + 1):
                    substring = text[i:i + min_match_length]
                    if substring in other_text[j:j + min_match_length]:
                        # Extend match as long as possible
                        k = min_match_length
                        while (i + k < len(text) and j + k < len(other_text) and
                               text[i:i + k + 1] == other_text[j:j + k + 1]):
                            k += 1
                        if k > max_common_length:
                            max_common_length = k

            if max_common_length > 0:
                # Calculate similarity as ratio of common substring length to text length
                similarity = max_common_length / min(len(text), len(other_text))
                _logger.info(
                    f"Similarity with report ID {report.id}: {similarity:.2%}, matched {max_common_length} characters")
                if similarity > threshold:
                    results.append(
                        f"Similarity {similarity:.2%} with {report.student_name}'s report "
                        f"(ID: {report.id}, Title: {report.report_title or 'Untitled'}, "
                        f"Matched {max_common_length} characters)"
                    )

        return "\n".join(results) or "No significant similarities detected."

    def action_check_plagiarism(self):
        """Manually trigger plagiarism check for the current application."""
        self.ensure_one()
        if not self.final_report:
            raise UserError("No final report uploaded to check for plagiarism.")
        # Use existing report_text or re-extract
        text = self.report_text or self._extract_text(self.final_report, self.report_filename)
        if not text:
            raise UserError("Failed to extract text from the report.")
        # Update report_text if re-extracted
        if not self.report_text:
            self.report_text = text
        # Run plagiarism check
        self.plagiarism_results = self._check_plagiarism(text)
        self.env.cr.commit()  # Ensure results are saved
        # Return notification and reload action
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Plagiarism Check Completed',
                'message': 'Plagiarism check has been performed. Results are updated in the Final Report tab.',
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'pt.place.application',
                    'res_id': self.id,
                    'view_mode': 'form',
                    'view_id': self.env.ref('custom_ptms.pt_application_form').id,
                    'target': 'current',
                    'context': dict(self.env.context, default_active_tab='final_report'),
                    'flags': {'initial_mode': 'view'},
                }
            }
        }

    @api.model
    def create(self, vals):
        if 'final_report' in vals and vals.get('final_report'):
            filename = vals.get('report_filename', 'report')
            text = self._extract_text(vals['final_report'], filename)
            vals['report_text'] = text
            vals['plagiarism_results'] = self._check_plagiarism(text)
        return super().create(vals)

    def write(self, vals):
        if 'final_report' in vals and vals.get('final_report'):
            filename = vals.get('report_filename', 'report')
            text = self._extract_text(vals['final_report'], filename)
            vals['report_text'] = text
            vals['plagiarism_results'] = self._check_plagiarism(text)
        return super().write(vals)

    # ==================== Existing Methods ====================
    def _mark_pt_status(self):
        _logger.info("Running _mark_pt_status for pt.place.application")
        current_active_year = self.env['academic.year'].search([('current', '=', True)], limit=1)
        if not current_active_year:
            _logger.warning("No current academic year found. Skipping _mark_pt_status.")
            return
        applications = self.search([('current_year', '=', True), ('academic_year', '!=', False)])
        for application in applications:
            if not application.academic_year or application.academic_year != current_active_year:
                _logger.info(f"Setting current_year = False for application {application.id}")
                application.current_year = False

    @api.depends('officer_marks', 'logbook_marks', 'supervisor_marks', 'report_marks')
    def _compute_total_marks(self):
        for record in self:
            record.total_marks = sum([
                record.officer_marks or 0,
                record.logbook_marks or 0,
                record.supervisor_marks or 0,
                record.report_marks or 0
            ])

    @api.model
    def _default_reference(self):
        return self.env['ir.sequence'].next_by_code('pt.place.application') or 'New'

    @api.model
    def _get_student(self):
        return self.env['student.student'].search([('user_id', '=', self.env.user.id)], limit=1).id

    def action_submit(self):
        for application in self:
            if application.state != 'draft':
                raise ValidationError("Only draft applications can be submitted.")
            if not application.is_self and application.place_id.available_chances < 1:
                raise ValidationError(f"No available chances at {application.place_id.name}")
            if application.is_self and not application.confirmation_letter:
                raise ValidationError("Confirmation letter is required for self-submitted applications!")
            application.state = 'submitted'

    def action_approve(self):
        for application in self:
            if application.state != 'submitted':
                raise ValidationError("Only submitted applications can be approved.")
            if application.is_self:
                if not application.place_id:
                    if not application.self_company_name:
                        raise ValidationError("Company name is required for self-submitted applications")
                    application.place_id = self.env['pt.place'].create({
                        'name': application.self_company_name,
                        'region': application.self_company_region or 'Unknown',
                        'district': application.self_company_district or 'Unknown',
                        'total_chances': 1
                    })
            else:
                if application.place_id.available_chances < 1:
                    raise ValidationError(f"No available chances at {application.place_id.name}")
                application.place_id.available_chances -= 1
            application.state = 'approved'

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_assign_supervisor(self, supervisor_id):
        self.write({
            'assignment_user_id': supervisor_id,
            'is_assigned': True,
            'state': 'in_progress'
        })

    def action_complete(self):
        self.write({'state': 'completed'})

    @api.constrains('student_id')
    def _check_duplicate_application(self):
        for application in self:
            if application.state in ['submitted', 'approved', 'in_progress']:
                existing = self.search_count([
                    ('student_id', '=', application.student_id.id),
                    ('state', 'in', ['submitted', 'approved', 'in_progress']),
                    ('id', '!=', application.id)
                ])
                if existing > 0:
                    raise ValidationError("You can only have one active PT application at a time!")

    def action_open_assessment_sheet(self):
        self.ensure_one()
        if not self.assignment_user_id:
            raise UserError("A supervisor must be assigned before assessing the student!")
        assessment = self.env['pt.application.assessment.sheet'].search([
            ('application_id', '=', self.id),
            ('supervisor_id', '=', self.assignment_user_id.id)
        ], limit=1)
        if not assessment:
            assessment = self.env['pt.application.assessment.sheet'].create({
                'application_id': self.id,
                'student_id': self.student_id.id,
                'supervisor_id': self.assignment_user_id.id,
                'date': fields.Date.today(),
            })
        return {
            'type': 'ir.actions.act_window',
            'name': f'Assessment for {self.student_name}',
            'res_model': 'pt.application.assessment.sheet',
            'res_id': assessment.id,
            'view_mode': 'form',
            'view_id': self.env.ref('custom_ptms.view_assessment_sheet_form').id,
            'target': 'current',
            'context': {
                'default_application_id': self.id,
                'default_student_id': self.student_id.id,
                'default_supervisor_id': self.assignment_user_id.id,
                'form_view_initial_mode': 'edit',
                'create': False
            },
        }


