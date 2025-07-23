#print("Helllo World")

input_dec = 2

input_str = str(input_dec)
#input_hex = hex(input_dec)
#input_binary = format(input_dec, 'b') #bin(input_dec)
#input_binary2 = f'{input_dec:b}' #bin(input_dec)
input_bytes = bytes(input_str, 'utf-8')
#input_bytes2 = input_dec.to_bytes(1, byteorder='little')
#input_str2 = str(input_bytes2)[4:6]

input_str3 = str(input_dec.to_bytes(1, byteorder='little'))[4:6]
input_bytes3 = bytes("None", 'utf-8')

print("input_str3 = {}".format(input_str3))
#print("input_hex = {}".format(input_hex))
#print("input_binary = {}".format(input_binary))
print("input_bytes3 = {}".format(input_bytes3))