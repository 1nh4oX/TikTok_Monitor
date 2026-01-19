/**
 * Douyin Monitor Pro - V4.2 Logic
 * Updates: Separated New/Ranked lists, improved drag/drop
 */

const API_BASE = '';
let compareWords = [];
let mainChart = null;
let refreshTimer = null;
let currentSettings = {};
let selectedHours = 1; // 默认显示 1 小时

// Colors
const PALETTE = ['#6366f1', '#ec4899', '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6'];

// DOM Elements
const els = {
    hotList: document.getElementById('hotList'),
    newList: document.getElementById('newList'),
    newSection: document.getElementById('newArrivalsSection'),
    dropZone: document.getElementById('dropZone'),
    activeTags: document.getElementById('compareTags'),
    mainChart: document.getElementById('mainChart'),
    risingList: document.getElementById('risingList'),
    manualInput: document.getElementById('manualInput'),
    btnManualAdd: document.getElementById('btnManualAdd'),
    btnRefresh: document.getElementById('btnRefresh'),
    updateTime: document.getElementById('updateTime'),

    // Stats
    statCurrentCount: document.getElementById('statCurrentCount'),
    statTotalSnapshots: document.getElementById('statTotalSnapshots'),

    // Settings
    settingInterval: document.getElementById('settingInterval'),
    settingRefresh: document.getElementById('settingRefresh'),
    settingHistory: document.getElementById('settingHistory'),
    btnSaveSettings: document.getElementById('btnSaveSettings') // Fixed typo btnSaveSetting -> btnSaveSettings
};

// ==========================================
// Initialization
// ==========================================

function init() {
    setupDragAndDrop();
    setupEventListeners();
    loadAllData();
    window.addEventListener('resize', () => mainChart && mainChart.resize());
}

function setupEventListeners() {
    els.btnManualAdd.addEventListener('click', () => {
        addWord(els.manualInput.value);
        els.manualInput.value = '';
    });

    els.manualInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addWord(els.manualInput.value);
            els.manualInput.value = '';
        }
    });

    els.btnRefresh.addEventListener('click', manualRefresh);
    if (els.btnSaveSettings) els.btnSaveSettings.addEventListener('click', saveSettings);

    // 时间范围选择器
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedHours = parseInt(btn.dataset.hours);
            if (compareWords.length > 0) {
                updateChart();
            }
        });
    });
}

function setupDragAndDrop() {
    // Drop Zone Events
    els.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        els.dropZone.classList.add('drag-over');
    });

    els.dropZone.addEventListener('dragleave', () => {
        els.dropZone.classList.remove('drag-over');
    });

    els.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        els.dropZone.classList.remove('drag-over');
        const word = e.dataTransfer.getData('text/plain');
        if (word) addWord(word);
    });
}

// ==========================================
// Data Logic
// ==========================================

async function loadAllData() {
    await Promise.all([
        fetchHotList(),
        fetchRising(),
        fetchStatus()
    ]);
}

async function fetchHotList() {
    try {
        const res = await fetch(`${API_BASE}/api/hot`);
        const data = await res.json();
        if (data.success) {
            renderHotList(data.data);
            els.statCurrentCount.textContent = data.count;
            updateStatusTime();
        }
    } catch (e) {
        console.error(e);
        showToast('热榜数据获取失败', 'error');
    }
}

async function fetchRising() {
    try {
        const res = await fetch(`${API_BASE}/api/rising`);
        const data = await res.json();
        if (data.success) renderRising(data.data);
    } catch (e) { console.error(e); }
}

async function fetchStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        const data = await res.json();
        if (data.success) {
            els.statTotalSnapshots.textContent = data.total_snapshots;
            if (data.settings) applySettings(data.settings);
        }
    } catch (e) { console.error(e); }
}

async function manualRefresh() {
    const btn = els.btnRefresh;
    btn.style.animation = 'spin 1s infinite linear';
    try {
        await fetch(`${API_BASE}/api/refresh`, { method: 'POST' });
        await new Promise(r => setTimeout(r, 1000));
        await loadAllData();
        showToast('数据已更新', 'success');
    } catch (e) {
        showToast('刷新失败', 'error');
    } finally {
        btn.style.animation = '';
    }
}

