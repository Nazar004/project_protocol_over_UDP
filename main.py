# main.py
import socket
import threading
import messages
import connection
import time
import video
import calculation

def main():
    pong_received = [False]
    running = [True]
    connection_status = [True]
    missed_heartbeats = [0]
    consecutive_ack = [0]
    pause_keep_alive = [False]
    last_frag_end = False

    our_receive_port = int(input("Our port for receiving messages: "))
    foreign_ip = input("IP address of another node: ")
    foreign_send_port = int(input("Port of another node to send messages: "))
    our_send_port = int(input("Our port for sending messages: "))
    max_fragment_size = int(input("Maximum fragment size (bytes): "))

    receive_server = connection.create_server(our_receive_port)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(("0.0.0.0", our_send_port))

    def process_pong():
        if not pong_received[0]:
            pong_received[0] = True
            connection_status[0] = True
            print("PONG received, connection established.")
            messages.sending(client_socket, "PONG", foreign_ip, foreign_send_port)

    thread_receive = threading.Thread(
        target=messages.receive,
        args=(
            receive_server,
            client_socket,
            foreign_ip,
            foreign_send_port,
            process_pong,
            running,
            connection_status,
            missed_heartbeats,
            consecutive_ack,
            pause_keep_alive,
            last_frag_end,
        )
    )
    thread_receive.daemon = True
    thread_receive.start()

    print("Sending initial PING to establish connection")
    connection.ping(foreign_ip, foreign_send_port, client_socket, pong_received)

    while not pong_received[0]:
        print("Waiting for PONG response...")
        time.sleep(5)

    print("Connection established!")

    time.sleep(1)

    def keep_alive_wrapper():
        connection.keep_alive(
            client_socket,
            foreign_ip,
            foreign_send_port,
            running,
            connection_status,
            missed_heartbeats,
            consecutive_ack,
            pause_keep_alive,
        )

    thread_keep_alive = threading.Thread(target=keep_alive_wrapper)
    thread_keep_alive.daemon = True
    thread_keep_alive.start()

    while running[0] and connection_status[0]:
        try:
            message = input("Write a message ('exit' for closing, 'file' for sending a file, 'size' for changing max size of fragment): ").strip()

            missed_heartbeats[0] = 0

            if message.lower() == "exit":
                running[0] = False
                connection_status[0] = False
                messages.exit_socket(client_socket, foreign_ip, foreign_send_port)

            elif message.lower() == "file":
                pause_keep_alive[0] = True
                messages.sending(client_socket, "FILE_RECEIVE", foreign_ip, foreign_send_port)
                print("Waiting for confirmation to send the file...")
                time.sleep(2) 

                file_path = input("Enter the path of the file to send: ").strip()
                video.send_file(client_socket, file_path, foreign_ip, foreign_send_port, max_fragment_size)
            
            elif message.lower() == "size":
                try:
                    new_size = int(input("Enter the new maximum fragment size (bytes): "))
                    if new_size <= 0:
                        print("Fragment size must be greater than 0.")
                        continue

                    size_change_message = f"SIZE_CHANGE:{new_size}"
                    messages.sending(client_socket, size_change_message, foreign_ip, foreign_send_port)
                    print(f"Sending new fragment size: {new_size} bytes.")
                    
                    max_fragment_size = calculation.fragment_change(new_size)
                    print(f"Fragment size updated locally to {max_fragment_size} bytes.")
            
                except ValueError:
                    print("Invalid input. Please enter a valid number.")

            else:
                messages.sending(client_socket, message, foreign_ip, foreign_send_port)
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")

    print("Connection terminated. Exiting program.")
    receive_server.close()
    client_socket.close()

if __name__ == "__main__":
    main()