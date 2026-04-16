// main.js – Intelligent Mess Management System
// Features: Dark mode, Toast, Notifications, Pagination, Search, Charts

const API_BASE = '/api';

// ── Dark Mode ────────────────────────────────────────────────
function initDarkMode() {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    const btn = document.getElementById('darkToggleBtn');
    if (btn) btn.textContent = saved === 'dark' ? '☀ Light' : '🌙 Dark';
}
function toggleDarkMode() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    const btn = document.getElementById('darkToggleBtn');
    if (btn) btn.textContent = next === 'dark' ? '☀ Light' : '🌙 Dark';
}

// ── Toast System ─────────────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span><span class="toast-close" onclick="this.parentElement.remove()">✕</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}
// Backward-compatible alias
function showAlert(message, type) { showToast(message, type); }

// ── Confirm Dialog ───────────────────────────────────────────
function confirmAction(message, callback) {
    let overlay = document.getElementById('confirm-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'confirm-overlay';
        overlay.innerHTML = `
            <div id="confirm-box">
                <p id="confirm-msg"></p>
                <div class="form-actions">
                    <button class="btn-danger" id="confirm-yes">Confirm</button>
                    <button class="btn-secondary" id="confirm-no">Cancel</button>
                </div>
            </div>`;
        document.body.appendChild(overlay);
        document.getElementById('confirm-no').onclick = () => overlay.classList.remove('open');
    }
    document.getElementById('confirm-msg').textContent = message;
    overlay.classList.add('open');
    document.getElementById('confirm-yes').onclick = () => {
        overlay.classList.remove('open');
        callback();
    };
}

// ── Skeleton Loading ─────────────────────────────────────────
function showSkeletonCards(containerId, count = 4) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = Array.from({length: count}).map(() =>
        `<div class="skeleton skeleton-card"></div>`).join('');
}
function showSkeletonRows(tbodyId, cols = 4, rows = 5) {
    const el = document.getElementById(tbodyId);
    if (!el) return;
    el.innerHTML = Array.from({length: rows}).map(() =>
        `<tr>${Array.from({length: cols}).map(() =>
            `<td><div class="skeleton skeleton-text" style="width:${60+Math.random()*30}%"></div></td>`
        ).join('')}</tr>`).join('');
}

// ── Table Search ─────────────────────────────────────────────
function addTableSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    if (!input || !table) return;
    input.addEventListener('input', () => {
        const q = input.value.toLowerCase();
        Array.from(table.querySelectorAll('tbody tr')).forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });
}

// ── Pagination ───────────────────────────────────────────────
function addPagination(tableId, pageSize = 10) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const allRows = () => Array.from(table.querySelectorAll('tbody tr:not(.pagination-skip)'));
    let currentPage = 1;

    function render() {
        const rows = allRows();
        const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
        rows.forEach((r, i) => {
            r.style.display = (i >= (currentPage-1)*pageSize && i < currentPage*pageSize) ? '' : 'none';
        });
        // Update or create pagination
        let pg = document.getElementById(tableId + '-pagination');
        if (!pg) {
            pg = document.createElement('div');
            pg.id = tableId + '-pagination';
            pg.className = 'pagination';
            table.parentNode.insertBefore(pg, table.nextSibling);
        }
        if (totalPages <= 1) { pg.innerHTML = ''; return; }
        pg.innerHTML = '';
        const mkBtn = (label, page) => {
            const b = document.createElement('button');
            b.textContent = label;
            if (page === currentPage) b.classList.add('active');
            b.onclick = () => { currentPage = page; render(); };
            pg.appendChild(b);
        };
        if (currentPage > 1) mkBtn('«', currentPage - 1);
        for (let p = 1; p <= totalPages; p++) mkBtn(p, p);
        if (currentPage < totalPages) mkBtn('»', currentPage + 1);
    }
    render();
    // Re-paginate after search filters
    const searchInput = document.getElementById(tableId.replace('Table', '') + 'SearchInput') ||
                        document.querySelector(`[data-search-for="${tableId}"]`);
    if (searchInput) {
        searchInput.addEventListener('input', () => { currentPage = 1; render(); });
    }
}

// ── Notification Bell ────────────────────────────────────────
let notifPollInterval = null;

async function setupNotificationBell() {
    const bell = document.getElementById('notifBtn');
    const badge = document.getElementById('notifBadge');
    const dropdown = document.getElementById('notifDropdown');
    if (!bell) return;

    bell.addEventListener('click', async (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
        if (dropdown.classList.contains('open')) await renderNotifications();
    });
    document.addEventListener('click', () => dropdown.classList.remove('open'));

    async function fetchUnread() {
        try {
            const r = await fetch(`${API_BASE}/notifications`, {credentials: 'include'});
            if (!r.ok) return;
            const data = await r.json();
            const count = data.unread_count || 0;
            if (badge) {
                badge.style.display = count > 0 ? 'flex' : 'none';
                badge.textContent = count > 9 ? '9+' : count;
            }
        } catch {}
    }

    async function renderNotifications() {
        const list = document.getElementById('notifList');
        if (!list) return;
        list.innerHTML = '<div class="notif-empty">Loading…</div>';
        const r = await fetch(`${API_BASE}/notifications`, {credentials: 'include'});
        const data = await r.json();
        const items = data.notifications || [];
        if (!items.length) { list.innerHTML = '<div class="notif-empty">No notifications</div>'; return; }
        list.innerHTML = items.map(n => `
            <div class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}" onclick="markNotifRead(${n.id}, this)">
                <div>${n.message}</div>
                <div class="notif-time">${new Date(n.created_at).toLocaleString()}</div>
            </div>`).join('');
    }

    fetchUnread();
    notifPollInterval = setInterval(fetchUnread, 30000);
}

