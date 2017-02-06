# telnet program example
import socket, select, string, sys
 
def prompt() :
    sys.stdout.write('<You> ')
    sys.stdout.flush()
 
#main function
if __name__ == "__main__":
     
    if(len(sys.argv) != 4) :
        print 'Usage : python client.py hostname port username'
        sys.exit()
     
    host = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3]
     
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     
    try :
        s.connect((host, port))
    except :
        print 'Unable to connect'
        sys.exit()

    s.send("?!@#" + username)
     
    print 'Connected to server. You may send messages!'
    prompt()
     
    while 1:
        socket_list = [sys.stdin, s]
         
        read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
         
        for sock in read_sockets:
            if sock == s:
                data = sock.recv(4096)
                sys.stdout.write(data)
             
            else :
                msg = sys.stdin.readline()
                s.send(msg)
            prompt()
