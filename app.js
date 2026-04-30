// ═══════════════════════════════════════════════════════════
//  CONFIG  –  change this if your backend runs on another port
// ═══════════════════════════════════════════════════════════
const API = 'https://dynamic-sales-dashboard.onrender.com/api';

// ═══════════════════════════════════════════════════════════
//  TOAST  –  small notification popup
// ═══════════════════════════════════════════════════════════
function showToast(msg, type = 'success') {
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3500);
}

// ═══════════════════════════════════════════════════════════
//  AUTH HELPERS
// ═══════════════════════════════════════════════════════════
function getToken()         { return localStorage.getItem('token'); }
function setToken(t)        { localStorage.setItem('token', t); }
function getUsername()      { return localStorage.getItem('username'); }
function setUsername(u)     { localStorage.setItem('username', u); }

function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
}

// Switch between Login / Register tabs
function switchTab(tab) {
    const isLogin = tab === 'login';
    document.getElementById('loginForm').classList.toggle('hidden', !isLogin);
    document.getElementById('registerForm').classList.toggle('hidden', isLogin);
    document.getElementById('tabLogin').classList.toggle('active', isLogin);
    document.getElementById('tabRegister').classList.toggle('active', !isLogin);
    document.getElementById('tabLogin').classList.toggle('text-white/50', !isLogin);
    document.getElementById('tabRegister').classList.toggle('text-white/50', isLogin);
}

// ── REGISTER ──────────────────────────────────────────────
async function register() {
    const username = document.getElementById('regUsername').value.trim();
    const email    = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;

    if (!username || !email || !password) { showToast('Please fill all fields', 'error'); return; }

    document.getElementById('regBtnText').classList.add('hidden');
    document.getElementById('regSpinner').classList.remove('hidden');

    try {
        const res = await fetch(`${API}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Registration failed');
        showToast('Account created! Please log in.');
        switchTab('login');
        document.getElementById('loginUsername').value = username;
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        document.getElementById('regBtnText').classList.remove('hidden');
        document.getElementById('regSpinner').classList.add('hidden');
    }
}

// ── LOGIN ─────────────────────────────────────────────────
async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    if (!username || !password) { showToast('Please fill all fields', 'error'); return; }

    document.getElementById('loginBtnText').classList.add('hidden');
    document.getElementById('loginSpinner').classList.remove('hidden');

    try {
        const res = await fetch(`${API}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Login failed');

        setToken(data.access_token);
        setUsername(data.user.username);
        showDashboard();
        showToast(`Welcome back, ${data.user.username}!`);
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        document.getElementById('loginBtnText').classList.remove('hidden');
        document.getElementById('loginSpinner').classList.add('hidden');
    }
}

// ── LOGOUT ────────────────────────────────────────────────
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    document.getElementById('authSection').classList.remove('hidden');
    document.getElementById('dashboardSection').classList.add('hidden');
    document.getElementById('navUser').classList.add('hidden');
    showToast('Logged out successfully.');
}

// ═══════════════════════════════════════════════════════════
//  SHOW / HIDE SECTIONS
// ═══════════════════════════════════════════════════════════
function showDashboard() {
    document.getElementById('authSection').classList.add('hidden');
    document.getElementById('dashboardSection').classList.remove('hidden');
    document.getElementById('navUser').classList.remove('hidden');
    document.getElementById('navUsername').textContent = `👤 ${getUsername()}`;
    loadSavedFiles();
}

// ═══════════════════════════════════════════════════════════
//  SAVED FILES LIST
// ═══════════════════════════════════════════════════════════
async function loadSavedFiles() {
    try {
        const res = await fetch(`${API}/files/`, { headers: authHeaders() });
        const files = await res.json();

        const section = document.getElementById('savedFilesSection');
        const list    = document.getElementById('savedFilesList');

        if (!files.length) { section.classList.add('hidden'); return; }

        section.classList.remove('hidden');
        list.innerHTML = files.map(f => `
            <div class="glass p-4 flex flex-col gap-2">
                <div class="font-600 text-sm truncate">📄 ${f.filename}</div>
                <div class="text-xs text-white/40">${f.rows?.toLocaleString()} rows · ${f.columns} cols</div>
                <div class="text-xs text-white/30">${new Date(f.uploaded_at).toLocaleDateString()}</div>
                <button onclick="deleteFile(${f.id})" class="text-xs text-red-400 hover:text-red-300 text-left mt-1">🗑 Delete</button>
            </div>
        `).join('');
    } catch(e) { /* silent */ }
}

