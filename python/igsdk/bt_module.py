#
# bt_module.py
#
# Bluetooth API for Sentrius IG devices
#

import dbus
import dbus.exceptions
import threading
import dbus.mainloop.glib
import logging
import sys
import json

PYTHON3 = sys.version_info >= (3, 0)
if PYTHON3:
    from gi.repository import GObject as gobject
    from gi.repository import GLib as glib
else:
    import gobject

BT_OBJ='org.bluez'
BT_OBJ_PATH='/org/bluez/hci0'
BT_ADAPTER_IFACE='org.bluez.Adapter1'
BT_DEVICE_IFACE='org.bluez.Device1'
BT_SERVICE_IFACE='org.bluez.GattService1'
BT_CHARACTERISTIC_IFACE='org.bluez.GattCharacteristic1'
DBUS_OBJ_MGR_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

result_success = 0
result_err = -1

class BtMgr(threading.Thread):
    """
    Class that manages all bluetooth API functionality
    """
    def __init__(self, discovery_callback, characteristic_property_change_callback, connection_callback = None, write_notification_callback = None):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initalizing BtMgr')

        self.devices = {}

        # Set up DBus loop
        self.loop = None
        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        if PYTHON3:
            self.loop = glib.MainLoop()
        else:
            self.loop = gobject.MainLoop()
            gobject.threads_init()

        # Get DBus objects
        self.manager = dbus.Interface(dbus.SystemBus().get_object(BT_OBJ,
            "/"), DBUS_OBJ_MGR_IFACE)
        self.adapter = dbus.Interface(dbus.SystemBus().get_object(BT_OBJ,
            BT_OBJ_PATH), BT_ADAPTER_IFACE)
        self.adapter_props = dbus.Interface(dbus.SystemBus().get_object(BT_OBJ,
            BT_OBJ_PATH), DBUS_PROP_IFACE)
        self.objects = self.manager.GetManagedObjects()

        # Register signal handlers
        self.manager.connect_to_signal('InterfacesAdded', discovery_callback)
        super(BtMgr, self).__init__()

        # Save custom callbacks with the client
        self.characteristic_property_change_callback = characteristic_property_change_callback
        self.connection_callback = connection_callback
        self.write_notification_callback = write_notification_callback

        # Power on the bluetooth module
        self.adapter_props.Set(BT_ADAPTER_IFACE, "Powered", dbus.Boolean(1))

        # Run main loop
        self.start()

    def run(self):
        """
        Method to run the DBus main loop (on a thread)
        """
        self.logger.info('Starting main loop.')
        self.loop.run()
        self.logger.info('Main loop has exited.')

    def quit_loop(self):
        if self.loop:
            self.loop.quit()

    def deinit(self):
        if self.loop:
            gobject.timeout_add(0, self.quit_loop)

    def start_discovery(self):
        """
        Activate bluetooth discovery of peripherals
        """
        self.logger.info('Starting Discovery')
        self.adapter.StartDiscovery()

    def stop_discovery(self):
        """
        Deactivate bluetooth discovery of peripherals
        """
        self.logger.info('Stopping Discovery')
        self.adapter.StopDiscovery()

    def find_service(self, device_path, service_uuid):
        """
        Returns a path to the service for the given device identified by the UUID
        """
        for path, interfaces in self.objects.items():
            if path.startswith(device_path):
                service = interfaces.get(BT_SERVICE_IFACE)
                if service and str(service['UUID']) == service_uuid:
                    return path
        return None

    def find_characteristics(self, service_path):
        """
        Returns an array of dictionaries containing the UUID and path for
        every characteristic associated with the given service
        """
        chars_array = []
        for path, interfaces in self.objects.items():
            if path.startswith(service_path):
                char = interfaces.get(BT_CHARACTERISTIC_IFACE)
                if char:
                    char_elements = {}
                    char_elements['uuid'] = char['UUID']
                    char_elements['path'] = path
                    chars_array.append(char_elements)

        return chars_array

    def connect(self, address):
        """
        Connect to the bluetooth device at the designated address
        """
        self.logger.info('Connecting to {}'.format(address))
        self.objects = self.manager.GetManagedObjects()

        success = False
        for path, interfaces in self.objects.items():
            if path.startswith(self.adapter.object_path):
                device = interfaces.get(BT_DEVICE_IFACE)
                if device and str(device['Address']) == address:
                    # Found it; create and connect
                    # NOTE: The 'mgr_connection_callback' will store the device locally if it connects successfully
                    device = Device(address, path, self.characteristic_property_change_callback, self.mgr_connection_callback, self.write_notification_callback)
                    device.connect()
                    success = True

        if not success:
            self.logger.error('Device {} was not found'.format(address))

    def disconnect(self, address, purge):
        """
        Disconnect from the bluetooth device at the designated address
        then purge (if requested) from the adapter's discovered list
        """
        self.logger.info('Disconnecting from {}'.format(address))

        device = self.devices.get(address)
        if device is not None:
            device_path = device.get_path()
            device.disconnect()
            if purge:
                self.adapter.RemoveDevice(device_path)
        else:
            self.logger.error('Device {} was not found'.format(address))

    def build_device_services(self, address):
        """
        Build a list of services for the given device
        """
        self.logger.info('Building services and characteristics for {}'.format(address))

        try:
            self.objects = self.manager.GetManagedObjects()

            device = self.devices.get(address)
            if device is not None:
                uuids = device.get_service_uuids()
                for uuid in uuids:
                    service_path = self.find_service(device.get_path(), uuid)
                    if service_path:
                        device.add_service(uuid, service_path)
                        service = device.get_service(uuid)

                        chars_array = self.find_characteristics(service_path)
                        for char in chars_array:
                            service.add_characteristic(char['uuid'], char['path'])
        except dbus.exceptions.DBusException as e:
            self.logger.error('Failed to build services for device {}: {}'.format(address, e))

    def get_device_services(self, address):
        """
        Returns all the services and characteristics for the given device
        """
        self.logger.info('Retrieving services and characteristics for {}'.format(address))

        services = {}
        device = self.devices.get(address)
        if device is not None:
            services['services'] = device.get_services()
        else:
            self.logger.error('Device {} was not found'.format(address))

        return services

    def read_characteristic(self, address, service_uuid, char_uuid, offset = 0):
        """
        Returns the characteristic value for the given device/service
        None if reading the characteristic was a failure
        """
        value = None
        self.logger.info('Reading characteristic {} in service {} for device {}'.format(char_uuid, service_uuid, address))

        try:
            device = self.devices.get(address)
            if device is not None:
                service = device.get_service(service_uuid)
                if service:
                    char = service.get_characteristic(char_uuid)
                    if char:
                       value = char.read_value(offset)
                    else:
                        self.logger.error('Characteristic UUID {} not found for service {} and device {}'.format(char_uuid, service_uuid, address))
                else:
                    self.logger.error('Service UUID {} not found for device {}'.format(service_uuid, address))
            else:
                self.logger.error('Device {} was not found'.format(address))
        except dbus.exceptions.DBusException as e:
            self.logger.error('Failed to read device {} characteristic {}: {}'.format(address, char_uuid, e))

        return value

    def write_characteristic(self, address, service_uuid, char_uuid, value, offset = 0):
        """
        Write a value to the given characteristic for the given device/service
        The value is an array of bytes
        """
        self.logger.info('Writing to characteristic {} in service {} for device {}'.format(char_uuid, service_uuid, address))

        try:
            device = self.devices.get(address)
            if device is not None:
                service = device.get_service(service_uuid)
                if service:
                    char = service.get_characteristic(char_uuid)
                    if char:
                        # Convert the value to a DBus-formatted byte array
                        value_bytes = [dbus.Byte(b) for b in value]

                        # Write the value
                        char.write_value(value_bytes, offset)
                    else:
                        self.logger.error('Characteristic UUID {} not found for service {} and device {}'.format(char_uuid, service_uuid, address))
                else:
                    self.logger.error('Service UUID {} not found for device {}'.format(service_uuid, address))
            else:
                self.logger.error('Device {} was not found'.format(address))
        except (dbus.exceptions.DBusException) as e:
            self.logger.error('Failed to write device {} characteristic {}: {}'.format(address, char_uuid, e))

    def configure_characteristic_notification(self, address, service_uuid, char_uuid, enable):
        """
        Enable/Disable notifications for the given device characteristic
        """
        if enable:
            self.logger.info('Starting notifications for characteristic {} in service {} for device {}'.format(char_uuid, service_uuid, address))
        else:
            self.logger.info('Stopping notifications for characteristic {} in service {} for device {}'.format(char_uuid, service_uuid, address))

        try:
            device = self.devices.get(address)
            if device is not None:
                service = device.get_service(service_uuid)
                if service:
                    char = service.get_characteristic(char_uuid)
                    if char:
                        if enable:
                            if not char.is_notifying():
                                char.start_notifications()
                            else:
                                self.logger.error('Characteristic {} is already sending notifications'.format(char_uuid))
                        else:
                            char.stop_notifications()
                    else:
                        self.logger.error('Characteristic UUID {} not found for service {} and device {}'.format(char_uuid, service_uuid, address))
                else:
                    self.logger.error('Service UUID {} not found for device {}'.format(service_uuid, address))
            else:
                self.logger.error('Device {} was not found'.format(address))
        except (dbus.exceptions.DBusException) as e:
            self.logger.error('Failed to configure characteristic notifications for device {} characteristic {}: {}'.format(address, char_uuid, e))

    def mgr_connection_callback(self, device):
        data = {}
        data['connected'] = device.is_connected()
        data['address'] = device.get_address()
        if data['connected']:
            # Add the new connected device to the managed device array
            self.devices[data['address']] = device
            self.logger.info('Added device {}, path {}, list count {}'.format(data['address'], device.get_path(), len(self.devices)))

            # Build the list of services for the newly connected device
            self.build_device_services(data['address'])
        elif not data['connected']:
            # Disconnected; cleanup the device
            device.disconnect_signal()
            device2 = self.devices.pop(data['address'], None)
            if device2 is None:
                self.logger.info('No device to remove for {}, list count {}'.format(data['address'], len(self.devices)))
            else:
                self.logger.info('Removed device {}, list count {}'.format(data['address'], len(self.devices)))

        # Forward the connection data to the client (if callback provided)
        if self.connection_callback is not None:
            self.connection_callback(data)

