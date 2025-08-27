#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

@app.route('/')
def registration_form():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>EPOS - Zahtjev za Aktivaciju</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #1f6feb, #0969da);
                color: white;
                padding: 40px;
                text-align: center;
            }
            .header h1 {
                font-size: 3em;
                margin-bottom: 10px;
                font-weight: 700;
            }
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
                margin-bottom: 20px;
            }
            .main-content {
                padding: 50px 40px;
            }
            .form-section {
                margin-bottom: 40px;
            }
            .form-section h2 {
                color: #2d3748;
                margin-bottom: 20px;
                font-size: 1.5em;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 10px;
            }
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            .form-row.full {
                grid-template-columns: 1fr;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                color: #4a5568;
                font-weight: 600;
                font-size: 14px;
            }
            .required {
                color: #e53e3e;
            }
            input, textarea, select {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 16px;
                transition: all 0.3s ease;
                background: white;
            }
            input:focus, textarea:focus, select:focus {
                outline: none;
                border-color: #1f6feb;
                box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.1);
            }
            textarea {
                resize: vertical;
                min-height: 100px;
            }
            .submit-btn {
                background: linear-gradient(135deg, #1f6feb, #0969da);
                color: white;
                border: none;
                padding: 16px 40px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                transition: all 0.3s ease;
                margin-top: 20px;
            }
            .submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(31, 111, 235, 0.3);
            }
            .submit-btn:disabled {
                background: #cbd5e0;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            .success-message, .error-message {
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: 500;
            }
            .success-message {
                background: #f0fff4;
                color: #22543d;
                border: 1px solid #9ae6b4;
            }
            .error-message {
                background: #fed7d7;
                color: #822727;
                border: 1px solid #feb2b2;
            }
            .loading {
                display: none;
                text-align: center;
                margin: 20px 0;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #1f6feb;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @media (max-width: 768px) {
                .container {
                    margin: 10px;
                    border-radius: 15px;
                }
                .header {
                    padding: 30px 20px;
                }
                .header h1 {
                    font-size: 2em;
                }
                .main-content {
                    padding: 30px 20px;
                }
                .form-row {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>EPOS</h1>
                <p>Elektronski Sistem za Upravljanje Poslovanjem</p>
            </div>
            <div class="main-content">
                <form id="registrationForm">
                    <div class="form-section">
                        <h2>Informacije o kompaniji</h2>
                        <div class="form-group">
                            <label for="nazivKompanije">
                                Naziv kompanije <span class="required">*</span>
                            </label>
                            <input type="text" id="nazivKompanije" name="naziv_kompanije" required>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="kontaktOsoba">
                                    Kontakt osoba <span class="required">*</span>
                                </label>
                                <input type="text" id="kontaktOsoba" name="kontakt_osoba" required>
                            </div>
                            <div class="form-group">
                                <label for="email">
                                    Email adresa <span class="required">*</span>
                                </label>
                                <input type="email" id="email" name="email" required>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="telefon">Broj telefona</label>
                                <input type="tel" id="telefon" name="telefon">
                            </div>
                            <div class="form-group">
                                <label for="adresa">Adresa</label>
                                <input type="text" id="adresa" name="adresa">
                            </div>
                        </div>
                    </div>
                    <div class="form-section">
                        <h2>O vašem poslovanju</h2>
                        <div class="form-group">
                            <label for="opisPoslovanja">
                                Kratko opišite vaše poslovanje <span class="required">*</span>
                            </label>
                            <textarea id="opisPoslovanja" name="opis_poslovanja" 
                                    placeholder="Opišite čime se bavite, koliko klijenata imate, koliko faktura mjesečno kreirate..." 
                                    required></textarea>
                        </div>
                    </div>
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>Šaljemo vaš zahtjev...</p>
                    </div>
                    <div id="messages"></div>
                    <button type="submit" class="submit-btn" id="submitBtn">
                        Pošaljite Zahtjev za Aktivaciju
                    </button>
                </form>
            </div>
        </div>
        <script>
            document.getElementById('registrationForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const submitBtn = document.getElementById('submitBtn');
                const loading = document.getElementById('loading');
                const messages = document.getElementById('messages');
                messages.innerHTML = '';
                const formData = {
                    naziv_kompanije: document.getElementById('nazivKompanije').value,
                    kontakt_osoba: document.getElementById('kontaktOsoba').value,
                    email: document.getElementById('email').value,
                    telefon: document.getElementById('telefon').value,
                    adresa: document.getElementById('adresa').value,
                    opis_poslovanja: document.getElementById('opisPoslovanja').value
                };
                if (!formData.naziv_kompanije || !formData.kontakt_osoba || 
                    !formData.email || !formData.opis_poslovanja) {
                    messages.innerHTML = `
                        <div class="error-message">
                            <strong>Greška:</strong> Molimo unesite sva obavezna polja označena sa *.
                        </div>
                    `;
                    return;
                }
                submitBtn.disabled = true;
                loading.style.display = 'block';
                try {
                    const response = await fetch('http://localhost:5004/api/tenant/request', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(formData)
                    });
                    const result = await response.json();
                    if (response.ok) {
                        messages.innerHTML = `
                            <div class="success-message">
                                <strong>Uspjeh!</strong> Vaš zahtjev je uspješno poslat.
                                <br><br>
                                <strong>Zahtjev ID:</strong> ${result.request_id}
                                <br><br>
                            </div>
                        `;
                        this.reset();
                    } else {
                        throw new Error(result.error || 'Greška prilikom slanja zahtjeva');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    messages.innerHTML = `
                        <div class="error-message">
                            <strong>Greška:</strong> ${error.message}
                            <br><br>
                            Molimo pokušajte ponovo.
                        </div>
                    `;
                } finally {
                    submitBtn.disabled = false;
                    loading.style.display = 'none';
                    messages.scrollIntoView({ behavior: 'smooth' });
                }
            });
            document.getElementById('email').addEventListener('blur', function() {
                const email = this.value;
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (email && !emailRegex.test(email)) {
                    this.style.borderColor = '#e53e3e';
                } else {
                    this.style.borderColor = '#e2e8f0';
                }
            });
        </script>
    </body>
    </html>
    ''')

if __name__ == "__main__":
    print("Pokretanje javne registracije na portu 3000...")
    app.run(host='0.0.0.0', port=3000, debug=True)