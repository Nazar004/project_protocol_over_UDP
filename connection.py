# connection.py
import socket
import time
import messages

def create_server(our_receive_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server.bind(("0.0.0.0", our_receive_port))
        print(f"Server listening on port {our_receive_port}")
    except Exception as e:
        print(f"Failed to bind server on port {our_receive_port}: {e}")
        server.close()
        exit(1)
    return server

def ping(foreign_ip, foreign_port, client_socket, pong_received):
    messages.sending(client_socket, "PING", foreign_ip, foreign_port)
    for _ in range(50): 
        if pong_received[0]:
            return True
        time.sleep(0.1)
    return False

def keep_alive(client_socket, foreign_ip, foreign_send_port, running, connection_status, missed_heartbeats, consecutive_ack, pause_keep_alive):
    while running[0]:
        if not pause_keep_alive[0] and connection_status[0]:
            messages.sending(client_socket, "HEARTBEAT", foreign_ip, foreign_send_port)
            print("HEATBEAT SEND")
            client_socket.settimeout(5)
            try:
                ack, _ = client_socket.recvfrom(1024)
                if ack.decode('utf-8') == "HEARTBEAT_ACK":
                    missed_heartbeats[0] = 0
            except socket.timeout:
                missed_heartbeats[0] += 1
            if missed_heartbeats[0] >= 3:
                print("No response to HEARTBEAT for 3 attempts. Closing connection.")
                messages.sending(client_socket, "\exit", foreign_ip, foreign_send_port)
                connection_status[0] = False
                running[0] = False 
                client_socket.close()
                break
        else:
            time.sleep(1) 
