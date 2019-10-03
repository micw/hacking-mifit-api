#!/usr/bin/env python3

import argparse
import requests
import urllib.parse
import json
import base64
import datetime
import hashlib
import logging

def fail(message):
	print("Error: {}".format(message))
	quit(1)

def main():
	parser = argparse.ArgumentParser(description="Get an app token from a manual mi account login.\n\n"+
		"To login, visit:\nhttps://account.xiaomi.com/oauth2/authorize?skip_confirm=false&client_id=428135909242707968&pt=1&scope=1+6000+16001+20000&redirect_uri=https%3A%2F%2Fapi-mifit-cn.huami.com%2Fhuami.health.loginview.do_not&_locale=de_DE&response_type=code\n\n"+
		"Login and copy the code after 'code=' from the redirect URL.",
		formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--code",required=True,help="Code obtained from oauth login")
	args=parser.parse_args()

	login_url='https://account.huami.com/v2/client/login'
	data={
		'app_name': 'com.xiaomi.hm.health',
		'country_code': 'DE',
		'code': args.code,
		'device_id': '02:00:00:00:00:00',
		'device_model': 'android_phone',
		'app_version': '4.0.9',
		'grant_type': 'request_token',
		'allow_registration': 'false',
		'dn': 'account.huami.com,api-user.huami.com,api-watch.huami.com,api-analytics.huami.com,app-analytics.huami.com,api-mifit.huami.com',
		'third_name': 'xiaomi-hm-mifit',
		'source': 'com.xiaomi.hm.health:4.0.9:8046',
		'lang': 'de',
	}
	response=requests.post(login_url,data=data,allow_redirects=False)
	result=response.json()

	if 'error_code' in result:
		error_code=result['error_code']
		if error_code=='0106':
			fail("The code is invalid or was already used")
		fail("Failed with error code {}".format(error_code))

	print(result);

if __name__== "__main__":
	main()
