-- Registrácia nového protokolu
myproto = Proto("myproto", "My Custom Protocol")

-- Definovanie polí protokolu
local fields = myproto.fields
fields.length = ProtoField.uint16("myproto.length", "Length")
fields.message_id = ProtoField.uint16("myproto.message_id", "Message ID")
fields.seq_num = ProtoField.uint16("myproto.seq_num", "Sequence Number")
fields.ack_num = ProtoField.uint16("myproto.ack_num", "Acknowledgment Number")
fields.frag_num = ProtoField.uint16("myproto.frag_num", "Fragment Number")
fields.window = ProtoField.uint8("myproto.window", "Window")
fields.flags = ProtoField.uint8("myproto.flags", "Flags")
fields.msg_type = ProtoField.uint16("myproto.msg_type", "Message Type")
fields.data_offset = ProtoField.uint16("myproto.data_offset", "Data Offset")
fields.checksum = ProtoField.uint16("myproto.checksum", "Checksum")

-- Port používaný pre identifikáciu protokolu
local MYPROTO_PORT = 5001

-- Dekódovanie paketov
function myproto.dissector(buffer, pinfo, tree)
    -- Skontroluj veľkosť paketu
    if buffer:len() < 2 then
        return
    end

    -- Nastavenie informácií o pakete vo Wiresharku
    pinfo.cols.protocol = "proto"

    -- Pridanie uzla protokolu do stromu
    local subtree = tree:add(myproto, buffer(), "My Custom Protocol")

    -- Dekódovanie jednotlivých polí
    subtree:add(fields.length, buffer(0, 2))
    subtree:add(fields.message_id, buffer(2, 2))
    subtree:add(fields.seq_num, buffer(4, 2))
    subtree:add(fields.ack_num, buffer(6, 2))
    subtree:add(fields.frag_num, buffer(8, 2))
    subtree:add(fields.window, buffer(10, 1))
    subtree:add(fields.flags, buffer(11, 1))
    subtree:add(fields.msg_type, buffer(12, 2))
    subtree:add(fields.data_offset, buffer(14, 2))
    subtree:add(fields.checksum, buffer(16, 2))
end

-- Registrácia dissektora na špecifický UDP port
local udp_table = DissectorTable.get("udp.port")
udp_table:add(MYPROTO_PORT, myproto)
