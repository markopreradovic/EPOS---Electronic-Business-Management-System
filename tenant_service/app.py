#!/usr/bin/env python3
import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from dataclasses import dataclass

try:
    import pika
except ImportError:
    print("Warning: pika not installed, MQ functionality disabled")
    pika = None

@dataclass
class Tenant:
    id: str
    naziv: str
    kontakt_email: str
    kontakt_telefon: str
    adresa: str
    status: str
    datum_kreiranja: str
    datum_aktivacije: str = None
    api_key: str = None

@dataclass
class TenantRequest:
    id: str
    naziv_kompanije: str
    kontakt_osoba: str
    email: str
    telefon: str
    adresa: str
    opis_poslovanja: str
    status: str
    datum_zahtjeva: str
    napomene: str = None

class TenantDatabaseManager:
    def __init__(self, db_path="../db/epos.db"):
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), db_path))
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        print(f"Database path: {self.db_path}")
        if not os.path.isfile(self.db_path):
            print(f"Database file {self.db_path} does not exist, creating it...")
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS tenants
                       (
                           id TEXT PRIMARY KEY,
                           naziv TEXT NOT NULL,
                           kontakt_email TEXT UNIQUE NOT NULL,
                           kontakt_telefon TEXT,
                           adresa TEXT,
                           status TEXT DEFAULT 'pending',
                           datum_kreiranja TEXT,
                           datum_aktivacije TEXT,
                           api_key TEXT UNIQUE
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS tenant_requests
                       (
                           id TEXT PRIMARY KEY,
                           naziv_kompanije TEXT NOT NULL,
                           kontakt_osoba TEXT NOT NULL,
                           email TEXT NOT NULL,
                           telefon TEXT,
                           adresa TEXT,
                           opis_poslovanja TEXT,
                           status TEXT DEFAULT 'submitted',
                           datum_zahtjeva TEXT,
                           napomene TEXT
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS api_usage
                       (
                           id TEXT PRIMARY KEY,
                           tenant_id TEXT,
                           endpoint TEXT,
                           method TEXT,
                           timestamp TEXT,
                           cost REAL,
                           FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS klijenti
                       (
                           id TEXT PRIMARY KEY,
                           tenant_id TEXT,
                           naziv TEXT NOT NULL,
                           email TEXT UNIQUE,
                           telefon TEXT,
                           adresa TEXT,
                           datum_kreiranja TEXT,
                           aktivan INTEGER DEFAULT 1,
                           FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS fakture
                       (
                           id TEXT PRIMARY KEY,
                           tenant_id TEXT,
                           klijent_id TEXT,
                           broj_fakture TEXT UNIQUE,
                           datum TEXT,
                           iznos REAL,
                           status TEXT,
                           FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                           FOREIGN KEY (klijent_id) REFERENCES klijenti(id)
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS stavke
                       (
                           id TEXT PRIMARY KEY,
                           tenant_id TEXT,
                           faktura_id TEXT,
                           naziv TEXT,
                           kolicina REAL,
                           cijena REAL,
                           ukupno REAL,
                           FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                           FOREIGN KEY (faktura_id) REFERENCES fakture(id)
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS troskovi
                       (
                           id TEXT PRIMARY KEY,
                           tenant_id TEXT,
                           naziv TEXT NOT NULL,
                           kategorija TEXT NOT NULL,
                           iznos REAL NOT NULL,
                           datum TEXT NOT NULL,
                           opis TEXT,
                           status TEXT DEFAULT 'planiran',
                           povezano_sa TEXT,
                           datum_kreiranja TEXT,
                           FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS kategorije_troskova
                       (
                           id TEXT PRIMARY KEY,
                           tenant_id TEXT,
                           naziv TEXT NOT NULL,
                           opis TEXT,
                           FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                       )
                       ''')
        cursor.execute("PRAGMA table_info(kategorije_troskova)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'tenant_id' not in columns:
            print("Adding tenant_id column to kategorije_troskova table...")
            cursor.execute('''
                           ALTER TABLE kategorije_troskova
                               ADD COLUMN tenant_id TEXT
                           ''')
        kategorije = [
            ('materijal', 'Troškovi materijala i sirovina'),
            ('usluga', 'Troškovi usluga od vanjskih dobavljača'),
            ('plata', 'Troškovi plača i beneficija zaposlenih'),
            ('rezija', 'Režijski troškovi (struja, voda, internet, kirija)'),
            ('marketing', 'Troškovi marketinga i reklame'),
            ('putovanje', 'Troškovi transporta i dostave'),
            ('ostalo', 'Ostali troškovi')
        ]
        cursor.execute("SELECT id FROM tenants")
        tenants = cursor.fetchall()
        for tenant_id in tenants:
            for kat_id, opis in kategorije:
                cursor.execute(
                    "INSERT OR IGNORE INTO kategorije_troskova (id, tenant_id, naziv, opis) VALUES (?, ?, ?, ?)",
                    (f"{tenant_id[0]}_{kat_id}", tenant_id[0], kat_id.title(), opis)
                )
        conn.commit()
        conn.close()
        print(f"Database initialized at: {self.db_path}")

    def execute_master_query(self, query, params=None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            conn.commit()
            return result
        except Exception as e:
            print(f"Database error: {e}")
            return []
        finally:
            conn.close()

class TenantService:
    def __init__(self, db_manager: TenantDatabaseManager):
        self.db = db_manager

    def submit_tenant_request(self, naziv_kompanije: str, kontakt_osoba: str,
                              email: str, telefon: str, adresa: str,
                              opis_poslovanja: str) -> str:
        request_id = str(uuid.uuid4())
        datum = datetime.now().isoformat()
        existing = self.db.execute_master_query(
            "SELECT id FROM tenant_requests WHERE email = ? OR EXISTS (SELECT 1 FROM tenants WHERE kontakt_email = ?)",
            (email, email)
        )
        if existing:
            raise ValueError(f"Email {email} je već registrovan")
        self.db.execute_master_query(
            """INSERT INTO tenant_requests
               (id, naziv_kompanije, kontakt_osoba, email, telefon, adresa, opis_poslovanja, datum_zahtjeva)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (request_id, naziv_kompanije, kontakt_osoba, email, telefon, adresa, opis_poslovanja, datum)
        )
        print(f"Submitted tenant request: {naziv_kompanije} - {email}")
        return request_id

    def get_pending_requests(self) -> List[Dict]:
        result = self.db.execute_master_query(
            "SELECT * FROM tenant_requests WHERE status = 'submitted' ORDER BY datum_zahtjeva DESC"
        )
        cols = ['id', 'naziv_kompanije', 'kontakt_osoba', 'email', 'telefon',
                'adresa', 'opis_poslovanja', 'status', 'datum_zahtjeva', 'napomene']
        return [dict(zip(cols, row)) for row in result]

    def get_all_requests(self) -> List[Dict]:
        result = self.db.execute_master_query(
            "SELECT * FROM tenant_requests ORDER BY datum_zahtjeva DESC"
        )
        cols = ['id', 'naziv_kompanije', 'kontakt_osoba', 'email', 'telefon',
                'adresa', 'opis_poslovanja', 'status', 'datum_zahtjeva', 'napomene']
        return [dict(zip(cols, row)) for row in result]

    def approve_tenant_request(self, request_id: str, napomene: str = None) -> str:
        result = self.db.execute_master_query(
            "SELECT * FROM tenant_requests WHERE id = ? AND status = 'submitted'",
            (request_id,)
        )
        if not result:
            raise ValueError("Zahtjev nije pronađen ili je već obrađen")
        request_data = result[0]
        tenant_id = str(uuid.uuid4())
        api_key = str(uuid.uuid4())
        datum = datetime.now().isoformat()
        self.db.execute_master_query(
            """INSERT INTO tenants
               (id, naziv, kontakt_email, kontakt_telefon, adresa, status, datum_kreiranja, datum_aktivacije, api_key)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tenant_id, request_data[1], request_data[3], request_data[4], request_data[5],
             'active', datum, datum, api_key)
        )
        self.db.execute_master_query(
            "UPDATE tenant_requests SET status = 'approved', napomene = ? WHERE id = ?",
            (napomene, request_id)
        )
        kategorije = [
            ('materijal', 'Troškovi materijala i sirovina'),
            ('usluga', 'Troškovi usluga od vanjskih dobavljača'),
            ('plata', 'Troškovi plača i beneficija zaposlenih'),
            ('rezija', 'Režijski troškovi (struja, voda, internet, kirija)'),
            ('marketing', 'Troškovi marketinga i reklame'),
            ('putovanje', 'Troškovi transporta i dostave'),
            ('ostalo', 'Ostali troškovi')
        ]
        for kat_id, opis in kategorije:
            self.db.execute_master_query(
                "INSERT OR IGNORE INTO kategorije_troskova (id, tenant_id, naziv, opis) VALUES (?, ?, ?, ?)",
                (f"{tenant_id}_{kat_id}", tenant_id, kat_id.title(), opis)
            )
        print(f"Approved tenant: {request_data[1]} - ID: {tenant_id}")
        return tenant_id

    def reject_tenant_request(self, request_id: str, napomene: str) -> bool:
        result = self.db.execute_master_query(
            "UPDATE tenant_requests SET status = 'rejected', napomene = ? WHERE id = ? AND status = 'submitted'",
            (napomene, request_id)
        )
        return True

    def get_tenant_by_api_key(self, api_key: str) -> Optional[Dict]:
        result = self.db.execute_master_query(
            "SELECT * FROM tenants WHERE api_key = ? AND status = 'active'",
            (api_key,)
        )
        if result:
            cols = ['id', 'naziv', 'kontakt_email', 'kontakt_telefon', 'adresa',
                    'status', 'datum_kreiranja', 'datum_aktivacije', 'api_key']
            return dict(zip(cols, result[0]))
        return None

    def get_all_tenants(self) -> List[Dict]:
        result = self.db.execute_master_query("SELECT * FROM tenants ORDER BY datum_kreiranja DESC")
        cols = ['id', 'naziv', 'kontakt_email', 'kontakt_telefon', 'adresa',
                'status', 'datum_kreiranja', 'datum_aktivacije', 'api_key']
        return [dict(zip(cols, row)) for row in result]

    def suspend_tenant(self, tenant_id: str, razlog: str) -> bool:
        try:
            result = self.db.execute_master_query(
                "UPDATE tenants SET status = 'suspended' WHERE id = ?",
                (tenant_id,)
            )
            print(f"Suspended tenant: {tenant_id} - {razlog}")
            return True
        except Exception as e:
            print(f"Error suspending tenant: {e}")
            return False

    def record_api_usage(self, tenant_id: str, endpoint: str, method: str, cost: float):
        usage_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        self.db.execute_master_query(
            "INSERT INTO api_usage (id, tenant_id, endpoint, method, timestamp, cost) VALUES (?, ?, ?, ?, ?, ?)",
            (usage_id, tenant_id, endpoint, method, timestamp, cost)
        )

class TenantMQHandler:
    def __init__(self, tenant_service: TenantService):
        self.tenant_service = tenant_service
        self.connection = None
        self.channel = None
        if pika:
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host='localhost')
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue='tenant_queue', durable=True)
                print("Connected to RabbitMQ for tenant management")
            except Exception as e:
                print(f"Failed to connect to RabbitMQ: {e}")
                self.connection = None
                self.channel = None

    def publish_tenant_event(self, event_type: str, tenant_data: Dict):
        if not self.channel:
            return
        message = {
            'id': str(uuid.uuid4()),
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': tenant_data
        }
        self.channel.basic_publish(
            exchange='',
            routing_key='tenant_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2) if pika else None
        )
        print(f"Published tenant event: {event_type}")

app = Flask(__name__)
CORS(app,
     origins=[
         'http://localhost:3000',
         'http://127.0.0.1:3000',
         'http://localhost:5000',
         'http://127.0.0.1:5000',
         'http://localhost:5005',
         'http://127.0.0.1:5005'
     ],
     allow_headers=['Content-Type', 'Authorization', 'X-Tenant-API-Key'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

db_manager = TenantDatabaseManager()
tenant_service = TenantService(db_manager)
mq_handler = TenantMQHandler(tenant_service)

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    allowed_origins = [
        'http://localhost:3000', 'http://127.0.0.1:3000',
        'http://localhost:5000', 'http://127.0.0.1:5000',
        'http://localhost:5005', 'http://127.0.0.1:5005'
    ]
    if origin in allowed_origins:
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
        allowed_origins = [
            'http://localhost:3000', 'http://127.0.0.1:3000',
            'http://localhost:5000', 'http://127.0.0.1:5000',
            'http://localhost:5005', 'http://127.0.0.1:5005'
        ]
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Tenant-API-Key'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
        return response

@app.before_request
def identify_tenant():
    if request.endpoint in ['health', 'submit_request', 'admin_requests', 'admin_approve', 'admin_reject',
                            'admin_tenants', 'admin_suspend', 'handle_preflight']:
        return
    api_key = request.headers.get('X-Tenant-API-Key')
    if not api_key:
        return jsonify({'error': 'Missing X-Tenant-API-Key header'}), 401
    tenant = tenant_service.get_tenant_by_api_key(api_key)
    if not tenant:
        return jsonify({'error': 'Invalid API key'}), 401
    if tenant['status'] != 'active':
        return jsonify({'error': f'Tenant status: {tenant["status"]}'}), 403
    request.tenant = tenant

@app.route('/api/tenant/request', methods=['POST', 'OPTIONS'])
def submit_request():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    try:
        data = request.json
        print(f"Received tenant request data: {data}")
        required = ['naziv_kompanije', 'kontakt_osoba', 'email', 'telefon', 'adresa', 'opis_poslovanja']
        if not data or not all(k in data for k in required):
            return jsonify({'error': f'Nedostaju podaci: {required}'}), 400
        request_id = tenant_service.submit_tenant_request(
            data['naziv_kompanije'], data['kontakt_osoba'], data['email'],
            data['telefon'], data['adresa'], data['opis_poslovanja']
        )
        print(f"Created tenant request with ID: {request_id}")
        return jsonify({'request_id': request_id, 'status': 'submitted'})
    except ValueError as e:
        print(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/admin/requests', methods=['GET', 'OPTIONS'])
def admin_requests():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    try:
        requests = tenant_service.get_all_requests()
        print(f"Returning {len(requests)} tenant requests")
        return jsonify(requests)
    except Exception as e:
        print(f"Error getting requests: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/admin/requests/<request_id>/approve', methods=['POST', 'OPTIONS'])
def admin_approve(request_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    try:
        data = request.json or {}
        napomene = data.get('napomene', '')
        tenant_id = tenant_service.approve_tenant_request(request_id, napomene)
        if mq_handler:
            mq_handler.publish_tenant_event('tenant_activated', {'tenant_id': tenant_id})
        return jsonify({'tenant_id': tenant_id, 'status': 'approved'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error approving request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/admin/requests/<request_id>/reject', methods=['POST', 'OPTIONS'])
def admin_reject(request_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    try:
        data = request.json or {}
        napomene = data.get('napomene', 'No reason provided')
        success = tenant_service.reject_tenant_request(request_id, napomene)
        return jsonify({'status': 'rejected'})
    except Exception as e:
        print(f"Error rejecting request: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/admin/tenants', methods=['GET', 'OPTIONS'])
def admin_tenants():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    try:
        tenants = tenant_service.get_all_tenants()
        print(f"Returning {len(tenants)} tenants")
        return jsonify(tenants)
    except Exception as e:
        print(f"Error getting tenants: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/admin/tenants/<tenant_id>/suspend', methods=['POST', 'OPTIONS'])
def admin_suspend(tenant_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    try:
        data = request.json or {}
        razlog = data.get('razlog', 'No reason provided')
        success = tenant_service.suspend_tenant(tenant_id, razlog)
        return jsonify({'status': 'suspended' if success else 'failed'})
    except Exception as e:
        print(f"Error suspending tenant: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/tenant/info', methods=['GET', 'OPTIONS'])
def tenant_info():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    try:
        tenant = request.tenant
        safe_data = {k: v for k, v in tenant.items() if k not in ['api_key']}
        return jsonify(safe_data)
    except Exception as e:
        print(f"Error getting tenant info: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'tenant-management',
        'rabbitmq_connected': mq_handler.connection is not None if mq_handler else False
    })

if __name__ == "__main__":
    print("🚀 Pokretanje Tenant Management servisa na portu 5004...")
    print("📝 CORS podešen za portove: 3000, 5000, 5005")
    app.run(host='0.0.0.0', port=5004, debug=True)