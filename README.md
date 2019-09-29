# Reverse engineering of the Mi Fit API wit the goal to retrieve my stored fitness data

## Tools

- a spare android device
- if android is >=7.1.1
    - magisk installed
    - https://github.com/NVISO-BE/MagiskTrustUserCerts installed and activated
    - alternatively: any other root/su and a tool like "certInstaller [Root]"
- mitmproxy (must be in the same network as the android wifi)


## Toolchain Setup

- install Mi Fit (from playstore or APK)
- run mitmproxy on your PC
- copy the mitmproxy root ca to the android device (can be tricky, easieast way is to use email, usb file transfer or adb push)
- import the cert to the device. you may need to set a device to do so. On Android >7.1.1 with "MagiskTrustUserCerts" module or "certInstaller [Root]"" you also need to reboot afterwards to make cert work as system certificate
- go to the android device's wifi settings, open the wifi connection, advaned option. Add mitmproxy ip and port
- ensure that internet (including https) works through mitmproxy


## Hacking the API

- login in to your Mi Fit account. In my case it's "sign in with email"
- check mitmproxy traffic

### Login process

#### Obtaining an access token

- a POST is sent to https://api-user.huami.com/registrations/[EMAIL-ADDRESS]/tokens
- encoding is URL-Encoded
- the field "password" contains the password in plain text
- the following form fields are required:

```
	'state': 'REDIRECTION',
	'client_id': 'HuaMi',
	'redirect_uri': 'https://s3-us-west-2.amazonws.com/hm-registration/successsignin.html',
	'token': 'access',
	'password': password
```

- the response contains the redirect_uri, followed by some url parameters. The required parameters are "access" which contains an access token and "country_code"

#### Getting API credentials

- a POST ist sent to https://account.huami.com/v2/client/login
- encoding is URL-Encoded
- the following form fields are required:

```
	'app_name': 'com.xiaomi.hm.health',
	'dn': 'account.huami.com,api-user.huami.com,api-watch.huami.com,api-analytics.huami.com,app-analytics.huami.com,api-mifit.huami.com',
	'device_id': '02:00:00:00:00:00',
	'device_model': 'android_phone',
	'app_version': '4.0.9',
	'allow_registration': 'false',
	'third_name': 'huami',
	'grant_type': 'access_token',
	'country_code': country_code,
	'code': access_token,
```

- on success, a JSON structure is returned which contains (beside others): 'login_token', 'app_token' and 'user_id'
- these values are used for further API communication


### Retrieving mi band data

- a GET request is sent to https://api-mifit.huami.com/v1/data/band_data.json
- the pi creadentials also contained a mapping for hosts, e.g. api-mifit.huami.com to api-mifit-de.huami.com. But it seems also to work on the generic hosts 
- parameters are sent as GET params

- the following paremeters are required:

```
	'query_type': 'summary',
	'device_type': 'android_phone',
	'userid': auth_info['token_info']['user_id'], # user_id from API credentials
	'from_date': '2019-01-01',
	'to_date': '2019-12-31',
```

- a header 'apptoken' must be set which contains the app_token from API credentials

- the repsonse is a JSON structure which contains data for every requested day. the field "summary" of each day contains a BASE64 encoded JSON structure.

After decoding, the following structure can be found:

- key "goal": goal (steps) for this day
- key "tz": probably timezone (offset in minutes to GMT)
- key "stp": step data (see below)
- key "slp": sleep data (see below)

#### step data

- key in summary structure is "stp" which has the following properties:
    - ttl: total steps for this day
    - dis: total distance in meters for this day
    - cal: kcals used for this day
    - wk, rn, runDist, runCal: TODO: figure out and verify against mi fit app
    - stage: list individual activities for this day, each with the following properties
        - start: start time (minutes from begin of day. e.g. 460 meansthe 460th minute of the day which is 07:40am)
        - end: end time (minutes from begin of day)
        - step: number of steps
        - dis: distance in meters
        - cal: kcals used
        - mode: detected activity type
            - 1 - walking
            - 7 - normal steps (no sport activity)
            - others needs to be figured out


#### sleep data

- key in summary structure is "slp" which has the following properties:
    - st: start of sleep (epoch seconds)
    - ed: end of sleep (epoch seconds)
    - dp: deep sleep in minutes
    - lt: light sleep in minutes
    - usrSt, usrEd, wc, is, lb, to, dt, rhr, ss: TODO: figure out and verify against mi fit app
    - stage: list individual sleep phases, each with the following properties
        - start: start time (minutes from begin of day. e.g. 460 meansthe 460th minute of the day which is 07:40am)
        - end: end time (minutes from begin of day)
        - mode: sleep type
            - 4 - light sleep
            - 5 - deep sleep
            - others needs to be figured out

# Example implementation:

```
./mifit_api.py  --email me@mydomain.com --password s3cr3t

Logging in with email me@mydomain.com
Obtained access token
Retrieveing mi band data
2019-08-02
v = 5
Total sleep:  07:24 , deep sleep 03:14 , light sleep 04:10 , slept from 2019-08-02 23:51:00 until 2019-08-03 07:15:00
23:51 - 00:00 light sleep
00:01 - 00:35 deep sleep
00:36 - 00:46 light sleep
00:47 - 01:23 deep sleep
01:24 - 02:40 light sleep
02:41 - 03:26 deep sleep
03:27 - 03:50 light sleep
03:51 - 04:10 deep sleep
04:11 - 04:21 light sleep
04:22 - 04:36 deep sleep
04:37 - 04:48 light sleep
04:49 - 05:01 deep sleep
05:02 - 05:45 light sleep
05:46 - 06:03 deep sleep
[...]
Total steps:  1119 , used 27 kcals , walked 757 meters
21:17 - 21:31 338 steps 
21:33 - 21:59 110 steps walking
22:03 - 22:07 153 steps 
22:49 - 22:54 100 steps 
goal = 8000
tz = 3600
2019-08-03
v = 5
[...]
```
