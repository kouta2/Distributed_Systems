import socket, select, sys, string, threading

CLIENTS = {} # contains my server socket and everyone's client socket (5 sockets)
RECV_BUFFER = 4096
PORT = 5001

HOST = ["172.22.146.231", "172.22.146.233", "172.22.146.235", "172.22.146.237", "172.22.146.239"] # all of the hosts allowed in this group ch
SEND_SOCKS = {} # all of my sockets I need to write to other servers (4 sockets)

DISCONNECTED_CLIENTS = set() # keeps track of the clients who have disconnected

GET_SOCKET = socket.socket
AF_INET = socket.AF_INET
SOCK_STREAM = socket.SOCK_STREAM

PROCESS_NUM = int(socket.gethostname()[15:17])

'''
def handleFailureDetection():
    for sock in SEND_SOCKS:
        sock.send(")(*&^%$#@!")
'''

# handles new connections and messages from other clients
def handleNewConnections():
    server_socket = GET_SOCKET(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(10)

    CLIENTS[server_socket] = 'SERVER'

    print "Chat server started on port " + str(PORT)

    while 1:
        read_sockets,write_sockets,error_sockets = select.select(CLIENTS.keys(),[],[])
        for sock in read_sockets:
            # new connection
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                CLIENTS[sockfd] = ''
            else: # message from another client
                try:
                    data = sock.recv(RECV_BUFFER)
                    if data[0:4] == "?!@#":
                        CLIENTS[sock] = data[4:]
                        # sys.stdout.write("\r" + CLIENTS[sock] + " entered room" + "\n")
                    elif sock in DISCONNECTED_CLIENTS:
                        s = sock
                        # ignore messages that come from a client after he/she disconnected
                    elif len(data) == 0:
                        sys.stdout.write("\r" + CLIENTS[sock] + " disconnected\n")
                        prompt()
                        del CLIENTS[sock]
                        DISCONNECTED_CLIENTS.add(sock)
                    else:
                        sys.stdout.write("\r" + data)
                        prompt()
                except:
                    sys.stdout.write("\r" + CLIENTS[sock] + " disconnected\n")
                    prompt()
                    del CLIENTS[sock]
                    DISCONNECTED_CLIENTS.add(sock)

def prompt():
    sys.stdout.write('<' + username + '> ')
    sys.stdout.flush()

def send_message(username, msg):
    for s in SEND_SOCKS:
        try:
            s.send('<' + username + '> ' + msg)
        except:
            sock = s
            # sys.stdout.write("client message did not get sent\n")

if __name__=="__main__":
    if(len(sys.argv) != 2):
        print 'Usage : python distributed_group_chat.py username'
        sys.exit()

    username = sys.argv[1]

    thread_connect = threading.Thread(target = handleNewConnections)
    thread_connect.start()
    # thread_fail = threading.Thread(target = handleFailureDetection)
    # thread_fail.start()
    HOST.remove(socket.gethostbyname(socket.gethostname())) 
    while 1:
        for host in HOST:
            if host in SEND_SOCKS.values():
                continue
            s = GET_SOCKET(AF_INET, SOCK_STREAM)
            try:
                s.connect((host, PORT))
                SEND_SOCKS[s] = host
                s.send("?!@#" + username)
            except:
                socket = s
                # do nothing
        prompt()
        read_sockets, write_sockets, error_sockets = select.select([sys.stdin], [], [])
        for host in HOST:
            if host in SEND_SOCKS.values():
                continue
            s = GET_SOCKET(AF_INET, SOCK_STREAM)
            try:
                s.connect((host, PORT))
                SEND_SOCKS[s] = host
                s.send("?!@#" + username)
            except:
                socket = s
                # do nothing

        for sock in read_sockets:
            if sock == sys.stdin:
                msg = sys.stdin.readline()
                if len(msg) > 0:
                    send_message(username, msg)

    thread_connect.join()
    # thread_fail.join()