async function markNotifRead(id, el) {
    await fetch(`${API_BASE}/notifications/${id}/read`, {method:'PUT', credentials:'include'});
    if (el) el.classList.remove('unread');
}

async function markAllRead() {
    await fetch(`${API_BASE}/notifications/read_all`, {method:'PUT', credentials:'include'});
    document.querySelectorAll('.notif-item.unread').forEach(el => el.classList.remove('unread'));
    const badge = document.getElementById('notifBadge');
    if (badge) badge.style.display = 'none';
}

// ── Auth Check ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async function () {
    initDarkMode();

    const darkBtn = document.getElementById('darkToggleBtn');
    if (darkBtn) darkBtn.addEventListener('click', toggleDarkMode);

    const pathname = window.location.pathname;
    if (pathname === '/' || pathname.includes('index.html') || pathname.includes('signup.html')) {
        setupAuthForms();
        return;
    }

    try {
        const resp = await fetch(`${API_BASE}/current_user`, {credentials: 'include'});
        if (!resp.ok) { window.location.href = 'index.html'; return; }
        const user = await resp.json();
        setupNavigation(user.role);
        setupNotificationBell();
        loadPageContent(user);
    } catch (e) {
        window.location.href = 'index.html';
    }
});

// ── Auth Forms ───────────────────────────────────────────────
function setupAuthForms() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const [un, pw] = loginForm.querySelectorAll('input');
            const btn = loginForm.querySelector('button[type="submit"]');
            btn.textContent = 'Logging in…';
            btn.disabled = true;
            try {
                const r = await fetch(`${API_BASE}/login`, {
                    method: 'POST', credentials: 'include',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({username: un.value, password: pw.value})
                });
                const res = await r.json();
                if (res.success) {
                    window.location.href = 'dashboard.html';
                } else {
                    const err = document.getElementById('loginError');
                    if (err) { err.textContent = res.message || 'Invalid credentials'; err.style.display = 'block'; }
                    else showToast(res.message || 'Invalid credentials', 'danger');
                }
            } catch { showToast('Connection error', 'danger'); }
            btn.textContent = 'Login'; btn.disabled = false;
        });
    }

    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const d = Object.fromEntries(new FormData(signupForm));
            const r = await fetch(`${API_BASE}/signup`, {
                method: 'POST', credentials: 'include',
                headers: {'Content-Type':'application/json'}, body: JSON.stringify(d)
            });
            const res = await r.json();
            if (res.success) { showToast('Registered! Please login.', 'success'); setTimeout(() => window.location.href = 'index.html', 2000); }
            else showToast(res.message || 'Signup failed', 'danger');
        });
    }
}

