s = input()
'''a = s.encode('cp1251')
b = a.decode('utf-8')
print(b)'''

a = s.encode('cp1251').decode('utf-8')
print(a)
