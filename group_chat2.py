import socket, select, sys, string, threading, Queue, time, signal

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

CLIENTS = {} # contains my server socket and everyone's client socket (5 sockts)

RECV_BUFFER = 4096
PORT = 5002

HOST = ["172.22.146.231", "172.22.146.233", "172.22.146.235", "172.22.146.237", "172.22.146.239", "172.22.146.241", "172.22.146.243", "172.22.146.245", "172.22.146.247", "172.22.146.249"] # all of the hosts allowed in this group cHat

SEND_SOCKS = {} # all of my sockets I need to write to other servers (5 sockets cuz I have myself)

DISCONNECTED_CLIENTS = set() # keeps track of the clients who have disconnected

PROCESS_NUM = int(socket.gethostname()[15:17])

number_of_multicasts = 0

sequence_numbers_of_processes = [0 for x in range(10)]

USERNAME = ''

ERASE_LINE = '\x1b[2K'
CURSOR_UP_ONE_LEVEL = '\x1b[1A'

message_number_we_are_on = 0 # counts number of delievered messages
p_queue_deliverable = Queue.PriorityQueue() # holds queue of processed msg's
local_messages = {} # maps seq_num to msg
received_proposals = {} # maps seq_num to tuple containing current max and number of people that have sent in proposals

heartbeat_arr = {} # maps pid to (last time stamp of heartbeat, username, sock) # [-1 for x in range(10)]
current_milli_time = lambda: int(round(time.time() * 1000))
HEART_BEAT_TIME = .2
WORST_CASE_DETECTION_TIME = 100 * HEART_BEAT_TIME * 1000
address_to_send_socket = {}
client_socket_to_addr = {}

num_deliverables = 1

def check_for_failures():
    for key in heartbeat_arr.keys():
        if heartbeat_arr[key][0] != -1 and current_milli_time() - heartbeat_arr[key][0] > WORST_CASE_DETECTION_TIME:
    
            heartbeat_arr[key] = (-1, heartbeat_arr[key][1], heartbeat_arr[key][2])
            sock = heartbeat_arr[key][2]
            addr = client_socket_to_addr[sock]
            sock.close()
            send_sock = address_to_send_socket[addr]
            send_sock.close()
            del address_to_send_socket[addr]
            del SEND_SOCKS[send_sock]
            del CLIENTS[sock]

            failure_msg = heartbeat_arr[key][1] + ' disconnected and left the chat\n'
            send_message('f|' + str(key) + '|' + failure_msg)
            sys.stdout.write('\r' + failure_msg)
            sys.stdout.flush()
            prompt()
            # check if messages can be sent now that there is one less client
            for key_proposals in received_proposals:
                send_agreed_msg_if_ready(str(PROCESS_NUM), key_proposals)

def handleFailures():
    # send heartbeat msg
    while 1:
        time.sleep(HEART_BEAT_TIME)
        send_message('we here boizzz|' + str(PROCESS_NUM) + '|')

def handleConnections():
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(10)

    print "Chat server started on port " + str(PORT)
    
    while 1:
        read_sockets,write_sockets,error_sockets = select.select([server_socket],[],[])
        for sock in read_sockets:
            try:
                sockfd, addr = server_socket.accept()
                username_pid_client = sockfd.recv(RECV_BUFFER)
                username_pid_split = username_pid_client.split('|')
                client_socket_to_addr[sockfd] = addr[0]
                CLIENTS[sockfd] = username_pid_split[0]
                heartbeat_arr[int(username_pid_split[1])] = (-1, username_pid_split[0], sockfd)
            except:
                break

def prompt():
    sys.stdout.write('<' + USERNAME + '> ')
    sys.stdout.flush()

# PROCESS Number < sequence number < proposed number < agreed # < msg < ip_address
def create_process_init_message():
    return str(PROCESS_NUM) + '<' + str(number_of_multicasts) + '<' + '<' + '<' + '<' + socket.gethostbyname(socket.gethostname()) + '<'

def create_proposed_order_number_message(pid, seq_num, prop_num):
    return pid + '<' + seq_num + '<' + str(prop_num) + '<' + '<' + '<'

# assuming msg starts with '<'
def create_agreed_number_message(pid, seq_num, agreed_num, msg):
    return pid + '<' + str(seq_num) + '<' + '<' + str(agreed_num) + msg + '<'

def send_agreed_msg_if_ready(pid, seq_num):
    if received_proposals[seq_num][1] == len(CLIENTS.keys()):
        message_number_we_are_on = max(message_number_we_are_on, received_proposals[seq_num][0])
        send_message(create_agreed_number_message(pid, seq_num, received_proposals[seq_num][0], local_messages[seq_num]))
        del received_proposals[seq_num]
        del local_messages[seq_num]

def send_proposed_msg(pid, seq_num, ip_address):
    # address_to_send_socket[ip_address].send(create_proposed_order_number_message(pid, seq_num, message_number_we_are_on))
    message_number_we_are_on += 1
    send_message(create_proposed_order_number_message(pid, seq_num, message_number_we_are_on))

