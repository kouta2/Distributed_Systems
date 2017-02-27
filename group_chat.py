import socket, select, sys, string, threading

CLIENTS = {} # contains my server socket and everyone's client socket (5 sockts)

RECV_BUFFER = 4096
PORT = 5002

HOST = ["172.22.146.231", "172.22.146.233", "172.22.146.235", "172.22.146.237", "172.22.146.239", "172.22.146.241", "172.22.146.243", "172.22.146.245", "172.22.146.247", "172.22.146.249"] # all of the hosts allowed in this group cHat

SEND_SOCKS = [] # all of my sockets I need to write to other servers (5 sockets cuz I have myself)

CONNECTED_SEND_SOCKS = []

DISCONNECTED_CLIENTS = set() # keeps track of the clients who have disconnected

PROCESS_NUM = int(socket.gethostname()[15:17])

number_of_multicasts = 0

sequence_numbers_of_processes = [0 for x in range(10)]

USERNAME = ''

def handleConnections():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(10)

    print "Chat server started on port " + str(PORT)
    
    while 1:
        read_sockets,write_sockets,error_sockets = select.select([server_socket],[],[])
        connect_to_send_socks()
        for sock in read_sockets:
            try:
                sockfd, addr = server_socket.accept()
                username_client = sockfd.recv(RECV_BUFFER)
                CLIENTS[sockfd] = username_client
            except:
                break

def prompt():
    sys.stdout.write('<' + USERNAME + '> ')
    sys.stdout.flush()


def create_message(msg):
    return str(PROCESS_NUM) + '<' + str(number_of_multicasts) + '<' + USERNAME + '> ' + msg

def send_message(msg):
    for s in SEND_SOCKS:
        try:
            s.send(msg)
        except:
            pass


def connect_to_send_socks():
    for host in HOST:
        if host not in CONNECTED_SEND_SOCKS:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((host, PORT))
                SEND_SOCKS.append(s)
                CONNECTED_SEND_SOCKS.append(host)
                s.send(USERNAME)
            except:
                pass

if __name__=="__main__":
    if(len(sys.argv) != 2):
        print 'Usage : python distributed_group_chat.py username'
        sys.exit()

    USERNAME = sys.argv[1]

    thread_connect = threading.Thread(target = handleConnections)
    thread_connect.start()
    connect_to_send_socks()
    prompt()

    while 1:
        read_sockets, write_sockets, error_sockets = select.select(CLIENTS.keys() + [sys.stdin], [], [], 0)

        # try connecting to sockets before a send messages
        connect_to_send_socks()
        
        for sock in read_sockets:
            if sock == sys.stdin:
                msg = sys.stdin.readline()
                prompt()
                if len(msg) > 1:
                    number_of_multicasts += 1
                    send_message(create_message(msg))
                    sequence_numbers_of_processes[PROCESS_NUM - 1] = number_of_multicasts
    
            else:
                msg = sock.recv(RECV_BUFFER)
                if len(msg) == 0:
                    if sock not in CLIENTS.keys():
                        continue
                    sys.stdout.write("\r" + CLIENTS[sock] + " disconnected and left the room\n")
                    sys.stdout.flush()
                    del CLIENTS[sock]
                    DISCONNECTED_CLIENTS.add(sock)
                    sock.close()
                    prompt()
                else:
                    data_process = msg.split('<')
                    process_id = int(data_process[0])
                    index = process_id - 1
                    if sequence_numbers_of_processes[index] < int(data_process[1]):
                        if process_id != PROCESS_NUM:
                            send_message(msg)
                        sequence_numbers_of_processes[index] = int(data_process[1])
                        print_msg = '<'
                        for i in range(2, len(data_process)):
                            print_msg += data_process[i]
                        sys.stdout.write('\r' + print_msg)
                        sys.stdout.flush()
                        prompt()