async function deleteFile(id) {
    if (!confirm('Delete this file and its dashboards?')) return;
    await fetch(`${API}/files/${id}`, { method: 'DELETE', headers: authHeaders() });
    showToast('File deleted.');
    loadSavedFiles();
}

// ═══════════════════════════════════════════════════════════
//  FILE UPLOAD  →  send to backend  →  render results
// ═══════════════════════════════════════════════════════════
async function handleFile(file) {
    const spinner = document.getElementById('uploadSpinner');
    spinner.classList.remove('hidden');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch(`${API}/files/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${getToken()}` },
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Upload failed');

        showToast(`✅ ${data.filename} analyzed — ${data.rows.toLocaleString()} rows`);
        renderResults(data, file);
        loadSavedFiles();

    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        spinner.classList.add('hidden');
    }
}

// ═══════════════════════════════════════════════════════════
//  RENDER RESULTS FROM BACKEND RESPONSE
// ═══════════════════════════════════════════════════════════
function renderResults(data, file) {
    const analysis = data.analysis;

    // ── File Info ─────────────────────────────────────────
    document.getElementById('fileInfo').classList.remove('hidden');
    document.getElementById('fileDetails').innerHTML = [
        ['📄 File Name',  data.filename],
        ['📋 Rows',       data.rows?.toLocaleString()],
        ['🔢 Columns',    data.columns],
        ['💾 Size',       data.file_size_kb + ' KB'],
    ].map(([label, value]) => `
        <div class="kpi-card text-center">
            <div class="text-xs text-white/40 mb-1">${label}</div>
            <div class="text-lg font-700 text-white">${value}</div>
        </div>
    `).join('');

    // ── KPIs ──────────────────────────────────────────────
    const kpis = analysis.kpis;
    if (kpis && kpis.total !== undefined) {
        document.getElementById('kpiSection').classList.remove('hidden');
        const items = [
            ['💰', 'Total',    fmt(kpis.total)],
            ['📊', 'Average',  fmt(kpis.average)],
            ['📈', 'Maximum',  fmt(kpis.maximum)],
            ['📉', 'Minimum',  fmt(kpis.minimum)],
            ['🚀', 'Growth',   kpis.growth_rate_pct + '%'],
        ];
        document.getElementById('kpiGrid').innerHTML = items.map(([icon, label, value]) => `
            <div class="kpi-card text-center">
                <div class="text-2xl mb-1">${icon}</div>
                <div class="text-xl font-700">${value}</div>
                <div class="text-xs text-white/40 mt-1">${label}</div>
            </div>
        `).join('');
    }

    // ── Column Table ──────────────────────────────────────
    document.getElementById('columnInfo').classList.remove('hidden');
    const cols = analysis.columns || [];
    document.getElementById('columnDetails').innerHTML = `
        <table class="w-full text-sm">
            <thead>
                <tr class="text-white/40 border-b border-white/10">
                    <th class="text-left py-2 pr-4">Column</th>
                    <th class="text-left py-2 pr-4">Type</th>
                    <th class="text-left py-2 pr-4">Unique Values</th>
                    <th class="text-left py-2">Sample</th>
                </tr>
            </thead>
            <tbody>
                ${cols.map(col => {
                    const badgeClass = col.type === 'numeric' ? 'badge-number' :
                                       col.type === 'date'    ? 'badge-date'   :
                                       col.type === 'boolean' ? 'badge-bool'   : 'badge-text';
                    const sample = col.top_values
                        ? Object.keys(col.top_values).slice(0,3).join(', ')
                        : '';
                    return `<tr class="border-b border-white/5 hover:bg-white/3">
                        <td class="py-2 pr-4 font-500">${col.name}</td>
                        <td class="py-2 pr-4"><span class="badge ${badgeClass}">${col.type}</span></td>
                        <td class="py-2 pr-4 text-white/60">${col.unique_values}</td>
                        <td class="py-2 text-white/40 text-xs">${sample}</td>
                    </tr>`;
                }).join('')}
            </tbody>
        </table>
    `;

    // ── Charts  ───────────────────────────────────────────
    document.getElementById('chartsSection').classList.remove('hidden');
    generateChartsFromData(data, analysis);
}

// ═══════════════════════════════════════════════════════════
//  CHART GENERATION  (uses backend analysis + local SheetJS)
// ═══════════════════════════════════════════════════════════
let activeCharts = [];

