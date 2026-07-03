const API_URL = "http://127.0.0.1:18080/chat";
const UPLOAD_URL = "http://127.0.0.1:18080/upload";

const queryInput = document.querySelector("#queryInput");
const compactQueryInput = document.querySelector("#compactQueryInput");
const searchForm = document.querySelector("#searchForm");
const compactSearchForm = document.querySelector("#compactSearchForm");
const statusLine = document.querySelector("#statusLine");
const hero = document.querySelector("#hero");
const results = document.querySelector("#results");
const answerText = document.querySelector("#answerText");
const userQuestion = document.querySelector("#userQuestion");
const followQuestions = document.querySelector("#followQuestions");
const graphStage = document.querySelector("#graphStage");
const graphStats = document.querySelector("#graphStats");
const documentsList = document.querySelector("#documentsList");
const hypothesesList = document.querySelector("#hypothesesList");
const docsCount = document.querySelector("#docsCount");
const hypothesesCount = document.querySelector("#hypothesesCount");
const fileInput = document.querySelector("#fileInput");
const sourcesCard = document.querySelector("#sourcesCard");
const demoButtons = document.querySelectorAll(".demo-query");

demoButtons.forEach((button) => {
  button.addEventListener("click", () => {
    demoButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    queryInput.value = button.textContent.trim();
    compactQueryInput.value = button.textContent.trim();
  });
});

fileInput.addEventListener("change", async () => {
  const files = Array.from(fileInput.files);
  if (!files.length) return;

  renderUploadList(files.map((file) => ({ file, status: "Загрузка..." })));

  const uploaded = [];
  for (const file of files) {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(UPLOAD_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`backend вернул ${response.status}`);
      }

      const data = await response.json();
      uploaded.push({ file, status: "Загружен", size: data.size });
    } catch (error) {
      uploaded.push({ file, status: `Ошибка: ${error.message}` });
    }
    renderUploadList([
      ...uploaded,
      ...files
        .slice(uploaded.length)
        .map((pendingFile) => ({ file: pendingFile, status: "Ожидает..." })),
    ]);
  }
});

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  runChat(queryInput.value);
});

compactSearchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  runChat(compactQueryInput.value);
});

async function runChat(rawQuery) {
  const query = rawQuery.trim();
  if (!query) {
    statusLine.textContent = "Введите запрос для исследования.";
    return;
  }

  setLoading(true);
  statusLine.textContent = "Агент ищет документы, граф и гипотезы...";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: query,
        session_id: "frontend-web-demo",
      }),
    });

    if (!response.ok) {
      throw new Error(`backend вернул ${response.status}`);
    }

    const data = await response.json();
    compactQueryInput.value = query;
    renderResult(query, data);
    hero.classList.add("hidden");
    results.classList.remove("hidden");
    statusLine.textContent = "";
  } catch (error) {
    statusLine.textContent = `Не удалось связаться с backend: ${error.message}`;
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  document.body.style.cursor = isLoading ? "wait" : "default";
  searchForm.querySelector("button").disabled = isLoading;
  compactSearchForm.querySelector("button").disabled = isLoading;
}

function renderResult(query, data) {
  answerText.innerHTML = renderMarkdown(data.answer || "Ответ пока не сформирован.");
  userQuestion.textContent = query;

  renderFollowQuestions(data.follow_up_questions || []);
  renderGraph(data.graph || { nodes: [], edges: [] });
  renderDocuments(data.documents || []);
  renderHypotheses(data.hypotheses || []);
}

