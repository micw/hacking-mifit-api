#!/usr/bin/env python3

import argparse
import requests
import urllib.parse
import json
import base64
import datetime

def fail(message):
	print("Error: {}".format(message))
	quit(1)

def mifit_auth_email(email,password):
	print("Logging in with email {}".format(email))
	auth_url='https://api-user.huami.com/registrations/{}/tokens'.format(urllib.parse.quote(email))
	data={
		'state': 'REDIRECTION',
		'client_id': 'HuaMi',
		'redirect_uri': 'https://s3-us-west-2.amazonws.com/hm-registration/successsignin.html',
		'token': 'access',
		'password': password,
	}
	response=requests.post(auth_url,data=data,allow_redirects=False)
	response.raise_for_status()
	redirect_url=urllib.parse.urlparse(response.headers.get('location'))
	response_args=urllib.parse.parse_qs(redirect_url.query)
	if ('access' not in response_args):
		fail('No access token in response')
	if ('country_code' not in response_args):
		fail('No country_code in response')

	print("Obtained access token")
	access_token=response_args['access'];
	country_code=response_args['country_code'];
	return mifit_login_with_token({
		'grant_type': 'access_token',
		'country_code': country_code,
		'code': access_token,
	})

def mifit_login_with_token(login_data):
	login_url='https://account.huami.com/v2/client/login'
	data={
		'app_name': 'com.xiaomi.hm.health',
		'dn': 'account.huami.com,api-user.huami.com,api-watch.huami.com,api-analytics.huami.com,app-analytics.huami.com,api-mifit.huami.com',
		'device_id': '02:00:00:00:00:00',
		'device_model': 'android_phone',
		'app_version': '4.0.9',
		'allow_registration': 'false',
		'third_name': 'huami',
	}
	data.update(login_data)
	response=requests.post(login_url,data=data,allow_redirects=False)
	result=response.json()
	return result;

def minutes_as_time(minutes):
	return "{:02d}:{:02d}".format((minutes//60)%24,minutes%60)

def dump_sleep_data(day, slp):
	print("Total sleep: ",minutes_as_time(slp['lt']+slp['dp']),
		", deep sleep",minutes_as_time(slp['dp']),
		", light sleep",minutes_as_time(slp['lt']),
		", slept from",datetime.datetime.fromtimestamp(slp['st']),
		"until",datetime.datetime.fromtimestamp(slp['ed']))
	if 'stage' in slp:
		for sleep in slp['stage']:
			if sleep['mode']==4:
				sleep_type='light sleep'
			elif sleep['mode']==5:
				sleep_type='deep sleep'
			else:
				sleep_type="unknown sleep type: {}".format(sleep['mode'])
			print(format(minutes_as_time(sleep['start'])),"-",minutes_as_time(sleep['stop']),
				sleep_type)

def dump_step_data(day, stp):
	print("Total steps: ",stp['ttl'],", used",stp['cal'],"kcals",", walked",stp['dis'],"meters")

	for activity in stp['stage']:
		if activity['mode']==1:
			activity_type=''
		elif activity['mode']==7:
			activity_type='walking'
		else:
			activity_type="unknown activity type: {}".format(activity['mode'])
		print(format(minutes_as_time(activity['start'])),"-",minutes_as_time(activity['stop']),
			activity['step'],'steps',activity_type)

def get_band_data(auth_info):
	print("Retrieveing mi band data")
	band_data_url='https://api-mifit.huami.com/v1/data/band_data.json'
	headers={
		'apptoken': auth_info['token_info']['app_token'],
	}
	data={
		'query_type': 'summary',
		'device_type': 'android_phone',
		'userid': auth_info['token_info']['user_id'],
		'from_date': '2019-01-01',
		'to_date': '2019-12-31',
	}
	response=requests.get(band_data_url,params=data,headers=headers)
	for daydata in response.json()['data']:
		day = daydata['date_time']
		print(day)
		summary=json.loads(base64.b64decode(daydata['summary']))
		for k,v in summary.items():
			if k=='stp':
				dump_step_data(day,v)
			elif k=='slp':
				dump_sleep_data(day,v)
			else:
				print(k,"=",v)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--email",required=True,help="email address for login")
	parser.add_argument("--password",required=True,help="password for login")
	args=parser.parse_args()
	auth_info=mifit_auth_email(args.email,args.password)
	get_band_data(auth_info)


if __name__== "__main__":
	main()
