import os
import sys
import difflib
import re
import threading
import queue


# Маскирование дат и путей из строк
def remove_from_lines(line):
    line = re.sub(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}", "", line)
    line = re.sub(r"[\/\\].*?[\/\\]", "", line)
    return line.strip()


# Маскирование дат и путей из текста с удалением пустых строк
def remove_from_text(text):
    return [remove_from_lines(line) for line in text if line.strip()]


# Проверка существования файлов
def existence_check(filepaths):
    for path in filepaths:
        if not os.path.exists(path):
            print(f"Файл {path} не найден.")
            sys.exit("\nВыполнение остановлено.")


# Проверка аргументов
def arg_check(command):
    if len(command) < 3:
        print("Формат ввода: python compare.py <файл1> <файл2> [<файл3> ...]")
        sys.exit("\nВыполнение остановлено.")


# Открытие файла
def get_text_threaded(filepath, result_queue):
    with open(filepath, "r", encoding="utf-8") as file:
        text = file.readlines()
    result_queue.put((filepath, text))


# Окрашивание линий
def colored(text, color):
    # Словарь цветов ANSI для окрашивания
    color_dictionary = {
        "red": "\033[91m",
        "green": "\033[92m",
        "reset": "\033[0m"  # Для сброса цвета
    }
    return f"{color_dictionary[color]}{text}{color_dictionary['reset']}"


# Цветной вывод по типу строк
def colored_diff(diff):
    for line in diff:
        # Убедимся, что каждая строка заканчивается символом новой строки
        if not line.endswith("\n"):
            line += "\n"
        
        # Цветной вывод
        if line.startswith("+"):
            print(colored(line, "green"), end="")
        elif line.startswith("-"):
            print(colored(line, "red"), end="")
        else:
            print(line, end="")


# Сравнение двух файлов
def compare_two_files(path1, path2):
    result_queue = queue.Queue()

    # Создаем потоки для чтения файлов
    thread1 = threading.Thread(target=get_text_threaded, args=(path1, result_queue))
    thread2 = threading.Thread(target=get_text_threaded, args=(path2, result_queue))

    # Запускаем потоки
    thread1.start()
    thread2.start()

    # Ожидаем завершения потоков
    thread1.join()
    thread2.join()

    # Получаем результаты из очереди
    result1 = result_queue.get()
    result2 = result_queue.get()

    # Извлекаем тексты
    text1 = remove_from_text(result1[1])
    text2 = remove_from_text(result2[1])

    # Проверяем, отличаются ли файлы только временем и местом сборки
    if text1 == text2:
        print(f"Файлы {result1[0]} и {result2[0]} отличаются только временем и местом сборки.")
        return

    # Выводим различия
    print(f"\nСравнение {result1[0]} и {result2[0]}:")
    diff = difflib.unified_diff(
        text1, text2,
        fromfile=result1[0],
        tofile=result2[0],
        lineterm=""
    )
    colored_diff(diff)


# Основная логика
def main(filepaths):
    # Проверяем существование файлов
    existence_check(filepaths)

    # Сравниваем файлы попарно
    for i in range(1, len(filepaths)):
        compare_two_files(filepaths[0], filepaths[i])


# Точка входа
if __name__ == "__main__":
    # Проверяем аргументы на минимум
    arg_check(sys.argv)

    # Получаем список файлов (исключаем первый аргумент, это имя скрипта)
    filepaths = sys.argv[1:]

    # Запускаем основную логику
    main(filepaths)