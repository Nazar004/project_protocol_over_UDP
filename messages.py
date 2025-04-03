# messages.py
import header
import calculation
import video
import os
import random

def sending(client_socket, message, foreign_ip, foreign_send_port, max_fragment_size=1024, inject_error=True):

    message_bytes = message.encode('utf-8')
    fragments = calculation.fragment_data(message_bytes, max_fragment_size)

    for frag_num, fragment, is_last in fragments:
        flags = 0x01 if is_last else 0x00
        checksum = calculation.calculate_checksum(fragment)
        if inject_error and random.random() < 0.03:
            print(f"Injecting error into fragment {frag_num + 1}")
            fragment = b"corrupted_data" 
            checksum = 0xFFFF 

        header_data = header.create_header(
            length=len(fragment),
            message_id=0,
            seq_num=0,
            ack_num=0,
            frag_num=frag_num,
            window=0,
            flags=flags,
            msg_type=0,
            data_offset=0,
            checksum=checksum
        )

        packet = header_data + fragment

        try:
            client_socket.sendto(packet, (foreign_ip, foreign_send_port))
            print(f"Fragment {frag_num + 1}/{len(fragments)} sent.")
        except Exception as e:
            print(f"Error sending fragment {frag_num + 1}: {e}")


def receive(
    server, client_socket, foreign_ip, foreign_send_port, process_pong, running, connection_status, missed_heartbeats, consecutive_ack, pause_keep_alive, last_frag_end
):
    while running[0]:
        try:
            message, addr = server.recvfrom(1500)
            header_data = message[:header.HEADER_SIZE]
            fragment_data = message[header.HEADER_SIZE:]

            _, _, _, _, _, _, flags, _, _, _ = header.parse_header(header_data)

            decoded_message = fragment_data.decode('utf-8').strip()
            if decoded_message == "FILE_RECEIVE":
                print("Received FILE_RECEIVE. Preparing to save the file.")
                pause_keep_alive[0] = True

                try:
                    output_directory = input("Enter the directory to save the file: ").strip()
                    while not os.path.isdir(output_directory):
                        print("Invalid directory. Please try again.")
                        output_directory = input("Enter the directory to save the file: ").strip()

                    video.receive_file(server, client_socket, output_directory, running, foreign_ip, foreign_send_port, pause_keep_alive)
                finally:
                    # Возобновляем keep-alive
                    pause_keep_alive[0] = False

            elif decoded_message == "PING":
                print("PING received, sending PONG.")
                sending(client_socket, "PONG", foreign_ip, foreign_send_port)

            elif decoded_message == "PONG":
                print("PONG received.")
                process_pong()

            elif decoded_message == "HEARTBEAT":
                missed_heartbeats[0] = 0
                print("HEARTBEAT received, sending HEARTBEAT_ACK.")
                sending(client_socket, "HEARTBEAT_ACK", foreign_ip, foreign_send_port)

            elif decoded_message == "HEARTBEAT_ACK":
                missed_heartbeats[0] = 0
                print("HEARTBEAT_ACK received.")

            elif decoded_message == "/exit":
                print("Exit signal received. Terminating connection.")
                running[0] = False
                connection_status[0] = False
                break

            elif decoded_message == "STOP_PAUSE":
                pause_keep_alive[0] = False

            elif decoded_message == "FILE_END":
                last_frag_end[0] = True
            elif decoded_message.startswith("SIZE_CHANGE:"):
                try:
                    new_size = int(decoded_message.split(":")[1].strip())
                    if new_size <= 0:
                        print("Invalid fragment size received. It must be greater than 0.")
                        continue
                    
                    max_fragment_size = calculation.fragment_change(new_size)
                    print(f"Fragment size updated to {max_fragment_size} bytes from remote command.")

                except (ValueError, IndexError):
                    print("Invalid SIZE_CHANGE message format received.")
            else:
                print(f"Message received: {decoded_message}")
        except Exception as e:
            print(f"Error in receive: {e}")

def exit_socket(client_socket, foreign_ip, foreign_send_port):
    sending(client_socket, "/exit", foreign_ip, foreign_send_port)
