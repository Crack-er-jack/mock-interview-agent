/* ================================================================
   MOCK INTERVIEW AGENT — Client-Side SPA Logic
   Config → Interview (Chat + Code) → Scorecard
   ================================================================ */

const API = '';  // same origin

// ── Error Toast ─────────────────────────────────────────────
function showError(msg) {
    // Remove existing toast if any
    const old = document.getElementById('error-toast');
    if (old) old.remove();

    const toast = document.createElement('div');
    toast.id = 'error-toast';
    toast.style.cssText = `
        position: fixed; top: 24px; left: 50%; transform: translateX(-50%);
        background: #1e1028; border: 1px solid rgba(239,68,68,0.5);
        color: #f87171; padding: 1rem 1.5rem; border-radius: 12px;
        font-family: 'Inter', sans-serif; font-size: 0.9rem;
        z-index: 9999; max-width: 500px; text-align: center;
        box-shadow: 0 8px 32px rgba(239,68,68,0.2);
        animation: fadeIn 0.3s ease;
    `;
    toast.textContent = msg;

    const close = document.createElement('span');
    close.textContent = ' ✕';
    close.style.cssText = 'cursor:pointer; margin-left:0.5rem; opacity:0.7;';
    close.onclick = () => toast.remove();
    toast.appendChild(close);

    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 8000);
}

// ── State ───────────────────────────────────────────────────
let state = {
    sessionId: null,
    plan: null,
    phase: 'planning',
    timerInterval: null,
    elapsedSeconds: 0,
};

// ── DOM Refs ────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const views = {
    config: $('#config-view'),
    interview: $('#interview-view'),
    scorecard: $('#scorecard-view'),
};

// ── View Navigation ─────────────────────────────────────────
function showView(name) {
    Object.values(views).forEach(v => v.classList.remove('active'));
    views[name].classList.add('active');
}

// ── Button loading helpers ──────────────────────────────────
function setLoading(btn, isLoading) {
    const text = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');
    if (text) text.style.display = isLoading ? 'none' : '';
    if (loader) loader.style.display = isLoading ? 'inline-flex' : 'none';
    btn.disabled = isLoading;
}

// ══════════════════════════════════════════════════════════════
// CONFIG VIEW
// ══════════════════════════════════════════════════════════════

// Chip group selection
document.querySelectorAll('#round-type-group .chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('#round-type-group .chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
    });
});

// Form submit
$('#config-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = $('#start-btn');
    setLoading(btn, true);

    const company = $('#company-input').value.trim();
    const role = $('#role-select').value;
    const level = $('#level-select').value;
    const roundType = document.querySelector('#round-type-group .chip.active')?.dataset.value || 'DSA';

    try {
        const res = await fetch(`${API}/api/session/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company, role, level, round_type: roundType }),
        });

        if (!res.ok) {
            let detail = 'Failed to start session';
            try {
                const err = await res.json();
                detail = err.detail || detail;
            } catch (_) { }
            // Provide user-friendly hint for auth errors
            if (detail.includes('Authorization') || detail.includes('API key') || detail.includes('auth')) {
                detail = '⚠️ API key not configured! Open .env file and add your Gemini API key from aistudio.google.com';
            }
            throw new Error(detail);
        }

        const data = await res.json();
        state.sessionId = data.session_id;
        state.plan = data.plan;

        enterInterviewView(company);
    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(btn, false);
    }
});

// ══════════════════════════════════════════════════════════════
// INTERVIEW VIEW
// ══════════════════════════════════════════════════════════════

function enterInterviewView(company) {
    showView('interview');

    // Set header
    $('#company-badge').textContent = company;
    updatePhase('question');

    // Show plan banner
    if (state.plan) {
        const details = $('#plan-details');
        details.innerHTML = `
            <div class="plan-item"><span class="plan-label">Duration:</span> <span class="plan-value">${state.plan.duration_minutes} min</span></div>
            <div class="plan-item"><span class="plan-label">Difficulty:</span> <span class="plan-value">${state.plan.difficulty}</span></div>
            <div class="plan-item"><span class="plan-label">Persona:</span> <span class="plan-value">${capitalize(state.plan.persona)}</span></div>
            <div class="plan-item"><span class="plan-label">Topic:</span> <span class="plan-value">${state.plan.question_topic_hint}</span></div>
            <div class="plan-item"><span class="plan-label">AI Policy:</span> <span class="plan-value">${state.plan.ai_policy}</span></div>
        `;
        $('#plan-banner').style.display = '';
    }

    // Load initial conversation
    loadConversation();

    // Start timer
    state.elapsedSeconds = 0;
    startTimer();
}

function capitalize(s) {
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}

// ── Plan banner dismiss ─────────────────────────────────────
$('#dismiss-plan-btn').addEventListener('click', () => {
    $('#plan-banner').style.display = 'none';
});

// ── Timer ───────────────────────────────────────────────────
function startTimer() {
    if (state.timerInterval) clearInterval(state.timerInterval);
    state.timerInterval = setInterval(() => {
        state.elapsedSeconds++;
        const m = String(Math.floor(state.elapsedSeconds / 60)).padStart(2, '0');
        const s = String(state.elapsedSeconds % 60).padStart(2, '0');
        $('#timer').textContent = `${m}:${s}`;
    }, 1000);
}

function stopTimer() {
    if (state.timerInterval) clearInterval(state.timerInterval);
}

// ── Phase badge ─────────────────────────────────────────────
function updatePhase(phase) {
    state.phase = phase;
    const badge = $('#phase-badge');
    const labels = {
        question: 'Question',
        clarification: 'Clarification',
        complexity: 'Complexity',
        edge_cases: 'Edge Cases',
        coding: 'Coding',
        evaluating: 'Evaluating...',
        completed: 'Completed',
    };
    badge.textContent = labels[phase] || phase;
}

// ── Chat ────────────────────────────────────────────────────
async function loadConversation() {
    try {
        const res = await fetch(`${API}/api/session/${state.sessionId}`);
        const session = await res.json();

        const container = $('#chat-messages');
        container.innerHTML = '';

        for (const msg of session.conversation) {
            addMessage(msg.role, msg.content);
        }
    } catch (err) {
        console.error('Failed to load conversation:', err);
    }
}

function addMessage(role, content) {
    const container = $('#chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = role === 'assistant' ? '🎯 Interviewer' : '👤 You';
    div.appendChild(label);

    const text = document.createElement('div');
    text.textContent = content;
    div.appendChild(text);

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// Send message
$('#send-btn').addEventListener('click', sendMessage);
$('#chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const input = $('#chat-input');
    const message = input.value.trim();
    if (!message) return;

    const btn = $('#send-btn');
    setLoading(btn, true);
    input.value = '';

    addMessage('user', message);

    try {
        const res = await fetch(`${API}/api/interview/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: state.sessionId, message }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to send message');
        }

        const data = await res.json();
        addMessage('assistant', data.reply);
        updatePhase(data.phase);
    } catch (err) {
        addMessage('assistant', `⚠️ Error: ${err.message}`);
    } finally {
        setLoading(btn, false);
        input.focus();
    }
}

