import os
from textwrap import dedent

import streamlit as st
import streamlit.components.v1 as components


API_URL = os.getenv("SCIENCE_KNOT_API_URL", "http://127.0.0.1:18080/chat")


st.set_page_config(page_title="Научный клубок", layout="wide")

st.markdown(
    """
    <style>
    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    #MainMenu,
    footer {
        display: none !important;
    }

    .stApp {
        background: #F7F5F1;
    }

    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: none !important;
    }

    iframe {
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


html_app = dedent(
    f"""
    <!doctype html>
    <html lang="ru">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800;900&display=swap');

        :root {{
          --bg: #F7F5F1;
          --text: #2B2111;
          --blue: #5B74FF;
          --muted: #D9C7A3;
          --panel: #EEECE8;
          --dark: #0E1118;
          --line: rgba(43, 33, 17, 0.85);
          --soft-line: rgba(43, 33, 17, 0.16);
        }}

        * {{
          box-sizing: border-box;
        }}

        html,
        body {{
          margin: 0;
          width: 100%;
          min-height: 100%;
          background: var(--bg);
          color: var(--text);
          font-family: Inter, Arial, sans-serif;
          overflow-x: hidden;
        }}

        button,
        input,
        select {{
          font: inherit;
        }}

        .app {{
          width: 100vw;
          min-height: 100vh;
          display: grid;
          grid-template-columns: 443px 1fr;
          background: var(--bg);
        }}

        .sources {{
          min-height: 100vh;
          border-right: 1px solid var(--line);
          padding: 43px 39px 36px 39px;
          background: var(--bg);
        }}

        .sources-title {{
          margin: 0 0 38px 0;
          font-size: 36px;
          line-height: 1;
          font-weight: 900;
          letter-spacing: -0.065em;
        }}

        .upload-frame {{
          width: 365px;
          height: 236px;
          border: 1px solid var(--line);
          border-radius: 17px;
          padding: 20px 15px 14px 15px;
          margin-bottom: 52px;
        }}

        .upload-title {{
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 11px;
        }}

        .upload-drop {{
          position: relative;
          height: 174px;
          border-radius: 9px;
          background: var(--dark);
          padding: 25px 20px;
          color: rgba(247, 245, 241, 0.7);
          overflow: hidden;
        }}

        .upload-drop input {{
          position: absolute;
          inset: 0;
          opacity: 0;
          cursor: pointer;
        }}

        .drop-main {{
          color: rgba(43, 33, 17, 0.78);
          font-size: 17px;
          margin-bottom: 14px;
        }}

        .drop-limit {{
          max-width: 260px;
          color: rgba(247, 245, 241, 0.72);
          font-size: 16px;
          line-height: 1.35;
          font-weight: 700;
        }}

        .browse {{
          display: inline-flex;
          align-items: center;
          justify-content: center;
          height: 49px;
          margin-top: 24px;
          padding: 0 16px;
          border-radius: 9px;
          background: #272936;
          border: 1px solid #424554;
          color: #fff;
          font-size: 18px;
          font-weight: 700;
        }}

        .empty-card {{
          width: 365px;
          height: 291px;
          border-radius: 16px;
          background: var(--panel);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          margin-bottom: 86px;
        }}

        .empty-icon {{
          font-size: 64px;
          line-height: 1;
          letter-spacing: -0.12em;
          margin-bottom: 32px;
        }}

        .empty-text {{
          width: 260px;
          text-align: center;
          color: #B5AC99;
          font-size: 18px;
          line-height: 1.55;
          font-weight: 600;
        }}

        .demo-title {{
          margin: 0 0 19px 0;
          font-size: 30px;
          line-height: 1;
          font-weight: 900;
          letter-spacing: -0.075em;
        }}

        .demo-select {{
          width: 365px;
          height: 50px;
          border: 0;
          border-radius: 8px;
          background: var(--dark);
          color: rgba(247, 245, 241, 0.9);
          padding: 0 18px;
          outline: none;
          cursor: pointer;
        }}

        .main {{
          min-height: 100vh;
          position: relative;
          background: var(--bg);
        }}

        .hero {{
          width: 680px;
          position: absolute;
          left: 128px;
          top: 146px;
        }}

        .logo {{
          width: 91px;
          height: 91px;
          margin-left: 53px;
          margin-bottom: 55px;
        }}

        .hero-title {{
          margin: 0;
          font-size: 43px;
          line-height: 0.94;
          font-weight: 900;
          letter-spacing: -0.085em;
          text-transform: uppercase;
          white-space: nowrap;
        }}

        .hero-subtitle {{
          margin-top: 54px;
          font-size: 18px;
          line-height: 1;
          font-weight: 800;
        }}

        .hero-note {{
          margin-top: 13px;
          color: #B5AC99;
          font-size: 16px;
          font-weight: 600;
        }}

        .search-row {{
          position: relative;
          width: 680px;
          height: 78px;
          margin-top: 56px;
        }}

        .search-input {{
          width: 680px;
          height: 78px;
          border: 1.5px solid var(--text);
          border-radius: 999px;
          background: var(--bg);
          color: var(--text);
          padding: 0 84px 0 28px;
          outline: none;
          font-size: 20px;
          font-weight: 600;
        }}

        .search-input::placeholder {{
          color: #B5AC99;
        }}

        .search-button {{
          position: absolute;
          right: 23px;
          top: 21px;
          width: 38px;
          height: 38px;
          border: 0;
          border-radius: 50%;
          background: var(--blue);
          color: #fff;
          display: grid;
          place-items: center;
          cursor: pointer;
        }}

        .search-button svg {{
          width: 24px;
          height: 24px;
        }}

        .status {{
          min-height: 22px;
          margin-top: 18px;
          color: #B5AC99;
          font-size: 14px;
          font-weight: 700;
        }}

        .results {{
          display: none;
          min-height: 100vh;
          grid-template-columns: 382px 1fr;
        }}

        .chat-panel {{
          border-right: 1px solid var(--line);
          padding: 26px 39px 34px 39px;
        }}

        .chat-head {{
          border-top: 1px solid var(--line);
          padding-top: 16px;
          font-size: 31px;
          line-height: 1;
          font-weight: 900;
          letter-spacing: -0.07em;
          margin-bottom: 77px;
          display: flex;
          justify-content: space-between;
        }}

        .chat-box {{
          width: 100%;
          min-height: 408px;
          border-radius: 18px;
          background: #fff;
          padding: 40px;
        }}

        .bubble-ai {{
          display: inline-block;
          max-width: 255px;
          background: #BDB5A1;
          border-radius: 8px;
          padding: 8px 10px;
          font-size: 16px;
          line-height: 1.25;
          margin-bottom: 36px;
        }}

        .bubble-user {{
          display: block;
          width: fit-content;
          max-width: 235px;
          margin-left: auto;
          background: #E9E7E3;
          border-radius: 8px;
          padding: 8px 12px;
          font-size: 16px;
          line-height: 1.25;
          margin-bottom: 12px;
        }}

        .follow-title {{
          margin-top: 22px;
          font-size: 18px;
          font-weight: 900;
          letter-spacing: -0.04em;
        }}

        .follow-list {{
          margin: 10px 0 0 0;
          padding-left: 18px;
          font-size: 14px;
          line-height: 1.4;
        }}

        .graph-panel {{
          position: relative;
          background: var(--bg);
          min-height: 100vh;
          padding: 48px 64px;
        }}

        .graph-search {{
          position: absolute;
          right: 40px;
          top: 40px;
          width: 41px;
          height: 41px;
          border: 1.5px solid #B9AF9E;
          border-radius: 50%;
          display: grid;
          place-items: center;
          color: #B9AF9E;
        }}

        .graph-canvas {{
          position: absolute;
          inset: 72px 50px 40px 50px;
        }}

        .cards {{
          position: absolute;
          left: 64px;
          bottom: 42px;
          right: 64px;
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
        }}

        .data-card {{
          border-radius: 16px;
          background: rgba(238, 236, 232, 0.78);
          padding: 14px;
          font-size: 13px;
          line-height: 1.35;
        }}

        .data-card strong {{
          display: block;
          font-size: 14px;
          margin-bottom: 7px;
        }}

        body.has-results .hero {{
          display: none;
        }}

        body.has-results .results {{
          display: grid;
        }}

        @media (min-width: 1200px) {{
          .hero-title {{
            font-size: 43px;
          }}
        }}
      </style>
    </head>
    <body>
      <div class="app">
        <aside class="sources">
          <h1 class="sources-title">Источники</h1>

          <div class="upload-frame">
            <div class="upload-title">Добавить источники</div>
            <label class="upload-drop">
              <input id="fileInput" type="file" multiple />
              <div class="drop-main">Drag and drop files here</div>
              <div class="drop-limit">Limit 200MB per file • PDF, TXT, DOCX, JSON</div>
              <div class="browse">Browse files</div>
            </label>
          </div>

          <div class="empty-card" id="sourceState">
            <div class="empty-icon">□+</div>
            <div class="empty-text">Загрузите свои источники или используйте mock-данные демо.</div>
          </div>

          <h2 class="demo-title">Демо-запросы</h2>
          <select class="demo-select" id="demoSelect">
            <option>Что известно про Ti-6Al-4V после закалки?</option>
            <option>Какие режимы повышали прочность алюминиевых сплавов?</option>
            <option>Что делали для повышения коррозионной стойкости?</option>
            <option>Где есть пробелы по лазерной обработке?</option>
            <option>Какие эксперименты связаны с Inconel 718?</option>
          </select>
        </aside>

        <main class="main">
          <section class="hero">
            <div class="logo">
              <svg viewBox="0 0 96 96" fill="none">
                <line x1="28" y1="28" x2="48" y2="14" stroke="#0B0B0B" stroke-width="6"/>
                <line x1="48" y1="14" x2="70" y2="28" stroke="#0B0B0B" stroke-width="6"/>
                <line x1="70" y1="28" x2="70" y2="58" stroke="#0B0B0B" stroke-width="6"/>
                <line x1="70" y1="58" x2="48" y2="74" stroke="#0B0B0B" stroke-width="6"/>
                <line x1="48" y1="74" x2="28" y2="58" stroke="#0B0B0B" stroke-width="6"/>
                <line x1="28" y1="58" x2="28" y2="28" stroke="#0B0B0B" stroke-width="6"/>
                <line x1="28" y1="58" x2="48" y2="14" stroke="#0B0B0B" stroke-width="5"/>
                <line x1="48" y1="14" x2="70" y2="58" stroke="#0B0B0B" stroke-width="5"/>
                <line x1="28" y1="28" x2="70" y2="58" stroke="#0B0B0B" stroke-width="5"/>
                <circle cx="28" cy="28" r="9" fill="#0B0B0B"/>
                <circle cx="48" cy="14" r="9" fill="#0B0B0B"/>
                <circle cx="70" cy="28" r="9" fill="#0B0B0B"/>
                <circle cx="70" cy="58" r="9" fill="#0B0B0B"/>
                <circle cx="48" cy="74" r="9" fill="#0B0B0B"/>
                <circle cx="28" cy="58" r="9" fill="#0B0B0B"/>
              </svg>
            </div>

            <h1 class="hero-title">ВВЕДИТЕ ЗАПРОС</h1>
            <div class="hero-subtitle">для исследования</div>
            <div class="hero-note">Загрузите источники, перед тем как начать исследование</div>

            <form class="search-row" id="searchForm">
              <input
                class="search-input"
                id="queryInput"
                value="Что известно про Ti-6Al-4V после закалки?"
                autocomplete="off"
              />
              <button class="search-button" type="submit" aria-label="Найти связи">
                <svg viewBox="0 0 24 24" fill="none">
                  <circle cx="10.5" cy="10.5" r="6.5" stroke="white" stroke-width="2.4"/>
                  <path d="M15.5 15.5L21 21" stroke="white" stroke-width="2.4" stroke-linecap="round"/>
                </svg>
              </button>
            </form>
            <div class="status" id="status"></div>
          </section>

          <section class="results" id="results">
            <div class="chat-panel">
              <div class="chat-head">
                <span>Чат с ИИ</span>
                <span>&lt;</span>
              </div>
              <div class="chat-box" id="chatBox"></div>
            </div>

            <div class="graph-panel">
              <div class="graph-search">
                <svg viewBox="0 0 24 24" width="23" height="23" fill="none">
                  <circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="2"/>
                  <path d="M15.5 15.5L21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="graph-canvas" id="graphCanvas"></div>
              <div class="cards" id="cards"></div>
            </div>
          </section>
        </main>
      </div>

      <script>
        const apiUrl = {API_URL!r};
        const demoSelect = document.getElementById("demoSelect");
        const queryInput = document.getElementById("queryInput");
        const searchForm = document.getElementById("searchForm");
        const statusNode = document.getElementById("status");
        const chatBox = document.getElementById("chatBox");
        const graphCanvas = document.getElementById("graphCanvas");
        const cards = document.getElementById("cards");
        const fileInput = document.getElementById("fileInput");
        const sourceState = document.getElementById("sourceState");

        demoSelect.addEventListener("change", () => {{
          queryInput.value = demoSelect.value;
        }});

        fileInput.addEventListener("change", () => {{
          const files = Array.from(fileInput.files);
          if (!files.length) return;
          sourceState.innerHTML = `
            <div style="width:100%; text-align:left;">
              <div style="font-size:24px; font-weight:800; margin-bottom:18px;">Файлы(${{files.length}})</div>
              ${{files.map(file => `
                <div style="font-family:monospace; font-size:20px; margin:12px 0;">
                  <span style="display:inline-grid; place-items:center; width:23px; height:23px; border:1px solid #2B2111; border-radius:4px; margin-right:13px;">✓</span>
                  ${{escapeHtml(file.name)}}
                </div>
              `).join("")}}
            </div>
          `;
        }});

        searchForm.addEventListener("submit", async (event) => {{
          event.preventDefault();
          const query = queryInput.value.trim();
          if (!query) {{
            statusNode.textContent = "Введите запрос для исследования";
            return;
          }}

          statusNode.textContent = "Строим связи...";
          try {{
            const response = await fetch(apiUrl, {{
              method: "POST",
              headers: {{ "Content-Type": "application/json" }},
              body: JSON.stringify({{ message: query, session_id: "figma-ui" }}),
            }});
            if (!response.ok) {{
              throw new Error(`Backend вернул ${{response.status}}`);
            }}
            const data = await response.json();
            renderResult(query, data);
            document.body.classList.add("has-results");
            statusNode.textContent = "";
          }} catch (error) {{
            statusNode.textContent = `Не удалось связаться с backend: ${{error.message}}`;
          }}
        }});

        function renderResult(query, data) {{
          const questions = data.follow_up_questions || [];
          chatBox.innerHTML = `
            <div class="bubble-ai">${{escapeHtml(data.answer || "Ответ пока не сформирован.")}}</div>
            <div class="bubble-user">${{escapeHtml(query)}}</div>
            <div class="follow-title">Уточнить отсутствующие параметры?</div>
            <ul class="follow-list">
              ${{questions.map(item => `<li>${{escapeHtml(item)}}</li>`).join("")}}
            </ul>
          `;

          renderGraph(data.graph || {{ nodes: [], edges: [] }});
          renderCards(data.documents || [], data.hypotheses || []);
        }}

        function renderGraph(graph) {{
          const nodes = (graph.nodes || []).slice(0, 10);
          const edges = (graph.edges || []).slice(0, 16);
          const width = 850;
          const height = 740;
          const cx = width / 2;
          const cy = height / 2;
          const rx = 300;
          const ry = 250;
          const pos = {{}};

          nodes.forEach((node, index) => {{
            const angle = (Math.PI * 2 * index / Math.max(nodes.length, 1)) - Math.PI / 2;
            pos[node.id] = {{
              x: cx + Math.cos(angle) * rx,
              y: cy + Math.sin(angle) * ry,
            }};
          }});

          const lineSvg = edges
            .filter(edge => pos[edge.source] && pos[edge.target])
            .map(edge => `
              <line
                x1="${{pos[edge.source].x}}" y1="${{pos[edge.source].y}}"
                x2="${{pos[edge.target].x}}" y2="${{pos[edge.target].y}}"
                stroke="#D8D6D1" stroke-width="1.4"
              />
            `)
            .join("");

          const nodeSvg = nodes.map(node => {{
            const p = pos[node.id];
            const label = escapeHtml(String(node.label || node.id || "").slice(0, 18));
            return `
              <g>
                <circle cx="${{p.x}}" cy="${{p.y}}" r="61" fill="#D9D9D9"/>
                <text x="${{p.x}}" y="${{p.y + 5}}" text-anchor="middle"
                  font-family="Inter, Arial, sans-serif" font-size="13" font-weight="800"
                  fill="#2B2111">${{label}}</text>
              </g>
            `;
          }}).join("");

          graphCanvas.innerHTML = `
            <svg viewBox="0 0 ${{width}} ${{height}}" width="100%" height="100%">
              ${{lineSvg}}
              ${{nodeSvg}}
            </svg>
          `;
        }}

        function renderCards(documents, hypotheses) {{
          const docs = documents.slice(0, 2);
          const hyps = hypotheses.slice(0, 2);
          cards.innerHTML = [
            ...docs.map(doc => `
              <div class="data-card">
                <strong>${{escapeHtml(doc.title || "Документ")}}</strong>
                <div>${{escapeHtml(doc.snippet || "")}}</div>
              </div>
            `),
            ...hyps.map(item => `
              <div class="data-card">
                <strong>${{escapeHtml(item.title || "Гипотеза")}}</strong>
                <div>${{escapeHtml(item.reason || "")}}</div>
              </div>
            `),
          ].join("");
        }}

        function escapeHtml(value) {{
          return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
        }}
      </script>
    </body>
    </html>
    """
)

components.html(html_app, height=1024, scrolling=False)