def check_if_messages_can_be_delievered():
    global message_number_we_are_on
    global num_of_deliverables
    while len(p_queue_deliverable.queue) > 0 and  p_queue_deliverable.queue[0][0] == num_of_deliverables:
        sender_sock = p_queue_deliverable.queue[0][1] 
        if heartbeat_arr[sender_sock][0] == -1:
            p_queue_deliverable.get()
        else:
            sys.stdout.write(ERASE_LINE + '\r')
            sys.stdout.write(p_queue_deliverable.get()[2])
            sys.stdout.flush()
            if len(p_queue_deliverable.queue) > 0 and p_queue_deliverable.queue[0][0] == num_of_deliverables:
                num_of_deliverables -= 1
            num_of_deliverables += 1
            prompt()

def send_message(msg):
    for s in SEND_SOCKS.keys()[::-1]:
        try:
            s.send(msg)
        except:
            pass

def connect_to_send_socks():
    for host in HOST:
        if host not in SEND_SOCKS.values():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((host, PORT))
                SEND_SOCKS[s] = host
                address_to_send_socket[host] = s
                s.send(USERNAME + '|' + str(PROCESS_NUM))
            except:
                pass

def signal_handler(signal, frame):
    for elem in SEND_SOCKS.keys():
        elem.close()
    for elem in CLIENTS.keys():
        if elem != sys.stdin:
            elem.close()
    server_socket.close()
    thread_connect.join()
    thread_fail.join()
    sys.exit()

if __name__=="__main__":
    if(len(sys.argv) != 2):
        print 'Usage : python distributed_group_chat.py username'
        sys.exit()

    USERNAME = sys.argv[1]
    
    signal.signal(signal.SIGINT, signal_handler)

    thread_fail = threading.Thread(target = handleFailures)
    thread_connect = threading.Thread(target = handleConnections)
    thread_connect.start()
    thread_fail.start()
    connect_to_send_socks()
    prompt()

    while 1:
        read_sockets, write_sockets, error_sockets = select.select(CLIENTS.keys() + [sys.stdin], [], [], 0)

        # try connecting to sockets before a send messages
        connect_to_send_socks()
        
        for sock in read_sockets:
            if sock == sys.stdin:
                msg = sys.stdin.readline()
                if len(msg) > 1:
                    sys.stdout.write(CURSOR_UP_ONE_LEVEL)
                    sys.stdout.flush()
                    number_of_multicasts += 1
                    local_messages[number_of_multicasts] = '<' + USERNAME + '> ' + msg
                    send_message(create_process_init_message())
                else:
                    prompt()
            else:
                msg = ''
                if sock in CLIENTS:
                    msg = sock.recv(RECV_BUFFER)
                else:
                    continue
                data_split = msg.split('<')
                if len(msg) == 0:
                    pass
                elif msg[0] == 'w':
                    heartbeat_msg_split = msg.split('|')
                    key = int(heartbeat_msg_split[1])
                    heartbeat_arr[key] = (current_milli_time(), heartbeat_arr[key][1], heartbeat_arr[key][2])
                    check_for_failures()
                elif msg[0] == 'f':
                    failure_msg_split = msg.split('|')
                    pid = int(failure_msg_split[1])
                    if heartbeat_arr[pid][0] != -1:
                        failed_sock = heartbeat_arr[pid][2]
                        heartbeat_arr[pid] = (-1, heartbeat_arr[pid][1], failed_sock)
                        sys.stdout.write('\r' + failure_msg_split[2])
                        sys.stdout.flush()
                        del CLIENTS[failed_sock]
                        failed_sock.close()
                        send_message(msg)
                        prompt()
                elif len(data_split[3]) > 0 and len(data_split[4]) > 0: # send process gave agreed_num for his msg. Add it to your p_queue
                    process_id = int(data_split[0])
                    index = process_id - 1
                    if sequence_numbers_of_processes[index] < int(data_split[1]):
                        sequence_numbers_of_processes[index] = int(data_split[1])
                        if process_id != PROCESS_NUM:
                            send_message(msg)
                        nummber_of_message_we_are_on = max(number_of_message_we_are_on, int(data_split[3]))
                        p_queue_msg = '<'
                        for i in range(4, len(data_split) - 1):
                            p_queue_msg += data_split[i]
                        p_queue_deliverable.put((int(data_split[3]), int(data_split[0]), p_queue_msg))
                        check_if_messages_can_be_delievered()
                        
                elif len(data_split[0]) > 0 and len(data_split[1]) > 0 and len(data_split[2]) > 0: # check if pid is our pid, if so, find max prop_num
                    if int(data_split[0]) == PROCESS_NUM:
                        seq_num = int(data_split[1])
                        if seq_num not in received_proposals:
                            received_proposals[seq_num] = (int(data_split[2]), 1)
                        else:
                            curr_val = received_proposals[seq_num]
                            max_num = max(curr_val[0], int(data_split[2]))
                            received_proposals[seq_num] = (max_num, curr_val[1] + 1)

                        send_agreed_msg_if_ready(data_split[0], seq_num)

                elif len(data_split[0]) > 0 and len(data_split[1]) > 0: # a process declared they want to send a msg, send a prop_num
                    send_proposed_msg(data_split[0], data_split[1], data_split[5])