// ==========================================
// Rendering Logic
// ==========================================

function renderHotList(list) {
    const rankedItems = list.filter(item => item.hot_value > 0);
    const newItems = list.filter(item => item.hot_value === 0);

    // Render Ranked List
    if (rankedItems.length === 0 && newItems.length === 0) {
        els.hotList.innerHTML = `<div style="text-align:center; padding: 40px; color: var(--text-muted);">暂无数据</div>`;
    } else {
        els.hotList.innerHTML = rankedItems.map((item, idx) => {
            let tagHtml = '';
            if (item.tag === '热' || item.tag === '爆') tagHtml = `<span class="tag hot">HOT</span>`;

            return `
            <div class="hot-item" draggable="true" data-word="${escapeHtml(item.word)}">
                <div class="rank-num">${idx + 1}</div>
                <div class="item-info">
                    <div class="item-title">${escapeHtml(item.word)}</div>
                    <div class="item-meta">
                        ${tagHtml}
                        <span>${formatHot(item.hot_value)}</span>
                    </div>
                </div>
                <button class="action-add" onclick="addWord('${escapeHtml(item.word)}')" title="添加到对比">
                    <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
                </button>
            </div>`;
        }).join('');
    }

    // Render New Items (Grid)
    if (newItems.length > 0) {
        els.newSection.style.display = 'block';
        els.newList.innerHTML = newItems.map(item => `
            <div class="new-item" draggable="true" data-word="${escapeHtml(item.word)}">
                <div class="new-title">${escapeHtml(item.word)}</div>
                <div style="display:flex; justify-content:space-between; align-items:end;">
                    <span class="new-tag">NEW ENTRY</span>
                    <!-- Add Button Overlay -->
                    <div class="new-add-btn" onclick="addWord('${escapeHtml(item.word)}')">
                        <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        els.newSection.style.display = 'none';
        els.newList.innerHTML = '';
    }

    attachDragEvents();
}

function attachDragEvents() {
    // Select both hot items and new items
    const allDraggables = document.querySelectorAll('.hot-item, .new-item');
    allDraggables.forEach(item => {
        // Drag events
        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', item.dataset.word);
            item.classList.add('dragging');
        });
        item.addEventListener('dragend', () => {
            item.classList.remove('dragging');
        });

        // Click to quick preview (single word)
        item.addEventListener('click', (e) => {
            // Ignore if clicking on the action button
            if (e.target.closest('.action-add') || e.target.closest('.new-add-btn')) return;

            const word = item.dataset.word;
            if (word) {
                quickPreview(word);
            }
        });
    });
}

// Quick preview: Clear workspace and show single word trend
async function quickPreview(word) {
    compareWords = [word];
    renderTags();
    showToast(`正在查看: ${word}`, 'info');
    await updateChart();
}

function renderRising(list) {
    els.risingList.innerHTML = list.slice(0, 20).map(item => `
        <div class="rising-item">
            <span style="display:flex; gap:8px; align-items:center;">
                <span style="width:16px; height:16px; background:rgba(255,255,255,0.1); border-radius:4px; font-size:10px; display:flex; align-items:center; justify-content:center;">${item.rank_change > 10 ? '🚀' : '⚡'}</span>
                ${escapeHtml(item.word)}
            </span>
            <span class="trend-up">↑${item.rank_change}</span>
        </div>
    `).join('');
}

// ==========================================
// Workspace / Comparision Logic
// ==========================================

async function addWord(word) {
    if (!word) return;
    word = word.trim();
    if (compareWords.includes(word)) {
        showToast(`"${word}" 已经在列表中`, 'warning');
        return;
    }
    if (compareWords.length >= 5) {
        showToast('最多对比 5 个热词', 'warning');
        return;
    }

    compareWords.push(word);
    renderTags();
    await updateChart();
}

function removeWord(word) {
    compareWords = compareWords.filter(w => w !== word);
    renderTags();
    if (compareWords.length === 0) {
        if (mainChart) mainChart.clear();
        const placeholder = document.querySelector('.drop-placeholder');
        if (placeholder) placeholder.style.display = 'flex';
    } else {
        updateChart();
    }
}

function renderTags() {
    els.activeTags.innerHTML = compareWords.map(word => `
        <span class="compare-tag">
            ${escapeHtml(word)}
            <span class="remove-btn" onclick="removeWord('${escapeHtml(word)}')">&times;</span>
        </span>
    `).join('');

    // Toggle Placeholder
    const placeholder = document.querySelector('.drop-placeholder');
    if (placeholder) {
        placeholder.style.display = compareWords.length > 0 ? 'none' : 'flex';
    }
}

async function updateChart() {
    if (compareWords.length === 0) return;

    // Fetch data for all words
    const seriesData = [];
    const allDates = new Set();
    const dataMap = {};

    showToast('正在加载趋势数据...', 'system');

    for (const word of compareWords) {
        try {
            let data = [];
            const r1 = await fetch(`${API_BASE}/api/trend/${encodeURIComponent(word)}?hours=${selectedHours}`);
            const j1 = await r1.json();

            if (j1.success && j1.trend.length > 0) {
                data = j1.trend;
            } else {
                // 将小时转换为天数（至少1天）
                const days = Math.max(1, Math.ceil(selectedHours / 24));
                const r2 = await fetch(`${API_BASE}/api/history/${encodeURIComponent(word)}?days=${days}`);
                const j2 = await r2.json();
                if (j2.success) data = j2.history;
            }

            // 前端过滤：确保只显示选定时间范围内的数据
            const cutoffTime = Date.now() - (selectedHours * 60 * 60 * 1000);
            data = data.filter(d => {
                const itemTime = new Date(d.time || d.timestamp).getTime();
                return itemTime >= cutoffTime;
            });

            if (data.length > 0) {
                dataMap[word] = data;
                data.forEach(d => allDates.add(new Date(d.time || d.timestamp).getTime()));
            }
        } catch (e) {
            console.error(e);
        }
    }

    compareWords.forEach((word, idx) => {
        const rawData = dataMap[word] || [];

        // 使用 [timestamp, value] 格式，适配 time 类型 xAxis
        const plotData = rawData.map(d => {
            const timestamp = new Date(d.time || d.timestamp).getTime();
            return [timestamp, d.hot_value];
        });

        seriesData.push({
            name: word,
            type: 'line',
            data: plotData,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { width: 3, shadowBlur: 10, shadowColor: PALETTE[idx % PALETTE.length] },
            itemStyle: { color: PALETTE[idx % PALETTE.length] },
            connectNulls: true
        });
    });

    renderEChart(seriesData);
}

function renderEChart(series) {
    if (!mainChart) mainChart = echarts.init(els.mainChart);

    // 清除旧图表状态
    mainChart.clear();

    // 从数据中计算实际时间范围
    let dataMinTime = Infinity;
    let dataMaxTime = -Infinity;
    series.forEach(s => {
        s.data.forEach(d => {
            if (d[0] < dataMinTime) dataMinTime = d[0];
            if (d[0] > dataMaxTime) dataMaxTime = d[0];
        });
    });

    // 如果没有数据，使用默认范围
    if (dataMinTime === Infinity) {
        const now = Date.now();
        dataMinTime = now - (selectedHours * 60 * 60 * 1000);
        dataMaxTime = now;
    }

    // 计算时间跨度（小时）
    const timeSpanHours = (dataMaxTime - dataMinTime) / (1000 * 60 * 60);

    const option = {
        backgroundColor: 'transparent',
        grid: { top: 30, right: 20, bottom: 60, left: 10, containLabel: true },
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(24, 24, 27, 0.9)',
            borderColor: '#3f3f46',
            textStyle: { color: '#fafafa' },
            formatter: function (params) {
                if (!params || params.length === 0) return '';
                const time = new Date(params[0].value[0]);
                const timeStr = `${time.getMonth() + 1}/${time.getDate()} ${time.getHours()}:${String(time.getMinutes()).padStart(2, '0')}`;
                let html = `<div style="font-weight:bold;margin-bottom:8px">${timeStr}</div>`;
                params.forEach(p => {
                    html += `<div style="display:flex;justify-content:space-between;gap:20px">
                        <span>${p.marker} ${p.seriesName}</span>
                        <span style="font-weight:bold">${compactNumber(p.value[1])}</span>
                    </div>`;
                });
                return html;
            }
        },
        legend: {
            data: series.map(s => s.name),
            textStyle: { color: '#a1a1aa' },
            icon: 'circle',
            top: 0
        },
        xAxis: {
            type: 'time',
            axisLine: { lineStyle: { color: '#3f3f46' } },
            axisLabel: {
                color: '#71717a',
                fontSize: 10,
                formatter: function (value) {
                    const d = new Date(value);
                    // 根据时间跨度决定显示格式
                    if (timeSpanHours > 24) {
                        // 超过一天显示日期+时间
                        return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
                    } else {
                        // 同一天只显示时间
                        return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
                    }
                }
            },
            axisTick: { show: false },
            splitLine: { show: false }
        },
        yAxis: {
            type: 'value',
            splitLine: { lineStyle: { color: '#27272a' } },
            axisLabel: { color: '#71717a', formatter: compactNumber }
        },
        series: series,
        dataZoom: [
            {
                type: 'inside',
                start: 0,
                end: 100,
                zoomLock: true,
                moveOnMouseMove: true,
                moveOnMouseWheel: true
            },
            {
                type: 'slider',
                show: true,
                height: 20,
                bottom: 10,
                start: 0,
                end: 100,
                zoomLock: true,
                brushSelect: false,
                handleSize: '100%',
                handleStyle: { color: '#6366f1', borderColor: '#6366f1' },
                textStyle: { color: '#71717a' },
                borderColor: 'transparent',
                backgroundColor: '#18181b',
                fillerColor: 'rgba(99, 102, 241, 0.3)',
                labelFormatter: function (value) {
                    const d = new Date(value);
                    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
                }
            }
        ]
    };
    mainChart.setOption(option);
}

// Helpers
function updateStatusTime() {
    const now = new Date();
    els.updateTime.textContent = `最后更新: ${now.toLocaleTimeString()}`;
}

function applySettings(s) {
    currentSettings = s;
    if (els.settingInterval) els.settingInterval.value = s.scrape_interval_minutes || 10;
    if (els.settingRefresh) els.settingRefresh.value = s.auto_refresh_seconds || 60;
    if (els.settingHistory) els.settingHistory.value = s.max_history_days || 7;

    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(loadAllData, (s.auto_refresh_seconds || 60) * 1000);
}

async function saveSettings() {
    const config = {
        scrape_interval_minutes: parseInt(els.settingInterval.value),
        auto_refresh_seconds: parseInt(els.settingRefresh.value),
        max_history_days: parseInt(els.settingHistory.value)
    };

    try {
        await fetch(`${API_BASE}/api/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        showToast('设置已保存', 'success');
        applySettings(config);
    } catch (e) {
        showToast('保存失败', 'error');
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatHot(num) {
    if (!num) return '0';
    if (num > 100000000) return (num / 100000000).toFixed(1) + '亿';
    if (num > 10000) return (num / 10000).toFixed(1) + '万';
    return num;
}

function compactNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(0) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(0) + 'k';
    return num;
}

function formatDate(ts) {
    const d = new Date(ts);
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
}

function showToast(msg, type = 'info') {
    const t = document.createElement('div');
    t.className = 'toast';
    let icon = '';
    if (type === 'success') icon = '<svg width="16" height="16" fill="none" stroke="#10b981" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>';
    else if (type === 'error') icon = '<svg width="16" height="16" fill="none" stroke="#ef4444" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>';

    t.innerHTML = `${icon}<span>${msg}</span>`;
    document.getElementById('toastContainer').appendChild(t);
    setTimeout(() => {
        t.style.opacity = '0';
        t.style.transform = 'translateY(20px)';
        setTimeout(() => t.remove(), 300);
    }, 3000);
}

document.addEventListener('DOMContentLoaded', init);
