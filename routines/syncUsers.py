#!/usr/bin/env python3

# Import directories
import os
import sys
import json
import base64
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
        conn.disable_device()

        #print ('--- Get User ---')
        users = conn.get_users()
        newUsers = []
        for user in users:
            privilege = 'user'
            if user.privilege == const.USER_ADMIN: privilege = 'admin'
            elif user.privilege == const.USER_ENROLLER: privilege = 'enroller'
            elif user.privilege == const.USER_MANAGER: privilege = 'manager'

            # Get fingerprints
            user.template = []
            for i in range(10): 
                template = conn.get_user_template(user.uid,i)
                if template is not None: user.template.append(list(template.template))
                else: 
                    if conn.verbose: print('Finger template {} from user {} not found'.format(i, user.uid))
                    break
            
            # Config client parse
            client = parseClient(parse['server'], 
                                parse['appId'], 
                                parse['restKey'], 
                                mountPath = parse['mountPath'])

            # Check if user exist in database
            res = client.query('Collaborator', where={'accessId': user.user_id})
            # Add user if it does not exists
            if(len(res['results'])==0):
                newUsers.append({ 'name': user.name, 'accessId': user.user_id, 'accessPrivilege': privilege, 'accessFingerprints': user.template})
                print('New user added to database')
                print ('+ UID #{}'.format(user.uid))
                print ('  Name       : {}'.format(user.name))
                print ('  Privilege  : {}'.format(privilege))
                print ('  Password   : {}'.format(user.password))
                print ('  Group ID   : {}'.format(user.group_id))
                print ('  User  ID   : {}'.format(user.user_id))
                print ('  User fingerprints : {}'.format(len(user.template)))

        if len(newUsers)>0: 
            res = client.createObject('Collaborator', newUsers)
            if all('success' in r for r in res): print("{} users were created in database".format(len(newUsers)))
        else: print('There are not new users')

    except Exception as e:
        print ("Process terminate : {}".format(e))
    finally:
        if conn:
            conn.disconnect()
else: print('Could not find ip_address from MAC and ip_range')
