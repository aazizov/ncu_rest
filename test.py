
original_string = "This is a sample string to demonstrate removing characters."
trimmed_string = original_string[10:]
print(trimmed_string)

input_dec = 15

input_str = str(input_dec)
input_hex = hex(input_dec) #[2:4]

input_dec_from_hex = int(input_hex, 16)
input_binary_from_dec = format(int(input_hex, 16), 'b')

#input_binary_from_dec = format(input_dec, 'b') #bin(input_dec)
input_binary_from_hex = int(input_hex, 16)
input_binary_from_dec_from_hex = int(input_hex, 16)

#input_binary2 = f'{input_dec:b}' #bin(input_dec)
input_bytes = bytes(input_str, 'utf-8')
#input_bytes2 = input_dec.to_bytes(1, byteorder='little')
#input_str2 = str(input_bytes2)[4:6]

input_str3 = str(input_dec.to_bytes(1, byteorder='little'))[4:6]
input_str3_full = input_dec.to_bytes(1, byteorder='little').hex() #str(input_dec.to_bytes(1, byteorder='little'))
input_bytes3 = bytes("None", 'utf-8')

print("input_dec_from_hex = {}".format(input_dec_from_hex))
print("input_str3 = {}".format(input_str3))
print("input_str3_full = {}".format(input_str3_full))
print("input_hex = {}".format(input_hex))
print("input_binary_from_dec = {}".format(input_binary_from_dec))
print("input_binary_from_hex = {}".format(input_binary_from_hex))
print("input_bytes3 = {}".format(input_bytes3))




'''
    while count_of_board >= 1:
        result_one_board = response['response_hex'][0:18]
        result = result_one_board[8:10] + result_one_board[6:8]  # reverse bytes = 0900 -> 0009
        result_bin = format(int(result, 16), 'b')[::-1]
        if len(result_bin) < 16:
            result_bin = result_bin.ljust(16, '0')

        lock_index = 0
        locks_array = [None] * 16  # Initial empty Array
        while lock_index < 16:
            locks_array[lock_index] = result_bin[lock_index]
            lock_index = lock_index + 1
        response_result = {"Board#" : count_of_board,
                           "Lock#1": locks_array[0],
                           "Lock#2": locks_array[1],
                           "Lock#3": locks_array[2],
                           "Lock#4": locks_array[3],
                           "Lock#5": locks_array[4],
                           "Lock#6": locks_array[5],
                           "Lock#7": locks_array[6],
                           "Lock#8": locks_array[7],
                           "Lock#9": locks_array[8],
                           "Lock#10": locks_array[9],
                           "Lock#11": locks_array[10],
                           "Lock#12": locks_array[11],
                           "Lock#13": locks_array[12],
                           "Lock#14": locks_array[13],
                           "Lock#15": locks_array[14],
                           "Lock#16": locks_array[15],
                           }

        response['response_hex'] = response['response_hex'][18:]    # Trim Left 18 symbols for One Board
        count_of_board = count_of_board - 1
'''
