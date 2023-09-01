test_dict = {'3': 'blue',
             '61': 'red',
             '123': 'yellow'}

#print(sorted(list(test_dict.keys()), key=int)[0])

#print(sorted(list(test_dict.keys()), key=int)[-1])

print(type(sorted(list(test_dict.keys()), key=int)[-1]))

key_ints = []

for str_key in test_dict.keys():
    key_ints.append(int(str_key))

min_key = None

for str_key in test_dict.keys():
    if not min_key:
        min_key = int(str_key)

    elif int(str_key) < min_key:
        min_key = int(str_key)