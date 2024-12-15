import json
from bs4 import BeautifulSoup

def getJSONFromHTML(path_in: str, path_out: str, save=False) -> dict:
    # Загрузка HTML контента из файла
    with open(path_in, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Парсинг HTML контента через BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Извлечение названия и кода индикатора
    indicators_with_names = []
    for link in soup.find_all('a', href=True):
        if '/indicator/' in link['href']:
            indicator_code = link['href'].split('/indicator/')[1].split('?')[0]
            indicator_name = link.get_text(strip=True)
            indicators_with_names.append({"name": indicator_name, "indicator": indicator_code})
    
    # Формирование валидного для MongoDB словаря    
    for ind, i in enumerate(indicators_with_names):
        i["_id"] = ind
    # Формирование JSON структуры
    indicators_json = {"indicators": indicators_with_names}

    # Запись JSON файла 
    json_output = json.dumps(indicators_json, ensure_ascii=False, indent=4)

    if save:
        with open(path_out, "w", encoding="utf-8") as json_file:
           json_file.write(json_output)

    return indicators_json