class Device():
    """
    Class that encapsulates a bluetooth device
    """
    def __init__(self, address, path, property_change_callback, connection_callback, write_notification_callback = None):
        self.logger = logging.getLogger(__name__)
        self.address = address
        self.property_change_callback = property_change_callback
        self.connection_callback = connection_callback
        self.write_notification_callback = write_notification_callback
        self.services = []

        self.path = path
        self.object = dbus.SystemBus().get_object(BT_OBJ, path)
        self.interface = dbus.Interface(self.object, BT_DEVICE_IFACE)
        self.properties = dbus.Interface(self.object, DBUS_PROP_IFACE)
        self.properties_signal = None

    def connect(self):
        """
        Connect to the device
        """
        try:
            # Connect to the device property signals to receive notifications
            if self.properties_signal is None:
                self.properties_signal = self.properties.connect_to_signal('PropertiesChanged', self.properties_changed)

            self.interface.Connect()
        except dbus.exceptions.DBusException as e:
            self.logger.error('Failed to connect device {}: {}'.format(self.address, e))

    def disconnect(self):
        """
        Disconnect from a device
        """
        try:
            self.interface.Disconnect()
        except dbus.exceptions.DBusException as e:
            self.logger.error('Failed to disconnect device {}: {}'.format(self.address, e))

    def add_service(self, uuid, path):
        """
        Create and store a new service linked to this device
        """
        service = Service(uuid, path, self.write_characteristic_notification_callback, self.characteristic_property_change_callback)
        self.services.append(service)

    def get_service(self, uuid):
        """
        Returns the device service matching the UUID
        None if the service is not found
        """
        for service in self.services:
            if service.get_uuid() == uuid:
                return service

        return None

    def get_services(self):
        """
        Returns a dictionary of dictionaries including each device's service
        characteristic properties identified by the service UUID
        """
        services_dict = {}
        for service in self.services:
            service_chars = {}
            service_chars['characteristics'] = service.get_characteristics()
            services_dict[service.get_uuid()] = service_chars

        return services_dict

    def get_path(self):
        """
        Returns the device path
        """
        return self.path

    def get_address(self):
        """
        Returns the device address
        """
        return self.address

    def get_service_uuids(self):
        """
        Returns all of the UUIDs of the device services
        """
        uuids = []
        try:
            uuids = self.properties.Get(BT_DEVICE_IFACE, 'UUIDs')
        except:
            # Ignore; means we are not connected
            pass

        return uuids

    def is_connected(self):
        """
        Returns True if currently connected to the device; false otherwise
        """
        connected = False
        try:
            connected = self.properties.Get(BT_DEVICE_IFACE, 'Connected') == 1
        except:
            # Ignore; means we are not connected
            pass

        return connected

    def is_services_resolved(self):
        """
        Returns True if all the device services have been discovered; false otherwise
        """
        resolved = False
        try:
            resolved = self.properties.Get(BT_DEVICE_IFACE, 'ServicesResolved') == 1
        except:
            # Ignore; means we are not connected
            pass

        return resolved

    def disconnect_signal(self):
        """
        Disconnect the signal to receive property updates
        """
        if self.properties_signal is not None:
            self.properties_signal.remove()
            self.properties_signal = None

        for service in self.services:
            service.disconnect_signal()

    def properties_changed(self, interface, changed_properties, invalidated_properties):
        """
        A callback when a device property changes

        Notifies the client when the device has been both connected
        and all services have been discovered
        """
        if 'Connected' in changed_properties and changed_properties['Connected'] == 0:
            # Send notification that device disconnected
            self.connection_callback(self)
        if 'ServicesResolved' in changed_properties and changed_properties['ServicesResolved'] == 1 and self.is_connected():
            # Send notification that the device is connected and services discovered
            self.connection_callback(self)

    def write_characteristic_notification_callback(self, data):
        """
        Callback for a managed characteristic write operation
        Includes data on the success/failure of the write
        Package the device address and forward the notification to the client
        """
        if self.write_notification_callback is not None:
            data['address'] = self.address
            self.write_notification_callback(data)

    def characteristic_property_change_callback(self, data):
        """
        Callback for a managed characteristic property change
        Includes the characteristic value that changed
        Package the device address and forward the notification to the client
        """
        data['address'] = self.address
        self.property_change_callback(data)

