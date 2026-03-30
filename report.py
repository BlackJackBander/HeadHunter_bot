import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Настройки (те же, что в скрипте парсера)
MONGO_URL = "mongodb://admin:secret_password@localhost:27017"
DB_NAME = "hh_parser"
COLLECTION_NAME = "vacancies"
REPORT_FILE = "vacancy_report.md"

async def generate_markdown():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # 1. Получаем все вакансии (можно добавить фильтр по дате .find({"parsed_at": {"$gte": ...}}))
    cursor = collection.find().sort("parsed_at", -1)
    vacancies = await cursor.to_list(length=100) # Берем последние 100 для отчета

    if not vacancies:
        print("База пуста. Нечего анализировать.")
        return

    # 2. Собираем статистику
    total = len(vacancies)
    cities = {}
    skills_map = {}
    
    for v in vacancies:
        # Считаем по городам
        area = v.get('area', 'Не указан')
        cities[area] = cities.get(area, 0) + 1
        
        # Считаем популярные навыки
        for skill in v.get('skills', []):
            skills_map[skill] = skills_map.get(skill, 0) + 1

    # Сортируем навыки по популярности
    top_skills = sorted(skills_map.items(), key=lambda x: x[1], reverse=True)[:10]

    # 3. Формируем Markdown контент
    md_content = []
    md_content.append(f"# Отчет по вакансиям HH.ru")
    md_content.append(f"*Сформировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    md_content.append("\n---")

    # Секция статистики
    md_content.append("## 📊 Общая статистика")
    md_content.append(f"- **Всего вакансий в базе:** {total}")
    
    md_content.append("\n### Топ городов:")
    for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]:
        md_content.append(f"- {city}: {count}")

    md_content.append("\n### Ключевые навыки (Top 10):")
    md_content.append(", ".join([f"`{s[0]}` ({s[1]})" for s in top_skills]))

    md_content.append("\n---")
    
    # Секция списка вакансий
    md_content.append("## 💼 Список вакансий")
    md_content.append("| Название | Зарплата | Город | Ссылка |")
    md_content.append("| :--- | :--- | :--- | :--- |")

    for v in vacancies:
        name = v.get('title', 'Без названия')
        # Форматируем зарплату
        s = v.get('salary', {})
        s_from = s.get('from')
        s_to = s.get('to')
        cur = s.get('currency', '')
        
        if s_from or s_to:
            sal_str = f"{s_from or ''}-{s_to or ''} {cur}".strip()
        else:
            sal_str = "По договоренности"

        area = v.get('area', '-')
        url = v.get('url', '#')
        
        # Очищаем название от лишних символов для таблицы
        clean_name = name.replace('|', '/') 
        md_content.append(f"| {clean_name} | {sal_str} | {area} | [Перейти]({url}) |")

    # 4. Сохраняем в файл
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    print(f"Отчет успешно сохранен в файл: {REPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(generate_markdown())
