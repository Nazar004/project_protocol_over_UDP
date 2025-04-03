# video.py
import socket
import calculation
import header
import os
import messages
import time
# Updated `send_file` function in `video.py` to handle binary data of all formats properly.
def send_file(client_socket, file_path, foreign_ip, foreign_send_port,max_fragment_size):
    try:
        file_name = os.path.basename(file_path)

        with open(file_path, 'rb') as file:
            file_data = file.read()

        max_data_size = max_fragment_size - header.HEADER_SIZE

        fragments = calculation.fragment_data(file_data, max_data_size)
        total_fragments = len(fragments)
        sent_fragments = {}  # To store sent fragments for retransmission

        print(f"Sending file: {file_name}")
        print(f"Total size: {len(file_data)} bytes, Fragment size: {max_data_size} bytes")
        if len(fragments[-1][1]) != max_data_size:
            print(f"Last fragment size: {len(fragments[-1][1])} bytes")
        print(f"File size: {len(file_data)} bytes, Fragment size: {max_data_size} bytes, Total fragments: {total_fragments}")

        # Signal the start of file transmission
        start_file_message = f"START_FILE:{file_name}"
        print(f"Sending START_FILE signal for: {file_name}")
        messages.sending(client_socket, start_file_message, foreign_ip, foreign_send_port)

        # Send fragments
        for frag_num, fragment, is_last in fragments:
            checksum = calculation.calculate_checksum(fragment)
            flags = 0x01 if is_last else 0x00
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
                checksum=checksum,
            )
            packet = header_data + fragment

            try:
                client_socket.sendto(packet, (foreign_ip, foreign_send_port))
                sent_fragments[frag_num] = packet  # Store for retransmission
                time.sleep(0.01)  # Delay to prevent overloading
                print(f"Fragment {frag_num + 1}/{total_fragments} sent with size: {len(fragment)} bytes.")
            except Exception as e:
                print(f"Error sending fragment {frag_num + 1}: {e}")

        # Handle NACKs
        print("Waiting for NACKs...")
        client_socket.settimeout(2)  # Increased timeout for NACK
        while True:
            try:
                nack_message, _ = client_socket.recvfrom(65535)
                nack_header = header.parse_header(nack_message[:header.HEADER_SIZE])
                nack_frag_num = nack_header[4]  # Fragment number in NACK

                if nack_frag_num in sent_fragments:
                    client_socket.sendto(sent_fragments[nack_frag_num], (foreign_ip, foreign_send_port))
                    print(f"Fragment {nack_frag_num} retransmitted.")
            except socket.timeout:
                print("No more NACKs received.")
                # pause_keep_alive[0] = False

                break
        
        if(frag_num+1 == total_fragments):

            messages.sending(client_socket, "FILE_END", foreign_ip, foreign_send_port)
            print(f"File {file_name} sent successfully.")
            # pause_keep_alive[0] = False

        else: 
            print(f"File {file_name} not sent .")
    except FileNotFoundError:
        print("File not found. Please provide a valid file path.")
    except Exception as e:
        print(f"Error in send_file: {e}")



# Updated `receive_file` function in `video.py` for binary data reception.
def receive_file(server, client_socket, output_directory, running, foreign_ip, foreign_send_port, pause_keep_alive):
    try:
        file_name = None
        file_path = None
        received_fragments = {}
        last_frag_num = None

        print("Waiting to receive file...")

        while running[0]:
            try:
                # Receive packet
                message, addr = server.recvfrom(65535)
                header_data = message[:header.HEADER_SIZE]
                fragment_data = message[header.HEADER_SIZE:]

                # Parse header
                header_fields = header.parse_header(header_data)
                frag_num = header_fields[4]  # Fragment number
                flags = header_fields[6]  # Flags
                checksum = header_fields[-1]  # Checksum

                # Validate checksum
                if calculation.calculate_checksum(fragment_data) != checksum:
                    print(f"Fragment {frag_num} has a checksum error. Requesting retransmission.")
                    # Send NACK for damaged fragment
                    nack_header = header.create_header(
                        length=0,
                        message_id=0,
                        seq_num=0,
                        ack_num=0,
                        frag_num=frag_num,
                        window=0,
                        flags=0x02,  # NACK flag
                        msg_type=0,
                        data_offset=0,
                        checksum=0,
                    )
                    client_socket.sendto(nack_header, (foreign_ip, foreign_send_port))
                    print(f"NACK sent for fragment {frag_num}. Waiting 5 seconds before retry...")
                    time.sleep(5)  # Pause for 5 seconds to visualize the error handling
                    continue

                if frag_num == 0 and fragment_data.startswith(b"START_FILE:"):
                    file_name = fragment_data.split(b"START_FILE:")[1].strip().decode('utf-8', errors='ignore')
                    print(f"Receiving file: {file_name}")
                    file_path = os.path.join(output_directory, file_name)
                    print(f"Creating file at: {file_path}")

                    try:
                        with open(file_path, 'wb') as file:
                            print(f"File {file_name} created successfully.")
                    except Exception as e:
                        print(f"Error creating file {file_name}: {e}")
                        return

                    continue

                # If no file name was received, ignore fragments
                if not file_name:
                    print("No file name received yet. Ignoring fragment.")
                    continue

                # Store received fragment in memory
                if frag_num not in received_fragments:
                    received_fragments[frag_num] = fragment_data
                    print(f"Fragment {frag_num} received successfully and stored.")

                # Send acknowledgment for this fragment
                ack_header = header.create_header(
                    length=0,
                    message_id=0,
                    seq_num=0,
                    ack_num=0,
                    frag_num=frag_num,
                    window=0,
                    flags=0,
                    msg_type=0,
                    data_offset=0,
                    checksum=0,
                )
                try:
                    client_socket.sendto(ack_header, (foreign_ip, foreign_send_port))
                    print(f"ACK sent for fragment {frag_num}.")
                except Exception as e:
                    print(f"Error sending ACK for fragment {frag_num}: {e}")
                    time.sleep(0.1)

                # Determine if this is the last fragment
                if flags & 0x01:  # Last fragment flag
                    last_frag_num = frag_num

                # Write file when all fragments are received
                if file_name and last_frag_num is not None and len(received_fragments) == last_frag_num + 1:
                    print(f"Writing fragments to file {file_name}...")
                    try:
                        with open(file_path, 'wb') as file:
                            for frag_num in range(last_frag_num + 1):
                                if frag_num in received_fragments:
                                    file.write(received_fragments[frag_num])
                        print(f"File {file_name} saved successfully to {file_path}.")
                        print(f"Total file size: {os.path.getsize(file_path)} bytes.")
                        # Inform sender that file transfer is complete
                        messages.sending(client_socket, "FILE_RECEIVE_COMPLETE", foreign_ip, foreign_send_port)
                        break
                    except Exception as e:
                        print(f"Error writing file {file_name}: {e}")

            except Exception as e:
                print(f"Error while receiving fragment: {e}")

    except Exception as e:
        print(f"Error in receive_file: {e}")