class Service():
    """
    Class that encapsulates a bluetooth device service
    """
    def __init__(self, uuid, path, property_change_callback, write_notification_callback = None):
        self.logger = logging.getLogger(__name__)
        self.uuid = uuid
        self.path = path
        self.property_change_callback = property_change_callback
        self.write_notification_callback = write_notification_callback
        self.characteristics = []

        self.object = dbus.SystemBus().get_object(BT_OBJ, path)
        self.interface = dbus.Interface(self.object, BT_SERVICE_IFACE)
        self.properties = dbus.Interface(self.object, DBUS_PROP_IFACE)
        self.properties_signal = None

    def add_characteristic(self, uuid, path):
        char = Characteristic(uuid, path, self.write_characteristic_notification_callback, self.characteristic_property_change_callback)
        self.characteristics.append(char)

    def get_characteristic(self, uuid):
        """
        Returns the service characteristic matching the UUID
        None if the characteristic is not found
        """
        for char in self.characteristics:
            if char.get_uuid() == uuid:
                return char

        return None

    def get_characteristics(self):
        """
        Returns an array of dictionaries including each service's characteristic
        properties (UUID and flags)
        """
        char_array = []
        for char in self.characteristics:
            char_props = {}
            char_flags = {}

            char_flags['Flags'] = char.get_flags()
            char_props[char.get_uuid()] = char_flags
            char_array.append(char_props)

        return char_array

    def get_uuid(self):
        """
        Returns the UUID for the service
        """
        return self.uuid

    def disconnect_signal(self):
        """
        Disconnect the signal to receive property updates
        """
        if self.properties_signal is not None:
            self.properties_signal.remove()
            self.properties_signal = None

        for char in self.characteristics:
            char.disconnect_signal()

    def write_characteristic_notification_callback(self, data):
        """
        Callback for a managed characteristic write operation
        Includes data on the success/failure of the write
        Package the service UUID and forward the notification to the client
        """
        if self.write_notification_callback is not None:
            data['service_uuid'] = self.uuid
            self.write_notification_callback(data)

    def characteristic_property_change_callback(self, data):
        """
        Callback for a managed characteristic property change
        Includes the characteristic value that changed
        Package the service UUID and forward the notification to the client
        """
        data['service_uuid'] = self.uuid
        self.property_change_callback(data)

