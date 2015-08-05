#coding:utf-8
__author__ = 'zhanglong'

import rsa
import alipay_config
import base64

SIGN_TYPE = "SHA-1"
import urllib
import requests
import hashlib


def params_filter(params):
    """
    去掉不需要验证前面的参数
    :param params:
    :return:
    """
    """
    :param params:
    :return:
    """
    ret = {}
    for key, value in params.items():
        if key == "sign" or key == "sign_type" or value == "":
            continue
        ret[key] = value
    return ret


def query_to_dict(query):
    """
    将query string转换成字典
    :param query:
    :return:
    """
    res = {}
    k_v_pairs = query.split("&")
    for item in k_v_pairs:
        sp_item = item.split("=", 1)  #注意这里，因为sign秘钥里面肯那个包含'='符号，所以splint一次就可以了
        key = sp_item[0]
        value = sp_item[1]
        res[key] = value

    return res


def params_to_query(params, quotes=False, reverse=False):
    """
        生成需要签名的字符串
    :param params:
    :return:
    """
    """
    :param params:
    :return:
    """
    query = ""
    for key in sorted(params.keys(), reverse=reverse):
        value = params[key]
        if quotes == True:
            query += str(key) + "=\"" + str(value) + "\"&"
        else:
            query += str(key) + "=" + str(value) + "&"
    query = query[0:-1]
    return query


def make_sign(message):
    """
    签名
    :param message:
    :return:
    """
    private_key = rsa.PrivateKey._load_pkcs1_pem(alipay_config.RSA_PRIVATE)
    sign = rsa.sign(message, private_key, SIGN_TYPE)
    b64sing = base64.b64encode(sign)
    return b64sing

def make_md5_sign(message):
    m = hashlib.md5()
    m.update(message)
    m.update(alipay_config.key)
    return m.hexdigest()


def check_sign(message, sign):
    """
    验证自签名
    :param message:
    :param sign:
    :return:
    """
    sign = base64.b64decode(sign)
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(alipay_config.RSA_PUBLIC)
    return rsa.verify(message, sign, pubkey)


def check_ali_sign(message, sign):
    """
    验证ali签名
    :param message:
    :param sign:
    :return:
    """
    sign = base64.b64decode(sign)
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(alipay_config.RSA_ALIPAY_PUBLIC)
    res = False
    try:
        res = rsa.verify(message, sign, pubkey)
    except Exception as e:
        print e
        res = False
    return res


def make_payment_request(params_dict):
    """
    构造一个支付请求的信息，包含最终结果里面包含签名
    :param params_dict:
    :return:
    """
    query_str = params_to_query(params_dict, quotes=True) #拼接签名字符串
    sign = make_sign(query_str) #生成签名
    sign = urllib.quote_plus(sign)
    res = "%s&sign=\"%s\"&sign_type=\"RSA\"" % (query_str, sign)
    return res




def verify_alipay_request_sign(params_dict):
    """
    验证阿里支付回调接口签名
    :param params_dict: 阿里回调的参数列表
    :return:True or False
    """
    sign = params_dict['sign']
    params = params_filter(params_dict)
    message = params_to_query(params, quotes=False, reverse=False)
    check_res = check_ali_sign(message, sign)
    return check_res


def verify_from_gateway(params_dict):
    """
    从阿里网管验证请求是否正确
    :param params_dict:
    :return:
    """
    ali_gateway_url = "https://mapi.alipay.com/gateway.do?service=notify_verify&partner=%(partner)d&notify_id=%(notify_id)s"
    notify_id = params_dict["notify_id"]
    partner = alipay_config.partner_id
    ali_gateway_url = ali_gateway_url % {"partner": partner, "notify_id": notify_id}
    res = requests.get(ali_gateway_url)
    #    res_dict = encoder.XML2Dict.parse(res.text)
    if res.text == "true":
        return True
    return False