// ── Code execution ──────────────────────────────────────────
$('#run-code-btn').addEventListener('click', runCode);

// Handle Tab key in code editor
$('#code-editor').addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
        e.preventDefault();
        const editor = e.target;
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
        editor.selectionStart = editor.selectionEnd = start + 4;
    }
});

async function runCode() {
    const code = $('#code-editor').value;
    if (!code.trim()) return;

    const btn = $('#run-code-btn');
    const output = $('#code-output');
    setLoading(btn, true);
    output.textContent = 'Running...';
    output.className = 'code-output';

    try {
        const res = await fetch(`${API}/api/code/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: state.sessionId, code }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Execution failed');
        }

        const data = await res.json();

        if (data.timed_out) {
            output.textContent = '⏱️ Code timed out!';
            output.className = 'code-output error';
        } else if (data.stderr) {
            output.textContent = data.stderr;
            output.className = 'code-output error';
        } else {
            output.textContent = data.stdout || '(No output)';
            output.className = 'code-output success';
        }
    } catch (err) {
        output.textContent = `Error: ${err.message}`;
        output.className = 'code-output error';
    } finally {
        setLoading(btn, false);
    }
}

// ── End Interview ───────────────────────────────────────────
$('#end-interview-btn').addEventListener('click', async () => {

    const btn = $('#end-interview-btn');
    btn.disabled = true;
    btn.textContent = 'Evaluating...';
    updatePhase('evaluating');
    stopTimer();

    try {
        const res = await fetch(`${API}/api/interview/evaluate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: state.sessionId }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Evaluation failed');
        }

        const data = await res.json();
        showScorecard(data.scorecard);
    } catch (err) {
        showError(`Evaluation error: ${err.message}`);
        btn.disabled = false;
        btn.textContent = 'End Interview';
    }
});

// ══════════════════════════════════════════════════════════════
// SCORECARD VIEW
// ══════════════════════════════════════════════════════════════

function showScorecard(scorecard) {
    showView('scorecard');

    // Subtitle
    const company = $('#company-badge').textContent;
    $('#scorecard-subtitle').textContent = `${company} · Interview Duration: ${formatTime(state.elapsedSeconds)}`;

    // Verdict
    const verdictEl = $('#verdict-value');
    verdictEl.textContent = scorecard.overall;
    verdictEl.className = 'verdict-value ' + scorecard.overall.toLowerCase().replace(/\s+/g, '-');
    $('#verdict-score').textContent = `${scorecard.total} / ${scorecard.max_total}`;

    // Score cards
    const grid = $('#scores-grid');
    grid.innerHTML = '';

    const labels = {
        problem_understanding: '🧩 Problem Understanding',
        logical_correctness: '🎯 Logical Correctness',
        code_quality: '💎 Code Quality',
        optimization: '⚡ Optimization',
        communication: '💬 Communication',
    };

    for (const [key, cat] of Object.entries(scorecard.scores)) {
        const pct = (cat.score / cat.max) * 100;
        const card = document.createElement('div');
        card.className = 'score-card glass-card';
        card.innerHTML = `
            <div class="score-card-header">
                <span class="score-name">${labels[key] || key}</span>
                <span class="score-value">${cat.score}/${cat.max}</span>
            </div>
            <div class="score-bar">
                <div class="score-bar-fill" style="width: 0%"></div>
            </div>
            <div class="score-feedback">${cat.feedback}</div>
        `;
        grid.appendChild(card);

        // Animate bar
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                card.querySelector('.score-bar-fill').style.width = pct + '%';
            });
        });
    }

    // Summary
    $('#summary-text').textContent = scorecard.summary;
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}m ${s}s`;
}

// ── New Interview ───────────────────────────────────────────
$('#new-interview-btn').addEventListener('click', () => {
    state = { sessionId: null, plan: null, phase: 'planning', timerInterval: null, elapsedSeconds: 0 };
    $('#chat-messages').innerHTML = '';
    $('#code-editor').value = '';
    $('#code-output').textContent = 'Run your code to see output here...';
    $('#code-output').className = 'code-output';
    $('#config-form').reset();
    showView('config');
});
