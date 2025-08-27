#!/usr/bin/env python3
import sqlite3
import json
import uuid
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from dataclasses import dataclass

class TenantIntegration:
    def __init__(self, tenant_service_url='http://localhost:5004'):
        self.tenant_service_url = tenant_service_url

    def validate_tenant(self, api_key: str) -> Optional[Dict]:
        try:
            response = requests.get(
                f'{self.tenant_service_url}/api/tenant/info',
                headers={'X-Tenant-API-Key': api_key}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error validating tenant: {e}")
            return None

    def record_api_usage(self, tenant_id: str, endpoint: str, method: str, cost: float):
        try:
            print(f"API Usage: {tenant_id} - {method} {endpoint} - Cost: {cost} KM")
        except Exception as e:
            print(f"Error recording API usage: {e}")

@dataclass
class Klijent:
    id: str
    naziv: str
    email: str
    telefon: str
    adresa: str
    datum_kreiranja: str
    aktivan: bool = True

class TenantDatabaseManager:
    def __init__(self, db_path="../db/epos.db"):
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), db_path))
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        print(f"Client Service Database path: {self.db_path}")
        if not os.path.isfile(self.db_path):
            print(f"Database file {self.db_path} does not exist, creating it...")
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS klijenti
                       (
                           id
                           TEXT
                           PRIMARY
                           KEY,
                           tenant_id
                           TEXT
                           NOT
                           NULL,
                           naziv
                           TEXT
                           NOT
                           NULL,
                           email
                           TEXT
                           NOT
                           NULL,
                           telefon
                           TEXT,
                           adresa
                           TEXT,
                           datum_kreiranja
                           TEXT,
                           aktivan
                           INTEGER
                           DEFAULT
                           1,
                           UNIQUE
                       (
                           tenant_id,
                           email
                       )
                           )
                       ''')
        cursor.execute("SELECT COUNT(*) FROM klijenti")
        existing_clients = cursor.fetchone()[0]
        print(f"Existing clients in database: {existing_clients}")
        if existing_clients == 0:
            print("No clients found, creating demo clients...")
            self.create_demo_clients(cursor)
        conn.commit()
        conn.close()
        print(f"Client database initialized at: {self.db_path}")

    def create_demo_clients(self, cursor):
        try:
            demo_tenant_id = "demo-tenant-12345"
            demo_api_key = "demo-api-key-12345"
            cursor.execute("SELECT COUNT(*) FROM tenants WHERE id = ?", (demo_tenant_id,))
            if cursor.fetchone()[0] == 0:
                print("Creating demo tenant...")
                cursor.execute('''
                               INSERT INTO tenants
                               (id, naziv, kontakt_email, kontakt_telefon, adresa, status, datum_kreiranja,
                                datum_aktivacije, api_key)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                               ''', (
                                   demo_tenant_id, "Demo Kompanija", "demo@example.com", "+387 51 000 000",
                                   "Demo Adresa, Banja Luka", "active", datetime.now().isoformat(),
                                   datetime.now().isoformat(), demo_api_key
                               ))
            test_clients = [
                ("Atlantik d.o.o.", "info@atlantik.ba", "+387 51 123 456", "Banja Luka, Srpska"),
                ("TechCorp Solutions", "contact@techcorp.ba", "+387 51 234 567", "Sarajevo, BiH"),
                ("Green Energy Ltd", "office@greenenergy.ba", "+387 51 345 678", "Mostar, BiH"),
                ("Digital Solutions", "hello@digitalsol.ba", "+387 51 456 789", "Tuzla, BiH"),
                ("Zdravstveni Centar", "info@zdravlje.ba", "+387 51 555 123", "Prijedor, Srpska")
            ]
            print(f"Creating {len(test_clients)} demo clients for demo tenant...")
            for i, (naziv, email, telefon, adresa) in enumerate(test_clients):
                klijent_id = str(uuid.uuid4())
                datum = datetime.now().isoformat()
                try:
                    cursor.execute('''
                                   INSERT INTO klijenti
                                   (id, tenant_id, naziv, email, telefon, adresa, datum_kreiranja, aktivan)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', (klijent_id, demo_tenant_id, naziv, email, telefon, adresa, datum, 1))
                    print(f"  ✅ Added client: {naziv} ({email})")
                except sqlite3.IntegrityError as e:
                    print(f"  ⚠️  Skipped duplicate client: {naziv} ({email}) - {e}")
            print(f"Demo tenant created with API key: {demo_api_key}")
        except Exception as e:
            print(f"Error creating demo clients: {e}")

    def execute_query(self, query: str, params=None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
                conn.commit()
            return result
        except Exception as e:
            print(f"Database error in execute_query: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            return [] if query.strip().upper().startswith('SELECT') else 0
        finally:
            conn.close()

class KlijentService:
    def __init__(self, db_manager: TenantDatabaseManager, tenant_integration: TenantIntegration):
        self.db = db_manager
        self.tenant_integration = tenant_integration

    def kreiraj_klijenta(self, tenant_id: str, naziv: str, email: str, telefon: str, adresa: str) -> str:
        klijent_id = str(uuid.uuid4())
        datum = datetime.now().isoformat()
        postojeci = self.db.execute_query(
            "SELECT id FROM klijenti WHERE email = ? AND tenant_id = ?",
            (email, tenant_id)
        )
        if postojeci:
            raise ValueError(f"Klijent sa email-om {email} već postoji")
        result = self.db.execute_query(
            "INSERT INTO klijenti (id, tenant_id, naziv, email, telefon, adresa, datum_kreiranja, aktivan) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (klijent_id, tenant_id, naziv, email, telefon, adresa, datum, 1)
        )
        if result > 0:
            self.tenant_integration.record_api_usage(tenant_id, '/api/klijenti', 'POST', 0.5)
            print(f"Kreiran klijent za tenant {tenant_id}: {naziv} sa ID: {klijent_id}")
            return klijent_id
        else:
            raise Exception("Greška pri kreiranju klijenta")

    def azuriraj_klijenta(self, tenant_id: str, klijent_id: str, naziv: str = None, email: str = None,
                          telefon: str = None, adresa: str = None) -> bool:
        try:
            updates = []
            params = []
            if naziv is not None:
                updates.append("naziv = ?")
                params.append(naziv)
            if email is not None:
                updates.append("email = ?")
                params.append(email)
            if telefon is not None:
                updates.append("telefon = ?")
                params.append(telefon)
            if adresa is not None:
                updates.append("adresa = ?")
                params.append(adresa)
            if not updates:
                return False
            query = f"UPDATE klijenti SET {', '.join(updates)} WHERE id = ? AND tenant_id = ?"
            params.extend([klijent_id, tenant_id])
            result = self.db.execute_query(query, params)
            success = result > 0
            if success:
                self.tenant_integration.record_api_usage(tenant_id, f'/api/klijenti/{klijent_id}', 'PUT', 0.0)
                print(f"Ažuriran klijent {klijent_id} za tenant {tenant_id}")
            return success
        except Exception as e:
            print(f"Greška pri ažuriranju: {e}")
            return False

    def obrisi_klijenta(self, tenant_id: str, klijent_id: str) -> bool:
        try:
            result = self.db.execute_query(
                "UPDATE klijenti SET aktivan = 0 WHERE id = ? AND tenant_id = ?",
                (klijent_id, tenant_id)
            )
            success = result > 0
            if success:
                self.tenant_integration.record_api_usage(tenant_id, f'/api/klijenti/{klijent_id}', 'DELETE', 0.0)
                print(f"Obrisan klijent {klijent_id} za tenant {tenant_id}")
            return success
        except Exception as e:
            print(f"Greška pri brisanju: {e}")
            return False

    def dobij_klijenta(self, tenant_id: str, klijent_id: str) -> Optional[Dict]:
        result = self.db.execute_query(
            "SELECT id, naziv, email, telefon, adresa, datum_kreiranja, aktivan FROM klijenti WHERE id = ? AND tenant_id = ? AND aktivan = 1",
            (klijent_id, tenant_id)
        )
        if result:
            cols = ['id', 'naziv', 'email', 'telefon', 'adresa', 'datum_kreiranja', 'aktivan']
            self.tenant_integration.record_api_usage(tenant_id, f'/api/klijenti/{klijent_id}', 'GET', 0.01)
            return dict(zip(cols, result[0]))
        return None

    def dobij_sve_klijente(self, tenant_id: str) -> List[Dict]:
        print(f"🔍 Searching for clients for tenant: {tenant_id}")
        result = self.db.execute_query(
            "SELECT id, naziv, email, telefon, adresa, datum_kreiranja, aktivan FROM klijenti WHERE tenant_id = ? AND aktivan = 1 ORDER BY naziv",
            (tenant_id,)
        )
        print(f"🔍 Raw database result: {result}")
        cols = ['id', 'naziv', 'email', 'telefon', 'adresa', 'datum_kreiranja', 'aktivan']
        klijenti = [dict(zip(cols, row)) for row in result]
        self.tenant_integration.record_api_usage(tenant_id, '/api/klijenti', 'GET', 0.01)
        print(f"✅ Returning {len(klijenti)} clients for tenant {tenant_id}")
        return klijenti

    def ensure_test_data_for_tenant(self, tenant_id: str):
        print(f"🔧 Checking test data for tenant: {tenant_id}")
        existing = self.db.execute_query(
            "SELECT COUNT(*) FROM klijenti WHERE tenant_id = ? AND aktivan = 1",
            (tenant_id,)
        )
        client_count = existing[0][0] if existing and existing[0] else 0
        print(f"📊 Found {client_count} existing clients for tenant {tenant_id}")
        if client_count == 0:
            print(f"➕ Creating test clients for tenant {tenant_id}...")
            test_clients = [
                ("Demo Klijent 1", f"demo1.{tenant_id[:8]}@test.ba", "+387 51 111 111", "Banja Luka"),
                ("Demo Klijent 2", f"demo2.{tenant_id[:8]}@test.ba", "+387 51 222 222", "Sarajevo"),
                ("Demo Klijent 3", f"demo3.{tenant_id[:8]}@test.ba", "+387 51 333 333", "Mostar")
            ]
            created_count = 0
            for naziv, email, telefon, adresa in test_clients:
                try:
                    self.kreiraj_klijenta(tenant_id, naziv, email, telefon, adresa)
                    created_count += 1
                    print(f"  ✅ Created: {naziv}")
                except Exception as e:
                    print(f"  ❌ Error creating {naziv}: {e}")
            print(f"✅ Created {created_count} test clients for tenant {tenant_id}")

app = Flask(__name__)
#Problem solucija!!!
CORS(app,
     origins=['http://localhost:5000', 'http://127.0.0.1:5000'],
     allow_headers=['Content-Type', 'Authorization', 'X-Tenant-API-Key'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

db_manager = TenantDatabaseManager()
tenant_integration = TenantIntegration()
klijent_service = KlijentService(db_manager, tenant_integration)

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in ['http://localhost:5000', 'http://127.0.0.1:5000']:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Tenant-API-Key'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin')
        if origin in ['http://localhost:5000', 'http://127.0.0.1:5000']:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Tenant-API-Key'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
        return response

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Tenant-API-Key')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/klijenti', methods=['OPTIONS'])
@app.route('/api/klijenti/<klijent_id>', methods=['OPTIONS'])
def handle_options(klijent_id=None):
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Tenant-API-Key')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.before_request
def authenticate_tenant():
    if request.endpoint == 'health':
        return
    api_key = request.headers.get('X-Tenant-API-Key')
    if not api_key:
        print("❌ Missing X-Tenant-API-Key header")
        return jsonify({'error': 'Missing X-Tenant-API-Key header'}), 401
    tenant_info = tenant_integration.validate_tenant(api_key)
    if not tenant_info:
        print(f"❌ Invalid tenant for API key: {api_key[:8]}...")
        return jsonify({'error': 'Invalid or inactive tenant'}), 401
    request.tenant = tenant_info
    print(f"✅ Authenticated tenant: {tenant_info['naziv']} ({tenant_info['id']})")
    klijent_service.ensure_test_data_for_tenant(tenant_info['id'])

@app.route('/api/klijenti', methods=['GET', 'POST'])
def klijenti_api():
    try:
        tenant_id = request.tenant['id']
        print(f"🌐 Processing {request.method} request for tenant: {tenant_id}")
        if request.method == 'POST':
            data = request.json
            print(f"📝 Received data for tenant {tenant_id}: {data}")
            if not data or not all(k in data for k in ['naziv', 'email']):
                return jsonify({'error': 'Nedostaju obavezni podaci (naziv, email)'}), 400
            klijent_id = klijent_service.kreiraj_klijenta(
                tenant_id, data['naziv'], data['email'],
                data.get('telefon', ''), data.get('adresa', '')
            )
            return jsonify({'id': klijent_id, 'status': 'success'})
        else:
            klijenti = klijent_service.dobij_sve_klijente(tenant_id)
            print(f"📤 Returning {len(klijenti)} clients for tenant {tenant_id}")
            return jsonify(klijenti)
    except ValueError as e:
        print(f"❌ Validation Error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"❌ API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Greška na serveru'}), 500

@app.route('/api/klijenti/<klijent_id>', methods=['GET', 'PUT', 'DELETE'])
def klijent_api(klijent_id):
    try:
        tenant_id = request.tenant['id']
        print(f"🌐 Processing {request.method} request for tenant: {tenant_id}, client: {klijent_id}")
        if request.method == 'PUT':
            data = request.json
            if not data:
                return jsonify({'error': 'Nedostaju podaci'}), 400
            success = klijent_service.azuriraj_klijenta(
                tenant_id, klijent_id,
                data.get('naziv'), data.get('email'),
                data.get('telefon'), data.get('adresa')
            )
            return jsonify({'status': 'success' if success else 'failure'})
        elif request.method == 'DELETE':
            success = klijent_service.obrisi_klijenta(tenant_id, klijent_id)
            return jsonify({'status': 'success' if success else 'failure'})
        else:
            klijent = klijent_service.dobij_klijenta(tenant_id, klijent_id)
            if not klijent:
                return jsonify({'error': 'Klijent nije pronađen'}), 404
            return jsonify(klijent)
    except Exception as e:
        print(f"❌ API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Greška na serveru'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'klijent-service-multitenant'})

@app.route('/debug/database')
def debug_database():
    try:
        all_clients = db_manager.execute_query("SELECT * FROM klijenti")
        all_tenants = db_manager.execute_query("SELECT * FROM tenants")
        return jsonify({
            'total_clients': len(all_clients),
            'total_tenants': len(all_tenants),
            'clients': all_clients[:10],
            'tenants': all_tenants
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    print("🚀 Pokretanje Multitenant Klijent mikroservisa na portu 5001...")
    app.run(host='0.0.0.0', port=5001, debug=True)