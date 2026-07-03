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

    materials = sorted({value for doc in documents for value in doc.get("materials", [])})
    processes = sorted({value for doc in documents for value in doc.get("processes", [])})
    properties = sorted({value for doc in documents for value in doc.get("properties", [])})

    if documents:
        answer = f"Найдено {len(documents)} релевантных документов."
        if materials:
            answer += f" Материалы: {', '.join(materials)}."
        if processes:
            answer += f" Рассмотренные процессы: {', '.join(processes)}."
        if properties:
            answer += f" Связанные свойства: {', '.join(properties)}."
        answer += " Ниже показаны источники, связи и потенциальные направления исследования."
    else:
        answer = (
            "Точных документов по запросу не найдено. Показаны обзорный фрагмент графа "
            "и ближайшие гипотезы, которые помогут уточнить направление поиска."
        )

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