// ── Navigation ───────────────────────────────────────────────
function setupNavigation(role) {
    const page = window.location.pathname.split('/').pop() || 'dashboard.html';
    document.querySelectorAll('nav a').forEach(a => {
        const href = a.getAttribute('href') || '';
        if (href === page || href === page.replace(/.*\//, '')) a.classList.add('active');
    });

    // Hide admin-only nav items from students
    if (role === 'student') {
        ['nav-inventory','nav-users','nav-settings'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        // Redirect students away from admin-only pages
        const adminPages = ['inventory.html','users.html','settings.html'];
        if (adminPages.includes(page)) {
            showToast('Access restricted to admins only.', 'warning');
            setTimeout(() => window.location.href = 'dashboard.html', 1500);
            return;
        }
    }

    // Hide admin-only buttons for students
    document.querySelectorAll('#addMealBtn,#addItemBtn').forEach(b => {
        if (b) b.style.display = role === 'admin' ? 'inline-flex' : 'none';
    });

    // Logout link
    const logoutLink = document.getElementById('logoutLink');
    if (logoutLink) {
        logoutLink.addEventListener('click', async (e) => {
            e.preventDefault();
            await fetch('/api/logout', {method:'POST', credentials:'include'});
            window.location.href = 'index.html';
        });
    }
}

// ── Page Router ──────────────────────────────────────────────
function loadPageContent(user) {
    const page = window.location.pathname.split('/').pop() || 'dashboard.html';
    switch (page) {
        case 'dashboard.html':  loadDashboard(user); break;
        case 'meals.html':      loadMeals(user); break;
        case 'billing.html':    loadBilling(user); break;
        case 'attendance.html': loadAttendance(user); break;
        case 'inventory.html':  loadInventory(user); break;
        case 'feedback.html':   loadFeedback(); break;
        case 'users.html':      loadUsers(); break;
        case 'reports.html':    loadReports(); break;
        case 'settings.html':   loadSettings(); break;
        case 'profile.html':    loadProfile(); break;
    }
}

// ── Dashboard ────────────────────────────────────────────────
async function loadDashboard(user) {
    showSkeletonCards('statsContainer', 5);
    try {
        const [dash, announcements] = await Promise.all([
            fetch(`${API_BASE}/analytics/dashboard`, {credentials:'include'}).then(r => r.json()),
            fetch(`${API_BASE}/announcements`, {credentials:'include'}).then(r => r.json())
        ]);

        const sc = document.getElementById('statsContainer');
        if (sc) {
            if (dash.role === 'admin') {
                sc.innerHTML = `
                    <div class="stat-card"><div class="stat-title">Total Students</div><div class="stat-value">${dash.total_students||0}</div></div>
                    <div class="stat-card"><div class="stat-title">Today's Bookings</div><div class="stat-value">${dash.today_bookings||0}</div></div>
                    <div class="stat-card"><div class="stat-title">Pending Payments</div><div class="stat-value">${dash.pending_payments||0}</div></div>
                    <div class="stat-card"><div class="stat-title">Low Stock Items</div><div class="stat-value">${dash.low_stock_items||0}</div></div>
                    <div class="stat-card"><div class="stat-title">Recent Feedback</div><div class="stat-value">${dash.recent_feedback||0}</div></div>`;
            } else {
                sc.innerHTML = `
                    <div class="stat-card"><div class="stat-title">Today's Bookings</div><div class="stat-value">${dash.today_bookings||0}</div></div>
                    <div class="stat-card"><div class="stat-title">Upcoming Meals</div><div class="stat-value">${dash.upcoming_meals||0}</div></div>
                    <div class="stat-card"><div class="stat-title">Pending Bills</div><div class="stat-value">${dash.pending_bills||0}</div></div>
                    <div class="stat-card"><div class="stat-title">Total Spent</div><div class="stat-value">₹${(dash.total_spent||0).toFixed(0)}</div></div>
                    <div class="stat-card"><div class="stat-title">Attendance (7d)</div><div class="stat-value">${dash.recent_attendance||0}</div></div>`;
            }
        }

        // Announcements board
        const annBox = document.getElementById('announcementsContainer');
        if (annBox && announcements.length) {
            annBox.innerHTML = announcements.slice(0,5).map(a => `
                <div class="announcement-item priority-${a.priority}">
                    <h4>📢 ${a.title}</h4>
                    <div>${a.message}</div>
                    <div class="ann-meta">By ${a.author_name} · ${new Date(a.created_at).toLocaleDateString()}</div>
                </div>`).join('');
        }

        // Charts
        if (dash.role === 'admin') {
            await loadRevenueChart();
        } else {
            await loadRecentBookings();
            await loadTodayMeals();
        }
    } catch (e) {
        const sc = document.getElementById('statsContainer');
        if (sc) sc.innerHTML = '<div class="alert alert-danger">Failed to load dashboard data</div>';
    }
}

async function loadRevenueChart() {
    const ctx = document.getElementById('revenueChart');
    if (!ctx || !window.Chart) return;
    const data = await fetch(`${API_BASE}/reports/revenue`, {credentials:'include'}).then(r=>r.json());
    const labels = data.map(d => d.month).reverse();
    const billed = data.map(d => d.total_billed).reverse();
    const collected = data.map(d => d.collected).reverse();
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { label: 'Billed (₹)', data: billed, backgroundColor: 'rgba(32,102,172,0.7)', borderRadius: 6 },
                { label: 'Collected (₹)', data: collected, backgroundColor: 'rgba(25,135,84,0.7)', borderRadius: 6 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } } }
    });
}

async function loadRecentBookings() {
    try {
        const r = await fetch(`${API_BASE}/bookings`, {credentials:'include'});
        const bookings = await r.json();
        let el = document.getElementById('recentBookings');
        if (!el) {
            const c = document.querySelector('.container');
            if (!c) return;
            const sec = document.createElement('div'); sec.className = 'card';
            sec.innerHTML = '<h3>Recent Bookings</h3><div id="recentBookings"></div>';
            c.appendChild(sec); el = document.getElementById('recentBookings');
        }
        const recent = bookings.slice(0, 5);
        el.innerHTML = recent.length ? `
            <div class="table-wrapper"><table>
                <thead><tr><th>Date</th><th>Meal</th><th>Menu</th><th>Status</th></tr></thead>
                <tbody>${recent.map(b => `<tr>
                    <td>${b.date}</td>
                    <td>${b.meal_type ? b.meal_type.charAt(0).toUpperCase()+b.meal_type.slice(1) : '—'}</td>
                    <td>${b.menu_items||'—'}</td>
                    <td><span class="badge badge-${b.status==='completed'?'success':b.status==='booked'?'info':'warning'}">${b.status}</span></td>
                </tr>`).join('')}</tbody>
            </table></div>` : '<p class="text-muted">No bookings yet.</p>';
    } catch {}
}

async function loadTodayMeals() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const meals = await fetch(`${API_BASE}/meals?date=${today}`, {credentials:'include'}).then(r=>r.json());
        let el = document.getElementById('todayMeals');
        if (!el) {
            const c = document.querySelector('.container'); if (!c) return;
            const sec = document.createElement('div'); sec.className = 'card'; sec.style.marginTop='1rem';
            sec.innerHTML = '<h3>Today\'s Menu</h3><div id="todayMeals"></div>';
            c.appendChild(sec); el = document.getElementById('todayMeals');
        }
        el.innerHTML = meals.length ? `<div style="display:grid;gap:.8rem;margin-top:.8rem">
            ${meals.map(m => `<div style="padding:.9rem;border:1px solid var(--border-color);border-radius:var(--radius-md);background:var(--bg-surface)">
                <h4 style="color:var(--brand-main);margin-bottom:.4rem">${m.meal_type.charAt(0).toUpperCase()+m.meal_type.slice(1)}
                ${m.meal_tag==='veg'?'<span class="badge badge-success">🟢 Veg</span>':'<span class="badge badge-danger">🔴 Non-veg</span>'}</h4>
                <p><strong>Menu:</strong> ${m.menu_items}</p>
                <p><strong>Price:</strong> ₹${m.price}</p>
                <button class="btn-sm" onclick="bookMeal(${m.id})">Book</button>
            </div>`).join('')}</div>` : '<p class="text-muted">No meals scheduled today.</p>';
    } catch {}
}

