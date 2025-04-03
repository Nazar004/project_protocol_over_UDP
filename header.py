import struct

HEADER_FORMAT = '!HHHHHBBHHH'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

def create_header(length, message_id, seq_num, ack_num, frag_num, window, flags, msg_type, data_offset, checksum):
    header = struct.pack(
        HEADER_FORMAT,
        length,
        message_id,
        seq_num,
        ack_num,
        frag_num,
        window,
        flags,
        msg_type,
        data_offset,
        checksum
    )
    return header

def parse_header(header_data):
    header_fields = struct.unpack(HEADER_FORMAT, header_data)
    return header_fields