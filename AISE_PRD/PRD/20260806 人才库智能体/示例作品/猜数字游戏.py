# 猜数字游戏（AI 提示版）
import random

target = random.randint(1, 100)
print("我想了一个 1-100 之间的数字，你来猜猜看！")
tries = 0
while True:
    try:
        guess = int(input("请输入你的猜测："))
    except ValueError:
        print("请输入数字哦")
        continue
    tries += 1
    if guess < target:
        print("太小了，再大一点")
    elif guess > target:
        print("太大了，再小一点")
    else:
        print(f"恭喜！你用了 {tries} 次猜中了数字 {target}")
        if tries <= 5:
            print("评价：你是猜数字高手！")
        elif tries <= 10:
            print("评价：不错，继续加油！")
        else:
            print("评价：可以试试二分查找法，会更高效")
        break
