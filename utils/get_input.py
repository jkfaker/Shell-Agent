def get_input() -> str:
    print("Insert your text. Enter 'q' or press Ctrl-D (or Ctrl-Z on Windows) to end.")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "q":
            break
        contents.append(line)
    text = "\n".join(contents)
    print(f"用户输入：{text}")
    return text

if __name__ == "__main__":
    print(get_input())


def agree_to_continue():
  while True:
    user_input = input("是否继续执行？(y/n)")
    if user_input in ["y", "Y", "yes", "Yes"]:
      print("获得用户许可，继续执行！")
      return True
    elif user_input in ["n", "N", "no", "No"]:
      print("用户终止程序，退出！")
      return False
    else:
      print("输入无效，请输入 y 或 n。")
