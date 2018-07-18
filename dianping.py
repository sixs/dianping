#encoding:utf-8
"""
@Author: sixseven 
@Date: 2018-05-31 17:14:11 
@Last Modified by: sixseven 
@Last Modified time: 2018-05-31 17:14:11 
@desc: 大众点评验证码加密破解
"""
import PyV8
import os
import requests
from copy import deepcopy
from random import random
import math
import time
import re
import json

jsctx = PyV8.JSContext()
jsctx.enter()
js_file_path = os.path.join(os.path.dirname(__file__), 'dianping.js')
jsctx.eval(open(js_file_path).read().decode('utf-8'))

session = requests.Session()
headers = {
    'Host': 'www.dianping.com',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0',
}       
data_headers = deepcopy(headers)
proxies = {
    
}

def get_hcv():
    """
    计算cookies中的_hc.v
    """
    def n():
        def n():
            return str(hex(int(65536 * (1 + random()))))[3:]
        return '-'.join([n()+n(), n(), n(), n(), n()+n()+n()])
    def i():
        return n() + '.' + str(int(time.time()))
    return i()

def get_captcha_url(request_code):
    """
    计算captcha验证码
    """
    return jsctx.eval('getCaptchaUrl')(request_code)

def download_captcha(captcha_url):
    """
    下载验证码
    """
    captcha_headers = deepcopy(headers)
    captcha_headers.update({
        'Host': 'verify.meituan.com'
    })
    req = session.get(captcha_url, headers=captcha_headers, proxies=proxies)
    with open('./captcha.jpg', 'wb') as fp:
        fp.write(req.content)

def get_token(request_code):
    """
    计算token
    """
    return jsctx.eval('getToken')(request_code)

def get_data(data_url, is_first):
    """
    爬取点评数据
    """
    if is_first:
        data_headers.update({
            'Cookie': '_hc.v={};'.format(get_hcv())
        })
    req = session.get(data_url, headers=data_headers,
                      allow_redirects=False, proxies=proxies)
    req.encoding = "utf-8"
    status_code = req.status_code
    if status_code == 200:
        return (status_code, req.text)
    elif status_code == 302 and 'Location' in req.headers:
        return (status_code, req.headers['Location'])
    return (status_code, 'code = {}'.format(status_code))


def verify_captcha(verify_page_url, data_url):
    """
    发送验证码
    """
    request_code_match = re.findall(
        r'requestCode=([0-9a-z]{32})&', verify_page_url)
    if request_code_match:
        request_code = request_code_match[0]
        captcha_url = get_captcha_url(request_code)
        download_captcha(captcha_url)

        verify_url = 'https://verify.meituan.com/v2/ext_api/spiderindefence/verify?id=1'
        headers = {
            'Host': 'verify.meituan.com',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0',
            'Referer': 'https://verify.meituan.com/v2/web/general_page?action=spiderindefence&requestCode=ae02af4518124c56a05a6e46a7f50acb&platform=1&adaptor=auto&succCallbackUrl=https%3A%2F%2Foptimus-mtsi.meituan.com%2Foptimus%2FverifyResult%3ForiginUrl%3Dhttp%253A%252F%252Fwww.dianping.com%252Fshop%252F93482327&theme=dianping',
        }
        captcha_code = raw_input('输入验证码：')
        _token = jsctx.eval('getToken')(request_code)
        data = {
            'id': 71,
            'request_code': request_code,
            'captchacode': captcha_code,
            '_token': _token
        }
        req = session.post(verify_url, headers=headers,
                            data=data, proxies=proxies)
        try:
            json_data = json.loads(req.text)
            if 'status' in json_data:
                if json_data['status'] == 1:
                    print('verify captcha_code succeed')
                    response_code = json_data['data']['response_code']
                    (status_code, result) = verify_result(data_url, request_code, response_code)
                    if status_code == 200:
                        print('verify_result succeed')
                        print(get_data(data_url, False))
                    else:
                        print('verify_result failed', status_code, result)
                else:
                    print(json_data)

        except:
            print(req.text)

def verify_result(origin_url, request_code, response_code):
    """
    验证验证码是否通过
    """
    verify_result_url = 'https://optimus-mtsi.meituan.com/optimus/verifyResult'
    verify_result_headers = deepcopy(headers)
    verify_result_headers.update({
        'Host': 'optimus-mtsi.meituan.com',
    })
    params = {
        'originUrl': origin_url,
        'request_code': request_code,
        'response_code': response_code
    }
    req = session.get(
        verify_result_url, headers=verify_result_headers, params=params, 
        allow_redirects=False, proxies=proxies)
    if req.status_code == 302:
        location = req.headers['Location']
        req = session.get(location, headers=verify_result_headers, allow_redirects=False,
                            proxies=proxies)
        return (req.status_code, req.headers)

def main():

    data_url = 'http://www.dianping.com/shop/93482327'
    (status_code, result) = get_data(data_url, True)
    if status_code == 200:
        print(result)
    elif status_code == 302:
        location = result
        verify_captcha(location, data_url)

if __name__ == '__main__':
    main()
