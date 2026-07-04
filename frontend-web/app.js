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
      const chunks = Number(data.indexed_chunks || 0);
      const indexMessage = data.index_message || "";
      uploaded.push({
        file,
        status: chunks
          ? `Загружен и проиндексирован (${chunks} чанков)`
          : "Загружен, но текстовый индекс не создан",
        detail: indexMessage,
        size: data.size,
      });
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
  const readyCount = items.filter((item) => item.status.startsWith("Загружен")).length;
  sourcesCard.innerHTML = `
    <div class="source-list">
      <div class="source-list-title">
        <span>Файлы (${items.length})</span>
        <span>${readyCount}/${items.length} ✓</span>
      </div>
      ${items
        .map((item) => {
          const isReady = item.status.startsWith("Загружен");
          const isError = item.status.startsWith("Ошибка");
          const statusClass = isReady ? "ready" : isError ? "error" : "pending";
          return `
            <div class="source-item">
              <span class="source-check ${statusClass}">${isReady ? "✓" : isError ? "!" : "..."}</span>
              <span>
                ${escapeHtml(item.file.name)}
                <small>${escapeHtml(item.status)}</small>
                ${item.detail ? `<small>${escapeHtml(item.detail)}</small>` : ""}
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
  const nodes = (graph.nodes || []).slice(0, 14);
  const edges = (graph.edges || []).slice(0, 22);
  graphStats.textContent = `${nodes.length} узлов / ${edges.length} связей`;

  if (!nodes.length) {
    graphStage.innerHTML = `<div class="info-card"><p>Граф пуст.</p></div>`;
    return;
  }

  const width = 1080;
  const height = 680;
  const centerX = width / 2;
  const centerY = height / 2;
  const radiusX = 410;
  const radiusY = 255;
  const positions = {};
  const sortedNodes = sortGraphNodes(nodes, edges);

  sortedNodes.forEach((node, index) => {
    if (index === 0) {
      positions[node.id] = { x: centerX, y: centerY };
      return;
    }

    const ringIndex = index - 1;
    const ringCount = sortedNodes.length - 1;
    const angle = (2 * Math.PI * ringIndex) / Math.max(ringCount, 1) - Math.PI / 2;
    const stagger = ringIndex % 2 === 0 ? 1 : 0.88;
    positions[node.id] = {
      x: centerX + Math.cos(angle) * radiusX * stagger,
      y: centerY + Math.sin(angle) * radiusY * stagger,
    };
  });

  const lines = edges
    .filter((edge) => positions[edge.source] && positions[edge.target])
    .map((edge, index) => {
      const source = positions[edge.source];
      const target = positions[edge.target];
      const labelX = (source.x + target.x) / 2;
      const labelY = (source.y + target.y) / 2;
      const label = String(edge.label || "связь").slice(0, 24);
      return `
        <g class="graph-edge">
          <line
            x1="${source.x}"
            y1="${source.y}"
            x2="${target.x}"
            y2="${target.y}"
            marker-end="url(#arrow)"
          />
          ${
            index < 10
              ? `<text x="${labelX}" y="${labelY - 8}" text-anchor="middle">${escapeHtml(label)}</text>`
              : ""
          }
        </g>
      `;
    })
    .join("");

  const circles = sortedNodes
    .map((node) => {
      const position = positions[node.id];
      const color = getNodeColor(node.type);
      const textColor = color === "#2f4a52" || color === "#5b74ff" ? "#ffffff" : "#2b2111";
      const label = wrapSvgLabel(String(node.label || node.id || ""), 16);
      const radius = getNodeRadius(node.type);

      return `
        <g class="graph-node graph-node-${escapeHtml(String(node.type || "Entity").toLowerCase())}">
          <circle
            cx="${position.x}"
            cy="${position.y}"
            r="${radius}"
            fill="${color}"
          />
          <text x="${position.x}" y="${position.y - (label.length - 1) * 8}" text-anchor="middle" fill="${textColor}">
            ${label
              .map(
                (line, lineIndex) =>
                  `<tspan x="${position.x}" dy="${lineIndex === 0 ? 0 : 17}">${escapeHtml(line)}</tspan>`,
              )
              .join("")}
          </text>
          <text class="graph-node-type" x="${position.x}" y="${position.y + radius + 20}" text-anchor="middle">
            ${escapeHtml(node.type || "Entity")}
          </text>
        </g>
      `;
    })
    .join("");

  const legend = buildGraphLegend(nodes);
  const relationList = edges
    .filter((edge) => positions[edge.source] && positions[edge.target])
    .slice(0, 8)
    .map((edge) => {
      const source = nodes.find((node) => node.id === edge.source);
      const target = nodes.find((node) => node.id === edge.target);
      return `<li><b>${escapeHtml(source?.label || edge.source)}</b> ${escapeHtml(edge.label || "связано с")} <b>${escapeHtml(target?.label || edge.target)}</b></li>`;
    })
    .join("");

  graphStage.innerHTML = `
    <div class="graph-visual">
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Граф связей">
        <defs>
          <marker id="arrow" markerWidth="13" markerHeight="13" refX="12" refY="6.5" orient="auto">
            <path d="M1,1 L12,6.5 L1,12 Z"></path>
          </marker>
        </defs>
        ${lines}
        ${circles}
      </svg>
    </div>
    <div class="graph-side">
      <div class="graph-legend">${legend}</div>
      <div class="graph-relations">
        <h3>Ключевые связи</h3>
        <ul>${relationList || "<li>Связи не найдены.</li>"}</ul>
      </div>
    </div>
  `;
}

function sortGraphNodes(nodes, edges) {
  const priority = {
    Material: 0,
    Experiment: 1,
    Process: 2,
    Property: 3,
    Equipment: 4,
    Paper: 5,
    Publication: 5,
    Team: 6,
    Expert: 6,
    Facility: 7,
  };
  const degree = {};
  edges.forEach((edge) => {
    degree[edge.source] = (degree[edge.source] || 0) + 1;
    degree[edge.target] = (degree[edge.target] || 0) + 1;
  });

  return [...nodes].sort((a, b) => {
    const typeA = priority[a.type] ?? 99;
    const typeB = priority[b.type] ?? 99;
    if (typeA !== typeB) return typeA - typeB;
    return (degree[b.id] || 0) - (degree[a.id] || 0);
  });
}

function wrapSvgLabel(value, limit) {
  const words = value.split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";

  words.forEach((word) => {
    const next = current ? `${current} ${word}` : word;
    if (next.length > limit && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  });

  if (current) lines.push(current);
  return (lines.length ? lines : [value]).slice(0, 3);
}

function getNodeRadius(type) {
  const radii = {
    Material: 70,
    Experiment: 64,
    Process: 58,
    Property: 56,
    Equipment: 52,
    Paper: 50,
    Publication: 50,
    Team: 48,
    Expert: 48,
  };
  return radii[type] || 52;
}

function buildGraphLegend(nodes) {
  const types = [...new Set(nodes.map((node) => node.type || "Entity"))];
  return types
    .map(
      (type) => `
        <span class="legend-item">
          <i style="background:${getNodeColor(type)}"></i>
          ${escapeHtml(type)}
        </span>
      `,
    )
    .join("");
}

function getNodeColor(type) {
  const colors = {
    Material: "#2f4a52",
    Process: "#5b74ff",
    Property: "#d9c7a3",
    Experiment: "#f0a85a",
    Paper: "#ffffff",
    Publication: "#ffffff",
    Team: "#eee1c7",
    Expert: "#eee1c7",
    Equipment: "#c9b993",
    Facility: "#9fb7b9",
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
