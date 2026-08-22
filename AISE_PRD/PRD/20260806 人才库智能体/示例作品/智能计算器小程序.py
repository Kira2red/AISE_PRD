# 智能计算器小程序
# 支持四则运算的交互式命令行计算器
def add(a, b):
    return a + b

def sub(a, b):
    return a - b

def mul(a, b):
    return a * b

def div(a, b):
    if b == 0:
        return "错误：除数不能为零"
    return a / b

print("欢迎使用智能计算器")
print("支持运算：+ - * /，输入 q 退出")
while True:
    expr = input("请输入表达式（如 1+2）：").strip()
    if expr.lower() == "q":
        print("再见！")
        break
    for op, fn in [("+", add), ("-", sub), ("*", mul), ("/", div)]:
        if op in expr:
            a, b = expr.split(op)
            result = fn(float(a), float(b))
            print(f"{a} {op} {b} = {result}")
            break
    else:
        print("无法识别该表达式，请重试")
