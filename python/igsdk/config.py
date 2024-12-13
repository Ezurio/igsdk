#
# config.py
#
# Config API for Sentrius IG devices
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

IGCONFD_SVC = 'com.lairdtech.security.ConfigService'
IGCONFD_IFACE = 'com.lairdtech.security.ConfigInterface'
IGCONFD_PUBLIC_IFACE = 'com.lairdtech.security.public.ConfigInterface'
IGCONFD_OBJ = '/com/lairdtech/security/ConfigService'

#
# Wireless profile activation status from Config Service
#
ACTIVATION_SUCCESS = 0
ACTIVATION_PENDING = 1
ACTIVATION_INVALID = -1
ACTIVATION_FAILED_AUTH = -3
ACTIVATION_FAILED_NETWORK = -2
ACTIVATION_NO_CONN = -5
ACTIVATION_NO_SIM = -8

#
# AP scanning vaues
#
AP_SCANNING_SUCCESS = 0
AP_SCANNING = 1

class ConfigManager(threading.Thread):
    """Class that encapsulates the config API functionality
    """
    def __init__(self,  lte_status_callback = None):
        self.logger = logging.getLogger(__name__)
        self.loop = None

        self.lte_status_callback = lte_status_callback

        # Set up DBus loop
        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        if PYTHON3:
            self.loop = glib.MainLoop()
        else:
            self.loop = gobject.MainLoop()
            gobject.threads_init()

        # Get DBus objects
        self.conf = dbus.Interface(dbus.SystemBus().get_object(IGCONFD_SVC, IGCONFD_OBJ), IGCONFD_IFACE)

        # Register signal handlers if using callback
        self.conf.connect_to_signal('LTEStatusChanged', self.cb_lte)

        self.logger.info('Config Manager starting.')
        super(ConfigManager, self).__init__()
        # Run main loop if using callback
        self.start()

    def run(self):
        """Method to run the DBus main loop (on a thread)
        """
        self.logger.info('Starting main loop.')
        self.loop.run()
        self.logger.info('Main loop has exited.')

    def quit_loop(self):
        self.logger.info('Quitting')
        if self.loop:
            self.loop.quit()

    def cb_lte(self, status):
        if status == ACTIVATION_SUCCESS:
            self.logger.info('Activation successful')
        elif status == ACTIVATION_PENDING:
            self.logger.info('Activation pending')
        else:
            self.logger.info('Activation failed')
        # callback return the activation status
        if self.lte_status_callback is not None:
            self.lte_status_callback(status)

    def connect_lte(self, config):
        """Send a command to the config service to initiate an LTE Connection
        """
        self.logger.info('Connecting to LTE')
        self.conf.ConnectLTE(config)

    def update_aps(self, config):
        """Modify the Wi-Fi profiles in NetworkManagers connection list
        """
        self.logger.info('Updating APs')
        self.conf.SetWifiConfigurations(config)



