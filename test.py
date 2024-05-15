import time

count = 0
while count < 5:
    print(f"current count is {count}")
    time.sleep(1)
    count += 1
    if count == 3:
        raise "error info"