function generateChartsFromData(uploadResponse, analysis) {
    activeCharts.forEach(c => c.destroy());
    activeCharts = [];

    const container = document.getElementById('chartsContainer');
    container.innerHTML = '';

    const numCols = analysis.numeric_columns || [];
    const allCols = analysis.columns || [];
    const textCols = allCols.filter(c => c.type === 'text');

    // We need to re-parse the file locally for chart data
    // (since backend already saved it, we use the analysis metadata)
    // Charts are rendered using the ExcelDashboard class below
    window._pendingAnalysis = { numCols, textCols, allCols };
    // Signal to the ExcelDashboard instance to render from backend analysis
    if (window.dashboard) {
        window.dashboard.renderChartsFromAnalysis(numCols, textCols);
    }
}

// ═══════════════════════════════════════════════════════════
//  HELPER
// ═══════════════════════════════════════════════════════════
function fmt(n) {
    return parseFloat(n).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

// ═══════════════════════════════════════════════════════════
//  EXCEL DASHBOARD CLASS  (original local chart logic kept)
// ═══════════════════════════════════════════════════════════
class ExcelDashboard {
    constructor() {
        this.currentData    = null;
        this.currentColumns = null;
        this.charts         = [];
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput  = document.getElementById('fileInput');

        uploadArea.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) this.handleFile(e.target.files[0]);
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) this.handleFile(e.dataTransfer.files[0]);
        });
    }

    async handleFile(file) {
        // 1. Send to backend first (saves file + analysis)
        await handleFile(file);  // global function above

        // 2. Also parse locally so we can draw charts with real data
        try {
            const data = await this.readExcelFile(file);
            this.currentData    = data;
            this.currentColumns = this.detectColumns(data);
            this.generateCharts();
        } catch(e) {
            console.warn('Local chart generation failed:', e);
        }
    }

    readExcelFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data     = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, { type: 'array' });
                    const sheet    = workbook.Sheets[workbook.SheetNames[0]];
                    const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1 });
                    const headers  = jsonData[0];
                    const rows     = jsonData.slice(1).filter(r => r.some(c => c !== null && c !== ''));
                    resolve(rows.map(row => {
                        const obj = {};
                        headers.forEach((h, i) => obj[h] = row[i] ?? null);
                        return obj;
                    }));
                } catch(e) { reject(e); }
            };
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsArrayBuffer(file);
        });
    }

    detectColumns(data) {
        if (!data?.length) return [];
        const sampleSize = Math.min(100, data.length);
        return Object.keys(data[0]).map(name => {
            const vals = data.slice(0, sampleSize).map(r => r[name]).filter(v => v !== null && v !== '');
            return {
                name,
                type: this.inferDataType(vals),
                uniqueValues: new Set(vals).size,
                totalValues: vals.length,
                nullCount: data.length - vals.length,
                sampleValues: vals.slice(0, 5)
            };
        });
    }

    inferDataType(values) {
        if (!values.length) return 'text';
        const numericCount = values.filter(v => !isNaN(v) && v !== '').length;
        if (numericCount / values.length > 0.8) return 'number';
        const dateCount = values.filter(v => {
            const d = new Date(v);
            return !isNaN(d.getTime()) && String(v).match(/\d{4}-\d{2}-\d{2}|\d{2}\/\d{2}\/\d{4}/);
        }).length;
        if (dateCount / values.length > 0.8) return 'date';
        const boolCount = values.filter(v =>
            typeof v === 'string' && ['true','false','yes','no','1','0'].includes(v.toLowerCase())
        ).length;
        if (boolCount / values.length > 0.8) return 'boolean';
        return 'text';
    }

    // Called by generateChartsFromData when we only have backend analysis (no local file)
    renderChartsFromAnalysis(numCols, textCols) {
        // Nothing to render without actual data rows — charts need real values.
        // This is called after handleFile re-parses locally, so charts are already drawn.
    }

    generateCharts() {
        this.charts.forEach(c => c.destroy());
        this.charts = [];
        activeCharts = this.charts;

        const container = document.getElementById('chartsContainer');
        container.innerHTML = '';

        const configs     = this.createChartConfigs();
        configs.forEach((cfg, i) => {
            const div = document.createElement('div');
            div.className = 'chart-card';
            div.innerHTML = `
                <h3 class="font-600 text-white mb-4">${cfg.title}</h3>
                <div class="chart-container"><canvas id="chart-${i}"></canvas></div>
            `;
            container.appendChild(div);
            const chart = new Chart(document.getElementById(`chart-${i}`).getContext('2d'), cfg.chartConfig);
            this.charts.push(chart);
        });
    }

    createChartConfigs() {
        const configs  = [];
        const numCols  = this.currentColumns.filter(c => c.type === 'number');
        const textCols = this.currentColumns.filter(c => c.type === 'text');
        const limit    = Math.min(50, this.currentData.length);
        const slice    = this.currentData.slice(0, limit);
        const COLORS   = ['#6366f1','#8b5cf6','#ec4899','#06b6d4','#10b981','#f59e0b','#ef4444','#84cc16'];

        // Bar chart
        if (numCols.length > 0) {
            const col    = numCols[0];
            const values = slice.map(r => r[col.name]).filter(v => v !== null && !isNaN(v));
            configs.push({
                title: `${col.name} – Bar Chart`,
                chartConfig: {
                    type: 'bar',
                    data: {
                        labels: values.map((_, i) => `Row ${i+1}`),
                        datasets: [{ label: col.name, data: values,
                            backgroundColor: COLORS[0] + 'aa', borderColor: COLORS[0], borderWidth: 2, borderRadius: 4 }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
                        plugins: { legend: { labels: { color: '#e8e8f0' } } },
                        scales: { x: { ticks: { color: '#ffffff50' }, grid: { display: false } },
                                  y: { ticks: { color: '#ffffff50' }, grid: { color: '#ffffff10' }, beginAtZero: true } } }
                }
            });
        }

        // Pie chart
        const catCol = textCols.find(c => c.uniqueValues <= 10);
        if (catCol) {
            const counts = {};
            this.currentData.forEach(r => {
                const v = r[catCol.name];
                if (v) counts[v] = (counts[v] || 0) + 1;
            });
            const entries = Object.entries(counts).sort((a,b) => b[1]-a[1]).slice(0,8);
            configs.push({
                title: `${catCol.name} – Pie Chart`,
                chartConfig: {
                    type: 'pie',
                    data: {
                        labels: entries.map(([k]) => k),
                        datasets: [{ data: entries.map(([,v]) => v),
                            backgroundColor: COLORS.map(c => c + 'cc'), borderColor: '#0a0a0f', borderWidth: 2 }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
                        plugins: { legend: { position: 'right', labels: { color: '#e8e8f0', font: { size: 11 } } } } }
                }
            });
        }

        // Line chart
        if (numCols.length >= 1) {
            const cols2 = numCols.slice(0, 2);
            configs.push({
                title: 'Trends – Line Chart',
                chartConfig: {
                    type: 'line',
                    data: {
                        labels: slice.map((_, i) => `P${i+1}`),
                        datasets: cols2.map((col, i) => ({
                            label: col.name,
                            data: slice.map(r => r[col.name]).filter(v => !isNaN(v)),
                            borderColor: COLORS[i], backgroundColor: COLORS[i] + '22',
                            borderWidth: 2, tension: 0.4, pointRadius: 2
                        }))
                    },
                    options: { responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
                        plugins: { legend: { labels: { color: '#e8e8f0' } } },
                        scales: { x: { ticks: { color: '#ffffff50' }, grid: { display: false } },
                                  y: { ticks: { color: '#ffffff50' }, grid: { color: '#ffffff10' } } } }
                }
            });
        }

        // Horizontal bar
        if (numCols.length > 1) {
            const col    = numCols[1];
            const values = slice.map(r => r[col.name]).filter(v => !isNaN(v)).slice(0, 15);
            configs.push({
                title: `${col.name} – Horizontal Bar`,
                chartConfig: {
                    type: 'bar',
                    data: {
                        labels: values.map((_, i) => `Item ${i+1}`),
                        datasets: [{ label: col.name, data: values,
                            backgroundColor: COLORS[2] + 'aa', borderColor: COLORS[2], borderWidth: 2, borderRadius: 4 }]
                    },
                    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
                        plugins: { legend: { labels: { color: '#e8e8f0' } } },
                        scales: { x: { ticks: { color: '#ffffff50' }, grid: { color: '#ffffff10' }, beginAtZero: true },
                                  y: { ticks: { color: '#ffffff50' }, grid: { display: false } } } }
                }
            });
        }

        return configs;
    }
}

// ═══════════════════════════════════════════════════════════
//  BOOT  –  check if already logged in
// ═══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ExcelDashboard();

    if (getToken()) {
        showDashboard();
    }
});
