# Диаграммы по запросу: Как устроен GPT Researcher?

_Сгенерировано: 2026-10-09 19:47:47_

---

```mermaid
graph TD
    A[Planировщик] --> B(Исполнительные Агенты)
    B --> C[Генерация Отчетов]
    style A fill:#f9f,stroke:#333,stroke-width:4
    style C fill:#ccf,stroke:#333,stroke-width:4
    note right of B "Гибкость и Настраиваемость"
    note left of C "Форматы Представления Отчета: Markdown, PDF, DOCX, JSON"
```
This Mermaid diagram illustrates the architecture of GPT Researcher, showing the relationship between the planner, execution agents, and report generation components.