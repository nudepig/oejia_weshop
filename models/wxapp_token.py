# -*- coding: utf-8 -*-

import time

from odoo import http
from odoo import models, fields, api, exceptions


class Token(models.Model):

    _name = 'wxapp.token'
    _description = u'wxapp token'

    # _transient_max_hours = 2

    # allow session to survive for 30min in case user is slow
    sub_domain = fields.Char(required=True, string='sub_domain')
    expires_in = fields.Integer(string='Expires')
    access_token = fields.Char(string='Access Token')

    # @api.model
    # def get_token(self, sub_domain):
    #     record = super(WxAppToken, self).search(['sub_domain','=', sub_domain])
    #     if not record:
    #         record = super(WxAppToken, self).create({'access_token': '123'})
    #     record.write({'access_token': '456'})
    #     return record