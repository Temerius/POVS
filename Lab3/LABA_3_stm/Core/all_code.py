import os

# Каталоги для обхода
dirs = ["./Inc", "./Src"]

# Файл-результат
output_file = os.path.abspath("all_code.txt")

# Список исключений (точные имена файлов)
exclude_files = {
    "stm32f1xx_hal_conf.h",
    "stm32f1xx_it.h",
    "stm32f1xx_hal_msp.c",
    "stm32f1xx_it.c",
    "system_stm32f1xx.c",
}

with open(output_file, "w", encoding="utf-8") as outfile:
    for d in dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for fname in files:
                if fname.endswith((".h", ".c")) and fname not in exclude_files:
                    path = os.path.join(root, fname)
                    print("Writing:", path)   # для отладки
                    outfile.write(f"\n\n// ===== File: {path} =====\n\n")
                    with open(path, "r", encoding="utf-8", errors="ignore") as infile:
                        outfile.write(infile.read())

print("Готово! Итоговый файл:", output_file)