#test
def test():
    params = {"a": 1, "b": 2, "c": "", 1: 1, "sign": "asdfasdfas", "sign_type": "rsa"}
    after_params = params_filter(params)
    assert after_params == {"a": 1, "b": 2, 1: 1}
    query = params_to_query(after_params)

    assert query == '1=1&a=1&b=2'
    print query

    query2 = params_to_query(after_params, quotes=True)
    assert query2 == '1="1"&a="1"&b="2"'
    print query2

    sign = make_sign(query)
    #print sign
    sign_res = check_sign(query, sign)
    assert sign_res == True

    check_signa = "body=商品描述&buyer_email=zhanglwork@gmail.com&buyer_id=2088102716951071&discount=0.00&gmt_create=2015-07-13 10:28:00&gmt_payment=2015-07-13 10:28:01&is_total_fee_adjust=N&notify_id=83ee2b993b46d3f5d1d27b9078199d062e&notify_time=2015-07-13 10:28:01&notify_type=trade_status_sync&out_trade_no=1WZ6ZYT9VYCTLN6&payment_type=1&price=0.01&quantity=1&seller_email=xiaowenwen@7500.com.cn&seller_id=2088021072549071&sign=H5VGZ63LYr3f9819ABuBuaxzRVOx5u3Ku3BI661jkW5gisD1XMc4PdV6bfI/5EIEFQvmSKLADYG3I/8N8Ty5eu/xsrcQXjsVC3Zr3wLOXaDnYh8Ale2crDoIQjgUrbg4d8csovBrJV9Fi+/SCM2/EXPxlO0qrilY/EpKYOczzZ8=&sign_type=RSA&subject=商品测试&total_fee=0.01&trade_no=2015071300001000070073886063&trade_status=TRADE_SUCCESS&use_coupon=N"

    """
  payment_url  body=商品描述&buyer_email=zhanglwork@gmail.com&buyer_id=2088102716951071&discount=0.00&gmt_create=2015-07-13 17:10:23&is_total_fee_adjust=Y&notify_id=a4b691fca6f6f79e816fe022e398d2532e&notify_time=2015-07-13 17:10:23&notify_type=trade_status_sync&out_trade_no=OWYNN72PRTU2G81&payment_type=1&price=0.10&quantity=1&seller_email=xiaowenwen@7500.com.cn&seller_id=2088021072549071&sign=oX0I0LR7YGH96d3fZY9MfLj7BlAWclwVR3kK5XMgmoWcjFTpclB6tXssL81a+JOsKP0bcPsbH3dygMjjCVZHnHOpArs0tzLutjj00XnqH8uXEAItTPs2Hf/ld3TIZqsdXYBfVHtZaiPko/CgN8VQwjjITW1IRIY5JTE/MWidE8A=&sign_type=RSA&subject=商品测试&total_fee=0.10&trade_no=2015071300001000070073922535&trade_status=WAIT_BUYER_PAY&use_coupon=N
[I 150713 17:10:23 web:1728] 200 POST /consumer/api/v1/alipay_callback (127.0.0.1) 1.21ms
payment_url  body=商品描述&buyer_email=zhanglwork@gmail.com&buyer_id=2088102716951071&discount=0.00&gmt_create=2015-07-13 17:10:23&gmt_payment=2015-07-13 17:10:24&is_total_fee_adjust=N&notify_id=4c8d6808aac61d3ead5cd1bb187374e72e&notify_time=2015-07-13 17:10:24&notify_type=trade_status_sync&out_trade_no=OWYNN72PRTU2G81&payment_type=1&price=0.10&quantity=1&seller_email=xiaowenwen@7500.com.cn&seller_id=2088021072549071&sign=KRffFX0OvuxQpusduxvMaJ0f6sVmY8Ta8go969W+sKkypkt8SoUTXpJ5jjysa+/y8CTazBd+K+1Co9my/RswoDBjjspupLiuU0QcrNDDIBPPathk6tEhv8/16CF+IFbn1HoPKVjeHheuBLzCyiEdveqN7ORk/2T/Q9KG0Qqqs/I=&sign_type=RSA&subject=商品测试&total_fee=0.10&trade_no=2015071300001000070073922535&trade_status=TRADE_SUCCESS&use_coupon=N

    """

    check_signa = "body=hsh_shop&buyer_email=ma.hongwei@foxmail.com&buyer_id=2088702056383644&discount=0.00&gmt_create=2015-07-28 19:56:11&is_total_fee_adjust=Y&notify_id=1f124ba6791b3fadfe0734e9345b00b75k&notify_time=2015-07-28 19:56:11&notify_type=trade_status_sync&out_trade_no=1438084559&payment_type=1&price=0.01&quantity=1&seller_email=xiaowenwen@7500.com.cn&seller_id=2088021072549071&sign=WhHQeslDI0YtWdPmXIvvsB9KBZza5Mrzy1AldAq3f6cNP4ebMdMhoXLHAzu9oujm4UxOmTZX60/suYc7ciqea5LCsJR55yUlf4mxrHYqMkYr9+Xt2r/nKaEDe3AXEQHFl+KHYrNiPm35WCmz7rsiTv5p0X3SWK5YhEWT9ycYoHU=&sign_type=RSA&subject=corp_order&total_fee=0.01&trade_no=2015072800001000640056773075&trade_status=WAIT_BUYER_PAY&use_coupon=N"

    check_signa = "body=hsh_shop&buyer_email=ma.hongwei@foxmail.com&buyer_id=2088702056383644&discount=0.00&gmt_create=2015-07-28 19:56:11&gmt_payment=2015-07-28 19:56:11&is_total_fee_adjust=N&notify_id=f6124d74bab89c36a7b3be29285110d25k&notify_time=2015-07-28 19:56:11&notify_type=trade_status_sync&out_trade_no=1438084559&payment_type=1&price=0.01&quantity=1&seller_email=xiaowenwen@7500.com.cn&seller_id=2088021072549071&sign=NFQvSMX3NPxRarKeQ4uJYfnL0z4Kx/bMvI6GbWJUNXRrEWHJ+PnLqiOCvy1EuO+doVBxiwL8acHOFSxyXBnevVG+2cq10YMTvTVet1ouhQNrL6WDZpqKC6TSjq8SRDvQooi9Kjeee4PuFJ6rnkFhRIeFebshLVi7MX3E3x+f808=&sign_type=RSA&subject=corp_order&total_fee=0.01&trade_no=2015072800001000640056773075&trade_status=TRADE_SUCCESS&use_coupon=N"

    params = query_to_dict(check_signa)
    sign = params['sign']
    #sign = sign.decode('utf-8')
    params = params_filter(params)
    message = params_to_query(params, quotes=False, reverse=False)
    check_res = check_ali_sign(message, sign)
    assert check_res == True
    res = verify_from_gateway({"partner": alipay_config.partner_id, "notify_id": params["notify_id"]})
    assert res == False


def test_refund():
    trade_order = "2015073000001000860056086838"














