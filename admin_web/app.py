#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)


@app.route('/')
def admin_dashboard():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>EPOS Admin Panel</title>
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #0d1117;
                color: #e6edf3;
            }
            .header {
                background: linear-gradient(135deg, #1f6feb, #0969da);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 30px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(31, 111, 235, 0.3);
            }
            .header h1 {
                margin: 0;
                color: white;
                font-size: 2.5em;
                font-weight: 600;
            }
            .header p {
                margin: 10px 0 0 0;
                color: rgba(255, 255, 255, 0.8);
                font-size: 1.1em;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            .tabs {
                display: flex;
                margin-bottom: 30px;
                border-bottom: 2px solid #21262d;
                background-color: #161b22;
                border-radius: 12px 12px 0 0;
                padding: 0 20px;
            }
            .tab {
                padding: 15px 25px;
                cursor: pointer;
                background: transparent;
                border: none;
                color: #7d8590;
                font-size: 16px;
                font-weight: 500;
                transition: all 0.3s ease;
                position: relative;
            }
            .tab:hover {
                color: #e6edf3;
                background-color: #262c36;
            }
            .tab.active {
                color: #1f6feb;
                background-color: #0d1117;
                border-radius: 8px 8px 0 0;
            }
            .tab.active::after {
                content: '';
                position: absolute;
                bottom: -2px;
                left: 0;
                right: 0;
                height: 2px;
                background-color: #1f6feb;
            }
            .tab-content {
                display: none;
                background-color: #161b22;
                padding: 30px;
                border-radius: 0 0 12px 12px;
                min-height: 600px;
            }
            .tab-content.active {
                display: block;
            }
            .card {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: linear-gradient(135deg, #21262d, #161b22);
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            }
            .stat-number {
                font-size: 2.5em;
                font-weight: 700;
                color: #1f6feb;
                margin-bottom: 8px;
            }
            .stat-label {
                color: #7d8590;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .request-item, .tenant-item {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 15px;
                transition: all 0.3s ease;
            }
            .request-item:hover, .tenant-item:hover {
                border-color: #1f6feb;
                box-shadow: 0 4px 12px rgba(31, 111, 235, 0.2);
            }
            .status-badge {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .status-submitted {
                background-color: #ffd60a;
                color: #1a1a1a;
            }
            .status-approved {
                background-color: #238636;
                color: white;
            }
            .status-rejected {
                background-color: #da3633;
                color: white;
            }
            .status-active {
                background-color: #238636;
                color: white;
            }
            .status-suspended {
                background-color: #fb8500;
                color: white;
            }
            .status-terminated {
                background-color: #da3633;
                color: white;
            }
            .btn {
                background-color: #1f6feb;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s ease;
                margin: 4px;
            }
            .btn:hover {
                background-color: #0969da;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(31, 111, 235, 0.3);
            }
            .btn.success {
                background-color: #238636;
            }
            .btn.success:hover {
                background-color: #1a7f37;
            }
            .btn.danger {
                background-color: #da3633;
            }
            .btn.danger:hover {
                background-color: #b91c1c;
            }
            .btn.warning {
                background-color: #fb8500;
            }
            .btn.warning:hover {
                background-color: #fd7e14;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: #e6edf3;
                font-weight: 500;
            }
            .form-group input, .form-group textarea, .form-group select {
                width: 100%;
                padding: 12px;
                border: 1px solid #30363d;
                border-radius: 6px;
                background-color: #0d1117;
                color: #e6edf3;
                font-size: 14px;
                box-sizing: border-box;
            }
            .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
                outline: none;
                border-color: #1f6feb;
                box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.1);
            }
            .loading {
                text-align: center;
                padding: 40px;
                color: #7d8590;
            }
            .loading::after {
                content: '';
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 2px solid #7d8590;
                border-radius: 50%;
                border-top-color: #1f6feb;
                animation: spin 1s ease-in-out infinite;
                margin-left: 10px;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #7d8590;
            }
            .empty-state h3 {
                margin-bottom: 10px;
                color: #7d8590;
            }
            .request-details, .tenant-details {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 15px 0;
            }
            .detail-item {
                background-color: #21262d;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #30363d;
            }
            .detail-label {
                font-size: 12px;
                color: #7d8590;
                text-transform: uppercase;
                margin-bottom: 4px;
            }
            .detail-value {
                color: #e6edf3;
                font-weight: 500;
            }
            .actions {
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #30363d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>EPOS Admin Panel</h1>
                <p>Upravljanje klijentima i zahtjevima za aktivaciju</p>
            </div>

            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <div class="stat-number" id="totalTenants">-</div>
                    <div class="stat-label">Ukupno Klijenata</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="activeTenants">-</div>
                    <div class="stat-label">Aktivni Klijenti</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="pendingRequests">-</div>
                    <div class="stat-label">Pending Zahtjevi</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="monthlyRevenue">-</div>
                    <div class="stat-label">Mjesečni Prihod</div>
                </div>
            </div>

            <div class="tabs">
                <button class="tab active" onclick="showTab('requests')">Zahtjevi za Aktivaciju</button>
                <button class="tab" onclick="showTab('tenants')">Aktivni Klijenti</button>
                <button class="tab" onclick="showTab('billing')">Naplata</button>
                <button class="tab" onclick="showTab('settings')">Postavke</button>
            </div>

            <div id="requests" class="tab-content active">
                <div class="card">
                    <h2>Zahtjevi za Aktivaciju</h2>
                    <div id="requestsList" class="loading">Učitavam zahtjeve...</div>
                </div>
            </div>

            <div id="tenants" class="tab-content">
                <div class="card">
                    <h2>Aktivni EPOS Klijenti</h2>
                    <div id="tenantsList" class="loading">Učitavam klijente...</div>
                </div>
            </div>

            <div id="billing" class="tab-content">
                <div class="card">

                </div>
            </div>

            <div id="settings" class="tab-content">
                <div class="card">
                    <h2>Sistemske Postavke</h2>
                    <div class="form-group">
                        <label>Cijena po fakturi (KM)</label>
                        <input type="number" id="pricePerInvoice" value="1.00" step="0.01">
                    </div>
                    <div class="form-group">
                        <label>Cijena po klijentu (KM)</label>
                        <input type="number" id="pricePerClient" value="0.50" step="0.01">
                    </div>
                    <div class="form-group">
                        <label>Cijena po zahtevu za pregled (KM)</label>
                        <input type="number" id="pricePerView" value="0.01" step="0.01">
                    </div>
                    <button class="btn" onclick="savePricing()">Sačuvaj Postavke</button>
                </div>
            </div>
        </div>

        <script>
            const API_BASE = 'http://localhost:5004/api';
            let currentRequests = [];
            let currentTenants = [];

            function showTab(tabName) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                event.target.classList.add('active');
                document.querySelector(`#${tabName}`).classList.add('active');
                if (tabName === 'requests') {
                    loadRequests();
                } else if (tabName === 'tenants') {
                    loadTenants();
                } else if (tabName === 'billing') {
                    loadBillingData();
                }
            }

            async function loadRequests() {
                try {
                    const response = await fetch(`${API_BASE}/admin/requests`);
                    if (!response.ok) throw new Error('Failed to fetch requests');
                    currentRequests = await response.json();
                    renderRequests();
                } catch (error) {
                    console.error('Error loading requests:', error);
                    document.getElementById('requestsList').innerHTML = 
                        '<div class="empty-state"><h3>Greška</h3><p>Nije moguće učitati zahtjeve.</p></div>';
                }
            }

            async function loadTenants() {
                try {
                    const response = await fetch(`${API_BASE}/admin/tenants`);
                    if (!response.ok) throw new Error('Failed to fetch tenants');
                    currentTenants = await response.json();
                    renderTenants();
                    updateStats();
                } catch (error) {
                    console.error('Error loading tenants:', error);
                    document.getElementById('tenantsList').innerHTML = 
                        '<div class="empty-state"><h3>Greška</h3><p>Nije moguće učitati klijente.</p></div>';
                }
            }

            async function approveRequest(requestId) {
                const napomene = prompt('Napomene za odobravanje (opcionalno):');
                try {
                    const response = await fetch(`${API_BASE}/admin/requests/${requestId}/approve`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({napomene})
                    });
                    if (!response.ok) throw new Error('Failed to approve request');
                    const result = await response.json();
                    alert(`Zahtjev je odobren! Tenant ID: ${result.tenant_id}`);
                    loadRequests();
                    loadTenants();
                } catch (error) {
                    console.error('Error approving request:', error);
                    alert('Greška pri odobravanju zahtjeva');
                }
            }

            async function rejectRequest(requestId) {
                const napomene = prompt('Razlog odbacivanja (obavezno):');
                if (!napomene) return;
                try {
                    const response = await fetch(`${API_BASE}/admin/requests/${requestId}/reject`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({napomene})
                    });
                    if (!response.ok) throw new Error('Failed to reject request');
                    alert('Zahtjev je odbačen');
                    loadRequests();
                } catch (error) {
                    console.error('Error rejecting request:', error);
                    alert('Greška pri odbacivanju zahtjeva');
                }
            }

            async function suspendTenant(tenantId) {
                const razlog = prompt('Razlog suspendovanja (obavezno):');
                if (!razlog) return;
                try {
                    const response = await fetch(`${API_BASE}/admin/tenants/${tenantId}/suspend`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({razlog})
                    });
                    if (!response.ok) throw new Error('Failed to suspend tenant');
                    alert('Klijent je suspendovan');
                    loadTenants();
                } catch (error) {
                    console.error('Error suspending tenant:', error);
                    alert('Greška pri suspendovanju klijenta');
                }
            }

            function renderRequests() {
                const container = document.getElementById('requestsList');
                if (currentRequests.length === 0) {
                    container.innerHTML = '<div class="empty-state"><h3>Nema zahtjeva</h3><p>Trenutno nema pending zahtjeva za aktivaciju.</p></div>';
                    return;
                }
                let html = '';
                currentRequests.forEach(request => {
                    const statusClass = `status-${request.status}`;
                    html += `
                        <div class="request-item">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                                <h3 style="margin: 0; color: #e6edf3;">${request.naziv_kompanije}</h3>
                                <span class="status-badge ${statusClass}">${request.status}</span>
                            </div>
                            <div class="request-details">
                                <div class="detail-item">
                                    <div class="detail-label">Kontakt Osoba</div>
                                    <div class="detail-value">${request.kontakt_osoba}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Email</div>
                                    <div class="detail-value">${request.email}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Telefon</div>
                                    <div class="detail-value">${request.telefon || 'N/A'}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Datum Zahtjeva</div>
                                    <div class="detail-value">${new Date(request.datum_zahtjeva).toLocaleDateString('hr-HR')}</div>
                                </div>
                            </div>
                            <div class="detail-item" style="grid-column: 1 / -1; margin: 15px 0;">
                                <div class="detail-label">Adresa</div>
                                <div class="detail-value">${request.adresa || 'N/A'}</div>
                            </div>
                            <div class="detail-item" style="grid-column: 1 / -1; margin-bottom: 15px;">
                                <div class="detail-label">Opis Poslovanja</div>
                                <div class="detail-value">${request.opis_poslovanja}</div>
                            </div>
                            ${request.napomene ? `
                                <div class="detail-item" style="grid-column: 1 / -1; margin-bottom: 15px;">
                                    <div class="detail-label">Napomene</div>
                                    <div class="detail-value">${request.napomene}</div>
                                </div>
                            ` : ''}
                            ${request.status === 'submitted' ? `
                                <div class="actions">
                                    <button class="btn success" onclick="approveRequest('${request.id}')">Odobri</button>
                                    <button class="btn danger" onclick="rejectRequest('${request.id}')">Odbaci</button>
                                </div>
                            ` : ''}
                        </div>
                    `;
                });
                container.innerHTML = html;
            }

            function renderTenants() {
                const container = document.getElementById('tenantsList');
                if (currentTenants.length === 0) {
                    container.innerHTML = '<div class="empty-state"><h3>Nema klijenata</h3><p>Trenutno nema aktivnih EPOS klijenata.</p></div>';
                    return;
                }
                let html = '';
                currentTenants.forEach(tenant => {
                    const statusClass = `status-${tenant.status}`;
                    html += `
                        <div class="tenant-item">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                                <h3 style="margin: 0; color: #e6edf3;">${tenant.naziv}</h3>
                                <span class="status-badge ${statusClass}">${tenant.status}</span>
                            </div>
                            <div class="tenant-details">
                                <div class="detail-item">
                                    <div class="detail-label">Email</div>
                                    <div class="detail-value">${tenant.kontakt_email}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Telefon</div>
                                    <div class="detail-value">${tenant.kontakt_telefon || 'N/A'}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Datum Kreiranja</div>
                                    <div class="detail-value">${new Date(tenant.datum_kreiranja).toLocaleDateString('hr-HR')}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Datum Aktivacije</div>
                                    <div class="detail-value">${tenant.datum_aktivacije ? new Date(tenant.datum_aktivacije).toLocaleDateString('hr-HR') : 'N/A'}</div>
                                </div>
                            </div>
                            <div class="detail-item" style="grid-column: 1 / -1; margin: 15px 0;">
                                <div class="detail-label">Adresa</div>
                                <div class="detail-value">${tenant.adresa || 'N/A'}</div>
                            </div>
                            <div class="detail-item" style="grid-column: 1 / -1; margin-bottom: 15px;">
                                <div class="detail-label">API Key (skraćeno)</div>
                                <div class="detail-value">${tenant.api_key || 'N/A'}</div>
                            </div>
                            ${tenant.status === 'active' ? `
                                <div class="actions">
                                    <button class="btn" onclick="viewTenantDetails('${tenant.id}')">Detalji</button>
                                    <button class="btn warning" onclick="suspendTenant('${tenant.id}')">Suspenduj</button>
                                </div>
                            ` : ''}
                        </div>
                    `;
                });
                container.innerHTML = html;
            }

            function updateStats() {
                const total = currentTenants.length;
                const active = currentTenants.filter(t => t.status === 'active').length;
                const pending = currentRequests.filter(r => r.status === 'submitted').length;
                document.getElementById('totalTenants').textContent = total;
                document.getElementById('activeTenants').textContent = active;
                document.getElementById('pendingRequests').textContent = pending;
                const estimatedRevenue = active * 50;
                document.getElementById('monthlyRevenue').textContent = estimatedRevenue.toFixed(0) + ' KM';
            }

            function viewTenantDetails(tenantId) {
                const tenant = currentTenants.find(t => t.id === tenantId);
                if (!tenant) return;
                let details = `
Detalji EPOS Klijenta: ${tenant.naziv}

ID: ${tenant.id}
Email: ${tenant.kontakt_email}
Telefon: ${tenant.kontakt_telefon || 'N/A'}
Adresa: ${tenant.adresa || 'N/A'}
Status: ${tenant.status}
Datum kreiranja: ${new Date(tenant.datum_kreiranja).toLocaleDateString('hr-HR')}
API Key: ${tenant.api_key}
                `;
                alert(details);
            }

            function loadBillingData() {
                console.log('Loading billing data...');
            }

            function savePricing() {
                const pricePerInvoice = document.getElementById('pricePerInvoice').value;
                const pricePerClient = document.getElementById('pricePerClient').value;
                const pricePerView = document.getElementById('pricePerView').value;
                console.log('Saving pricing:', {
                    pricePerInvoice,
                    pricePerClient,
                    pricePerView
                });
                alert('Postavke sačuvane!');
            }

            document.addEventListener('DOMContentLoaded', function() {
                loadRequests();
                loadTenants();
                setInterval(() => {
                    const activeTab = document.querySelector('.tab.active').textContent.toLowerCase();
                    if (activeTab.includes('zahtjevi')) {
                        loadRequests();
                    } else if (activeTab.includes('klijenti')) {
                        loadTenants();
                    }
                }, 30000);
            });
        </script>
    </body>
    </html>
    ''')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)