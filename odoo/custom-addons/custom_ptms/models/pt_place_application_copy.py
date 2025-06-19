from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging
import base64
import io
import PyPDF2
import pdfplumber
import re
import difflib
import time
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class PTPlaceApplication(models.Model):
    _name = 'pt.place.application'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "PT Application"
    _order = 'create_date desc'

    # ==================== Identification Fields ====================
    name = fields.Char(
        string="Application Reference",
        compute='_compute_name',
        store=True,
        readonly=True
    )
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

    logbook_ids = fields.One2many('pt.application.logbook', 'application_id', string='Logbook Entries')

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
    officer_marks = fields.Float(
        string="Officer Marks",
        compute='_compute_assessment_marks',
        store=True
    )
    logbook_marks = fields.Float(
        string="Log Book Marks",
        compute='_compute_assessment_marks',
        store=True
    )
    supervisor_marks = fields.Float(
        string="Supervisor Marks",
        compute='_compute_assessment_marks',
        store=True
    )
    report_marks = fields.Float(
        string="Final Report Marks",
        compute='_compute_assessment_marks',
        store=True
    )
    total_marks = fields.Float(
        string="Total Marks",
        compute='_compute_total_marks',
        store=True
    )
    officer_marks_label = fields.Float(string="Officer Marks", related='student_id.standard_id.officer_marks')
    logbook_marks_label = fields.Float(string="Log Book Marks", related='student_id.standard_id.logbook_marks')
    supervisor_marks_label = fields.Float(string="Supervisor Marks", related='student_id.standard_id.supervisor_marks')
    report_marks_label = fields.Float(string="Final Report Marks", related='student_id.standard_id.report_marks')
    assessment_sheet_ids = fields.One2many(
        'pt.application.assessment.sheet',
        'application_id',
        string="Assessment Sheets"
    )


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


    # SKILLS
    skill_ids = fields.Many2many(
        'pt.skill',
        string="Required Skills",
        related='place_id.skill_ids',
        readonly=True,
        store=False
    )

    # ==================== Computed Fields for Plagiarism ====================

    @api.depends('assessment_sheet_ids', 'assessment_sheet_ids.training_officer',
                 'assessment_sheet_ids.logbook_content',
                 'assessment_sheet_ids.logbook_neatness', 'assessment_sheet_ids.logbook_relevance',
                 'assessment_sheet_ids.logbook_organization', 'assessment_sheet_ids.academic_supervisor',
                 'assessment_sheet_ids.report_intro', 'assessment_sheet_ids.report_safety',
                 'assessment_sheet_ids.report_job_desc', 'assessment_sheet_ids.report_recruitment',
                 'assessment_sheet_ids.task_diagram', 'assessment_sheet_ids.task_problem',
                 'assessment_sheet_ids.task_solution', 'assessment_sheet_ids.task_comparison',
                 'assessment_sheet_ids.task_technical', 'assessment_sheet_ids.task_conclusion',
                 'assessment_sheet_ids.task_references', 'assessment_sheet_ids.task_formatting')
    def _compute_assessment_marks(self):
        for record in self:
            _logger.info(
                f"Computing marks for application {record.id}, assessments: {len(record.assessment_sheet_ids)}")
            # Get the latest assessment sheet (sorted by date)
            assessment = record.assessment_sheet_ids.sorted(key=lambda x: x.date, reverse=True)[:1]
            if assessment:
                _logger.info(f"Using assessment {assessment.id}: training_officer={assessment.training_officer}")
                record.officer_marks = assessment.training_officer
                record.logbook_marks = sum([
                    assessment.logbook_content,
                    assessment.logbook_neatness,
                    assessment.logbook_relevance,
                    assessment.logbook_organization
                ])
                record.supervisor_marks = assessment.academic_supervisor
                record.report_marks = sum([
                    assessment.report_intro,
                    assessment.report_safety,
                    assessment.report_job_desc,
                    assessment.report_recruitment,
                    assessment.task_diagram,
                    assessment.task_problem,
                    assessment.task_solution,
                    assessment.task_comparison,
                    assessment.task_technical,
                    assessment.task_conclusion,
                    assessment.task_references,
                    assessment.task_formatting
                ])
            else:
                _logger.warning(f"No assessments found for application {record.id}")
                record.officer_marks = 0
                record.logbook_marks = 0
                record.supervisor_marks = 0
                record.report_marks = 0

    @api.depends('officer_marks', 'logbook_marks', 'supervisor_marks', 'report_marks')
    def _compute_total_marks(self):
        for record in self:
            record.total_marks = sum([
                record.officer_marks or 0,
                record.logbook_marks or 0,
                record.supervisor_marks or 0,
                record.report_marks or 0
            ])

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


    # ==================== Compute Name Field ====================
    @api.depends('place_id.name', 'registration_no')
    def _compute_name(self):
        for record in self:
            place_name = record.place_id.name if record.place_id else 'Unknown'
            reg_number = record.registration_no if record.registration_no else 'Unknown'
            record.name = f"{place_name}/{reg_number}"


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
        start_time = time.time()
        _logger.info("Starting plagiarism check for application ID %s", self.id)

        if not text:
            _logger.info("No text extracted, took %.2f seconds", time.time() - start_time)
            return "No text extracted for plagiarism check."

        _logger.info(
            f"Checking plagiarism for application ID {self.id}, academic_year: {self.academic_year.id if self.academic_year else 'None'}, text_length: {len(text)}")

        search_start = time.time()
        other_reports = self.search([
            ('id', '!=', self.id),
            ('final_report', '!=', False),
            ('academic_year', '=', self.academic_year.id)
        ], limit=50)
        _logger.info("Search for other reports took %.2f seconds, found %d reports: %s",
                     time.time() - search_start, len(other_reports), [r.id for r in other_reports])

        if not other_reports:
            _logger.info("No other reports found, total time %.2f seconds", time.time() - start_time)
            return "No other reports to compare in this academic year."

        results = []
        threshold = 0.3  # 30% threshold
        updates = {}

        for report in other_reports:
            extract_start = time.time()
            other_text = report.report_text or self._extract_text(report.final_report, report.report_filename)
            _logger.info("Text extraction for report ID %s took %.2f seconds, text_length: %s",
                         report.id, time.time() - extract_start, len(other_text) if other_text else 0)

            if not other_text:
                _logger.warning(f"No text extracted for report ID {report.id}")
                continue

            compare_start = time.time()
            matcher = difflib.SequenceMatcher(None, text.lower(), other_text.lower())
            similarity = matcher.ratio()
            matched_length = int(similarity * min(len(text), len(other_text)))

            _logger.info(
                f"Similarity with report ID {report.id} (student: {report.student_name}): {similarity:.2%}, matched {matched_length} characters, took %.2f seconds",
                time.time() - compare_start)

            if similarity > threshold:
                result_str = (
                    f"Similarity {similarity:.2%} with {report.student_name}'s report "
                    f"(Student: {report.student_name}, Reg No: {report.registration_no or 'N/A'}, "
                    f"Title: {report.report_title or 'Untitled'}, Matched {matched_length} characters)"
                )
                results.append(result_str)

                other_result_str = (
                    f"Similarity {similarity:.2%} with {self.student_name}'s report "
                    f"(Student: {self.student_name}, Reg No: {self.registration_no or 'N/A'}, "
                    f"Title: {self.report_title or 'Untitled'}, Matched {matched_length} characters)"
                )
                existing_results = report.plagiarism_results.split("\n") if report.plagiarism_results else []
                _logger.info("Existing results for report ID %s: %s", report.id, existing_results)
                if other_result_str not in existing_results:
                    existing_results.append(other_result_str)
                    updates[report.id] = "\n".join(existing_results)
                    _logger.info("Scheduled update for report ID %s: %s", report.id, other_result_str)

        for report_id, new_results in updates.items():
            try:
                report = self.browse(report_id)
                report.write({'plagiarism_results': new_results})
                self.env.cr.commit()  # Force commit
                _logger.info("Successfully updated plagiarism_results for report ID %s: %s", report_id, new_results)
            except Exception as e:
                _logger.error("Failed to update report ID %s: %s", report_id, e)

        _logger.info("Plagiarism check completed for application ID %s, total time %.2f seconds",
                     self.id, time.time() - start_time)
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
        res = super().write(vals)
        if 'final_report' in vals and vals.get('final_report'):
            filename = vals.get('report_filename', 'report')
            text = self._extract_text(vals['final_report'], filename)
            _logger.info("Extracted text for application ID %s, length: %s", self.id, len(text) if text else 0)
            if text:
                self.report_text = text
                self.plagiarism_results = self._check_plagiarism(text)
                self.env.cr.commit()  # Ensure current report is saved
            other_reports = self.search([
                ('id', '!=', self.id),
                ('final_report', '!=', False),
                ('academic_year', '=', self.academic_year.id),
                ('report_text', '!=', False)
            ], limit=50)
            _logger.info("Found %d other reports for recheck: %s", len(other_reports), [r.id for r in other_reports])
            for report in other_reports:
                try:
                    _logger.info("Starting recheck for report ID %s", report.id)
                    report.plagiarism_results = report._check_plagiarism(report.report_text)
                    self.env.cr.commit()  # Force commit
                    _logger.info("Rechecked plagiarism for report ID %s", report.id)
                except Exception as e:
                    _logger.error("Failed to recheck report ID %s: %s", report.id, e)
        return res

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

    # @api.model
    # def _default_reference(self):
    #     return self.env['ir.sequence'].next_by_code('pt.place.application') or 'New'

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

        # Return action to redirect to My Applications
        return {
            'type': 'ir.actions.act_window',
            'name': 'My PT Applications',
            'res_model': 'pt.place.application',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'current',
            'domain': [('student_id.user_id', '=', self.env.user.id)],
            'context': {'create': False},
        }

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
            # Create 8 weeks of logbook entries upon approval
            self._create_logbook_entries(application)

    def _create_logbook_entries(self, application):
        """Create 8 weeks of logbook entries for the approved application."""
        start_date_record = self.env['pt.start.date'].search([], limit=1)
        start_date = start_date_record.logbook_start_date if start_date_record else datetime(2025, 6, 23).date()
        logbook_vals = []
        for i in range(8):
            week_start = start_date + timedelta(days=i * 7)
            week_end = week_start + timedelta(days=6)
            logbook_vals.append({
                'name': f'Week {i + 1}',
                'application_id': application.id,
                'date_from': week_start,
                'date_to': week_end,
            })
        self.env['pt.application.logbook'].create(logbook_vals)

    def update_logbook_dates(self):
        """Update dates of existing logbook entries based on the current start date."""
        start_date_record = self.env['pt.start.date'].search([], limit=1)
        start_date = start_date_record.logbook_start_date if start_date_record else datetime(2025, 6, 23).date()
        applications = self.search([('state', '=', 'approved')])
        for app in applications:
            logbooks = app.logbook_ids.sorted(key=lambda x: x.name)
            if len(logbooks) != 8:
                _logger.warning(f"Application {app.id} has {len(logbooks)} logbook entries, expected 8. Skipping.")
                continue
            for i, logbook in enumerate(logbooks):
                logbook.write({
                    'date_from': start_date + timedelta(days=i * 7),
                    'date_to': start_date + timedelta(days=i * 7 + 6),
                })
        self.env.cr.commit()

    def action_check_approved_application(self):
        """Check if the student has an approved application before showing logbooks."""
        _logger.info(f"Checking approved application for user {self.env.user.id}")
        student = self.env['student.student'].search([('user_id', '=', self.env.user.id)], limit=1)
        _logger.info(f"Found student: {student.id if student else 'None'}")
        approved_application = self.env['pt.place.application'].search([
            ('student_id.user_id', '=', self.env.user.id),
            ('state', '=', 'approved')
        ], limit=1)
        _logger.info(f"Found approved application: {approved_application.id if approved_application else 'None'}")
        if not approved_application:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Approved Application',
                    'message': 'You must have an approved PT application to access your logbook entries.',
                    'type': 'warning',
                    'sticky': True,
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Logbook Entries',
            'res_model': 'pt.application.logbook',
            'view_mode': 'kanban,form',
            'domain': [('student_id.user_id', '=', self.env.user.id), ('application_id.state', '=', 'approved')],
            'context': {'default_student_id': student.id if student else False},
        }

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
        # Ensure marks are recomputed after creating a new assessment
        self._compute_assessment_marks()
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

    def bulk_check_plagiarism(self):
        """Recheck plagiarism for all reports with final_report."""
        _logger.info("Starting bulk plagiarism recheck for all PT application reports")
        reports = self.search([('final_report', '!=', False)])
        _logger.info("Found %d reports for recheck: %s", len(reports), [r.id for r in reports])
        for report in reports:
            try:
                if report.report_text:
                    _logger.info("Rechecking report ID %s for student %s", report.id, report.student_name)
                    report.plagiarism_results = report._check_plagiarism(report.report_text)
                    self.env.cr.commit()
                    _logger.info("Updated report ID %s", report.id)
                else:
                    _logger.warning("No report_text for report ID %s", report.id)
            except Exception as e:
                _logger.error("Failed to recheck report ID %s: %s", report.id, e)
                continue
        _logger.info("Bulk plagiarism recheck completed")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Bulk Plagiarism Recheck Completed',
                'message': 'Plagiarism recheck has been performed for all reports with final reports.',
                'type': 'success',
                'sticky': False,
            }
        }


