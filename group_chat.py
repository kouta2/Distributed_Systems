import socket, select, sys, string, threading, Queue

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

message_number_we_are_on = 1 # counts number of delievered messages
p_queue_deliverable = Queue.PriorityQueue() # holds queue of processed msg's
local_messages = {} # maps seq_num to msg
received_proposals = {} # maps seq_num to tuple containing current max and number of people that have sent in proposals

def handleConnections():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(10)

    print "Chat server started on port " + str(PORT)
    
    while 1:
        read_sockets,write_sockets,error_sockets = select.select([server_socket],[],[])
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

'''
def create_message(msg):
    # PROCESS Number < sequence number < proposed number < agreed # < msg
    return str(PROCESS_NUM) + '<' + str(number_of_multicasts) + '<' + '<' + USERNAME + '> ' + msg
'''

# PROCESS Number < sequence number < proposed number < agreed # < msg
def create_process_init_message():
    return str(PROCESS_NUM) + '<' + str(number_of_multicasts) + '<' + '<' + '<'

def create_proposed_order_number_message(pid, seq_num, prop_num):
    return pid + '<' + seq_num + '<' + str(prop_num) + '<' + '<'

# assuming msg starts with '<'
def create_agreed_number_message(pid, seq_num, agreed_num, msg):
    return pid + '<' + str(seq_num) + '<' + '<' + str(agreed_num) + msg

def send_agreed_msg_if_ready(pid, seq_num):
    if received_proposals[seq_num][1] == len(CLIENTS.keys()):
        send_message(create_agreed_number_message(pid, seq_num, received_proposals[seq_num][0], local_messages[seq_num]))
        del received_proposals[seq_num]
        del local_messages[seq_num]

def send_proposed_msg(pid, seq_num):
    send_message(create_proposed_order_number_message(pid, seq_num, message_number_we_are_on))

def check_if_messages_can_be_delievered():
    global message_number_we_are_on
    while len(p_queue_deliverable.queue) > 0 and  p_queue_deliverable.queue[0][0] == message_number_we_are_on:
        sys.stdout.write(ERASE_LINE + '\r')
        sys.stdout.write(p_queue_deliverable.get()[1])
        sys.stdout.flush()
        message_number_we_are_on += 1
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
                if len(msg) > 1:
                    sys.stdout.write(CURSOR_UP_ONE_LEVEL)
                    sys.stdout.flush()
                    # prompt()
                    number_of_multicasts += 1
                    local_messages[number_of_multicasts] = '<' + USERNAME + '> ' + msg
                    send_message(create_process_init_message())
                '''
                msg = sys.stdin.readline()
                prompt()
                if len(msg) > 1:
                    number_of_multicasts += 1
                    send_message(create_message(msg))
                    sequence_numbers_of_processes[PROCESS_NUM - 1] = number_of_multicasts
                '''
            else:
                msg = sock.recv(RECV_BUFFER)
                data_split = msg.split('<')
                if len(msg) == 0:
                    sys.stdout.write("\r" + CLIENTS[sock] + " disconnected and left the room\n")
                    sys.stdout.flush()
                    del CLIENTS[sock]
                    DISCONNECTED_CLIENTS.add(sock)
                    sock.close()
                    prompt()    
                elif len(data_split[3]) > 0 and len(data_split[4]) > 0: # send process gave agreed_num for his msg. Add it to your p_queue
                    process_id = int(data_split[0])
                    index = process_id - 1
                    if sequence_numbers_of_processes[index] < int(data_split[1]):
                        sequence_numbers_of_processes[index] = int(data_split[1])
                        if process_id != PROCESS_NUM:
                            send_message(msg)
                        p_queue_deliverable.put((int(data_split[3]), '<' + data_split[4]))
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
                    send_proposed_msg(data_split[0], data_split[1])
                '''
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
                        sequence_numbers_of_processes[index] = int(data_process[1])
                        if process_id != PROCESS_NUM:
                            send_message(msg)
                        print_msg = '<'
                        for i in range(2, len(data_process)):
                            print_msg += data_process[i]
                        sys.stdout.write('\r' + print_msg)
                        sys.stdout.flush()
                        prompt()
                '''