class Characteristic():
    """
    Class that encapsulates a bluetooth device characteristic
    """
    def __init__(self, uuid, path, property_change_callback, write_notification_callback = None):
        self.logger = logging.getLogger(__name__)
        self.uuid = uuid
        self.path = path
        self.property_change_callback = property_change_callback
        self.write_notification_callback = write_notification_callback

        self.object = dbus.SystemBus().get_object(BT_OBJ, path)
        self.interface = dbus.Interface(self.object, BT_CHARACTERISTIC_IFACE)
        self.properties = dbus.Interface(self.object, DBUS_PROP_IFACE)
        self.properties_signal = self.properties.connect_to_signal('PropertiesChanged', self.characteristic_property_change_callback)

    def get_uuid(self):
        """
        Returns the UUID for the characteristic
        """
        return self.uuid;

    def get_flags(self):
        """
        Returns all of the characteristic flags
        """
        return self.properties.Get(BT_CHARACTERISTIC_IFACE, 'Flags')

    def is_notifying(self):
        """
        Returns whether or not the characteristic is notifying on its value changes
        """
        return self.properties.Get(BT_CHARACTERISTIC_IFACE, 'Notifying') == 1

    def read_value(self, offset):
        """
        Returns the value associated with this characteristic
        The value is an array of bytes
        """
        return self.object.ReadValue({'offset': dbus.UInt16(offset, variant_level=1)},
            dbus_interface=BT_CHARACTERISTIC_IFACE)

    def write_value(self, value, offset):
        """
        Write a value to this characteristic
        The value is an array of bytes
        """
        self.object.WriteValue(value, {'offset': dbus.UInt16(offset, variant_level=1)},
            reply_handler=self.write_characteristic_success_callback,
            error_handler=self.write_characteristic_error_callback,
            dbus_interface=BT_CHARACTERISTIC_IFACE)

    def start_notifications(self):
        """
        Start sending notifications on this characteristic's property changes
        """
        self.object.StartNotify(dbus_interface=BT_CHARACTERISTIC_IFACE)

    def stop_notifications(self):
        """
        Stop sending notifications on this characteristic's property changes
        """
        self.object.StopNotify(dbus_interface=BT_CHARACTERISTIC_IFACE)

    def disconnect_signal(self):
        """
        Disconnect the signal to receive property updates
        """
        if self.properties_signal is not None:
            self.properties_signal.remove()
            self.properties_signal = None

    def write_characteristic_success_callback(self):
        """
        Callback for a successful write operation
        Package the characteristic UUID and forward the notification to the client
        """
        if self.write_notification_callback is not None:
            data = {}
            data['result'] = result_success
            data['char_uuid'] = self.uuid
            self.write_notification_callback(data)

    def write_characteristic_error_callback(self, dbus_error):
        """
        Callback for a failed write operation
        Package the characteristic UUID and error, then forward the notification to the client
        """
        if self.write_notification_callback is not None:
            data = {}
            data['result'] = result_err
            data['char_uuid'] = self.uuid
            data['error'] = dbus_error.get_dbus_message()
            self.write_notification_callback(data)

    def characteristic_property_change_callback(self, interface, changed_properties, invalidated_properties):
        """
        Callback for all of this characteristic's property changes
        On value changes, package the characteristic's UUID and new value
        and forward the notification to the client
        """
        for property in changed_properties:
            if property == 'Value':
                data = {}
                data['char_uuid'] = self.uuid
                data['value'] = changed_properties[property]
                self.property_change_callback(data)

