from powersnitch_app.nut_setup import UsbUpsDevice, render_ups_conf


def test_render_ups_conf_uses_serial_matching():
    config = render_ups_conf(
        [
            UsbUpsDevice(
                vendor_id="0764",
                model_id="0601",
                vendor="CPS",
                model="CP1500PFCLCDa",
                serial="CXXQS7010035",
            )
        ]
    )
    assert "driver = usbhid-ups" in config
    assert "vendorid = 0764" in config
    assert "productid = 0601" in config
    assert "serial = CXXQS7010035" in config
