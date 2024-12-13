#
# device.py
#
# Device API for Sentrius IG devices
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

DEVICE_SERVICE='com.lairdtech.device.DeviceService'
DEVICE_SERVICE_OBJ_PATH='/com/lairdtech/device/DeviceService'
DEVICE_SERVICE_PUBLIC_IFACE='com.lairdtech.device.public.DeviceInterface'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
EXT_STORAGE_STATUS_PROP = 'ExtStorageStatus'
EXT_STORAGE_PATH_PROP = 'ExtStoragePath'
INT_STORAGE_PATH_PROP = 'IntStoragePath'

DEVICE_ERR_INVALID = -1
DEVICE_ERR_UNINIT = -2

#
# External storage status from Device Service
#
EXT_STORAGE_STATUS_FULL = -1
EXT_STORAGE_STATUS_FAILED = -2
EXT_STORAGE_STATUS_STOP_FAILED = -3
EXT_STORAGE_STATUS_READY = 0
EXT_STORAGE_STATUS_NOTPRESENT = 1
EXT_STORAGE_STATUS_UNFORMATTED = 2
EXT_STORAGE_STATUS_FORMATTING = 3
EXT_STORAGE_STATUS_STOPPING = 4
EXT_STORAGE_STATUS_STOPPED = 5

#
# External storage available values
#
EXT_STORAGE_NOT_AVAILABLE = 0
EXT_STORAGE_AVAILABLE = 1

class DeviceMgr(threading.Thread):
    """Class that encapsulates the device API functionality
    """
    def __init__(self, cb_ext_storage_available):
        self.logger = logging.getLogger(__name__)
        self.cb_ext_storage_available = cb_ext_storage_available
        self.loop = None
        if (cb_ext_storage_available):
            self.cb_ext_storage_available = cb_ext_storage_available
            # Set up DBus loop
            dbus.mainloop.glib.threads_init()
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            if PYTHON3:
                self.loop = glib.MainLoop()
            else:
                self.loop = gobject.MainLoop()
                gobject.threads_init()

        # Get DBus objects
        self.dev = dbus.Interface(dbus.SystemBus().get_object(DEVICE_SERVICE,
            DEVICE_SERVICE_OBJ_PATH), DEVICE_SERVICE_PUBLIC_IFACE)
        self.dev_props = dbus.Interface(dbus.SystemBus().get_object(DEVICE_SERVICE,
            DEVICE_SERVICE_OBJ_PATH), DBUS_PROP_IFACE)
        # Get current state of external storage
        if self.dev_props.Get(DEVICE_SERVICE_PUBLIC_IFACE, EXT_STORAGE_STATUS_PROP) == EXT_STORAGE_STATUS_READY:
            self.ext_storage_available = EXT_STORAGE_AVAILABLE
            self.ext_storage_path = self.dev_props.Get(DEVICE_SERVICE_PUBLIC_IFACE, EXT_STORAGE_PATH_PROP)
        else:
            self.ext_storage_available = EXT_STORAGE_NOT_AVAILABLE
            self.ext_storage_path = None
        self.logger.info('External storage available: {}'.format(self.ext_storage_available))
        # Register signal handlers if using callback
        if (self.cb_ext_storage_available):
            self.dev.connect_to_signal('ExtStorageStopping', self.ext_storage_stopping)
            self.dev_props.connect_to_signal('PropertiesChanged', self.dev_props_changed)
        super(DeviceMgr, self).__init__()
        # Run main loop if using callback
        if (self.cb_ext_storage_available):
            self.start()

    def run(self):
        """Method to run the DBus main loop (on a thread)
        """
        self.logger.info('Starting main loop.')
        self.loop.run()
        self.logger.info('Main loop has exited.')

    def quit_loop(self):
        if self.loop:
            self.loop.quit()

    def deinit(self):
        # Schedule call to stop DBus loop
        if self.loop:
            gobject.timeout_add(0, self.quit_loop)

    def ext_storage_stopping(self):
        """Callback for ExtStorageStopping signal from IG Device Service
        """
        self.update_ext_storage_available(EXT_STORAGE_NOT_AVAILABLE)

    def dev_props_changed(self, iface, props_changed, props_invalidated):
        """Callback for PropertiesChanged signal from IG Device Service
        """
        if props_changed and EXT_STORAGE_STATUS_PROP in props_changed:
            if props_changed[EXT_STORAGE_STATUS_PROP] == EXT_STORAGE_STATUS_READY:
                self.update_ext_storage_available(EXT_STORAGE_AVAILABLE)
            else:
                self.update_ext_storage_available(EXT_STORAGE_NOT_AVAILABLE)

    def update_ext_storage_available(self, ext_storage_available):
        """Method to update storage status via callback to client
        """
        if ext_storage_available != self.ext_storage_available:
            self.ext_storage_available = ext_storage_available
            # Get path if external storage is available
            if self.ext_storage_available == EXT_STORAGE_AVAILABLE:
                self.ext_storage_path = self.dev_props.Get(DEVICE_SERVICE_PUBLIC_IFACE, EXT_STORAGE_PATH_PROP)
                self.logger.info('External storage available at {}'.format(self.ext_storage_path))
            else:
                self.ext_storage_path = None
                self.logger.info('External storage not available.')
            if self.cb_ext_storage_available:
                self.cb_ext_storage_available(self.ext_storage_available, self.ext_storage_path)

    def DeviceEnabled(self):
        """Activate device LED as enabled via IG Device Service
        """
        self.dev.DeviceEnabled()

    def DeviceActivity(self):
        """Indicate device LED activity via IG Device Service
        """
        self.dev.DeviceActivity()

    def DeviceException(self):
        """Activate device LED exception via IG Device Service
        """
        self.dev.DeviceException()

    def SetSerialPortType(self, port_type):
        """Set serial port type via IG Device Service
        """
        return self.dev.SetSerialPortType(port_type)

    def SetSerialTermination(self, term):
        """Set serial termination via IG Device Service
        """
        return self.dev.SetSerialTermination(term)

    def get_ext_storage_available(self):
        """Return state of external storage, and path
        """
        return self.ext_storage_available, self.ext_storage_path

    def get_int_storage_path(self):
        """Return path to internal storage
        """
        return self.dev_props.Get(DEVICE_SERVICE_PUBLIC_IFACE, INT_STORAGE_PATH_PROP)

    def get_storage_status(self):
        """Return storage status via IG Device Service
        """
        return self.dev_props.GetAll(DEVICE_SERVICE_PUBLIC_IFACE)

    def Reboot(self):
        """Reboot
        """
        return self.dev.Reboot()