// ── Meals ────────────────────────────────────────────────────
let allMeals = [];

async function loadMeals(user) {
    const tbody = document.getElementById('mealsTableBody');
    if (tbody) showSkeletonRows('mealsTableBody', 5, 4);

    const addBtn = document.getElementById('addMealBtn');
    if (addBtn) addBtn.addEventListener('click', () => showMealModal());

    const today = new Date().toISOString().split('T')[0];
    const meals = await fetch(`${API_BASE}/meals`, {credentials:'include'}).then(r=>r.json());
    allMeals = meals;
    renderMealsTable(meals);
    addTableSearch('mealSearchInput', 'mealsTable');
    addPagination('mealsTable', 10);
}

function renderMealsTable(meals) {
    const tbody = document.getElementById('mealsTableBody');
    if (!tbody) return;
    if (!meals.length) { tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:2rem">No meals found.</td></tr>'; return; }
    tbody.innerHTML = meals.map(m => `<tr>
        <td>${m.date}</td>
        <td>${m.meal_type ? m.meal_type.charAt(0).toUpperCase()+m.meal_type.slice(1) : '—'}</td>
        <td>${m.menu_items}</td>
        <td>₹${m.price}</td>
        <td>${m.meal_tag==='veg'?'<span class="badge badge-success">🟢 Veg</span>':'<span class="badge badge-danger">🔴 Non-veg</span>'}</td>
        <td>
            <button class="btn-sm" onclick="bookMeal(${m.id})">Book</button>
            <button class="btn-sm btn-secondary" onclick="rateMeal(${m.id})">Rate</button>
        </td>
    </tr>`).join('');
}

function filterMealsByDiet(pref) {
    document.querySelectorAll('.diet-tag').forEach(t => t.classList.remove('active'));
    const tag = document.getElementById('diet_' + pref);
    if (tag) tag.classList.add('active');
    const filtered = pref === 'all' ? allMeals : allMeals.filter(m =>
        pref === 'veg' ? m.meal_tag === 'veg' : m.meal_tag !== 'veg');
    renderMealsTable(filtered);
}

async function bookMeal(mealId) {
    const r = await fetch(`${API_BASE}/bookings`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify({meal_id: mealId})
    });
    const res = await r.json();
    showToast(res.message || (res.success ? 'Booked!' : 'Failed'), res.success ? 'success' : 'danger');
    if (res.success) loadMeals();
}

function rateMeal(mealId) {
    const modal = document.getElementById('ratingModal');
    if (!modal) {
        const m = document.createElement('div'); m.className = 'modal'; m.id = 'ratingModal';
        m.innerHTML = `<div class="modal-content">
            <span class="close" onclick="document.getElementById('ratingModal').style.display='none'">✕</span>
            <h3>Rate this Meal</h3>
            <div class="star-rating" id="starRating">
                ${[1,2,3,4,5].map(i=>`<span data-val="${i}" onclick="selectStar(${i})">★</span>`).join('')}
            </div>
            <input type="hidden" id="selectedRating" value="0"/>
            <br><button onclick="submitMealRating(${mealId})">Submit Rating</button>
        </div>`;
        document.body.appendChild(m);
    }
    document.getElementById('ratingModal').style.display = 'block';
    document.getElementById('selectedRating').value = 0;
    document.querySelectorAll('#starRating span').forEach(s=>s.classList.remove('active'));
    document.getElementById('ratingModal').setAttribute('data-meal', mealId);
}

function selectStar(val) {
    document.getElementById('selectedRating').value = val;
    document.querySelectorAll('#starRating span').forEach(s => {
        s.classList.toggle('active', parseInt(s.dataset.val) <= val);
    });
}

async function submitMealRating(mealId) {
    const rating = parseInt(document.getElementById('selectedRating').value);
    if (!rating) { showToast('Please select a rating', 'warning'); return; }
    const r = await fetch(`${API_BASE}/meals/${mealId}/rate`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify({rating})
    });
    const res = await r.json();
    showToast(res.message, res.success ? 'success' : 'danger');
    document.getElementById('ratingModal').style.display = 'none';
}

