try:
    import usocket as socket
except:
    import socket


CONTENT = b"""\
HTTP/1.0 200 OK
<head>
	<meta http-equiv='refresh' content='5'/>
	<title>MPPT Stats</title>
	<style>
		body { background-color: #cccccc; font-family: Arial, Helvetica, Sans-Serif; Color: #000088; }
	</style>
<head>

<html>
	<body>
		<p>%d</p>
	</body>
</html>


LOAD	ON
IL	400
H19	39401
H20	0
H21	12
H22	108
H23	295
HSDS	287
Checksum	.
PID	0xA043
FW	116
SER#	HQ1341PSPAY
V	25000
I	-40
VPV	67760
PPV	11
CS	3
ERR	0
LOAD	ON
IL	400
H19	39401
H20	0
H21	12
H22	108
H23	295
HSDS	287
Checksum	²
PID	0xA043
FW	116
SER#	HQ1341PSPAY
V	24980
I	-60
VPV	61020
PPV	9
CS	3
ERR	0
LOAD	ON
IL	400
H19	39401
H20	0
H21	12
H22	108
H23	295
HSDS	287

"""





def main(micropython_optimize=False):
    s = socket.socket()

    # Binding to all interfaces - server will be accessible to other hosts!
    ai = socket.getaddrinfo("0.0.0.0", 8080)
    print("Bind address info:", ai)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
	
    print("Listening, connect your browser to http://<this_host>:8080/")

    counter = 0
    while True:
        res = s.accept()
        client_sock = res[0]
        client_addr = res[1]
        print("Client address:", client_addr)
        print("Client socket:", client_sock)

        if not micropython_optimize:
            # To read line-oriented protocol (like HTTP) from a socket (and
            # avoid short read problem), it must be wrapped in a stream (aka
            # file-like) object. That's how you do it in CPython:
            client_stream = client_sock.makefile("rwb")
        else:
            # .. but MicroPython socket objects support stream interface
            # directly, so calling .makefile() method is not required. If
            # you develop application which will run only on MicroPython,
            # especially on a resource-constrained embedded device, you
            # may take this shortcut to save resources.
            client_stream = client_sock

        print("Request:")
        req = client_stream.readline()
        print(req)
        while True:
            h = client_stream.readline()
            if h == b"" or h == b"\r\n":
                break
			
            print(h)

        client_stream.write(CONTENT % counter)

        client_stream.close()
        if not micropython_optimize:
            client_sock.close()
        counter += 1
        print()


print(CONTENT % 1)

main()