def device_init(cb_ext_storage_available = None):
    """Initialize the IG device API
    Returns:
        Device instance, to be used in device_* calls
    """
    try:
        dev = DeviceMgr(cb_ext_storage_available)
        return dev
    except dbus.exceptions.DBusException as e:
        logging.getLogger(__name__).error('Cannot open Device interface: {}'.format(e))
        return None

def device_deinit(dev):
    """De-initialize the IG device API
    """
    if dev:
        dev.deinit()

def device_enabled(dev):
    """Activate device LED as enabled
    """
    if dev:
        dev.DeviceEnabled()

def device_activity(dev):
    """Indicate device LED activity
    """
    if dev:
        dev.DeviceActivity()

def device_exception(dev):
    if dev:
        dev.DeviceException()

def set_serial_port_type(dev, port_type):
    """Set serial port type
    """
    if dev:
        return dev.SetSerialPortType(port_type)
    else:
        return DEVICE_ERR_UNINIT

def set_serial_termination(dev, term):
    """Set serial port termination
    """
    if dev:
        return dev.SetSerialTermination(term)
    else:
        return DEVICE_ERR_UNINIT

def get_ext_storage_available(dev):
    """Return state of external storage, and path
    """
    if dev:
        return dev.get_ext_storage_available()
    else:
        return DEVICE_ERR_UNINIT, None

def get_int_storage_path(dev):
    """Return internal storage path
    """
    if dev:
        return dev.get_int_storage_path()
    else:
        return None

def get_storage_status(dev):
    """Return storage status
    """
    if dev:
        return dev.get_storage_status()
    else:
        return None

def reboot(dev):
    """Reboot
    """
    if dev:
        dev.Reboot()