function renderUploadList(items) {
  const readyCount = items.filter((item) => item.status === "Загружен").length;
  sourcesCard.innerHTML = `
    <div class="source-list">
      <div class="source-list-title">
        <span>Файлы (${items.length})</span>
        <span>${readyCount}/${items.length} ✓</span>
      </div>
      ${items
        .map((item) => {
          const isReady = item.status === "Загружен";
          const isError = item.status.startsWith("Ошибка");
          const statusClass = isReady ? "ready" : isError ? "error" : "pending";
          return `
            <div class="source-item">
              <span class="source-check ${statusClass}">${isReady ? "✓" : isError ? "!" : "..."}</span>
              <span>
                ${escapeHtml(item.file.name)}
                <small>${escapeHtml(item.status)}</small>
              </span>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderFollowQuestions(questions) {
  followQuestions.innerHTML = questions
    .map((question) => `<li>${escapeHtml(question)}</li>`)
    .join("");
}

function renderDocuments(documents) {
  docsCount.textContent = documents.length;
  if (!documents.length) {
    documentsList.innerHTML = `<div class="info-card"><p>Документы не найдены.</p></div>`;
    return;
  }

  documentsList.innerHTML = documents
    .map((document) => {
      const chips = [
        ...(document.materials || []),
        ...(document.processes || []),
        ...(document.properties || []),
      ];
      return `
        <article class="info-card">
          <h3>${escapeHtml(document.title || "Документ")}</h3>
          <p>${escapeHtml(document.snippet || "")}</p>
          <div class="chips">
            <span class="chip">${escapeHtml(document.year || "год н/д")}</span>
            <span class="chip">score ${escapeHtml(document.score ?? 0)}</span>
            ${chips.map((chip) => `<span class="chip">${escapeHtml(chip)}</span>`).join("")}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderHypotheses(hypotheses) {
  hypothesesCount.textContent = hypotheses.length;
  if (!hypotheses.length) {
    hypothesesList.innerHTML = `<div class="info-card"><p>Гипотезы пока не сформированы.</p></div>`;
    return;
  }

  hypothesesList.innerHTML = hypotheses
    .map(
      (hypothesis) => `
        <article class="info-card">
          <h3>${escapeHtml(hypothesis.title || "Гипотеза")}</h3>
          <p>${escapeHtml(hypothesis.reason || "")}</p>
          <div class="chips">
            <span class="chip">novelty: ${escapeHtml(hypothesis.novelty || "-")}</span>
            <span class="chip">risk: ${escapeHtml(hypothesis.risk || "-")}</span>
            <span class="chip">value: ${escapeHtml(hypothesis.value || "-")}</span>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderGraph(graph) {
  const nodes = (graph.nodes || []).slice(0, 12);
  const edges = (graph.edges || []).slice(0, 18);
  graphStats.textContent = `${nodes.length} узлов / ${edges.length} связей`;

  if (!nodes.length) {
    graphStage.innerHTML = `<div class="info-card"><p>Граф пуст.</p></div>`;
    return;
  }

  const width = 920;
  const height = 580;
  const centerX = width / 2;
  const centerY = height / 2;
  const radiusX = 340;
  const radiusY = 210;
  const positions = {};

  nodes.forEach((node, index) => {
    const angle = (2 * Math.PI * index) / nodes.length - Math.PI / 2;
    positions[node.id] = {
      x: centerX + Math.cos(angle) * radiusX,
      y: centerY + Math.sin(angle) * radiusY,
    };
  });

  const lines = edges
    .filter((edge) => positions[edge.source] && positions[edge.target])
    .map((edge) => {
      const source = positions[edge.source];
      const target = positions[edge.target];
      return `
        <line
          x1="${source.x}"
          y1="${source.y}"
          x2="${target.x}"
          y2="${target.y}"
          stroke="rgba(43,33,17,0.16)"
          stroke-width="2"
        />
      `;
    })
    .join("");

  const circles = nodes
    .map((node) => {
      const position = positions[node.id];
      const color = getNodeColor(node.type);
      const textColor = color === "#2f4a52" || color === "#5b74ff" ? "#ffffff" : "#2b2111";
      const label = String(node.label || node.id || "").slice(0, 22);

      return `
        <g>
          <circle
            cx="${position.x}"
            cy="${position.y}"
            r="56"
            fill="${color}"
            stroke="#f7f5f1"
            stroke-width="6"
          />
          <text
            x="${position.x}"
            y="${position.y + 4}"
            text-anchor="middle"
            fill="${textColor}"
            font-size="13"
            font-weight="850"
          >${escapeHtml(label)}</text>
        </g>
      `;
    })
    .join("");

  graphStage.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Граф связей">
      ${lines}
      ${circles}
    </svg>
  `;
}

function getNodeColor(type) {
  const colors = {
    Material: "#2f4a52",
    Process: "#5b74ff",
    Property: "#d9c7a3",
    Experiment: "#d9d9d9",
    Paper: "#ffffff",
    Team: "#eee1c7",
    Equipment: "#c9b993",
  };
  return colors[type] || "#d9d9d9";
}

function renderMarkdown(value) {
  const escaped = escapeHtml(value);
  const blocks = escaped
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  if (!blocks.length) {
    return "";
  }

  return blocks
    .map((block) => {
      const lines = block.split(/\n/).map((line) => line.trim()).filter(Boolean);
      if (lines.length && lines.every((line) => /^[-*]\s+/.test(line))) {
        return `<ul>${lines
          .map((line) => `<li>${formatInlineMarkdown(line.replace(/^[-*]\s+/, ""))}</li>`)
          .join("")}</ul>`;
      }
      return `<p>${formatInlineMarkdown(lines.join("<br>"))}</p>`;
    })
    .join("");
}

function formatInlineMarkdown(value) {
  return value.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
