import asyncio
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные ДО импорта GPT Researcher
load_dotenv()

from multi_agents.agents import ChiefEditorAgent
from gpt_researcher.utils.enum import Tone


# === Настройки путей ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
INDEX_FILE = os.path.join(REPORTS_DIR, "index.md")


def extract_report_text(report_data) -> str:
    """Универсально извлекает текст отчёта из строки или словаря ResearchState."""
    if isinstance(report_data, dict):
        return (
            report_data.get("report")
            or report_data.get("initial_research")
            or str(report_data)
        )
    return str(report_data)


def make_safe_filename(query: str, index: int) -> str:
    """Формирует безопасное базовое имя папки для запроса."""
    safe_name = "".join(c for c in query if c.isalnum() or c in " _-")[:50]
    safe_name = safe_name.strip().replace(" ", "_")
    if not safe_name:
        safe_name = f"report_{index}"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"research_{index:03d}_{timestamp}_{safe_name}"


def update_index(query: str, run_dir_name: str):
    """
    Добавляет запись о новом отчёте в общий индекс reports/index.md.
    Создаёт файл с заголовком, если его ещё нет.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Создаём индекс с заголовком, если файла нет
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write("# Индекс отчётов GPT Researcher\n\n")
            f.write("| # | Дата | Запрос | Папка |\n")
            f.write("|:--|:-----|:-------|:------|\n")

    # Достаём номер из имени папки (research_001_...)
    try:
        num = run_dir_name.split("_")[1]
    except IndexError:
        num = "?"

    # Экранируем вертикальные черты в запросе для корректной таблицы Markdown
    safe_query = query.replace("|", "\\|")

    line = f"| {num} | {timestamp} | {safe_query} | [{run_dir_name}](./{run_dir_name}/report.md) |\n"

    with open(INDEX_FILE, "a", encoding="utf-8") as f:
        f.write(line)


async def run_multi_agent_research(query: str):
    """Запускает мультиагентное исследование."""
    print(f"\n Мультиагентное исследование: {query}")
    print(" Это может занять 3–5 минут...\n")

    task_path = os.path.join(BASE_DIR, "task.json")
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    task["query"] = query

    chief_editor = ChiefEditorAgent(
        task=task,
        websocket=None,
        stream_output=None,
        tone=Tone.Objective,
        headers=None,
    )

    return await chief_editor.run_research_task(task_id=uuid.uuid4())


def save_report(query: str, report_data, index: int):
    """
    Сохраняет отчёт и артефакты в отдельную подпапку внутри ./reports/.

    """
    # Создаём корневую папку reports
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Создаём отдельную подпапку под текущий запрос
    run_dir_name = make_safe_filename(query, index)
    run_dir = os.path.join(REPORTS_DIR, run_dir_name)
    os.makedirs(run_dir, exist_ok=True)

    base_path = os.path.join(run_dir, "report")
    saved_files = []

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(report_data, dict):
        # === Мультиагентный режим ===

        # 1. Основной отчёт
        report_filename = f"{base_path}.md"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(f"# Запрос: {query}\n\n")
            f.write(f"_Сгенерировано: {now_str}_\n\n")
            f.write("---\n\n")
            f.write(report_data.get("report", ""))
        saved_files.append(report_filename)

        # 2. Источники
        sources = report_data.get("sources", [])
        if sources:
            sources_filename = f"{base_path}_sources.md"
            with open(sources_filename, "w", encoding="utf-8") as f:
                f.write(f"# Источники по запросу: {query}\n\n")
                f.write(f"_Сгенерировано: {now_str}_\n\n")
                f.write("---\n\n")
                f.write("\n".join(sources))
            saved_files.append(sources_filename)

        # 3. Диаграммы
        diagrams = report_data.get("diagrams", [])
        if diagrams:
            diagrams_filename = f"{base_path}_diagrams.md"
            with open(diagrams_filename, "w", encoding="utf-8") as f:
                f.write(f"# Диаграммы по запросу: {query}\n\n")
                f.write(f"_Сгенерировано: {now_str}_\n\n")
                f.write("---\n\n")
                f.write("\n\n".join(diagrams))
            saved_files.append(diagrams_filename)

        # 4. Полное состояние JSON
        json_filename = f"{base_path}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        saved_files.append(json_filename)

    else:
        # === Одноагентный режим ===
        report_filename = f"{base_path}.md"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(f"# Запрос: {query}\n\n")
            f.write(f"_Сгенерировано: {now_str}_\n\n")
            f.write("---\n\n")
            f.write(str(report_data))
        saved_files.append(report_filename)

    # Обновляем общий индекс
    update_index(query, run_dir_name)

    return run_dir, saved_files


async def main():
    """Интерактивный режим с мультиагентной системой."""
    # Создаём папку reports сразу при старте
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print("=" * 60)
    print("  GPT Researcher — Мультиагентный режим (AG2 / LangGraph)")
    print("=" * 60)
    print(f"Папка для отчётов: {REPORTS_DIR}")
    print("Агенты: ChiefEditor, Editor, Researcher, Reviewer,")
    print("        Revisor, Writer, Publisher")
    print("Команды: 'exit' или 'quit' для выхода, 'cls' для очистки.\n")

    report_counter = 1

    while True:
        try:
            query = input(" Запрос: ").strip()

            if query.lower() in ("exit", "quit", "выход"):
                print("\n До встречи!")
                break

            if query.lower() == "cls":
                os.system("cls" if os.name == "nt" else "clear")
                continue

            if not query:
                continue

            # Запуск мультиагентного исследования
            report_data = await run_multi_agent_research(query)

            # Вывод отчёта в консоль
            print("\n" + "=" * 60)
            print(" ГОТОВЫЙ ОТЧЁТ")
            print("=" * 60)
            print(extract_report_text(report_data))
            print("=" * 60)

            # Сохранение в отдельную подпапку
            run_dir, saved_files = save_report(query, report_data, report_counter)

            print(f"\n Папка отчёта: {run_dir}")
            print(" Файлы в ней:")
            for path in saved_files:
                print(f"   • {os.path.basename(path)}")
            print(f"\n Общий индекс: {INDEX_FILE}")

            report_counter += 1

        except KeyboardInterrupt:
            print("\n\n Прервано пользователем. До встречи!")
            break
        except Exception as e:
            print(f"\n Ошибка: {e}")
            import traceback
            traceback.print_exc()
            print("Попробуйте другой запрос или проверьте настройки.\n")


if __name__ == "__main__":
    asyncio.run(main())