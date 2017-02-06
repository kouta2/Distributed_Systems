import socket, select
 
CLIENTS = {}
RECV_BUFFER = 4096
PORT = 5000

def broadcast_data (sock, message):
    for socket in CLIENTS.keys():
        if socket != server_socket and socket != sock :
            try :
                socket.send(message)
            except :
                if socket in CLIENTS:
                    socket.close()
                    del CLIENTS[socket]
 
if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(10)
 
    CLIENTS[server_socket] = 'SERVER'
 
    print "Chat server started on port " + str(PORT)
 
    while 1:
        read_sockets,write_sockets,error_sockets = select.select(CLIENTS.keys(),[],[])
 
        for sock in read_sockets:
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                CLIENTS[sockfd] = ''
            else:
                try:
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        if data[0:4] == "?!@#":
                            CLIENTS[sock] = data[4:]
                            print CLIENTS[sock] + " connected"
                            broadcast_data(sockfd,"\r" + CLIENTS[sock] + " entered room\n")
                        else:
                            broadcast_data(sock, "\r" + '<' + CLIENTS[sock] + '> ' + data)                
                 
                except:
                    if sock in CLIENTS.keys():
                        broadcast_data(sock, CLIENTS[sock] + " is offline")
                        print CLIENTS[sock] + " is offline"
                        sock.close()
                        del CLIENTS[sock]
                    continue
     
    server_socket.close()
