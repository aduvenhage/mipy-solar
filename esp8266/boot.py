# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)

import gc
import time
import network

sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)

sta_if.active(True)
ap_if.active(False)

# set fixed IP (comment out for dynamic IP)
sta_if.ifconfig(('192.168.8.50', '255.255.255.0', '192.168.8.1', '8.8.8.8'))

sta_if.connect('JARVIS-EXT', 'Barakus123')

wlan_init_time = time.ticks_ms()
while not sta_if.isconnected():
	if time.ticks_ms() - wlan_init_time > 5000: 
		break
	pass

sta_connected = sta_if.isconnected()
sta_ifconfig = sta_if.ifconfig();

print(sta_ifconfig)

import webrepl
webrepl.start()
gc.collect()
