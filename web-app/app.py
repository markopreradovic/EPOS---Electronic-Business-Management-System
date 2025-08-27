#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>EPOS Sistem</title>
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            .auth-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
            }
            .auth-container input {
                padding: 10px;
                margin: 10px 0;
                width: 300px;
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #333;
                color: #e0e0e0;
            }
            .auth-container button {
                background-color: #00bcd4;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .auth-container button:hover {
                background-color: #0097a7;
            }
            .auth-container .error {
                color: #f44336;
                margin-top: 10px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: #2c2c2c;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
                display: none;
            }
            h1 {
                color: #00bcd4;
                text-align: center;
                margin-bottom: 20px;
            }
            h2 {
                color: #b0bec5;
                border-bottom: 1px solid #444;
                padding-bottom: 5px;
            }
            .tabs {
                display: flex;
                margin-bottom: 20px;
                border-bottom: 2px solid #444;
            }
            .tab {
                padding: 10px 20px;
                cursor: pointer;
                background-color: #3a3a3a;
                margin-right: 5px;
                border-radius: 5px 5px 0 0;
            }
            .tab.active {
                background-color: #00bcd4;
                color: #fff;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .form-group {
                margin: 15px 0;
            }
            label {
                display: block;
                margin-bottom: 5px;
                color: #cfd8dc;
            }
            input, textarea, select {
                width: 100%;
                padding: 10px;
                margin-bottom: 10px;
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #333;
                color: #e0e0e0;
                box-sizing: border-box;
            }
            button {
                background-color: #00bcd4;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s;
                margin: 5px;
            }
            button:hover {
                background-color: #0097a7;
            }
            button.danger {
                background-color: #f44336;
            }
            button.danger:hover {
                background-color: #d32f2f;
            }
            .klijent, .faktura, .trosak {
                background-color: #3a3a3a;
                border: 1px solid #444;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
            }
            .status {
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                display: inline-block;
                margin: 5px 0;
            }
            .status.kreirana, .status.planiran { background-color: #424242; color: #ffca28; }
            .status.poslana { background-color: #424242; color: #81d4fa; }
            .status.placena, .status.izvršen { background-color: #424242; color: #a5d6a7; }
            .status.otkazan { background-color: #424242; color: #ef5350; }
            #stavke .stavka {
                display: flex;
                gap: 10px;
                margin-bottom: 10px;
            }
            #stavke .stavka input {
                flex: 1;
                margin: 0;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .stat-card {
                background-color: #3a3a3a;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
            }
            .stat-number {
                font-size: 24px;
                font-weight: bold;
                color: #00bcd4;
            }
            .filters {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            .filters input, .filters select {
                width: auto;
                min-width: 150px;
            }
        </style>
    </head>
    <body>
        <div id="authContainer" class="auth-container">
            <h2>Unesite API ključ</h2>
            <input type="text" id="apiKeyInput" placeholder="Unesite vaš API ključ">
            <button onclick="validateApiKey()">Potvrdi</button>
            <p id="authError" class="error"></p>
        </div>
        <div id="mainContainer" class="container">
            <h1>EPOS Kompanijski Sistem</h1>
            <div class="tabs">
                <div class="tab active" onclick="showTab('klijenti')">Klijenti</div>
                <div class="tab" onclick="showTab('fakture')">Fakture</div>
                <div class="tab" onclick="showTab('troskovi')">Troškovi</div>
                <div class="tab" onclick="showTab('statistike')">Statistike</div>
            </div>
            <div id="klijenti" class="tab-content active">
                <h2>Dodaj Novog Klijenta</h2>
                <form id="klijentForm">
                    <div class="form-group">
                        <label>Naziv:</label>
                        <input type="text" id="naziv" required>
                    </div>
                    <div class="form-group">
                        <label>Email:</label>
                        <input type="email" id="email" required>
                    </div>
                    <div class="form-group">
                        <label>Telefon:</label>
                        <input type="text" id="telefon">
                    </div>
                    <div class="form-group">
                        <label>Adresa:</label>
                        <textarea id="adresa"></textarea>
                    </div>
                    <button type="submit">Dodaj Klijenta</button>
                </form>
                <h2>Klijenti</h2>
                <div id="klijentiLista"></div>
            </div>
            <div id="fakture" class="tab-content">
                <h2>Kreiraj Fakturu</h2>
                <div id="fakturaForm">
                    <select id="klijentSelect">
                        <option value="">Izaberi klijenta...</option>
                    </select>
                    <div id="stavke">
                        <div class="stavka">
                            <input type="text" placeholder="Naziv stavke" class="stavka-naziv">
                            <input type="number" placeholder="Količina" class="stavka-kolicina" step="0.01">
                            <input type="number" placeholder="Cijena" class="stavka-cijena" step="0.01">
                        </div>
                    </div>
                    <button onclick="dodajStavku()">+ Dodaj Stavku</button>
                    <button onclick="kreiraFakturu()">Kreiraj Fakturu</button>
                </div>
                <h2>Fakture</h2>
                <div id="faktureLista"></div>
            </div>
            <div id="troskovi" class="tab-content">
                <h2>Dodaj Novi Trošak</h2>
                <form id="trosakForm">
                    <div class="form-group">
                        <label>Naziv:</label>
                        <input type="text" id="trosakNaziv" required>
                    </div>
                    <div class="form-group">
                        <label>Kategorija:</label>
                        <select id="trosakKategorija" required>
                            <option value="">Izaberi kategoriju...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Iznos (KM):</label>
                        <input type="number" id="trosakIznos" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Datum:</label>
                        <input type="date" id="trosakDatum" required>
                    </div>
                    <div class="form-group">
                        <label>Opis:</label>
                        <textarea id="trosakOpis"></textarea>
                    </div>
                    <button type="submit">Dodaj Trošak</button>
                </form>
                <h2>Troškovi</h2>
                <div class="filters">
                    <select id="filterKategorija">
                        <option value="">Sve kategorije</option>
                    </select>
                    <select id="filterStatus">
                        <option value="">Svi statusi</option>
                        <option value="planiran">Planirani</option>
                        <option value="izvršen">Izvršeni</option>
                        <option value="otkazan">Otkazani</option>
                    </select>
                    <input type="date" id="filterDatumOd" placeholder="Datum od">
                    <input type="date" id="filterDatumDo" placeholder="Datum do">
                    <button onclick="filtrirajTroskove()">Filtriraj</button>
                </div>
                <div id="troskoviLista"></div>
            </div>
            <div id="statistike" class="tab-content">
                <h2>Statistike Troškova</h2>
                <div class="filters">
                    <input type="date" id="statDatumOd" placeholder="Datum od">
                    <input type="date" id="statDatumDo" placeholder="Datum do">
                    <button onclick="ucitajStatistike()">Ažuriraj</button>
                </div>
                <div id="statistikeLista"></div>
            </div>
        </div>
        <script>
            let API_KEY = null;
            let trenutniKlijenti = [];
            const KATEGORIJE = [
                { id: 'materijal', naziv: 'Troškovi materijala i sirovina' },
                { id: 'usluga', naziv: 'Troškovi usluga od vanjskih dobavljača' },
                { id: 'plata', naziv: 'Troškovi plača i beneficija zaposlenih' },
                { id: 'rezija', naziv: 'Režijski troškovi (struja, voda, internet, kirija)' },
                { id: 'marketing', naziv: 'Troškovi marketinga i reklame' },
                { id: 'transport', naziv: 'Troškovi transporta i dostave' },
                { id: 'ostalo', naziv: 'Ostali troškovi' }
            ];
            function validateApiKey() {
                const apiKey = document.getElementById('apiKeyInput').value.trim();
                if (!apiKey) {
                    document.getElementById('authError').innerText = 'Molimo unesite API ključ.';
                    return;
                }
                fetch('/api/validate-api-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ api_key: apiKey })
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw new Error(err.error); });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        API_KEY = apiKey;
                        document.getElementById('authContainer').style.display = 'none';
                        document.getElementById('mainContainer').style.display = 'block';
                        ucitajKlijente();
                        ucitajKategorije();
                    } else {
                        document.getElementById('authError').innerText = data.error || 'Nevažeći API ključ.';
                    }
                })
                .catch(error => {
                    document.getElementById('authError').innerText = error.message || 'Greška pri validaciji API ključa.';
                    console.error('Error validating API key:', error);
                });
            }
            function renderKlijenti() {
                const div = document.getElementById('klijentiLista');
                div.innerHTML = '';
                if (trenutniKlijenti.length === 0) {
                    div.innerHTML = '<p>Nema klijenata za prikaz.</p>';
                    return;
                }
                trenutniKlijenti.forEach(k => {
                    div.innerHTML += `
                        <div class="klijent" data-id="${k.id}">
                            <h4>${k.naziv}</h4>
                            <p><strong>Email:</strong> ${k.email}</p>
                            <p><strong>Telefon:</strong> ${k.telefon || 'N/A'}</p>
                            <p><strong>Adresa:</strong> ${k.adresa || 'N/A'}</p>
                            <p><strong>Datum kreiranja:</strong> ${k.datum_kreiranja.split('T')[0]}</p>
                            <button onclick="azurirajKlijenta('${k.id}')">Ažuriraj</button>
                            <button class="danger" onclick="obrisiKlijenta('${k.id}')">Obriši</button>
                            <button onclick="prikaziFakture('${k.id}')">Prikaži Fakture</button>
                        </div>
                    `;
                });
                const select = document.getElementById('klijentSelect');
                select.innerHTML = '<option value="">Izaberi klijenta...</option>';
                trenutniKlijenti.forEach(k => {
                    select.innerHTML += `<option value="${k.id}">${k.naziv}</option>`;
                });
            }
            function showTab(tabName) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.querySelector(`#${tabName}`).classList.add('active');
                event.target.classList.add('active');
                if (tabName === 'klijenti') {
                    ucitajKlijente();
                } else if (tabName === 'fakture') {
                    ucitajFakture();
                } else if (tabName === 'troskovi') {
                    ucitajKategorije();
                    ucitajTroskove();
                } else if (tabName === 'statistike') {
                    ucitajStatistike();
                }
            }
            function ucitajKlijente() {
                fetch('http://localhost:5001/api/klijenti', {
                    headers: {
                        'X-Tenant-API-Key': API_KEY
                    }
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    return r.json();
                })
                .then(data => {
                    trenutniKlijenti = data;
                    renderKlijenti();
                })
                .catch(error => {
                    console.error('Error loading clients:', error);
                    document.getElementById('klijentiLista').innerHTML = `<p>Greška pri učitavanju klijenata: ${error.message}</p>`;
                });
            }
            document.getElementById('klijentForm').onsubmit = function(e) {
                e.preventDefault();
                const data = {
                    naziv: document.getElementById('naziv').value,
                    email: document.getElementById('email').value,
                    telefon: document.getElementById('telefon').value,
                    adresa: document.getElementById('adresa').value
                };
                fetch('http://localhost:5001/api/klijenti', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Tenant-API-Key': API_KEY
                    },
                    body: JSON.stringify(data)
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    return r.json();
                })
                .then(() => {
                    alert('Klijent dodan!');
                    this.reset();
                    ucitajKlijente();
                })
                .catch(error => {
                    console.error('Error adding client:', error);
                    alert(`Greška pri dodavanju klijenta: ${error.message}`);
                });
            };
            function azurirajKlijenta(klijentId) {
                const klijentDiv = document.querySelector(`.klijent[data-id="${klijentId}"]`);
                const naziv = prompt("Unesi novi naziv:", klijentDiv.querySelector('h4').textContent);
                const email = prompt("Unesi novi email:", klijentDiv.querySelector('p:nth-child(2)').textContent.split(': ')[1]);
                const telefon = prompt("Unesi novi telefon:", klijentDiv.querySelector('p:nth-child(3)').textContent.split(': ')[1]);
                const adresa = prompt("Unesi novu adresu:", klijentDiv.querySelector('p:nth-child(4)').textContent.split(': ')[1]);
                const data = {};
                if (naziv) data.naziv = naziv;
                if (email) data.email = email;
                if (telefon) data.telefon = telefon;
                if (adresa) data.adresa = adresa;
                if (Object.keys(data).length === 0) return;
                fetch(`http://localhost:5001/api/klijenti/${klijentId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Tenant-API-Key': API_KEY
                    },
                    body: JSON.stringify(data)
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    alert('Klijent ažuriran!');
                    ucitajKlijente();
                })
                .catch(error => {
                    console.error('Error updating client:', error);
                    alert(`Greška pri ažuriranju klijenta: ${error.message}`);
                });
            }
            function obrisiKlijenta(klijentId) {
                if (confirm('Jeste li sigurni da želite obrisati klijenta?')) {
                    fetch(`http://localhost:5001/api/klijenti/${klijentId}`, {
                        method: 'DELETE',
                        headers: {
                            'X-Tenant-API-Key': API_KEY
                        }
                    })
                    .then(r => {
                        if (!r.ok) {
                            throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                        }
                        alert('Klijent obrisan!');
                        ucitajKlijente();
                    })
                    .catch(error => {
                        console.error('Error deleting client:', error);
                        alert(`Greška pri brisanju klijenta: ${error.message}`);
                    });
                }
            }
            function dodajStavku() {
                const div = document.getElementById('stavke');
                div.innerHTML += `
                    <div class="stavka">
                        <input type="text" placeholder="Naziv stavke" class="stavka-naziv">
                        <input type="number" placeholder="Količina" class="stavka-kolicina" step="0.01">
                        <input type="number" placeholder="Cijena" class="stavka-cijena" step="0.01">
                    </div>
                `;
            }
            function kreiraFakturu() {
                const klijentId = document.getElementById('klijentSelect').value;
                if (!klijentId) return alert('Izaberi klijenta!');
                const stavke = [];
                document.querySelectorAll('.stavka').forEach(s => {
                    const naziv = s.querySelector('.stavka-naziv').value;
                    const kolicina = parseFloat(s.querySelector('.stavka-kolicina').value);
                    const cijena = parseFloat(s.querySelector('.stavka-cijena').value);
                    if (naziv && kolicina && cijena) {
                        stavke.push({naziv, kolicina, cijena});
                    }
                });
                if (stavke.length === 0) return alert('Dodaj najmanje jednu stavku!');
                fetch('http://localhost:5002/api/fakture', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Tenant-API-Key': API_KEY
                    },
                    body: JSON.stringify({klijent_id: klijentId, stavke})
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    return r.json();
                })
                .then(() => {
                    alert('Faktura kreirana!');
                    document.getElementById('stavke').innerHTML = `
                        <div class="stavka">
                            <input type="text" placeholder="Naziv stavke" class="stavka-naziv">
                            <input type="number" placeholder="Količina" class="stavka-kolicina" step="0.01">
                            <input type="number" placeholder="Cijena" class="stavka-cijena" step="0.01">
                        </div>
                    `;
                    ucitajFakture();
                })
                .catch(error => {
                    console.error('Error creating invoice:', error);
                    alert(`Greška pri kreiranju fakture: ${error.message}`);
                });
            }
            function ucitajFakture() {
                fetch('http://localhost:5002/api/fakture', {
                    headers: {
                        'X-Tenant-API-Key': API_KEY
                    }
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    return r.json();
                })
                .then(fakture => {
                    const div = document.getElementById('faktureLista');
                    div.innerHTML = '';
                    if (fakture.length === 0) {
                        div.innerHTML = '<p>Nema faktura za prikaz.</p>';
                        return;
                    }
                    fakture.forEach(f => {
                        div.innerHTML += `
                            <div class="faktura" data-id="${f.id}">
                                <h4>${f.broj_fakture}</h4>
                                <p><strong>Iznos:</strong> ${f.iznos.toFixed(2)} KM</p>
                                <p><strong>Datum:</strong> ${f.datum.split('T')[0]}</p>
                                <p><strong>Status:</strong> <span class="status ${f.status}">${f.status}</span></p>
                                <button onclick="azurirajFakturu('${f.id}')">Ažuriraj</button>
                                <button class="danger" onclick="obrisiFakturu('${f.id}')">Obriši</button>
                            </div>
                        `;
                    });
                })
                .catch(error => {
                    console.error('Error loading invoices:', error);
                    document.getElementById('faktureLista').innerHTML = `<p>Greška pri učitavanju faktura: ${error.message}</p>`;
                });
            }
            function azurirajFakturu(fakturaId) {
                const faktura = document.querySelector(`.faktura[data-id="${fakturaId}"]`);
                const status = prompt("Unesi novi status (kreirana/poslana/placena/otkazana):", faktura.querySelector('.status').textContent);
                const iznos = prompt("Unesi novi iznos (ostavi prazno za bez promjene):", parseFloat(faktura.querySelector('p:nth-child(2)').textContent.split(': ')[1].replace(' KM', '')));
                const data = {};
                if (status) data.status = status;
                if (iznos) data.iznos = parseFloat(iznos);
                if (Object.keys(data).length === 0) return;
                fetch(`http://localhost:5002/api/fakture/${fakturaId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Tenant-API-Key': API_KEY
                    },
                    body: JSON.stringify(data)
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    alert('Faktura ažurirana!');
                    ucitajFakture();
                })
                .catch(error => {
                    console.error('Error updating invoice:', error);
                    alert(`Greška pri ažuriranju fakture: ${error.message}`);
                });
            }
            function obrisiFakturu(fakturaId) {
                if (confirm('Jeste li sigurni da želite obrisati fakturu?')) {
                    fetch(`http://localhost:5002/api/fakture/${fakturaId}`, {
                        method: 'DELETE',
                        headers: {
                            'X-Tenant-API-Key': API_KEY
                        }
                    })
                    .then(r => {
                        if (!r.ok) {
                            throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                        }
                        alert('Faktura obrisana!');
                        ucitajFakture();
                    })
                    .catch(error => {
                        console.error('Error deleting invoice:', error);
                        alert(`Greška pri brisanju fakture: ${error.message}`);
                    });
                }
            }
            function prikaziFakture(klijentId) {
                fetch(`http://localhost:5002/api/klijenti/${klijentId}/fakture`, {
                    headers: {
                        'X-Tenant-API-Key': API_KEY
                    }
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    return r.json();
                })
                .then(fakture => {
                    let html = 'Fakture:\\n\\n';
                    if (fakture.length === 0) {
                        html += 'Nema faktura za ovog klijenta.';
                    } else {
                        fakture.forEach(f => {
                            html += `${f.broj_fakture} - ${f.iznos.toFixed(2)} KM (${f.status})\\n`;
                        });
                    }
                    alert(html);
                })
                .catch(error => {
                    console.error('Error loading invoices:', error);
                    alert(`Greška pri učitavanju faktura: ${error.message}`);
                });
            }
            function ucitajKategorije() {
                const select1 = document.getElementById('trosakKategorija');
                const select2 = document.getElementById('filterKategorija');
                select1.innerHTML = '<option value="">Izaberi kategoriju...</option>';
                select2.innerHTML = '<option value="">Sve kategorije</option>';
                KATEGORIJE.forEach(k => {
                    select1.innerHTML += `<option value="${k.id}">${k.naziv}</option>`;
                    select2.innerHTML += `<option value="${k.id}">${k.naziv}</option>`;
                });
            }
            function ucitajTroskove() {
                fetch('http://localhost:5003/api/troskovi', {
                    headers: {
                        'X-Tenant-API-Key': API_KEY
                    }
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    return r.json();
                })
                .then(troskovi => {
                    const div = document.getElementById('troskoviLista');
                    div.innerHTML = '';
                    if (troskovi.length === 0) {
                        div.innerHTML = '<p>Nema troškova za prikaz.</p>';
                        return;
                    }
                    troskovi.forEach(t => {
                        const kategorijaNaziv = KATEGORIJE.find(k => k.id === t.kategorija)?.naziv || t.kategorija;
                        div.innerHTML += `
                            <div class="trosak" data-id="${t.id}">
                                <h4>${t.naziv}</h4>
                                <p><strong>Kategorija:</strong> ${kategorijaNaziv}</p>
                                <p><strong>Iznos:</strong> ${parseFloat(t.iznos).toFixed(2)} KM</p>
                                <p><strong>Datum:</strong> ${t.datum}</p>
                                <p><strong>Status:</strong> <span class="status ${t.status}">${t.status}</span></p>
                                <p><strong>Opis:</strong> ${t.opis || 'Nema opisa'}</p>
                                <button onclick="azurirajTrosak('${t.id}')">Ažuriraj</button>
                                <button class="danger" onclick="obrisiTrosak('${t.id}')">Obriši</button>
                                <button onclick="promijeniStatus('${t.id}', '${t.status}')">Promijeni Status</button>
                            </div>
                        `;
                    });
                })
                .catch(error => {
                    console.error('Error loading expenses:', error);
                    document.getElementById('troskoviLista').innerHTML = `<p>Greška pri učitavanju troškova: ${error.message}</p>`;
                });
            }
            function filtrirajTroskove() {
                const kategorija = document.getElementById('filterKategorija').value;
                const status = document.getElementById('filterStatus').value;
                const datumOd = document.getElementById('filterDatumOd').value;
                const datumDo = document.getElementById('filterDatumDo').value;
                let url = 'http://localhost:5003/api/troskovi?';
                const params = [];
                if (kategorija) params.push(`kategorija=${kategorija}`);
                if (status) params.push(`status=${status}`);
                if (datumOd) params.push(`datum_od=${datumOd}`);
                if (datumDo) params.push(`datum_do=${datumDo}`);
                url += params.join('&');
                fetch(url, {
                    headers: {
                        'X-Tenant-API-Key': API_KEY
                    }
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    return r.json();
                })
                .then(troskovi => {
                    const div = document.getElementById('troskoviLista');
                    div.innerHTML = '';
                    if (troskovi.length === 0) {
                        div.innerHTML = '<p>Nema troškova koji zadovoljavaju kriterije.</p>';
                        return;
                    }
                    troskovi.forEach(t => {
                        const kategorijaNaziv = KATEGORIJE.find(k => k.id === t.kategorija)?.naziv || t.kategorija;
                        div.innerHTML += `
                            <div class="trosak" data-id="${t.id}">
                                <h4>${t.naziv}</h4>
                                <p><strong>Kategorija:</strong> ${kategorijaNaziv}</p>
                                <p><strong>Iznos:</strong> ${parseFloat(t.iznos).toFixed(2)} KM</p>
                                <p><strong>Datum:</strong> ${t.datum}</p>
                                <p><strong>Status:</strong> <span class="status ${t.status}">${t.status}</span></p>
                                <p><strong>Opis:</strong> ${t.opis || 'Nema opisa'}</p>
                                <button onclick="azurirajTrosak('${t.id}')">Ažuriraj</button>
                                <button class="danger" onclick="obrisiTrosak('${t.id}')">Obriši</button>
                                <button onclick="promijeniStatus('${t.id}', '${t.status}')">Promijeni Status</button>
                            </div>
                        `;
                    });
                })
                .catch(error => {
                    console.error('Error filtering expenses:', error);
                    document.getElementById('troskoviLista').innerHTML = `<p>Greška pri filtriranju troškova: ${error.message}</p>`;
                });
            }
            document.getElementById('trosakForm').onsubmit = function(e) {
                e.preventDefault();
                const data = {
                    naziv: document.getElementById('trosakNaziv').value,
                    kategorija: document.getElementById('trosakKategorija').value,
                    iznos: parseFloat(document.getElementById('trosakIznos').value),
                    datum: document.getElementById('trosakDatum').value,
                    opis: document.getElementById('trosakOpis').value
                };
                fetch('http://localhost:5003/api/troskovi', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Tenant-API-Key': API_KEY
                    },
                    body: JSON.stringify(data)
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    return r.json();
                })
                .then(() => {
                    alert('Trošak dodan!');
                    this.reset();
                    ucitajTroskove();
                })
                .catch(error => {
                    console.error('Error adding expense:', error);
                    alert(`Greška pri dodavanju troška: ${error.message}`);
                });
            }
            function azurirajTrosak(trosakId) {
                const trosak = document.querySelector(`.trosak[data-id="${trosakId}"]`);
                const naziv = prompt("Unesi novi naziv:", trosak.querySelector('h4').textContent);
                const iznos = prompt("Unesi novi iznos:", parseFloat(trosak.querySelector('p:nth-child(3)').textContent.split(': ')[1].replace(' KM', '')));
                if (naziv && iznos) {
                    fetch(`http://localhost:5003/api/troskovi/${trosakId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Tenant-API-Key': API_KEY
                        },
                        body: JSON.stringify({naziv, iznos: parseFloat(iznos)})
                    })
                    .then(r => {
                        if (!r.ok) {
                            throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                        }
                        alert('Trošak ažuriran!');
                        ucitajTroskove();
                    })
                    .catch(error => {
                        console.error('Error updating expense:', error);
                        alert(`Greška pri ažuriranju troška: ${error.message}`);
                    });
                }
            }
            function obrisiTrosak(trosakId) {
                if (confirm('Jeste li sigurni da želite obrisati trošak?')) {
                    fetch(`http://localhost:5003/api/troskovi/${trosakId}`, {
                        method: 'DELETE',
                        headers: {
                            'X-Tenant-API-Key': API_KEY
                        }
                    })
                    .then(r => {
                        if (!r.ok) {
                            throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                        }
                        alert('Trošak obrisan!');
                        ucitajTroskove();
                    })
                    .catch(error => {
                        console.error('Error deleting expense:', error);
                        alert(`Greška pri brisanju troška: ${error.message}`);
                    });
                }
            }
            function promijeniStatus(trosakId, trenutniStatus) {
                const noviStatus = prompt(`Unesi novi status (planiran/izvršen/otkazan):`, trenutniStatus);
                if (noviStatus && ['planiran', 'izvršen', 'otkazan'].includes(noviStatus)) {
                    fetch(`http://localhost:5003/api/troskovi/${trosakId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Tenant-API-Key': API_KEY
                        },
                        body: JSON.stringify({status: noviStatus})
                    })
                    .then(r => {
                        if (!r.ok) {
                            throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                        }
                        alert('Status ažuriran!');
                        ucitajTroskove();
                    })
                    .catch(error => {
                        console.error('Error updating status:', error);
                        alert(`Greška pri ažuriranju statusa: ${error.message}`);
                    });
                }
            }
            function ucitajStatistike() {
                const datumOd = document.getElementById('statDatumOd').value;
                const datumDo = document.getElementById('statDatumDo').value;
                let url = 'http://localhost:5003/api/troskovi/statistike?';
                const params = [];
                if (datumOd) params.push(`datum_od=${datumOd}`);
                if (datumDo) params.push(`datum_do=${datumDo}`);
                url += params.join('&');
                fetch(url, {
                    headers: {
                        'X-Tenant-API-Key': API_KEY
                    }
                })
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`HTTP error! Status: ${r.status}, ${r.statusText}`);
                    }
                    return r.json();
                })
                .then(stats => {
                    const div = document.getElementById('statistikeLista');
                    div.innerHTML = `
                        <div class="stats">
                            <div class="stat-card">
                                <div class="stat-number">${stats.ukupno.ukupno.toFixed(2)} KM</div>
                                <div>Ukupni troškovi</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.ukupno.broj}</div>
                                <div>Broj troškova</div>
                            </div>
                        </div>
                        <h3>Po kategorijama:</h3>
                        <div id="statKategorije"></div>
                        <h3>Po statusu:</h3>
                        <div id="statStatus"></div>
                    `;
                    const poKategorijama = {};
                    stats.po_kategorijama.forEach(s => {
                        if (!poKategorijama[s.kategorija]) {
                            poKategorijama[s.kategorija] = {ukupno: 0, broj: 0};
                        }
                        poKategorijama[s.kategorija].ukupno += s.ukupno;
                        poKategorijama[s.kategorija].broj += s.broj;
                    });
                    let katDiv = document.getElementById('statKategorije');
                    katDiv.innerHTML = '<div class="stats">';
                    Object.keys(poKategorijama).forEach(kat => {
                        const kategorijaNaziv = KATEGORIJE.find(k => k.id === kat)?.naziv || kat;
                        katDiv.innerHTML += `
                            <div class="stat-card">
                                <div class="stat-number">${poKategorijama[kat].ukupno.toFixed(2)} KM</div>
                                <div>${kategorijaNaziv}</div>
                                <small>${poKategorijama[kat].broj} troškova</small>
                            </div>
                        `;
                    });
                    katDiv.innerHTML += '</div>';
                    const poStatusu = {};
                    stats.po_statusu.forEach(s => {
                        if (!poStatusu[s.status]) {
                            poStatusu[s.status] = {ukupno: 0, broj: 0};
                        }
                        poStatusu[s.status].ukupno += s.ukupno;
                        poStatusu[s.status].broj += s.broj;
                    });
                    let statDiv = document.getElementById('statStatus');
                    statDiv.innerHTML = '<div class="stats">';
                    Object.keys(poStatusu).forEach(stat => {
                        statDiv.innerHTML += `
                            <div class="stat-card">
                                <div class="stat-number">${poStatusu[stat].ukupno.toFixed(2)} KM</div>
                                <div class="status ${stat}">${stat}</div>
                                <small>${poStatusu[stat].broj} troškova</small>
                            </div>
                        `;
                    });
                    statDiv.innerHTML += '</div>';
                })
                .catch(error => {
                    console.error('Error loading statistics:', error);
                    document.getElementById('statistikeLista').innerHTML = `<p>Greška pri učitavanju statistika: ${error.message}</p>`;
                });
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/api/validate-api-key', methods=['POST'])
def validate_api_key():
    try:
        api_key = request.json.get('api_key')
        if not api_key:
            return jsonify({'error': 'API ključ je obavezan'}), 400
        response = requests.get(
            'http://localhost:5004/api/tenant/info',
            headers={'X-Tenant-API-Key': api_key}
        )
        if response.status_code == 200:
            return jsonify({'status': 'success', 'tenant': response.json()})
        else:
            return jsonify({'error': 'Nevažeći ili neaktivan API ključ'}), 401
    except Exception as e:
        print(f"Error validating API key: {e}")
        return jsonify({'error': 'Greška na serveru prilikom validacije'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)