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
SOL_SOCKET = socket.SOL_SOCKET
SO_REUSEADDR = socket.SO_REUSEADDR

PROCESS_NUM = int(socket.gethostname()[15:17])

number_of_send_messages = 0

sequence_numbers_of_processes = [0 for x in range(10)]

'''
def handleFailureDetection():
    for sock in SEND_SOCKS:
        sock.send(")(*&^%$#@!")
'''

# handles new connections and messages from other clients
def handleNewConnections():
    server_socket = GET_SOCKET(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
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
                data = sock.recv(RECV_BUFFER)
                if sock in DISCONNECTED_CLIENTS:
                    s = sock
                    # ignore messages that come from a client after he/she disconnected
                elif len(data) == 0:
                    sys.stdout.write("\r" + CLIENTS[sock] + " disconnected\n")
                    prompt()
                    del CLIENTS[sock]
                    DISCONNECTED_CLIENTS.add(sock)
                else:
                    data_process = data.split('<')
                    process_id = int(data_process[0])
                    if process_id == PROCESS_NUM:
                        return
                    index = process_id - 1
                    if sequence_numbers_of_processes[index] < int(data_process[1]):
                        multicast(data)
                        sequence_numbers_of_processes[index] = int(data_process[1])
                        check = data_process[2].split(' ')
                        if len(check) > 1 and len(check[1]) >= 4 and (check[1])[0:4] == '?!@#':
                            CLIENTS[sock] = (check[1])[4:]
                        else:
                            msg = '<'
                            for i in range(2, len(data_process)):
                                msg += data_process[i]
                            sys.stdout.write("\r" + msg)
                            prompt()
                

def prompt():
    sys.stdout.write('<' + username + '> ')
    sys.stdout.flush()

def multicast(msg):
    for s in SEND_SOCKS:
        s.send(msg)

def send_message(username, msg):
    for s in SEND_SOCKS:
        s.send(str(PROCESS_NUM) + '<' + str(number_of_send_messages) + '<' + username + '> ' + msg)

if __name__=="__main__":
    if(len(sys.argv) != 2):
        print 'Usage : python distributed_group_chat.py username'
        sys.exit()

    username = sys.argv[1]

    thread_connect = threading.Thread(target = handleNewConnections)
    thread_connect.start()
    # thread_fail = threading.Thread(target = handleFailureDetection)
    # thread_fail.start()
    # HOST.remove(socket.gethostbyname(socket.gethostname())) 
    while 1:
        prompt()
        read_sockets, write_sockets, error_sockets = select.select([sys.stdin], [], [])
        for host in HOST:
            if host in SEND_SOCKS.values():
                continue
            s = GET_SOCKET(AF_INET, SOCK_STREAM)
            try:
                s.connect((host, PORT))
                SEND_SOCKS[s] = host
                msg = '?!@#' + username
                number_of_send_messages += 1
                send_message(username, msg)
                sequence_numbers_of_processes[PROCESS_NUM - 1] = number_of_send_messages
            except:
                socket = s
                # do nothing

        for sock in read_sockets:
            if sock == sys.stdin:
                msg = sys.stdin.readline()
                if len(msg) > 1:
                    number_of_send_messages += 1
                    send_message(username, msg)
                    sequence_numbers_of_processes[PROCESS_NUM - 1] = number_of_send_messages
                    

    thread_connect.join()
    # thread_fail.join()
