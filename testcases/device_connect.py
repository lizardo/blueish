def device_found(device_proxy):
    def device_connect_reply():
        print("device connected")
        sys.exit(0)

    def device_connect_error(error):
        print("Device1.Connect failed: %s" % error)
        sys.exit(1)

    dev = dbus.Interface(device_proxy, "org.bluez.Device1")
    dev.Connect(reply_handler=device_connect_reply,
            error_handler=device_connect_error)

wait_for_device(packets, "CA:FE:CA:FE:CA:FE", device_found)
