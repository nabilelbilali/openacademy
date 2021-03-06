# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class openacademy(models.Model):
#     _name = 'openacademy.openacademy'
#     _description = 'openacademy.openacademy'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
from datetime import timedelta
from odoo import models, fields, api, exceptions
from odoo import tools



from datetime import date
class Course(models.Model):
    _name = 'openacademy.course'
    _description = "OpenAcademy Courses"
    responsible_id = fields.Many2one('res.users',
                               ondelete='set null', string="Responsible", index=True)
    session_ids = fields.One2many(
        'openacademy.session','course_id',string="Sessions")
    instructor_ids = fields.One2many(
        'openacademy.session','course_id',string="Sessions")


    name = fields.Char(string="Title", required=True)
    description = fields.Text()
    price =fields.Integer(compute="price_calcul")
    count = fields.Integer(compute='count_sessions')
    session_count=fields.Integer(compute='session_counting')
    invoice_count=fields.Integer(compute='invoice_counting')

    #factures=fields.One2many('account.move','',string="Invoices")
    #_inherit = 'account.invoice.line'


    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', u"Copy of {}%".format(self.name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.name)
        else:
            new_name = u"Copy of {} ({})".format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)
    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "The title of the course should not be the description"),

        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
    ]

    def price_calcul_my(self):

        Course = self.browse(self.ids)
        print(Course)

        # invoice = self.env['account.move'].create({
        # 'move_type': 'out_invoice',
        # 'invoice_date': fields.Date.today(),
        # 'date': fields.Date.today(),
        # "'invoice_line_ids': [i * {
        #    'quantity': 1,
        #    'name': self.session_ids.name,
        #     'price_unit': price,
        #  } for i in range(self.env['openacademy.session'].search_count([('course_id', '=', self.id)])
        #                    )]
        # })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'quantity': self.env['openacademy.session'].search_count([('course_id', '=', self.id)]),
                'name': self.name,
                'price_unit': self.price,
            })]
        })

    def button_session(self):
        return {
            'name': ('sessions'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'openacademy.session',
            'domain': [('course_id', '=', self.id)],
            'type': 'ir.actions.act_window',
        }

    def button_facture(self):
        return {
            'name': ('invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'domain': [('name', '=', self.name)],
            'type': 'ir.actions.act_window',
        }

    def button_professeures(self):
        pass

    def price_calcul(self):
        for record in self:
            a = 0
            sessions = record.session_ids
            print(sessions)
            for s in sessions:
                a += s.price
                print(a)
            record.price = a

    def session_counting(self):
        for record in self:
            record.session_count = self.env['openacademy.session'].search_count([('course_id', '=', self.id)])

    def invoice_counting(self):
        for record in self:
            record.invoice_count = self.env['account.move.line'].search_count([('name', '=', self.name)])

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""SELECT * FROM openacademy.course""")


class Session(models.Model):
    _name = 'openacademy.session'
    _description = "OpenAcademy Sessions"

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    quantity=fields.Integer()
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    color = fields.Integer()
    instructor_id = fields.Many2one('res.partner', string="Instructor")
    course_id = fields.Many2one('openacademy.course',
        ondelete='cascade', string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')
    end_date = fields.Date(string="End Date", store=True,
        compute='_get_end_date', inverse='_set_end_date')
    attendees_count = fields.Integer(
        string="Attendees count", compute='_get_attendees_count', store=True)

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)



    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats
    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': "Incorrect 'seats' value",
                    'message': "The number of available seats may not be negative",
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': "Too many attendees",
                    'message': "Increase seats or remove excess attendees",
                },
            }
    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = r.start_date + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.duration = (r.end_date - r.start_date).days + 1


    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError("A session's instructor can't be an attendee")



    price =fields.Integer()
    invoice_count_session=fields.Integer(compute="button_facture_counting")
    def button_facture_session(self):
        return {
            'name': ('invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'domain': [('name', '=', self.name)],
            'type': 'ir.actions.act_window',
        }

    def button_facture_counting(self):
        for record in self:
            record.invoice_count_session = self.env['account.move.line'].search_count([('name', '=', self.name)])

    def invocing_session(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'quantity': 1,
                'name': self.name,
                'price_unit': self.price,
            })]
        })




class Instructor(models.Model):
    _name="openacademy.instructor"
    _description='the prof: a teacher who teaches a session '
    id=fields.Integer()
    name = fields.Char(required=True)
    informations = fields.Text()
    course_id=fields.Many2one('openacademy.course')
    session_ids = fields.Many2one('openacademy.session',
        string="Session")
    courses_count=fields.Integer(compute="courses_counting")
    sessions_count=fields.Integer(compute="sessions_counting")


    def button_Courses(self):
        return {
            'name': ('courses of the prof'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'openacademy.course',
            'domain': [('id', '=', self.course_id.id)],
            'type': 'ir.actions.act_window',
        }

    def button_Sessions(self):
        return {
            'name': ('sessions of the prof'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'openacademy.session',
            'domain': [('id', '=', self.session_ids.id)],
            'type': 'ir.actions.act_window',
        }
    def sessions_counting(self):
        for record in self:
            record.sessions_count = self.env['openacademy.session'].search_count([('id', '=', self.session_ids.id)])

    def courses_counting(self):
        for record in self:
            record.courses_count = self.env['openacademy.course'].search_count([('id', '=', self.course_id.id)])


# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

class Report(models.Model):
    _name = 'openacademy.report'
    _description = "OpenAcademy Report"
    _auto = False

    instru = fields.Many2one('res.partner',
                             string="Instructor")  # id many2one et remplacé id dans field de view... (voir pivot de session)
    session_name = fields.Char(readonly=True)
    courseid = fields.Many2many('openacademy.course', string="Course")
    course_name = fields.Char(readonly=True)
    sessionsid = fields.Many2many('openacademy.session', string="Session")
    responsible = fields.Char(readonly=True)
    # aussi resoudre probléme de session unique pour chaque cours

from odoo import models, fields, api

class ComputedModel(models.Model):
    _name = 'test.computed'

    name = fields.Char(compute='_compute_name')
    value = fields.Integer()

    @api.depends('value')
    def _compute_name(self):
        for record in self:
            record.name = "Record with value %s" % record.value

    from odoo import models, fields, api

    class Wizard(models.TransientModel):
        _name = 'openacademy.wizard'
        _description = "Wizard: Quick Registration of Attendees to Sessions"

        def _default_session(self):
            return self.env['openacademy.session'].browse(self._context.get('active_id'))

        session_id = fields.Many2one('openacademy.session',
                                     string="Session", required=True,default=_default_session)
        attendee_ids = fields.Many2many('res.partner', string="Attendees")
