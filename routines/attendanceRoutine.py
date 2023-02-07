# -*- coding: utf-8 -*-
import os
import sys
import json
from utils import scan_ip_address

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)
from zk import ZK, const

# Define config variables
with open("config.json") as f:
    data = json.load(f)
    zk_device = data["zk_device"] # Must include 'MAC', 'ip_range' and 'port'
    
ip_address = scan_ip_address(zk_device['ip_range'], zk_device['MAC'])

if ip_address is not None:
    conn = None
    zk = ZK(ip_address, port=int(zk_device['port']), verbose=False, encoding="iso-8859-1")
    try:
        conn = zk.connect()
        conn.disable_device()

        #print ('--- Get User ---')
        users = conn.get_users()
        for user in users:
            user.template = []
            for i in range(10): 
                template = conn.get_user_template(user.uid,i)
                if template is not None: user.template.append(template.template)
                else: 
                    if conn.verbose: print('Finger template {} from user {} not found'.format(i, user.uid))
                    break
            
            privilege = 'User'
            if user.privilege == const.USER_ADMIN: privilege = 'Admin'
            elif user.privilege == const.USER_ENROLLER: privilege = 'Enroller'
            elif user.privilege == const.USER_MANAGER: privilege = 'Manager'
            print ('+ UID #{}'.format(user.uid))
            print ('  Name       : {}'.format(user.name))
            print ('  Privilege  : {}'.format(privilege))
            print ('  Password   : {}'.format(user.password))
            print ('  Group ID   : {}'.format(user.group_id))
            print ('  User  ID   : {}'.format(user.user_id))
            print ('  User fingerprints : {}'.format(len(user.template)))
        
        print ('--- Get Attendance ---')
        attendance = conn.get_attendance()
        i = 0
        for att in attendance:
            i += 1
            print ("ATT {:>6}: uid:{:>3}, user_id:{:>8} t: {}, s:{} p:{}".format(i, att.uid, att.user_id, att.timestamp, att.status, att.punch))
        conn.enable_device()

    except Exception as e:
        print ("Process terminate : {}".format(e))
    finally:
        if conn:
            conn.disconnect()
else: print('Could not find ip_address from MAC and ip_range')
