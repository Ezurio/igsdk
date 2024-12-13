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
import json

import sys
PYTHON3 = sys.version_info >= (3, 0)
if PYTHON3:
    from gi.repository import GObject as gobject
    from gi.repository import GLib as glib
else:
    import gobject

PROV_SVC = 'com.lairdtech.IG.ProvService'
PROV_IFACE = 'com.lairdtech.IG.ProvInterface'
PROV_OBJ = '/com/lairdtech/IG/ProvService'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

PROVISION_INTERMEDIATE_TIMEOUT = 2
PROVISION_TIMER_MS = 500

PROV_COMPLETE_SUCCESS = 0
PROV_UNPROVISIONED = 1
PROV_INPROGRESS_DOWNLOADING = 2
PROV_INPROGRESS_APPLYING = 3
PROV_FAILED_INVALID = -1
PROV_FAILED_CONNECT = -2
PROV_FAILED_AUTH = -3
PROV_FAILED_TIMEOUT = -4
PROV_FAILED_NOT_FOUND = -5
PROV_FAILED_BAD_CONFIG = -6

class ProvManager(threading.Thread):
    """
    Class that encapsulates the prov API functionality
    """
    def __init__(self, provisioning_status_callback = None):
        self.logger = logging.getLogger(__name__)
        self.loop = None

        # Set up DBus loop
        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        if PYTHON3:
            self.loop = glib.MainLoop()
        else:
            self.loop = gobject.MainLoop()
            gobject.threads_init()

        # Get DBus objects
        self.prov = dbus.Interface(dbus.SystemBus().get_object(PROV_SVC, PROV_OBJ), PROV_IFACE)

        # Register signal handlers if using callback
        self.prov.connect_to_signal('StateChanged', self.state_changed)

        self.logger.info('Prov Manager starting.')
        super(ProvManager, self).__init__()

        # Save custom callbacks with the client
        self.provisioning_status_callback = provisioning_status_callback
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

    def state_changed(self, state):
        if state == PROV_COMPLETE_SUCCESS:
            self.logger.info('Provisioning State: Successful')
        elif state == PROV_UNPROVISIONED:
            self.logger.info('Provisioning State: Unprovisioned')
        elif state == PROV_INPROGRESS_DOWNLOADING:
            self.logger.info('Provisioning State: Downloading')
        elif state == PROV_INPROGRESS_APPLYING:
            self.logger.info('Provisioning State: Applying')
        elif state == PROV_FAILED_INVALID:
            self.logger.info('Provisioning State: Failed Invalid')
        elif state == PROV_FAILED_CONNECT:
            self.logger.info('Provisioning State: Failed Connect')
        elif state == PROV_FAILED_AUTH:
            self.logger.info('Provisioning State: Failed Auth')
        elif state == PROV_FAILED_TIMEOUT:
            self.logger.info('Provisioning State: Failed Timeout')
        elif state == PROV_FAILED_NOT_FOUND:
            self.logger.info('Provisioning State: Failed Not Found')
        elif state == PROV_FAILED_BAD_CONFIG:
            self.logger.info('Provisioning State: Failed Bad Config')
        else:
            self.logger.info('Provisioning Failed')
        if self.provisioning_status_callback is not None:
            self.provisioning_status_callback(state)

    def start_core_download(self, data):
        """
        Start a download of the green grass core, but wait to apply it
        The data dictionary fields include
        "url" : "http link to JSON Descriptor of Greengrass Core tarball"
        "username" : "username to access JSON Descriptor"
        "password" : "password to access JSON Descriptor"
        """
        self.logger.info('Starting the core download')
        data = json.loads(data)
        return self.prov.StartCoreDownload(data['url'], data)

    def perform_core_update(self):
        """
        Install the greengrass core binary
        """
        self.logger.info('Performing the core update')
        return self.prov.PerformCoreUpdate()




