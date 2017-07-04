# imports
import machine
import ssd1306
import time
import usocket as socket
import uselect as select


# constants
SYSTEM_I2C_ADDR	= 8

# globals
pin0_pmc = machine.Pin(0, machine.Pin.OUT)	# power meter on/off
pin4_i2c = machine.Pin(4, machine.Pin.OUT)	# i2c SDA
pin5_i2c = machine.Pin(5, machine.Pin.OUT)	# i2c SCL

clientAddr = ''								# last web-client addr
reqCounter = 0								# html request counter
strRequest = ''								# html request
strResponse = ''							# html response
strVbty = b''								# current battery voltage, [mV]
strVbtyNominal = b''						# nominal battery voltage, [mV]
strIbty = b''								# current battery current, [mA]
strIld = b''								# current load current, [mA]
strPpvmax = b''								# panel max power (today), [W]
strBtyChargeState = b''						# current battery charger state
strBtyLevel = b''							# current battery level/health, [%]


# html response header
HTML_TEXT_HEADER = b"""\
HTTP/1.0 200 OK
Content-Type: %s/%s; charset=utf-8

"""



#b'GET / HTTP/1.1\r\nHost: 192.168.8.50:8080\r\nConnection: keep-alive\r\nCache-Control: max-age=0\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nDNT: 1\r\nAccept-Encoding: gzip, deflate, sdch\r\nAccept-Language: en-US,en;q=0.8,en-GB;q=0.6\r\n\r\n'

#b'GET /style.css HTTP/1.1\r\nHost: 192.168.8.50:8080\r\nConnection: keep-alive\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36\r\nAccept: text/css,*/*;q=0.1\r\nDNT: 1\r\nReferer: http://192.168.8.50:8080/\r\nAccept-Encoding: gzip, deflate, sdch\r\nAccept-Language: en-US,en;q=0.8,en-GB;q=0.6\r\n\r\n'

#b'GET /favicon.ico HTTP/1.1\r\nHost: 192.168.8.50:8080\r\nConnection: keep-alive\r\nPragma: no-cache\r\nCache-Control: no-cache\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36\r\nAccept: image/webp,image/*,*/*;q=0.8\r\nDNT: 1\r\nReferer: http://192.168.8.50:8080/\r\nAccept-Encoding: gzip, deflate, sdch\r\nAccept-Language: en-US,en;q=0.8,en-GB;q=0.6\r\n\r\n'



######################################
def getSystemValue(key):
	i2c.writeto(SYSTEM_I2C_ADDR, key)
	raw = i2c.readfrom(SYSTEM_I2C_ADDR, 24)
	return raw.split(b'\xFF')[0].decode('ascii')
######################################


######################################
# update system values
def updateSystemValues():
	global strVbty
	global strVbtyNominal
	global strIbty
	global strIld
	global strPpvmax
	global strBtyChargeState
	global strBtyLevel
	
	# get system values via I2C
	strVbty = getSystemValue(b'vbty')
	strVbtyNominal = getSystemValue(b'vbty_nominal')
	strIbty = getSystemValue(b'ibty')
	strIld = getSystemValue(b'ild')
	strPpvmax = getSystemValue(b'ppv_max')
	strBtyChargeState = getSystemValue(b'cs')
	strBtyLevel = getSystemValue(b'vbty_level')
		
	# update OLED with system values
	oled.fill(0)
	oled.text(clientAddr, 0, 0)
	oled.text(str(reqCounter), 0, 10)
	oled.text('vbty=' + strVbty + "," + strBtyLevel, 0, 20)
	oled.text('ibty=' + strIbty, 0, 30)
	oled.text('cs=' + strBtyChargeState, 0, 40)
	oled.text('ppv_max=' + strPpvmax, 0, 50)
	oled.show()
######################################


######################################
# build main html response and store into 'strResponse'
def getHtmlIndex():
	global strResponse
	strResponse = HTML_TEXT_HEADER % (b'text', b'html')
	
	f = open('index.html')
	strResponse += f.read() % (str(reqCounter), strVbtyNominal, strVbty, strIbty, strProtocol, strPpvmax, strBtyChargeState, strBtyLevel)

#####################################


######################################
# build response and store into 'strResponse'
def getFile(strPath, strType, strSubType):
	global strResponse
	strResponse = HTML_TEXT_HEADER % (strType, strSubType)
	
	f = open(strPath)
	strResponse += f.read()
	
#####################################


######################################
# process request 'strRequest', build response and store into 'strResponse'
def getHtmlResponse():
	iPathStart = strRequest.find(b'/')
	iPathEnd = strRequest.find(b' ', iPathStart)
	strPath = strRequest[iPathStart:iPathEnd]
	
	if strPath == b'/':
		getHtmlIndex()

	else:
		iExtStart = strPath.find(b'.')
		strExt = strPath[iExtStart:-1]

		if strExt == b'.css':
			getFile(strPath, b'text', b'css')
		elif strExt == b'.ico':
			getFile(strPath, b'image', b'bmp')
		else:
			getFile(strPath, b'text', b'plain')

#####################################


#####################################
# main web request handler
def main():
	# create server socket
	s = socket.socket()
	ai = socket.getaddrinfo("0.0.0.0", 80)
	addr = ai[0][-1]

	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.settimeout(1.0)
	s.bind(addr)
	s.listen(5)

	# main loop
	while True:
		# get system values via I2C
		updateSystemValues()
		
		# check for a a new client connection
		poller = select.poll()
		poller.register(s, select.POLLIN)
		res = poller.poll(500)
		
		#print('go %s\n' % (time.ticks_ms()))
		
		if len(res) > 0:
			# accept new client connection
			res = s.accept()
			client_sock = res[0]
			client_sock.settimeout(12.0)
			
			global clientAddr
			clientAddr = res[1][0]
		
			# display client addr on OLED
			oled.text(clientAddr, 0, 0)
			oled.show()

			# process request 
			try:
				# receive client request
				global strRequest
				strRequest = client_sock.recv(2048)
				#print(b'-------------------')
				#print(req)
				#print(b'-------------------')
					
				# build HTML response
				global strResponse
				try:
					getHtmlResponse()
					#print(b'-------------------')
					#print(strResponse)
					#print(b'-------------------')
					
				except OSError:
					print('html file/response error.')				
						
				# send out response
				client_sock.sendall(strResponse)
				
				global reqCounter
				reqCounter += 1
			
			except OSError:
				print('send/recv timeout %s' % (clientAddr))				
				
			# finish
			client_sock.close()
		

# main web request handler end
##############################




##############################

# cycle power meter
pin0_pmc.off()
time.sleep_ms(1000)
pin0_pmc.on()
time.sleep_ms(2000)

# create I2C interface
i2c = machine.I2C(freq=400000,scl=pin5_i2c,sda=pin4_i2c)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# say hello
strProtocol = getSystemValue(b'name');

oled.fill(0)
oled.text('MiPy Energy', 0, 0)
oled.text(strProtocol, 0, 10)
oled.show()

time.sleep_ms(4000)


# start main web request handler
main()









		
	
