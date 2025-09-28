import re
from collections import defaultdict

def analyze_text_simple(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            text = file.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл {input_file} не найден")
        return

    words = re.findall(r'\b[а-яА-ЯёЁa-zA-Z]+\b', text)
    total_words = len(words)

    word_count = defaultdict(int)
    for word in words:
        word_lower = word.lower()
        word_count[word_lower] += 1

    with open(output_file, 'w', encoding='utf-8') as xml_file:
        xml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        xml_file.write('<text_analysis>\n')
        xml_file.write(f'  <total_words>{total_words}</total_words>\n')
        xml_file.write('  <word_statistics>\n')

        for word in sorted(word_count.keys()):
            xml_file.write(f'    <word>\n')
            xml_file.write(f'      <name>{word}</name>\n')
            xml_file.write(f'      <count>{word_count[word]}</count>\n')
            xml_file.write(f'    </word>\n')

        xml_file.write('  </word_statistics>\n')
        xml_file.write('</text_analysis>\n')

    print(f"Анализ завершен. Результаты сохранены в {output_file}")
    print(f"Всего проанализированно слов: {len(words)}")
    print(f"уникальных слов: {len(word_count)}")

analyze_text_simple("input.txt", "statistics.xml")
