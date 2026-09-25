import prompt


def welcome():
    print("exit - выйти из программы")
    print("help - справочная информация")

    while True:
        command = prompt.string("Введите команду: ")

        if command == "exit":
            break
        elif command == "help":
            print("exit - выйти из программы")
            print("help - справочная информация")
        else:
            print("Неизвестная команда")