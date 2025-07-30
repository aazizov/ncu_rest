
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