import math
total = 0
for x in range(1,1000):
    print(x, end='\t')
    y = math.pow(x,1/2)
    print(round(y,5), end='\t')
    ans = int(y) + (x - math.pow(int(y),2))/(2*y)
    print(round(ans, 5), end = '\t')
    total += ans - y
    print(ans - y)
print('\n', total/100)