// ── Billing ──────────────────────────────────────────────────
async function loadBilling(user) {
    const tbody = document.getElementById('billingTableBody');
    if (tbody) showSkeletonRows('billingTableBody', 5, 4);
    const bills = await fetch(`${API_BASE}/billing`, {credentials:'include'}).then(r=>r.json());
    if (tbody) {
        tbody.innerHTML = bills.map(b => `<tr>
            <td>${b.user_name||'—'}</td>
            <td>${b.month}</td>
            <td style="font-weight:600">₹${parseFloat(b.total_amount).toFixed(2)}</td>
            <td><span class="badge badge-${b.payment_status==='Paid'?'success':b.payment_status==='Overdue'?'danger':'warning'}">${b.payment_status}</span></td>
            <td style="display:flex;gap:6px;flex-wrap:wrap">
                <a href="${API_BASE}/billing/${b.id}/pdf" target="_blank">
                    <button class="btn-sm btn-secondary">📄 PDF</button></a>
                ${b.payment_status!=='Paid' ? `<button class="btn-sm btn-success" onclick="initiatePayment(${b.id},${b.total_amount})">💳 Pay</button>` : ''}
                ${user && user.role==='admin' ? `<button class="btn-sm" onclick="openEditBill(${b.id},${b.total_amount},'${b.payment_status}','${b.payment_date||''}')" style="background:linear-gradient(135deg,#f59e0b,#d97706)">✏️ Edit</button>
                <button class="btn-sm btn-danger" onclick="deleteBillRow(${b.id})">🗑</button>` : ''}
            </td>
        </tr>`).join('');
    }
    addTableSearch('billingSearchInput', 'billingTable');
    addPagination('billingTable', 10);
    const genPanel = document.getElementById('generateBillsPanel');
    if (genPanel && user && user.role === 'admin') genPanel.style.display = 'block';
}

function openEditBill(id, amount, status, date) {
    document.getElementById('editBillId').value = id;
    document.getElementById('editBillAmount').value = amount;
    document.getElementById('editBillStatus').value = status;
    document.getElementById('editBillDate').value = date;
    document.getElementById('editBillModal').style.display = 'block';
}

async function submitEditBill() {
    const id = document.getElementById('editBillId').value;
    const r = await fetch(`${API_BASE}/billing/${id}`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
            total_amount: document.getElementById('editBillAmount').value,
            payment_status: document.getElementById('editBillStatus').value,
            payment_date: document.getElementById('editBillDate').value
        })
    });
    const res = await r.json();
    showToast(res.message, res.success?'success':'danger');
    if (res.success) { document.getElementById('editBillModal').style.display='none'; loadBilling(); }
}

async function deleteBillRow(id) {
    confirmAction('Delete this bill record permanently?', async () => {
        const r = await fetch(`${API_BASE}/billing/${id}`, {method:'DELETE', credentials:'include'});
        const res = await r.json();
        showToast(res.message, res.success?'success':'danger');
        if (res.success) loadBilling();
    });
}

async function generateMonthlyBills() {
    const month = document.getElementById('billMonth').value;
    if (!month) { showToast('Enter month (e.g. March 2026)', 'warning'); return; }
    const r = await fetch(`${API_BASE}/billing/generate_monthly`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify({month})
    });
    const res = await r.json();
    showToast(res.message, res.success ? 'success' : 'danger');
    if (res.success) loadBilling();
}

async function initiatePayment(billId, amount) {
    const r = await fetch(`${API_BASE}/payment/create_order`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify({bill_id: billId, amount})
    });
    const res = await r.json();
    if (res.success && window.Razorpay) {
        new Razorpay({
            key: res.key, amount: res.amount, currency: 'INR', order_id: res.order_id,
            name: 'Mess Management', description: 'Meal Payment', theme: {color: '#2066ac'},
            handler: (resp) => verifyPayment(resp, billId)
        }).open();
    } else showToast('Payment not available', 'warning');
}

async function verifyPayment(response, billId) {
    const r = await fetch(`${API_BASE}/payment/verify`, {
        method:'POST', credentials:'include', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({...response, bill_id: billId})
    });
    const res = await r.json();
    showToast(res.success ? 'Payment successful!' : 'Verification failed', res.success ? 'success' : 'danger');
    if (res.success) loadBilling();
}

// ── Attendance ───────────────────────────────────────────────
async function loadAttendance(user) {
    const tbody = document.getElementById('attendanceTableBody');
    if (tbody) showSkeletonRows('attendanceTableBody', 5, 4);
    const att = await fetch(`${API_BASE}/attendance`, {credentials:'include'}).then(r=>r.json());
    if (tbody) {
        tbody.innerHTML = att.map(a => `<tr>
            <td>${a.user_name||'—'}</td>
            <td>${a.date}</td>
            <td>${a.meal_type ? a.meal_type.charAt(0).toUpperCase()+a.meal_type.slice(1) : '—'}</td>
            <td><span class="badge badge-success">${a.attendance_status}</span></td>
            <td>${new Date(a.timestamp).toLocaleString()}</td>
        </tr>`).join('');
    }
    addTableSearch('attendanceSearchInput', 'attendanceTable');
    addPagination('attendanceTable', 10);
}

async function generateQRCode(mealId) {
    const r = await fetch(`${API_BASE}/attendance/qr/${mealId}`, {credentials:'include'});
    const res = await r.json();
    if (res.success) {
        const img = document.getElementById('qrCodeImg');
        if (img) img.src = res.qr_code;
        const m = document.getElementById('qrModal');
        if (m) m.style.display = 'block';
    }
}

async function markAttendance(mealId) {
    const r = await fetch(`${API_BASE}/attendance`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify({meal_id: mealId})
    });
    const res = await r.json();
    showToast(res.message, res.success ? 'success' : 'danger');
    if (res.success) loadAttendance();
}

