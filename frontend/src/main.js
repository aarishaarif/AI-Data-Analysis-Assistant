import './style.css';

const app = document.querySelector('#app');
const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

let activeDataset = null;
let activeProfile = null;
let activeConversation = null;

// ============================================================
// HELPERS
// ============================================================

const escapeHtml = value =>
  String(value).replace(
    /[&<>'"]/g,
    character =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      })[character]
  );

const currentUser = () => {
  try {
    return JSON.parse(
      localStorage.getItem('insightflow-user') || 'null'
    );
  } catch {
    return null;
  }
};

const userName = () => currentUser()?.name || 'there';

const initials = () =>
  userName()
    .split(/\s+/)
    .map(part => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'IF';

// ============================================================
// ICONS
// ============================================================

const icon = (name, size = 18) => {
  const paths = {
    spark:
      '<path d="m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z"/><path d="m19 16 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7L19 16Z"/>',

    arrow:
      '<path d="M5 12h14M13 6l6 6-6 6"/>',

    upload:
      '<path d="M12 16V3m0 0L7 8m5-5 5 5"/><path d="M5 14v5h14v-5"/>',

    chart:
      '<path d="M4 19V5m0 14h16"/><path d="m7 15 4-4 3 2 5-7"/>',

    chat:
      '<path d="M20 15a4 4 0 0 1-4 4H8l-4 3v-7a4 4 0 0 1-1-3V8a4 4 0 0 1 4-4h9a4 4 0 0 1 4 4Z"/>',

    file:
      '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',

    close:
      '<path d="m6 6 12 12M18 6 6 18"/>',

    menu:
      '<path d="M4 6h16M4 12h16M4 18h16"/>',

    plus:
      '<path d="M12 5v14M5 12h14"/>',

    send:
      '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',

    check:
      '<path d="m5 12 4 4L19 6"/>',

    down:
      '<path d="m6 9 6 6 6-6"/>',

    dots:
      '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>'
  };

  return `
    <svg
      width="${size}"
      height="${size}"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      ${paths[name] || ''}
    </svg>
  `;
};

// ============================================================
// HEADER
// ============================================================

function header() {
  const user = currentUser();

  return `
    <header class="nav">

      <a class="brand" href="#top">
        <i>${icon('spark', 20)}</i>
        insightflow
      </a>

      <nav>
        <a href="#product">Product</a>
        <a href="#how">How it works</a>
        <a href="#security">Security</a>
      </nav>

      <div class="nav-actions">

        <button class="signin">
          ${user ? `Hi, ${escapeHtml(user.name)}` : 'Sign in'}
        </button>

        ${
          user
            ? '<button class="signout">Sign out</button>'
            : ''
        }

        <button class="button small upload-trigger">
          Try it free ${icon('arrow', 16)}
        </button>

      </div>

      <button class="mobile-menu">
        ${icon('menu')}
      </button>

    </header>
  `;
}

// ============================================================
// LANDING PAGE
// ============================================================

function landing() {
  return `
    <main id="top">

      <section class="hero">

        <div class="hero-copy">

          <div class="eyebrow">
            <span></span>
            YOUR DATA HAS A STORY
          </div>

          <h1>
            See what your data is <em>trying</em> to tell you.
          </h1>

          <p>
            Upload a spreadsheet. Ask a question in plain English.
            Get clear answers, beautiful charts, and the confidence to act.
          </p>

          <div class="hero-actions">

            <button class="button upload-trigger">
              Upload your data ${icon('upload', 17)}
            </button>

            <a href="#product" class="text-link">
              Explore the product ${icon('arrow', 16)}
            </a>

          </div>

        </div>

        <div class="hero-art">

          <div class="grid-glow"></div>

          <div class="mini-card card-one">

            <span>Revenue, this month</span>

            <strong>$284,400</strong>

            <small>↗ 18.4% from last month</small>

            <svg
              viewBox="0 0 200 60"
              preserveAspectRatio="none"
            >

              <path
                d="M0 54 C25 52 25 30 48 40 S75 45 94 24 S126 34 142 18 S174 21 200 2"
                fill="none"
                stroke="#72d7bd"
                stroke-width="3"
              />

              <path
                d="M0 54 C25 52 25 30 48 40 S75 45 94 24 S126 34 142 18 S174 21 200 2 V60 H0Z"
                fill="url(#g)"
                opacity=".35"
              />

              <defs>
                <linearGradient
                  id="g"
                  x1="0"
                  x2="0"
                  y1="0"
                  y2="1"
                >
                  <stop stop-color="#72d7bd"/>
                  <stop
                    offset="1"
                    stop-color="#72d7bd"
                    stop-opacity="0"
                  />
                </linearGradient>
              </defs>

            </svg>

          </div>

          <div class="mini-card insight-card">

            <i>${icon('spark', 16)}</i>

            <p>
              I've spotted a pattern in your
              <strong>customer retention.</strong>
            </p>

            <button>
              View insight ${icon('arrow', 14)}
            </button>

          </div>

          <div class="orbit orbit-a"></div>
          <div class="orbit orbit-b"></div>

        </div>

      </section>

      <section class="logos">

        <span>BUILT FOR CURIOUS TEAMS</span>

        <b>Brightside</b>
        <b>northstar</b>
        <b>venturo</b>
        <b>parallel</b>
        <b>arc</b>

      </section>

      <section class="product-section" id="product">

        <div class="section-intro">

          <div class="eyebrow">
            <span></span>
            MEET YOUR DATA COPILOT
          </div>

          <h2>
            From raw rows to <em>real clarity.</em>
          </h2>

          <p>
            No dashboards to learn. No formulas to memorize.
            Just a conversation with your data.
          </p>

        </div>

        <div class="product-preview">

          <div class="preview-side">

            <div class="preview-logo">
              in<span>✦</span>
            </div>

            <small>YOUR WORKSPACE</small>

            <a class="active">
              ${icon('chart', 16)}
              Overview
            </a>

            <a>
              ${icon('file', 16)}
              Customers.csv
            </a>

            <a>
              ${icon('file', 16)}
              Q2 Sales.xlsx
            </a>

            <button>
              ${icon('plus', 15)}
              Upload dataset
            </button>

            <div class="side-user">

              <span>AV</span>

              <div>
                <b>Ayesha Vazir</b>
                <small>Starter plan</small>
              </div>

            </div>

          </div>

          <div class="preview-main">

            <div class="preview-top">

              <div>
                <p>
                  Good morning, Ayesha
                  <span>✦</span>
                </p>

                <small>
                  Here's what is happening in your business.
                </small>
              </div>

              <button>
                Last 30 days ${icon('down', 14)}
              </button>

            </div>

            <div class="metrics">

              <div>
                <small>REVENUE</small>
                <strong>$284.4k</strong>
                <em>↗ 18.4%</em>
              </div>

              <div>
                <small>ACTIVE CUSTOMERS</small>
                <strong>12,420</strong>
                <em>↗ 6.2%</em>
              </div>

              <div>
                <small>CHURN RATE</small>
                <strong>2.8%</strong>
                <i>↘ 0.7%</i>
              </div>

            </div>

            <div class="chart-box">

              <div>
                <b>Revenue over time</b>
                <span>↗ Trending up</span>
              </div>

              <div class="bars">
                <i></i><i></i><i></i><i></i><i></i><i></i>
                <i></i><i></i><i></i><i></i><i></i><i></i>
              </div>

              <div class="axis">
                <span>May 1</span>
                <span>May 8</span>
                <span>May 15</span>
                <span>May 22</span>
                <span>May 30</span>
              </div>

            </div>

            <div class="ask-bar">

              ${icon('spark', 16)}

              <span>
                Ask anything about your data...
              </span>

              <button>
                ${icon('send', 15)}
              </button>

            </div>

          </div>

        </div>

      </section>

      <section class="features">

        <article>

          <i>${icon('upload')}</i>
          <span>01</span>

          <h3>Drop in your data</h3>

          <p>
            CSVs, spreadsheets, or exports from the tools
            you already use. We handle the messy bits.
          </p>

        </article>

        <article>

          <i>${icon('chat')}</i>
          <span>02</span>

          <h3>Ask naturally</h3>

          <p>
            “Which customers are most likely to churn?”
            No SQL, no pivot tables, no friction.
          </p>

        </article>

        <article>

          <i>${icon('chart')}</i>
          <span>03</span>

          <h3>Find the signal</h3>

          <p>
            Get answers you can trust, with interactive
            visualizations that make the story clear.
          </p>

        </article>

      </section>

      <section class="quote" id="how">

        <div class="quote-mark">“</div>

        <blockquote>
          InsightFlow gave our whole team a
          <em>common language</em> for our data.
          The questions got better overnight.
        </blockquote>

        <div class="person">

          <span>NO</span>

          <div>
            <b>Nora Owens</b>
            <small>Head of Growth, Brightside</small>
          </div>

        </div>

      </section>

      <section class="cta" id="security">

        <div class="eyebrow">
          <span></span>
          READY WHEN YOU ARE
        </div>

        <h2>
          Your next insight is already<br>
          <em>in your data.</em>
        </h2>

        <button class="button upload-trigger">
          Start exploring for free ${icon('arrow', 17)}
        </button>

        <p>
          No credit card needed · Your data stays yours
        </p>

      </section>

      <footer>

        <a class="brand">
          <i>${icon('spark', 20)}</i>
          insightflow
        </a>

        <span>
          © ${new Date().getFullYear()} InsightFlow, Inc.
        </span>

        <div>
          <a>Privacy</a>
          <a>Terms</a>
          <a>Contact</a>
        </div>

      </footer>

    </main>
  `;
}

// ============================================================
// DASHBOARD
// ============================================================

function dashboard() {
  const p = activeProfile;
  const ml = p?.ml_profile;

  const rows = p
    ? p.row_count.toLocaleString()
    : '—';

  const columns = p
    ? p.column_count
    : '—';

  const missing = p
    ? p.missing_values.toLocaleString()
    : '—';

  const duplicates = p
    ? p.duplicate_rows.toLocaleString()
    : '—';

  const name =
    activeDataset?.original_filename || 'Dataset';

  const mlCard = ml
    ? `
      <section class="ml-profile">

        <div>

          <small>
            DATASET TYPE ·
            ${escapeHtml(ml.confidence.toUpperCase())}
            CONFIDENCE
          </small>

          <h2>
            ${escapeHtml(ml.task_type)}
          </h2>

          <p>
            ${escapeHtml(ml.explanation)}
          </p>

        </div>

        <div class="model-pick">

          <small>RECOMMENDED START</small>

          <b>
            ${escapeHtml(ml.recommended_model)}
          </b>

          <span>
            ${escapeHtml(ml.model_architecture)}
          </span>

          <button
            type="button"
            class="ask-model"
          >
            Ask about training architecture
            ${icon('arrow', 15)}
          </button>

        </div>

      </section>
    `
    : '';

  return `
    <main class="dashboard">

      <aside class="dash-side">

        <a class="brand">
          <i>${icon('spark', 20)}</i>
          insightflow
        </a>

        <div class="workspace">

          <small>WORKSPACE</small>

          <button>
            My analysis ${icon('down', 14)}
          </button>

        </div>

        <nav>

          <a class="active">
            ${icon('chart', 17)}
            Overview
          </a>

          <a>
            ${icon('file', 17)}
            Datasets
            <span>1</span>
          </a>

          <a>
            ${icon('chat', 17)}
            Conversations
          </a>

        </nav>

        <div class="datasets">

          <small>CURRENT DATASET</small>

          <a class="current">
            ${icon('file', 16)}
            ${escapeHtml(name)}
          </a>

          <button class="outline upload-trigger">
            ${icon('plus', 16)}
            Upload dataset
          </button>

        </div>

      </aside>

      <section class="dash-content">

        <header class="dash-header">

          <button class="back-home">
            ← Back to site
          </button>

          <div>
            <button class="avatar">
              ${initials()}
            </button>
          </div>

        </header>

        <div class="dataset-heading">

          <div>

            <div class="crumb">
              DATASETS /
              ${escapeHtml(name.toUpperCase())}
            </div>

            <h1>
              Dataset overview
              <span class="live">● Live</span>
            </h1>

            <p>
              ${rows} rows · ${columns} columns · actual uploaded data
            </p>

          </div>

        </div>

        ${mlCard}

        <div class="quality">

          <div>

            <small>DATA QUALITY</small>

            <strong>
              ${missing === '0' ? '100' : '—'}
              <em>/ 100</em>
            </strong>

            <span>
              Missing values: ${missing}
            </span>

          </div>

          <div class="quality-line">

            <i
              style="width:${missing === '0' ? '100' : '65'}%"
            ></i>

          </div>

          <p>
            Duplicate rows: <b>${duplicates}</b>
          </p>

        </div>

        <div class="stat-grid">

          <div>
            <small>TOTAL ROWS</small>
            <strong>${rows}</strong>
          </div>

          <div>
            <small>COLUMNS</small>
            <strong>${columns}</strong>
          </div>

          <div>
            <small>MISSING VALUES</small>
            <strong>${missing}</strong>
          </div>

          <div>
            <small>DUPLICATE ROWS</small>
            <strong>${duplicates}</strong>
          </div>

        </div>

        <div class="dashboard-grid">

          <article class="wide-chart">

            <div class="card-title">

              <div>
                <b>Dataset columns</b>
                <small>
                  Name, type, missing values, and unique values
                </small>
              </div>

            </div>

            <div class="column-list">

              ${
                p
                  ? p.columns
                      .map(
                        c =>
                          `
                            <p>
                              <b>
                                ${escapeHtml(c.name)}
                              </b>

                              <span>
                                ${c.dtype} ·
                                ${c.unique} unique ·
                                ${c.missing} missing
                              </span>
                            </p>
                          `
                      )
                      .join('')
                  : '<p>Upload a dataset to inspect its columns.</p>'
              }

            </div>

          </article>

          <article class="segments">

            <div class="card-title">

              <div>
                <b>Suggested questions</b>

                <small>
                  Based on this dataset
                </small>
              </div>

            </div>

            <div class="legend suggestions-list">

              ${
                p
                  ? p.suggestions
                      .map(
                        q =>
                          `
                            <button
                              type="button"
                              class="ask-suggestion"
                            >
                              ${escapeHtml(q)}
                            </button>
                          `
                      )
                      .join('')
                  : ''
              }

            </div>

          </article>

          <article class="insight">

            <div class="insight-head">

              <i>${icon('spark', 17)}</i>
              <span>AI ANALYST</span>

            </div>

            <h3>
              Ask questions about your
              <em>actual dataset.</em>
            </h3>

            <p>
              Answers and charts are calculated by
              the FastAPI analysis engine.
            </p>

            <button
              type="button"
              class="ask-insight"
            >
              Open assistant ${icon('arrow', 15)}
            </button>

          </article>

        </div>

      </section>

    </main>
  `;
}

// ============================================================
// UPLOADER
// ============================================================

function uploader() {
  return `
    <div class="modal-wrap" id="upload-modal">

      <div class="modal">

        <button
          type="button"
          class="modal-close"
        >
          ${icon('close')}
        </button>

        <div class="upload-icon">
          ${icon('upload', 24)}
        </div>

        <h2>
          Bring your data to life.
        </h2>

        <p>
          Upload tables, NLP text data, or a ZIP of images
          for CV metadata analysis.
        </p>

        <label
          class="dropzone"
          for="file-input"
        >

          <input
            id="file-input"
            type="file"
            accept=".csv,.xlsx,.xls,.txt,.json,.jsonl,.zip"
          />

          <b>
            Drop your file here, or <u>browse</u>
          </b>

          <span>
            CSV, Excel, TXT, JSON, JSONL, or image ZIP
            · Up to 200 MB
          </span>

        </label>

        <small class="secure">
          ${icon('check', 13)}
          NLP text is profiled by rows; image ZIPs are profiled
          by filename, format, and size.
        </small>

      </div>

    </div>
  `;
}

// ============================================================
// CHATBOT
// ============================================================

function chat() {
  const datasetName = activeDataset
    ? escapeHtml(activeDataset.original_filename)
    : 'your dataset';

  const datasetType =
    activeProfile?.ml_profile?.task_type;

  return `
    <div class="chat-wrap">

      <section class="chat-panel">

        <header>

          <div class="chat-title">

            <i>
              ${icon('spark', 17)}
            </i>

            <div>

              <b>InsightFlow AI</b>

              <small>
                <span></span>
                Ready to analyze
              </small>

            </div>

          </div>

          <button
            type="button"
            class="chat-close"
          >
            ${icon('close', 18)}
          </button>

        </header>

        <div class="chat-body">

          <div class="assistant-msg">

            <i>
              ${icon('spark', 14)}
            </i>

            <div>

              <p>
                Hi ${escapeHtml(userName())}!

                ${
                  activeDataset
                    ? `
                      I’m looking at
                      <strong>${datasetName}</strong>
                      ${
                        datasetType
                          ? `
                            — a
                            <strong>
                              ${escapeHtml(datasetType)}
                            </strong>.
                          `
                          : '.'
                      }
                    `
                    : `
                      Upload a dataset and I’ll help you explore it.
                    `
                }

                What would you like to explore?
              </p>

            </div>

          </div>

          <div class="suggestions">

            <button type="button">
              Give me a dataset overview
            </button>

            <button type="button">
              Find missing values
            </button>

            <button type="button">
              Which model should I train?
            </button>

          </div>

        </div>

        <form class="chat-input">

          <input
            type="text"
            placeholder="Ask anything about your data..."
            autocomplete="off"
          />

          <button type="submit">
            ${icon('send', 16)}
          </button>

        </form>

      </section>

      <button
        type="button"
        class="chat-fab"
      >
        <span>
          ${icon('chat', 22)}
        </span>

        <b>
          Ask AI
        </b>

      </button>

    </div>
  `;
}

// ============================================================
// MAIN CHAT SEND FUNCTION
// ============================================================

async function sendChatMessage(question) {
  const cleanQuestion = String(question || '').trim();

  if (!cleanQuestion) return;

  const body = document.querySelector('.chat-body');
  const input = document.querySelector('.chat-input input');
  const chatWrap = document.querySelector('.chat-wrap');

  if (!body) return;

  // Open chatbot
  if (chatWrap) {
    chatWrap.classList.add('open');
  }

  // ==========================================================
  // NO DATASET
  // ==========================================================

  if (!activeDataset) {
    body.insertAdjacentHTML(
      'beforeend',
      `
        <div class="user-msg">
          ${escapeHtml(cleanQuestion)}
        </div>

        <div class="assistant-msg">

          <i>
            ${icon('spark', 14)}
          </i>

          <div>
            <p>
              Please upload a table, text file, JSON file,
              or image ZIP first.
            </p>
          </div>

        </div>
      `
    );

    body.scrollTop = body.scrollHeight;
    return;
  }

  // ==========================================================
  // USER MESSAGE
  // ==========================================================

  body.insertAdjacentHTML(
    'beforeend',
    `
      <div class="user-msg">
        ${escapeHtml(cleanQuestion)}
      </div>
    `
  );

  // ==========================================================
  // TYPING INDICATOR
  // ==========================================================

  const typingId =
    `typing-${Date.now()}-${Math.random()
      .toString(36)
      .slice(2)}`;

  body.insertAdjacentHTML(
    'beforeend',
    `
      <div
        id="${typingId}"
        class="assistant-msg typing"
      >

        <i>
          ${icon('spark', 14)}
        </i>

        <div>
          <span></span>
          <span></span>
          <span></span>
        </div>

      </div>
    `
  );

  // Clear input
  if (input) {
    input.value = '';
  }

  body.scrollTop = body.scrollHeight;

  // ==========================================================
  // API REQUEST
  // ==========================================================

  try {
    const response = await fetch(
      `${apiBase}/chat`,
      {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json'
        },

        body: JSON.stringify({
          dataset_id: activeDataset.id,
          conversation_id: activeConversation,
          message: cleanQuestion
        })
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(
        result.detail || 'Analysis failed.'
      );
    }

    // Save conversation
    activeConversation = result.conversation_id;

    // ========================================================
    // GENERATED CHART
    // ========================================================

    const chart = result.visualization
      ? `
        <figure class="chat-chart-card">

          <figcaption>
            ${escapeHtml(result.visualization.type)} chart
          </figcaption>

          <img
            class="chat-chart"
            src="${apiBase.replace('/api/v1', '')}/charts/${result.visualization.chart_id}.png"
            alt="${escapeHtml(
              result.visualization.type
            )} chart generated from your dataset"
          />

        </figure>
      `
      : '';

    // ========================================================
    // AI RESPONSE
    // ========================================================

    const messageContent =
      result.message?.content ||
      'No response was returned.';

    const messageHtml =
      escapeHtml(messageContent)
        .replace(/\\n/g, '\n')
        .replace(
          /\*\*(.*?)\*\*/g,
          '<strong>$1</strong>'
        )
        .replace(
          /\n/g,
          '<br>'
        );

    // ========================================================
    // REPLACE TYPING MESSAGE
    // ========================================================

    const typingMessage =
      document.getElementById(typingId);

    if (typingMessage) {
      typingMessage.outerHTML = `
        <div class="assistant-msg result-message">

          <i>
            ${icon('spark', 14)}
          </i>

          <div>

            <p>
              ${messageHtml}
            </p>

            ${chart}

          </div>

        </div>
      `;
    }

  } catch (error) {

    // ========================================================
    // ERROR
    // ========================================================

    const typingMessage =
      document.getElementById(typingId);

    if (typingMessage) {
      typingMessage.outerHTML = `
        <div class="assistant-msg">

          <i>
            ${icon('spark', 14)}
          </i>

          <div>

            <p>
              ${escapeHtml(error.message)}
            </p>

          </div>

        </div>
      `;
    }
  }

  body.scrollTop = body.scrollHeight;
}

// ============================================================
// BIND EVENTS
// ============================================================

function bind() {

  // ==========================================================
  // SIGN IN
  // ==========================================================

  const signin = document.querySelector('.signin');

  if (signin) {
    signin.onclick = () => {

      if (currentUser()) return;

      const name = window.prompt(
        'Enter your name to personalise InsightFlow:'
      );

      if (name?.trim()) {

        localStorage.setItem(
          'insightflow-user',
          JSON.stringify({
            name: name.trim().slice(0, 60)
          })
        );

        render(
          activeDataset
            ? 'dashboard'
            : 'landing'
        );
      }
    };
  }

  // ==========================================================
  // SIGN OUT
  // ==========================================================

  const signout =
    document.querySelector('.signout');

  if (signout) {

    signout.onclick = () => {

      localStorage.removeItem(
        'insightflow-user'
      );

      render(
        activeDataset
          ? 'dashboard'
          : 'landing'
      );
    };
  }

  // ==========================================================
  // UPLOAD BUTTONS
  // ==========================================================

  document
    .querySelectorAll('.upload-trigger')
    .forEach(button => {

      button.onclick = () => {

        const modal =
          document.querySelector('#upload-modal');

        if (modal) {
          modal.classList.add('show');
        }
      };
    });

  // ==========================================================
  // CLOSE UPLOAD MODAL
  // ==========================================================

  const modalClose =
    document.querySelector('.modal-close');

  if (modalClose) {

    modalClose.onclick = () => {

      const modal =
        document.querySelector('#upload-modal');

      if (modal) {
        modal.classList.remove('show');
      }
    };
  }

  // ==========================================================
  // FILE UPLOAD
  // ==========================================================

  const fileInput =
    document.querySelector('#file-input');

  if (fileInput) {

    fileInput.onchange = async e => {

      const file = e.target.files[0];

      if (!file) return;

      const modal =
        document.querySelector('#upload-modal');

      const label =
        modal.querySelector('.dropzone b');

      label.textContent =
        'Uploading and profiling your dataset…';

      try {

        const form = new FormData();

        form.append('file', file);

        const uploaded =
          await fetch(
            `${apiBase}/datasets/upload`,
            {
              method: 'POST',
              body: form
            }
          );

        const result =
          await uploaded.json();

        if (!uploaded.ok) {

          throw new Error(
            result.detail ||
            'Upload failed.'
          );
        }

        activeDataset = result;

        // ----------------------------------------------
        // Profile dataset
        // ----------------------------------------------

        const profileResponse =
          await fetch(
            `${apiBase}/datasets/${result.id}/profile`
          );

        activeProfile =
          await profileResponse.json();

        if (!profileResponse.ok) {

          throw new Error(
            activeProfile.detail ||
            'Profile could not be created.'
          );
        }

        // Start new conversation
        activeConversation = null;

        // Close modal
        modal.classList.remove('show');

        // Show dashboard
        render('dashboard');

      } catch (error) {

        label.textContent =
          error.message;
      }
    };
  }

  // ==========================================================
  // CHAT FAB
  // ==========================================================

  const chatWrap =
    document.querySelector('.chat-wrap');

  const chatFab =
    document.querySelector('.chat-fab');

  const chatClose =
    document.querySelector('.chat-close');

  if (chatFab) {

    chatFab.onclick = () => {

      chatWrap.classList.toggle('open');
    };
  }

  // ==========================================================
  // CHAT CLOSE
  // ==========================================================

  if (chatClose) {

    chatClose.onclick = () => {

      chatWrap.classList.remove('open');
    };
  }

  // ==========================================================
  // CHAT FORM
  // ==========================================================

  const chatForm =
    document.querySelector('.chat-input');

  if (chatForm) {

    chatForm.onsubmit = async e => {

      e.preventDefault();

      const input =
        e.currentTarget.querySelector('input');

      const question =
        input.value.trim();

      if (!question) return;

      await sendChatMessage(question);
    };
  }

  // ==========================================================
  // DASHBOARD SUGGESTED QUESTIONS
  // ==========================================================

  document
    .querySelectorAll('.ask-suggestion')
    .forEach(button => {

      button.onclick = async () => {

        const question =
          button.textContent.trim();

        if (!question) return;

        await sendChatMessage(question);
      };
    });

  // ==========================================================
  // CHATBOT SUGGESTED QUESTIONS
  // ==========================================================

  document
    .querySelectorAll('.suggestions button')
    .forEach(button => {

      button.onclick = async () => {

        const question =
          button.textContent.trim();

        if (!question) return;

        await sendChatMessage(question);
      };
    });

  // ==========================================================
  // ASK INSIGHT
  // ==========================================================

  const insight =
    document.querySelector('.ask-insight');

  if (insight) {

    insight.onclick = () => {

      if (chatWrap) {
        chatWrap.classList.add('open');
      }
    };
  }

  // ==========================================================
  // ASK MODEL / TRAINING ARCHITECTURE
  // ==========================================================

  const model =
    document.querySelector('.ask-model');

  if (model) {

    model.onclick = async () => {

      await sendChatMessage(
        'Which model should I train and what architecture should I use?'
      );
    };
  }

  // ==========================================================
  // BACK TO HOME
  // ==========================================================

  const back =
    document.querySelector('.back-home');

  if (back) {

    back.onclick = () => {
      render('landing');
    };
  }
}

// ============================================================
// RENDER
// ============================================================

function render(view = 'landing') {

  app.innerHTML =
    header() +
    (
      view === 'landing'
        ? landing()
        : dashboard()
    ) +
    uploader() +
    chat();

  bind();
}

// ============================================================
// INITIAL RENDER
// ============================================================

render('landing');