def bt_init(discovery_callback, characteristic_property_change_callback, connection_callback = None, write_notification_callback = None):
    """
    Initialize the IG bluetooth API
    Returns the device manager instance, to be used in bt_* calls
    """
    try:
        bt = BtMgr(discovery_callback, characteristic_property_change_callback, connection_callback, write_notification_callback)
        return bt
    except dbus.exceptions.DBusException as e:
        logging.getLogger(__name__).error('Cannot open BT interface: {}'.format(e))
        return None

def bt_deinit(bt):
    """De-initialize the IG bluetooth API
    """
    if bt:
        bt.deinit()

def bt_start_discovery(bt):
    """Activate bluetooth discovery of peripherals
    """
    if bt:
        bt.start_discovery()

def bt_stop_discovery(bt):
    """Deactivate bluetooth discovery of peripherals
    """
    if bt:
        bt.stop_discovery()

def bt_connect(bt, address):
    """
    Connect to the bluetooth device at the designated address
    """
    if bt:
        bt.connect(address)

def bt_disconnect(bt, address, purge):
    """
    Disconnect from the bluetooth device at the designated address
    """
    if bt:
        bt.disconnect(address, purge)

def bt_device_services(bt, address):
    """
    Returns all the services and characteristics for the given device
    """
    if bt:
        return bt.get_device_services(address)

def bt_read_characteristic(bt, address, service_uuid, char_uuid):
    """
    Read a value to the given characteristic for the given device/service
    Value is returned in the 'characteristic_property_change_callback'
    """
    if bt:
        bt.read_characteristic(address, service_uuid, char_uuid)

def bt_write_characteristic(bt, address, service_uuid, char_uuid, value):
    """
    Write a value to the given characteristic for the given device/service
    The value is an array of bytes
    """
    if bt:
        bt.write_characteristic(address, service_uuid, char_uuid, value)

def bt_config_characteristic_notification(bt, address, service_uuid, char_uuid, enable):
    """
    Enable/Disable notifications for the given device characteristic
    """
    if bt:
        bt.configure_characteristic_notification(address, service_uuid, char_uuid, enable)