// ── Inventory ────────────────────────────────────────────────
async function loadInventory(user) {
    const tbody = document.getElementById('inventoryTableBody');
    if (tbody) showSkeletonRows('inventoryTableBody', 7, 5);
    const items = await fetch(`${API_BASE}/inventory`, {credentials:'include'}).then(r=>r.json());
    if (tbody) {
        tbody.innerHTML = items.map(item => `<tr class="${item.low_stock?'table-danger':''}">
            <td>${item.item_name}</td>
            <td>${item.quantity} ${item.unit}</td>
            <td>${item.threshold} ${item.unit}</td>
            <td>${item.category}</td>
            <td>${item.last_updated}</td>
            <td>${item.low_stock ? '<span class="badge badge-danger">⚠ Low</span>' : '<span class="badge badge-success">OK</span>'}</td>
            <td>
                <button class="btn-sm btn-secondary" onclick="editInventory(${item.id})">Edit</button>
                <button class="btn-sm btn-danger" onclick="deductInventory(${item.id}, '${item.item_name}')">Deduct</button>
            </td>
        </tr>`).join('');
    }
    addTableSearch('inventorySearchInput', 'inventoryTable');
    addPagination('inventoryTable', 10);

    // Load suppliers section
    loadSuppliers();
}

async function deductInventory(itemId, name) {
    const amount = prompt(`Deduct how much from "${name}"?`);
    if (!amount || isNaN(amount)) return;
    const r = await fetch(`${API_BASE}/inventory/deduct`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify({item_id:itemId, amount:parseFloat(amount)})
    });
    const res = await r.json();
    showToast(res.message, res.success ? 'success' : 'danger');
    if (res.success) loadInventory();
}

async function loadSuppliers() {
    const cont = document.getElementById('suppliersContainer');
    if (!cont) return;
    const rows = await fetch(`${API_BASE}/suppliers`, {credentials:'include'}).then(r=>r.json());
    cont.innerHTML = `<h3>Suppliers</h3>
    <button onclick="showSupplierModal()" style="margin-bottom:.7rem">+ Add Supplier</button>
    <div class="table-wrapper"><table>
        <thead><tr><th>Name</th><th>Contact</th><th>Email</th><th>Category</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>${rows.map(s=>`<tr>
            <td>${s.name}</td><td>${s.contact||'—'}</td><td>${s.email||'—'}</td>
            <td>${s.category}</td>
            <td><span class="badge badge-${s.status==='active'?'success':'warning'}">${s.status}</span></td>
            <td><button class="btn-sm btn-danger" onclick="deleteSupplier(${s.id})">Delete</button></td>
        </tr>`).join('')}</tbody>
    </table></div>`;
}

