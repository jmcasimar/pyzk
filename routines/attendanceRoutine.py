# -*- coding: utf-8 -*-
import os
import sys

CWD = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CWD)
sys.path.append(ROOT_DIR)

from zk import ZK, const

conn = None
zk = ZK('192.168.7.60', port=4370, verbose=False, encoding="iso-8859-1")
try:
    conn = zk.connect()
    conn.disable_device()

    #print ('--- Get User ---')
    users = conn.get_users()
    """
    for user in users:
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
    """

    # Fingerprint export not working
    """
    print ('--- Get Templates (Fingers) ---')
    template = conn.get_templates()
    i = 0
    for tmp in template:
        i += 1
        print ('+ Template #{}- {}'.format(i, tmp))
    """

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
