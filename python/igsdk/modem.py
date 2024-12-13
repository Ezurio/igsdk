#
# modem.py
#
# Modem API for Sentrius IG60 devices
#
import dbus
import dbus.exceptions
import threading
import dbus.mainloop.glib
import logging

import sys
PYTHON3 = sys.version_info >= (3, 0)
if PYTHON3:
    from gi.repository import GObject as gobject
    from gi.repository import GLib as glib
else:
    import gobject

OFONO='org.ofono'
OFONO_MANAGER_IFACE='org.ofono.Manager'
OFONO_MODEM_IFACE='org.ofono.Modem'
OFONO_SIM_IFACE='org.ofono.SimManager'
OFONO_CONNMAN_IFACE='org.ofono.ConnectionManager'
OFONO_CONNECTION_IFACE='org.ofono.ConnectionContext'
OFONO_NETREG_IFACE='org.ofono.NetworkRegistration'

def _get_ofono_proxy(path, iface):
    return dbus.Interface(dbus.SystemBus().get_object(OFONO, path), iface)

# Query LTE modem, SIM, and network properties using Ofono APIs
# For more information, see:
# https://git.kernel.org/pub/scm/network/ofono/ofono.git/tree/doc

def get_modem_info():
    result = None
    try:
        manager = _get_ofono_proxy('/', OFONO_MANAGER_IFACE)
        modems = manager.GetModems()
        if modems is None or len(modems) < 1:
            return None
        modem = _get_ofono_proxy(modems[0][0], OFONO_MODEM_IFACE)
        modem_props = modem.GetProperties()
        modem_interfaces = modem_props['Interfaces']
        result = {}
        result['modem'] = {}
        result['modem']['IMEI'] = '%s' % modem_props.get('Serial', '')
        if OFONO_SIM_IFACE in modem_interfaces:
            sim = _get_ofono_proxy(modems[0][0], OFONO_SIM_IFACE)
            sim_props = sim.GetProperties()
            result['sim'] = {}
            result['sim']['IMSI'] = '%s' % sim_props.get('SubscriberIdentity', '')
            result['sim']['ICCID'] = '%s' % sim_props.get('CardIdentifier', '')
            result['sim']['MobileCountryCode'] = '%s' % sim_props.get('MobileCountryCode', '')
            result['sim']['MobileNetworkCode'] = '%s' % sim_props.get('MobileNetworkCode', '')
            result['sim']['Numbers'] =  []
            for n in sim_props.get('SubscriberNumbers', [])[:]:
                result['sim']['Numbers'].append('%s' % n)
        if OFONO_NETREG_IFACE in modem_interfaces:
            net = _get_ofono_proxy(modems[0][0], OFONO_NETREG_IFACE)
            net_props = net.GetProperties()
            result['net'] = {}
            result['net']['Operator'] = '%s' % net_props.get('Name', '')
            result['net']['Technology'] = '%s' % net_props.get('Technology', '')
            result['net']['Strength'] = int(net_props.get('Strength', 0))
            result['net']['MobileCountryCode'] = '%s' % net_props.get('MobileCountryCode', '')
            result['net']['MobileNetworkCode'] = '%s' % net_props.get('MobileNetworkCode', '')
            result['net']['LocationAreaCode'] = '%s' % int(net_props.get('LocationAreaCode', -1))
            result['net']['CellId'] = '%s' % int(net_props.get('CellId', -1))
        if OFONO_CONNMAN_IFACE in modem_interfaces:
            connman = _get_ofono_proxy(modems[0][0], OFONO_CONNMAN_IFACE)
            connman_props = connman.GetProperties()
            result['connection'] = {}
            result['connection']['Attached'] = bool(connman_props['Attached'])
            ctxs = connman.GetContexts()
            if ctxs and len(ctxs) > 0:
                ctx = _get_ofono_proxy(ctxs[0][0], OFONO_CONNECTION_IFACE)
                ctx_props = ctx.GetProperties()
                result['connection']['APN'] = '%s' % ctx_props.get('AccessPointName', '')
                if 'Settings' in ctx_props:
                    if 'Address' in ctx_props['Settings']:
                        result['connection']['Address'] = '%s' % ctx_props['Settings']['Address']
    except dbus.exceptions.DBusException as e:
        pass
    return result