function showSupplierModal() {
    const html = `<div class="modal" id="supplierModal" style="display:block">
        <div class="modal-content"><span class="close" onclick="this.closest('.modal').remove()">✕</span>
        <h3>Add Supplier</h3>
        <form id="supplierForm">
            <input name="name" placeholder="Supplier Name" required>
            <input name="contact" placeholder="Contact Number">
            <input name="email" type="email" placeholder="Email">
            <input name="address" placeholder="Address">
            <input name="category" placeholder="Category (e.g. grain, dairy)">
            <button type="submit">Save Supplier</button>
        </form></div></div>`;
    document.body.insertAdjacentHTML('beforeend', html);
    document.getElementById('supplierForm').addEventListener('submit', async e => {
        e.preventDefault();
        const d = Object.fromEntries(new FormData(e.target));
        const r = await fetch(`${API_BASE}/suppliers`, {method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
        const res = await r.json();
        showToast(res.message, res.success?'success':'danger');
        if (res.success) { document.getElementById('supplierModal').remove(); loadInventory(); }
    });
}

async function deleteSupplier(id) {
    confirmAction('Delete this supplier?', async () => {
        const r = await fetch(`${API_BASE}/suppliers/${id}`, {method:'DELETE', credentials:'include'});
        const res = await r.json();
        showToast(res.message, res.success?'success':'danger');
        if (res.success) loadInventory();
    });
}

// ── Feedback ─────────────────────────────────────────────────
async function loadFeedback() {
    const tbody = document.getElementById('feedbackTableBody');
    const form = document.getElementById('feedbackForm');
    if (form) {
        form.addEventListener('submit', async e => {
            e.preventDefault();
            const d = Object.fromEntries(new FormData(e.target));
            const r = await fetch(`${API_BASE}/feedback`, {method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify(d)});
            const res = await r.json();
            showToast(res.message || (res.success ? 'Submitted!' : 'Failed'), res.success ? 'success' : 'danger');
            if (res.success) { form.reset(); loadFeedback(); }
        });
    }
    if (tbody) showSkeletonRows('feedbackTableBody', 4, 4);
    const fb = await fetch(`${API_BASE}/feedback`, {credentials:'include'}).then(r=>r.json());
    if (tbody) {
        tbody.innerHTML = fb.map(f => `<tr>
            <td>${f.user_name||'—'}</td>
            <td>${f.message}</td>
            <td>${'⭐'.repeat(f.rating)}</td>
            <td>${new Date(f.created_at).toLocaleDateString()}</td>
        </tr>`).join('');
    }
    addTableSearch('feedbackSearchInput', 'feedbackTable');
    addPagination('feedbackTable', 10);
}

// ── Users ────────────────────────────────────────────────────
async function loadUsers() {
    const tbody = document.getElementById('usersTableBody');
    if (tbody) showSkeletonRows('usersTableBody', 5, 4);
    const users = await fetch(`${API_BASE}/users`, {credentials:'include'}).then(r=>r.json());
    if (tbody) {
        tbody.innerHTML = users.map(u => `<tr>
            <td>${u.name}</td>
            <td>${u.email}</td>
            <td>${u.roll_number||'—'}</td>
            <td><span class="badge badge-info">${u.role}</span></td>
            <td><span class="badge badge-${u.status==='active'?'success':'danger'}">${u.status}</span></td>
            <td>${new Date(u.created_at).toLocaleDateString()}</td>
        </tr>`).join('');
    }
    addTableSearch('usersSearchInput', 'usersTable');
    addPagination('usersTable', 10);
}

// ── Profile ──────────────────────────────────────────────────
async function loadProfile() {
    const profile = await fetch(`${API_BASE}/profile`, {credentials:'include'}).then(r=>r.json());
    ['name','email','roll_number','dietary_pref'].forEach(f => {
        const el = document.getElementById('profile_'+f);
        if (el) el.value = profile[f] || '';
    });
    const username = document.getElementById('profile_username');
    if (username) username.textContent = profile.username;

    const form = document.getElementById('profileForm');
    if (form) {
        form.addEventListener('submit', async e => {
            e.preventDefault();
            const d = Object.fromEntries(new FormData(e.target));
            const r = await fetch(`${API_BASE}/profile`, {method:'PUT', credentials:'include', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
            const res = await r.json();
            showToast(res.message, res.success?'success':'danger');
        });
    }
}

// ── Reports ──────────────────────────────────────────────────
async function loadReports() {
    const cont = document.getElementById('reportsContainer');
    if (!cont) return;

    // Attendance report
    const attData = await fetch(`${API_BASE}/reports/student_attendance`, {credentials:'include'}).then(r=>r.json()).catch(()=>[]);

    cont.innerHTML = `
    <div class="card">
        <h3>Student Attendance Report</h3>
        <div class="table-wrapper"><table id="attReportTable">
            <thead><tr><th>Name</th><th>Roll No.</th><th>Booked</th><th>Attended</th><th>Attendance %</th></tr></thead>
            <tbody>${attData.map(s=>`<tr>
                <td>${s.name}</td><td>${s.roll_number||'—'}</td>
                <td>${s.total_booked}</td><td>${s.attended}</td>
                <td><span class="badge badge-${s.attendance_pct>=75?'success':s.attendance_pct>=50?'warning':'danger'}">${s.attendance_pct}%</span></td>
            </tr>`).join('')}</tbody>
        </table></div>
    </div>
    <div class="card">
        <h3>Revenue Chart</h3>
        <div class="chart-wrapper"><canvas id="revenueChart2"></canvas></div>
    </div>
    <div class="card">
        <h3>Download Reports</h3>
        <div class="form-actions" style="flex-wrap:wrap">
            <button onclick="generateDailyReport()">📄 Daily Meal PDF</button>
            <button onclick="generatePaymentReport()">📊 Payment Excel</button>
            <button onclick="generateInventoryReport()">📦 Inventory Chart</button>
        </div>
        <h4 style="margin-top:1.2rem">Export CSV</h4>
        <div class="form-actions" style="flex-wrap:wrap">
            ${['meals','billing','attendance','inventory','feedback'].map(r=>
                `<a href="${API_BASE}/export/${r}" target="_blank"><button class="btn-secondary">⬇ ${r}</button></a>`
            ).join('')}
        </div>
    </div>
    <div class="card">
        <h3>ML Meal Prediction (Day-Aware)</h3>
        <button onclick="predictMealsV2()">🤖 Predict Tomorrow's Demand</button>
        <div id="predictionResult" style="margin-top:1rem"></div>
        <h4 style="margin-top:1.2rem">Menu Recommendations</h4>
        <button onclick="loadMenuRec()">⭐ Show Top Rated Menus</button>
        <div id="menuRecResult" style="margin-top:.8rem"></div>
    </div>`;

    setTimeout(() => loadRevenueChart2(), 200);
    addPagination('attReportTable', 10);
}

async function loadRevenueChart2() {
    const ctx = document.getElementById('revenueChart2');
    if (!ctx || !window.Chart) return;
    const data = await fetch(`${API_BASE}/reports/revenue`, {credentials:'include'}).then(r=>r.json());
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d=>d.month).reverse(),
            datasets: [
                { label: 'Billed (₹)', data: data.map(d=>d.total_billed).reverse(), borderColor:'#2066ac', backgroundColor:'rgba(32,102,172,0.1)', fill:true, tension:0.4 },
                { label: 'Collected (₹)', data: data.map(d=>d.collected).reverse(), borderColor:'#198754', backgroundColor:'rgba(25,135,84,0.08)', fill:true, tension:0.4 }
            ]
        },
        options: { responsive:true, maintainAspectRatio:false }
    });
}

async function predictMealsV2() {
    const cont = document.getElementById('predictionResult');
    cont.innerHTML = '<div class="skeleton skeleton-text" style="width:60%"></div>';
    const r = await fetch(`${API_BASE}/ml/predict_meals_v2`, {credentials:'include'});
    const res = await r.json();
    if (res.success) {
        cont.innerHTML = `<div class="alert alert-info">
            <strong>${res.weekday} (${res.date}):</strong> Predicted ~<strong>${res.prediction}</strong> meals
            | Model R²: ${res.model_score}
        </div>`;
    } else {
        cont.innerHTML = `<div class="alert alert-warning">${res.message||res.prediction}</div>`;
    }
}

