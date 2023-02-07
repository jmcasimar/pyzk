#!/usr/bin/env python3

# Import directories
import os
import sys
import json
import signal
from datetime import datetime
from itertools import groupby
from src.credentials import parse
from src.utils import scan_ip_address
from src.parseClient import parseClient

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)
from zk import ZK, const

# Define config variables
with open("config.json") as f:
    data = json.load(f)
    zk_device = data["zk_device"] # Must include 'MAC', 'ip_range' and 'port'
    myUbication = {"__type": "Pointer", "className": "Ubication", "objectId": data["ubicationId"]}

try:
    ip_address = zk_device['ip_address']
except:
    ip_address = scan_ip_address(zk_device['ip_range'], zk_device['MAC'])

if ip_address is not None:
    conn = None
    zk = ZK(ip_address, port=int(zk_device['port']), verbose=False, encoding="iso-8859-1")
    try:
        conn = zk.connect()
        conn.disable_device() # Disable device

        #print ('--- Get Attendance ---')
        attendance = conn.get_attendance()

        # If there are new entries
        if len(attendance)>=1:
            # Get attendances per day
            actual_date = attendance[0].timestamp
            att_per_day = []
            myAtt = []
            for att in attendance:
                # If there is a different day
                if att.timestamp.day != actual_date.day:
                    actual_date = att.timestamp
                    # Add new array
                    att_per_day.append(myAtt)
                    myAtt = []
                myObj = {'uid': att.uid, 'user_id': att.user_id, 'timestamp': att.timestamp.isoformat(), 'status': att.status, 'punch': att.punch}
                myAtt.append(myObj)
                print ("uid:{:>3}, user_id:{:>8} t: {}, s:{} p:{}".format(att.uid, att.user_id, att.timestamp, att.status, att.punch))
            att_per_day.append(myAtt)
            if conn.verbose: print('Days recorded', len(att_per_day))

            # Get attendance per day per user
            att_parse = []
            for att in att_per_day:
                myDate = datetime.fromisoformat(att[0]['timestamp'])
                d = datetime(myDate.year, myDate.month, myDate.day, 18, 59, 59, 0)
                if conn.verbose: print('Day {} were registered {} records'.format(d, len(att)))
                myAtt_obj = {}
                for key, group in groupby(att, lambda x: x['user_id']):
                    user_att = list(group)
                    hours_worked = 8
                    times_checked = len(user_att)
                    if times_checked>1:
                        seconds_worked = (datetime.fromisoformat(user_att[-1]['timestamp']) - datetime.fromisoformat(user_att[0]['timestamp'])).total_seconds()
                        hours_worked = seconds_worked/3600
                    myAtt_obj[key] = {'att': user_att, 'hours_worked': hours_worked, 'times_checked': times_checked}
                att = {"attendance": myAtt_obj, "ubication": myUbication, 'realDate': {"__type": "Date", "iso": d.isoformat()}}
                if conn.verbose: print(att)
                att_parse.append(att)

            # Config client parse
            client = parseClient(parse['server'], 
                                parse['appId'], 
                                parse['restKey'], 
                                mountPath = parse['mountPath'])

            res = client.createObject("Attendance", att_parse)
            delete = False
            if type(res) is list:
                if all('success' in r for r in res): delete = True
            elif not 'error' in res: delete = True

            if delete:
                if conn.verbose: print(res)
                conn.clear_attendance()
            else: print('Something goes wrong uploading attendance to database')
        else: print('There is not attendance entries in device')

        conn.enable_device() # Enable device

    except Exception as e:
        print ("Process terminate : {}".format(e))
    finally:
        if conn:
            conn.disconnect()
else: print('Could not find ip_address from MAC and ip_range')