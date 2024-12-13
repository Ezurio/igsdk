#!/usr/bin/python3
#
# Copyright (c) 2024 Ezurio LLC.
#
# IG60 helper script for remotely configuring the LTE APN via EdgeIQ.
#
# Usage: ig60_lte_config.py [APN [TYPE [USERNAME PASSWORD [AUTH]]]]
#
# APN:      APN name
# Type:     Connection type ("ip", "ipv6", or "dual")
# Username: Username
# Password: Password
# Auth:     Authentication type ("pap" or "chap")
#
# When called with no arguments, the APN settings are cleared
# and the modem will connect using the LTE default bearer.
#
# IMPORTANT: The LTE modem is taken offline in order to apply
# the new default settings.  This script will attempt to restore
# the previous settings in case the connection fails, but you
# should verify the APN details before calling this script,
# particularly if there is no other connectivity (WiFi, Ethernet).
#

import dbus
import sys

OFONO_MANAGER_IFACE = 'org.ofono.Manager'
OFONO_MODEM_IFACE = 'org.ofono.Modem'
OFONO_LTE_IFACE = 'org.ofono.LongTermEvolution'

MODEM_ONLINE = 'Online'

LTE_APN = 'DefaultAccessPointName'
LTE_CONNTYPE = 'Protocol'
LTE_USERNAME = 'Username'
LTE_PASSWORD = 'Password'
LTE_AUTH = 'AuthenticationMethod'

def get_proxy(path, obj):
    return dbus.Interface(dbus.SystemBus().get_object('org.ofono', path), obj)

def get_modem_obj():
    manager = get_proxy('/', OFONO_MANAGER_IFACE)
    modems = manager.GetModems()
    return modems[0][0]

def get_modem():
    return get_proxy(get_modem_obj(), OFONO_MODEM_IFACE)

def get_lte():
    return get_proxy(get_modem_obj(), OFONO_LTE_IFACE)

def get_apn_settings():
    modem = get_modem()
    lte = get_lte()
    lte_props = lte.GetProperties()
    apn = lte_props.get(LTE_APN, '')
    conntype = lte_props.get(LTE_CONNTYPE, '')
    username = lte_props.get(LTE_USERNAME, '')
    password = lte_props.get(LTE_PASSWORD, '')
    auth = lte_props.get(LTE_AUTH, '')
    return apn, conntype, username, password, auth

def configure_apn(apn, conntype, username, password, auth):
    modem = get_modem()
    lte = get_lte()
    modem.SetProperty(MODEM_ONLINE, False)
    lte.SetProperty(LTE_APN, apn)
    lte.SetProperty(LTE_CONNTYPE, conntype)
    lte.SetProperty(LTE_USERNAME, username)
    lte.SetProperty(LTE_PASSWORD, password)
    lte.SetProperty(LTE_AUTH, auth)
    modem.SetProperty(MODEM_ONLINE, True)

def failure(msg):
    print(msg)
    sys.exit(1)

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 0:
        apn = args[0]
        if len(args) > 1:
            conntype = args[1]
        else:
            conntype = 'dual'
        if len(args) > 3:
            username = args[2]
            password = args[3]
        else:
            username = ''
            password = ''
        if len(args) > 4:
            auth = args[4]
        else:
            auth = 'none'
        print('Reading current APN settings.')
        try:
            old_apn, old_conntype, old_username, old_password, old_auth = get_apn_settings()
        except:
            failure('Failed to read existing APN settings, exiting.')
        print('Setting APN configuration.')
        try:
            configure_apn(apn, conntype, username, password, auth)
        except:
            try:
                configure_apn(old_apn, old_conntype, old_username, old_password, old_auth)
            except:
                pass
            finally:
                failure('APN configuration failed, reverting.')
    else:
        print('Resetting default APN settings.')
        try:
            configure_apn('', 'dual', '', '', 'none')
        except:
            failure('Failed to reset APN settings.')
    sys.exit(0)

