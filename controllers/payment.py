# -*- coding: utf-8 -*-

import json

from odoo import http
from odoo.http import request
import requests
from .. import defs
from .base import BaseController, UserException
from weixin.pay import WXAppPay
import time
import logging

_logger = logging.getLogger(__name__)
TIMEOUT = 5


def get_order_code(id):
    order_no = str(time.strftime(
        '%Y%m%d%H%M%S', time.localtime(time.time()))) + str(id)
    return order_no


class WxappPayment(http.Controller, BaseController):

    def req_token(self, sub_domain):
        try:
            config = request.env['wxapp.config'].sudo()
            app_id = config.get_config('app_id', sub_domain)
            secret = config.get_config('secret', sub_domain)

            if not app_id or not secret:
                return self.res_err(404)
            params = {}
            url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" % (
                app_id, secret)
            res = requests.post(url)
            return res.json()
        except Exception as e:
            return self.res_err(-1, str(e))

    def get_token(self, sub_domain):
        try:
            ret, entry = self._check_domain(sub_domain)
            if ret:
                return ret

            wxToken = request.env(user=1)['wxapp.token'].search([
                ('sub_domain', '=', sub_domain),
            ])

            if not wxToken:
                token = self.req_token(sub_domain)
                expires_in = time.time() + token['expires_in']
                data = {
                    'access_token': token['access_token'],
                    'expires_in': expires_in,
                    'sub_domain': sub_domain,
                }
                wxToken = request.env(user=1)['wxapp.token'].create(data)
            else:
                if wxToken.expires_in < time.time():
                    token = self.req_token(sub_domain)
                    expires_in = time.time() + token['expires_in']
                    data = {
                        'access_token': token['access_token'],
                        'expires_in': expires_in,
                        'sub_domain': sub_domain,
                    }
                    wxToken.write(data)

            return wxToken.access_token
        except Exception as e:
            return self.res_err(-1, str(e))

    @http.route('/<string:sub_domain>/notify', auth='public', methods=['POST', 'GET'], csrf=False, type='http')
    # 支付回调
    def notify(self, sub_domain, **kwargs):
        # todo 支付回调
        token = self.get_token(sub_domain)
        return self.res_ok([token, kwargs])

    @http.route('/<string:sub_domain>/template-msg/wxa/formId', auth='public', methods=['POST', 'GET'], csrf=False, type='http')
    # 支付成功消息推送
    def formid(self, sub_domain, **kwargs):
        # todo 支付消息推送
        try:
            token = kwargs.pop('token', None)
            formId = kwargs.pop('formId', None)
            orderId = kwargs.pop('orderId', '')
            wxapp_access_token = request.env(user=1)['wxapp.access_token'].search([
                ('token', '=', token),
            ])
            
            if not wxapp_access_token:
                return self.res_err(901)
            saleOrder = request.env(user=1)['sale.order'].search([('id', '=', orderId)])
            if not saleOrder:
                return self.res_err(901)
            saleOrder.write({'customer_status': 'pending'})
            openid = wxapp_access_token.open_id
            access_token = self.get_token(sub_domain)
            pay_goods = '云辅材小程序下单'
            pay_time = str(time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            pay_type = '微信支付'
            pay_fee = 100
            url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token=%s' % access_token
            params = {
                "touser": openid,
                "template_id": "VtZGskB7XJ-EzTsCjR3LpOXJ-f_1OIDgEiZ8X2JWNCU",
                "page": "index",
                "form_id": formId,
                "data": {
                        "keyword1": {
                            "value": saleOrder.name
                        },
                    "keyword2": {
                            "value": pay_goods
                        },
                    "keyword3": {
                            "value": str(saleOrder.total)
                        },
                    "keyword4": {
                            "value": pay_type
                        },
                    "keyword5": {
                            "value": pay_time
                        }
                },
                "emphasis_keyword": "keyword1.DATA"
            }

            res = requests.post(url, json=params)
            return self.res_ok(params)
        except Exception as e:
            _logger.exception(e)
            return self.res_err(-1, str(e))

    @http.route('/<string:sub_domain>/pay/wx/wxapp', auth='public', methods=['POST', 'GET'], csrf=False, type='http')
    # 微信支付统一下单
    def wxPay(self, sub_domain, **kwargs):
        try:
            ret, entry = self._check_domain(sub_domain)
            if ret:
                return ret
            token = kwargs.pop('token', None)
            total_fee = int(float(kwargs.pop('money')) * 100)
            nextAction = kwargs.pop('nextAction', None)
            actionJson = json.loads(nextAction)
            orderId = actionJson['id']
            body = str(orderId)
            out_trade_no = get_order_code(orderId)
            access_token = request.env(user=1)['wxapp.access_token'].search([
                ('token', '=', token),
            ])
            if not access_token:
                return self.res_err(901)
            openid = access_token.open_id
            # return self.res_ok([entry.app_id, entry.wechat_pay_id, entry.wechat_pay_secret, openid])
            wxPay = WXAppPay(entry.app_id, entry.wechat_pay_id,
                             partner_key=entry.wechat_pay_secret, notify_url='http://erp.yunfc.net/yunfc/notify')
            # return self.res_ok([body, out_trade_no, total_fee, openid, wxPay.mch_id])
            res = wxPay.unifiedorder(
                body=body, out_trade_no=out_trade_no, total_fee=total_fee, openid=openid)
            res.update({'orderId': orderId})
            return self.res_ok(res)

        except Exception as e:
            _logger.exception(e)
            return self.res_err(-1, str(e))
