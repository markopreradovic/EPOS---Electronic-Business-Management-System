#!/usr/bin/env python3
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from dataclasses import dataclass
import os

@dataclass
class Faktura:
    id: str
    klijent_id: str
    broj_fakture: str
    datum: str
    iznos: float
    status: str
    stavke: List[Dict] = None

@dataclass
class Stavka:
    id: str
    faktura_id: str
    naziv: str
    kolicina: float
    cijena: float
    ukupno: float

class DatabaseManager:
    def __init__(self, db_path="../db/epos.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS fakture (
                                                              id TEXT PRIMARY KEY,
                                                              klijent_id TEXT,
                                                              broj_fakture TEXT UNIQUE,
                                                              datum TEXT,
                                                              iznos REAL,
                                                              status TEXT,
                                                              FOREIGN KEY (klijent_id) REFERENCES klijenti(id)
                           )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS stavke (
                                                             id TEXT PRIMARY KEY,
                                                             faktura_id TEXT,
                                                             naziv TEXT,
                                                             kolicina REAL,
                                                             cijena REAL,
                                                             ukupno REAL,
                                                             FOREIGN KEY (faktura_id) REFERENCES fakture(id)
                           )
                       ''')
        conn.commit()
        conn.close()
        print(f"Database inicijalizovana na: {os.path.abspath(self.db_path)}")

    def execute_query(self, query, params=None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            conn.commit()
            print(f"Query executed: {query[:50]}... with params: {params}")
            return result
        except Exception as e:
            print(f"Database error: {e}")
            return []
        finally:
            conn.close()

class FakturaService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def kreiraj_fakturu(self, klijent_id: str, stavke: List[Dict]) -> str:
        if not stavke:
            raise ValueError("Faktura mora imati najmanje jednu stavku")
        faktura_id = str(uuid.uuid4())
        result = self.db.execute_query("SELECT COUNT(*) FROM fakture")
        count = result[0][0] if result else 0
        broj_fakture = f"FAK-{count + 1:06d}"
        datum = datetime.now().isoformat()
        ukupan_iznos = sum(float(s['kolicina']) * float(s['cijena']) for s in stavke)
        self.db.execute_query(
            "INSERT INTO fakture (id, klijent_id, broj_fakture, datum, iznos, status) VALUES (?, ?, ?, ?, ?, ?)",
            (faktura_id, klijent_id, broj_fakture, datum, ukupan_iznos, "kreirana")
        )
        for stavka in stavke:
            stavka_id = str(uuid.uuid4())
            ukupno = float(stavka['kolicina']) * float(stavka['cijena'])
            self.db.execute_query(
                "INSERT INTO stavke (id, faktura_id, naziv, kolicina, cijena, ukupno) VALUES (?, ?, ?, ?, ?, ?)",
                (stavka_id, faktura_id, stavka['naziv'],
                 float(stavka['kolicina']), float(stavka['cijena']), ukupno)
            )
        print(f"Kreirana faktura {broj_fakture} sa {len(stavke)} stavki")
        return faktura_id

    def azuriraj_fakturu(self, faktura_id: str, status: str = None, iznos: float = None) -> bool:
        update_fields = []
        params = []
        if status:
            update_fields.append("status = ?")
            params.append(status)
        if iznos is not None:
            update_fields.append("iznos = ?")
            params.append(float(iznos))
        if not update_fields:
            return False
        params.append(faktura_id)
        query = f"UPDATE fakture SET {', '.join(update_fields)} WHERE id = ?"
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            print(f"Ažurirana faktura {faktura_id}: {success}")
            return success
        except Exception as e:
            print(f"Greška pri ažuriranju fakture: {e}")
            return False

    def obrisi_fakturu(self, faktura_id: str) -> bool:
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stavke WHERE faktura_id = ?", (faktura_id,))
            cursor.execute("DELETE FROM fakture WHERE id = ?", (faktura_id,))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            print(f"Obrisana faktura {faktura_id}: {success}")
            return success
        except Exception as e:
            print(f"Greška pri brisanju fakture: {e}")
            return False

    def dobij_fakturu(self, faktura_id: str) -> Optional[Dict]:
        result = self.db.execute_query("SELECT * FROM fakture WHERE id = ?", (faktura_id,))
        if not result:
            return None
        faktura_cols = ['id', 'klijent_id', 'broj_fakture', 'datum', 'iznos', 'status']
        faktura = dict(zip(faktura_cols, result[0]))
        stavke_result = self.db.execute_query("SELECT * FROM stavke WHERE faktura_id = ?", (faktura_id,))
        stavka_cols = ['id', 'faktura_id', 'naziv', 'kolicina', 'cijena', 'ukupno']
        faktura['stavke'] = [dict(zip(stavka_cols, row)) for row in stavke_result]
        return faktura

    def dobij_fakture_klijenta(self, klijent_id: str) -> List[Dict]:
        result = self.db.execute_query("SELECT * FROM fakture WHERE klijent_id = ? ORDER BY datum DESC", (klijent_id,))
        cols = ['id', 'klijent_id', 'broj_fakture', 'datum', 'iznos', 'status']
        fakture = [dict(zip(cols, row)) for row in result]
        print(f"Dobijeno {len(fakture)} faktura za klijenta {klijent_id}")
        return fakture

    def dobij_sve_fakture(self) -> List[Dict]:
        result = self.db.execute_query("SELECT * FROM fakture ORDER BY datum DESC")
        cols = ['id', 'klijent_id', 'broj_fakture', 'datum', 'iznos', 'status']
        fakture = [dict(zip(cols, row)) for row in result]
        print(f"Dobijeno {len(fakture)} faktura")
        return fakture

app = Flask(__name__)
CORS(app)
db = DatabaseManager()
faktura_service = FakturaService(db)

@app.route('/api/fakture', methods=['GET', 'POST'])
def fakture_api():
    try:
        if request.method == 'POST':
            data = request.json
            print(f"Received invoice data: {data}")
            if not data or 'klijent_id' not in data or 'stavke' not in data:
                return jsonify({'error': 'Nedostaju obavezni podaci (klijent_id, stavke)'}), 400
            if not data['stavke']:
                return jsonify({'error': 'Faktura mora imati najmanje jednu stavku'}), 400
            faktura_id = faktura_service.kreiraj_fakturu(data['klijent_id'], data['stavke'])
            return jsonify({'id': faktura_id, 'status': 'success'})
        else:
            fakture = faktura_service.dobij_sve_fakture()
            return jsonify(fakture)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': 'Greška na serveru'}), 500

@app.route('/api/fakture/<faktura_id>', methods=['GET', 'PUT', 'DELETE'])
def faktura_api(faktura_id):
    try:
        if request.method == 'PUT':
            data = request.json
            if not data:
                return jsonify({'error': 'Nedostaju podaci'}), 400
            success = faktura_service.azuriraj_fakturu(
                faktura_id, data.get('status'), data.get('iznos')
            )
            return jsonify({'status': 'success' if success else 'failure'})
        elif request.method == 'DELETE':
            success = faktura_service.obrisi_fakturu(faktura_id)
            return jsonify({'status': 'success' if success else 'failure'})
        else:
            faktura = faktura_service.dobij_fakturu(faktura_id)
            if not faktura:
                return jsonify({'error': 'Faktura nije pronađena'}), 404
            return jsonify(faktura)
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': 'Greška na serveru'}), 500

@app.route('/api/klijenti/<klijent_id>/fakture', methods=['GET'])
def klijent_fakture_api(klijent_id):
    try:
        fakture = faktura_service.dobij_fakture_klijenta(klijent_id)
        return jsonify(fakture)
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': 'Greška na serveru'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'faktura-service'})

if __name__ == "__main__":
    print("Pokretanje Faktura mikroservisa na portu 5002...")
    app.run(host='0.0.0.0', port=5002, debug=True)