async function loadMenuRec() {
    const cont = document.getElementById('menuRecResult');
    const data = await fetch(`${API_BASE}/ml/menu_recommendation`, {credentials:'include'}).then(r=>r.json());
    cont.innerHTML = data.length ? `<div class="table-wrapper"><table>
        <thead><tr><th>Menu</th><th>Type</th><th>Avg Rating</th><th>Votes</th></tr></thead>
        <tbody>${data.map(d=>`<tr>
            <td>${d.menu_items}</td><td>${d.meal_type}</td>
            <td>${'⭐'.repeat(Math.round(d.avg_rating))} (${d.avg_rating})</td>
            <td>${d.votes}</td>
        </tr>`).join('')}</tbody>
    </table></div>` : '<p class="text-muted">No rating data yet.</p>';
}

function generateDailyReport() {
    const s = prompt('Start date (YYYY-MM-DD):', new Date(Date.now()-7*86400000).toISOString().split('T')[0]);
    const e = prompt('End date (YYYY-MM-DD):', new Date().toISOString().split('T')[0]);
    if (s && e) window.open(`${API_BASE}/reports/daily_meal_count?start_date=${s}&end_date=${e}`, '_blank');
}
function generatePaymentReport() {
    const m = document.getElementById('paymentMonth');
    window.open(`${API_BASE}/reports/payment_report${m&&m.value ? '?month='+encodeURIComponent(m.value) : ''}`, '_blank');
}
function generateInventoryReport() { window.open(`${API_BASE}/reports/inventory_usage`, '_blank'); }

// ── Settings ─────────────────────────────────────────────────
async function loadSettings() {
    const settings = await fetch(`${API_BASE}/settings`, {credentials:'include'}).then(r=>r.json());
    Object.entries(settings).forEach(([k,v]) => {
        const el = document.getElementById('setting_'+k);
        if (el) el.value = v;
    });

    const form = document.getElementById('settingsForm');
    if (form) {
        form.addEventListener('submit', async e => {
            e.preventDefault();
            const updates = [...form.querySelectorAll('[data-setting]')];
            for (const el of updates) {
                await fetch(`${API_BASE}/settings/${el.dataset.setting}`, {
                    method:'PUT', credentials:'include',
                    headers:{'Content-Type':'application/json'}, body:JSON.stringify({value: el.value})
                });
            }
            showToast('Settings saved!', 'success');
        });
    }

    // Load announcements management
    loadAnnouncementsAdmin();
    // Load audit log
    loadAuditLog();
    // Load broadcast notif panel
}

async function loadAnnouncementsAdmin() {
    const cont = document.getElementById('announcementsAdmin');
    if (!cont) return;
    const rows = await fetch(`${API_BASE}/announcements`, {credentials:'include'}).then(r=>r.json());
    cont.innerHTML = rows.map(a => `
        <div class="announcement-item priority-${a.priority}">
            <div style="display:flex;justify-content:space-between;align-items:start">
                <div><h4>${a.title}</h4><p>${a.message}</p>
                <div class="ann-meta">${new Date(a.created_at).toLocaleDateString()} · ${a.priority}</div></div>
                <button class="btn-sm btn-danger" onclick="deleteAnnouncement(${a.id})">Delete</button>
            </div>
        </div>`).join('') || '<p class="text-muted">No announcements.</p>';
}

async function createAnnouncement() {
    const title = document.getElementById('ann_title').value;
    const message = document.getElementById('ann_message').value;
    const priority = document.getElementById('ann_priority').value;
    if (!title || !message) { showToast('Title and message required', 'warning'); return; }
    const r = await fetch(`${API_BASE}/announcements`, {method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body:JSON.stringify({title, message, priority})});
    const res = await r.json();
    showToast(res.message, res.success?'success':'danger');
    if (res.success) { document.getElementById('ann_title').value=''; document.getElementById('ann_message').value=''; loadAnnouncementsAdmin(); }
}

async function deleteAnnouncement(id) {
    confirmAction('Delete this announcement?', async () => {
        await fetch(`${API_BASE}/announcements/${id}`, {method:'DELETE', credentials:'include'});
        showToast('Announcement deleted', 'success'); loadAnnouncementsAdmin();
    });
}

async function broadcastNotification() {
    const msg = document.getElementById('broadcastMsg').value;
    if (!msg) { showToast('Enter a message', 'warning'); return; }
    const r = await fetch(`${API_BASE}/notifications/broadcast`, {method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:msg, type:'info'})});
    const res = await r.json();
    showToast(res.message, res.success?'success':'warning');
    if (res.success) document.getElementById('broadcastMsg').value = '';
}

async function loadAuditLog() {
    const cont = document.getElementById('auditLogContainer');
    if (!cont) return;
    const data = await fetch(`${API_BASE}/audit_log`, {credentials:'include'}).then(r=>r.json());
    const log = data.log || [];
    cont.innerHTML = `<div class="table-wrapper"><table id="auditTable">
        <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Resource</th><th>Details</th></tr></thead>
        <tbody>${log.map(l=>`<tr>
            <td>${new Date(l.timestamp).toLocaleString()}</td>
            <td>${l.username||'—'}</td>
            <td><span class="badge badge-info">${l.action}</span></td>
            <td>${l.resource||'—'}</td>
            <td>${l.details||'—'}</td>
        </tr>`).join('')}</tbody>
    </table></div>`;
    addPagination('auditTable', 15);
}

// ── Modals & Close ────────────────────────────────────────────
window.onclick = (e) => {
    document.querySelectorAll('.modal').forEach(m => { if (e.target === m) m.style.display='none'; });
};
