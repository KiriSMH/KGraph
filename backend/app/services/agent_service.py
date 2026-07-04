from typing import Any

from app.services.data_service import load_hypotheses
from app.services.graph_service import get_subgraph
from app.services.llm_service import generate_llm_answer
from app.services.search_service import search_documents


FOLLOW_UP_QUESTIONS = [
    "Какое свойство важнее: прочность, пластичность или коррозионная стойкость?",
    "Есть ли ограничения по температуре обработки?",
    "Рассматривать только этот материал или также близкие аналоги?",
]


def _unique_sorted(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return sorted(result)


def _format_list(values: list[str], fallback: str = "не выделено") -> str:
    return ", ".join(values) if values else fallback


def _top_documents(documents: list[dict[str, Any]], limit: int = 3) -> list[str]:
    items: list[str] = []
    for document in documents[:limit]:
        title = str(document.get("title") or "Документ")
        year = document.get("year")
        score = document.get("score")
        meta = []
        if year:
            meta.append(str(year))
        if score is not None:
            meta.append(f"score {score}")
        suffix = f" ({', '.join(meta)})" if meta else ""
        items.append(f"{title}{suffix}")
    return items


def _top_relations(graph: dict[str, Any], limit: int = 5) -> list[str]:
    nodes_by_id = {
        str(node.get("id")): str(node.get("label") or node.get("id"))
        for node in graph.get("nodes", [])
    }
    relations: list[str] = []
    for edge in graph.get("edges", [])[:limit]:
        source = nodes_by_id.get(str(edge.get("source")), str(edge.get("source")))
        target = nodes_by_id.get(str(edge.get("target")), str(edge.get("target")))
        label = str(edge.get("label") or "связано с")
        relations.append(f"{source} -> {label} -> {target}")
    return relations


def _build_offline_answer(
    query: str,
    documents: list[dict[str, Any]],
    graph: dict[str, Any],
    hypotheses: list[dict[str, Any]],
) -> str:
    materials = _unique_sorted([value for doc in documents for value in doc.get("materials", [])])
    processes = _unique_sorted([value for doc in documents for value in doc.get("processes", [])])
    properties = _unique_sorted([value for doc in documents for value in doc.get("properties", [])])
    top_documents = _top_documents(documents)
    top_relations = _top_relations(graph)
    top_hypotheses = [str(item.get("title")) for item in hypotheses[:2] if item.get("title")]

    if documents:
        summary = (
            f"По запросу найдено {len(documents)} релевантных источников. "
            f"Основной фокус: материалы — {_format_list(materials)}, "
            f"процессы — {_format_list(processes)}, свойства — {_format_list(properties)}."
        )
    else:
        summary = (
            "Точных документов по запросу не найдено. Ниже показан ближайший фрагмент графа "
            "и гипотезы, которые можно использовать для уточнения поиска."
        )

    answer_parts = [
        "**Краткий вывод**",
        "",
        summary,
        "",
        "**Что уже делали**",
        "",
    ]

    if top_documents:
        answer_parts.extend(f"- {item}" for item in top_documents)
    else:
        answer_parts.append("- Документы не найдены; используется обзорный mock-граф.")

    answer_parts.extend(["", "**Связи в графе**", ""])
    if top_relations:
        answer_parts.extend(f"- {item}" for item in top_relations)
    else:
        answer_parts.append("- Связанные узлы не найдены.")

    answer_parts.extend(["", "**Гипотезы и пробелы**", ""])
    if top_hypotheses:
        answer_parts.extend(f"- {item}" for item in top_hypotheses)
    else:
        answer_parts.append("- Нужно загрузить больше источников или уточнить материал/процесс/свойство.")

    answer_parts.extend(
        [
            "",
            "**Контроль противоречий**",
            "",
            (
                "Противоречие стоит отмечать только когда совпадают материал, режим обработки, "
                "условия эксперимента и измеряемое свойство. Если составы или условия разные, "
                "разное поведение свойства считается ожидаемым различием, а не конфликтом."
            ),
            "",
            "**Следующий шаг**",
            "",
            f"Уточнить запрос «{query}» через конкретное свойство, температуру обработки или источник данных.",
        ]
    )

    return "\n".join(answer_parts)


def _select_hypotheses(query: str) -> list[dict[str, Any]]:
    normalized = query.casefold()
    hypotheses = load_hypotheses()
    matched = [
        item
        for item in hypotheses
        if str(item.get("material", "")).casefold() in normalized
        or str(item.get("property", "")).casefold() in normalized
    ]
    return (matched or hypotheses)[:3]


def generate_agent_response(query: str) -> dict[str, Any]:
    documents = search_documents(query)
    graph = get_subgraph(query)
    hypotheses = _select_hypotheses(query)
    llm_context = {
        "documents": documents,
        "graph": graph,
        "hypotheses": hypotheses,
    }

    answer = _build_offline_answer(query, documents, graph, hypotheses)

    llm_answer = generate_llm_answer(query, llm_context)
    if llm_answer:
        answer = llm_answer

    return {
        "answer": answer,
        "follow_up_questions": FOLLOW_UP_QUESTIONS,
        "documents": documents,
        "graph": graph,
        "hypotheses": hypotheses,
    }
