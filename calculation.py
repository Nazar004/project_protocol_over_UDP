# calculation.py
import zlib

def calculate_checksum(data):
    return zlib.crc32(data) & 0xFFFF

def fragment_data(data, max_fragment_size):
    fragments = []
    total_size = len(data)
    num_fragments = (total_size + max_fragment_size - 1) // max_fragment_size 


    for frag_num in range(num_fragments):
        start = frag_num * max_fragment_size
        end = start + max_fragment_size
        fragment = data[start:end]
        fragments.append((frag_num, fragment, frag_num == num_fragments - 1)) 

    return fragments

def fragment_change(new_size=None):
    if new_size is None:
        try:
            new_size = int(input("Enter new fragment size: "))
            if new_size <= 0:
                raise ValueError("Fragment size must be greater than 0.")
        except ValueError as e:
            print(f"Error: {e}")
            return None
    print(f"Fragment size successfully updated to {new_size}.")
    return new_size