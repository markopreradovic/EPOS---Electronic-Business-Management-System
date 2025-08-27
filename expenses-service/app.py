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
class Trosak:
    id: str
    naziv: str
    kategorija: str
    iznos: float
    datum: str
    opis: str
    status: str
    povezano_sa: str = None

class DatabaseManager:
    def __init__(self, db_path="../db/epos.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS troskovi
                       (
                           id TEXT PRIMARY KEY,
                           naziv TEXT NOT NULL,
                           kategorija TEXT NOT NULL,
                           iznos REAL NOT NULL,
                           datum TEXT NOT NULL,
                           opis TEXT,
                           status TEXT DEFAULT 'planiran',
                           povezano_sa TEXT,
                           datum_kreiranja TEXT
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS kategorije_troskova
                       (
                           id TEXT PRIMARY KEY,
                           naziv TEXT UNIQUE NOT NULL,
                           opis TEXT
                       )
                       ''')
        kategorije = [
            ('materijal', 'Troškovi materijala i sirovina'),
            ('usluga', 'Troškovi usluga od vanjskih dobavljača'),
            ('placa', 'Troškovi plača i beneficija zaposlenih'),
            ('rezija', 'Režijski troškovi (struja, voda, internet, kirija)'),
            ('marketing', 'Troškovi marketinga i reklame'),
            ('transport', 'Troškovi transporta i dostave'),
            ('ostalo', 'Ostali troškovi')
        ]
        for kat_id, opis in kategorije:
            cursor.execute(
                "INSERT OR IGNORE INTO kategorije_troskova (id, naziv, opis) VALUES (?, ?, ?)",
                (kat_id, kat_id.title(), opis)
            )
        conn.commit()
        conn.close()
        print(f"Database za troškove inicijalizovana na: {os.path.abspath(self.db_path)}")

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
            print(f"Query executed: {query} with params: {params}, result: {result}")
            return result
        except Exception as e:
            print(f"Database error: {e}")
            return []
        finally:
            conn.close()

class TrosakService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def kreiraj_trosak(self, naziv: str, kategorija: str, iznos: float,
                       datum: str, opis: str = "", povezano_sa: str = None) -> str:
        trosak_id = str(uuid.uuid4())
        datum_kreiranja = datetime.now().isoformat()
        kategorije = self.db.execute_query("SELECT id FROM kategorije_troskova WHERE id = ?", (kategorija,))
        if not kategorije:
            raise ValueError(f"Neispravna kategorija: {kategorija}")
        self.db.execute_query(
            """INSERT INTO troskovi
               (id, naziv, kategorija, iznos, datum, opis, status, povezano_sa, datum_kreiranja)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (trosak_id, naziv, kategorija, float(iznos), datum, opis, 'planiran', povezano_sa, datum_kreiranja)
        )
        print(f"Kreiran trošak: {naziv} - {iznos} KM")
        return trosak_id

    def azuriraj_trosak(self, trosak_id: str, naziv: str = None, kategorija: str = None,
                        iznos: float = None, datum: str = None, opis: str = None,
                        status: str = None, povezano_sa: str = None) -> bool:
        update_fields = []
        params = []
        if naziv is not None:
            update_fields.append("naziv = ?")
            params.append(naziv)
        if kategorija is not None:
            kategorije = self.db.execute_query("SELECT id FROM kategorije_troskova WHERE id = ?", (kategorija,))
            if not kategorije:
                raise ValueError(f"Neispravna kategorija: {kategorija}")
            update_fields.append("kategorija = ?")
            params.append(kategorija)
        if iznos is not None:
            update_fields.append("iznos = ?")
            params.append(float(iznos))
        if datum is not None:
            update_fields.append("datum = ?")
            params.append(datum)
        if opis is not None:
            update_fields.append("opis = ?")
            params.append(opis)
        if status is not None:
            if status not in ['planiran', 'izvršen', 'otkazan']:
                raise ValueError(f"Neispravan status: {status}")
            update_fields.append("status = ?")
            params.append(status)
        if povezano_sa is not None:
            update_fields.append("povezano_sa = ?")
            params.append(povezano_sa)
        if not update_fields:
            return False
        params.append(trosak_id)
        query = f"UPDATE troskovi SET {', '.join(update_fields)} WHERE id = ?"
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            print(f"Ažuriran trošak {trosak_id}: {success}")
            return success
        except Exception as e:
            print(f"Greška pri ažuriranju troška: {e}")
            return False

    def obrisi_trosak(self, trosak_id: str) -> bool:
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM troskovi WHERE id = ?", (trosak_id,))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            print(f"Obrisan trošak {trosak_id}: {success}")
            return success
        except Exception as e:
            print(f"Greška pri brisanju troška: {e}")
            return False

    def dobij_trosak(self, trosak_id: str) -> Optional[Dict]:
        result = self.db.execute_query("SELECT * FROM troskovi WHERE id = ?", (trosak_id,))
        if result:
            cols = ['id', 'naziv', 'kategorija', 'iznos', 'datum', 'opis', 'status', 'povezano_sa', 'datum_kreiranja']
            return dict(zip(cols, result[0]))
        return None

    def dobij_troskove(self, kategorija: str = None, status: str = None,
                       datum_od: str = None, datum_do: str = None) -> List[Dict]:
        query = "SELECT * FROM troskovi WHERE 1=1"
        params = []
        if kategorija:
            query += " AND kategorija = ?"
            params.append(kategorija)
        if status:
            query += " AND status = ?"
            params.append(status)
        if datum_od:
            query += " AND datum >= ?"
            params.append(datum_od)
        if datum_do:
            query += " AND datum <= ?"
            params.append(datum_do)
        query += " ORDER BY datum DESC"
        result = self.db.execute_query(query, params if params else None)
        cols = ['id', 'naziv', 'kategorija', 'iznos', 'datum', 'opis', 'status', 'povezano_sa', 'datum_kreiranja']
        troskovi = [dict(zip(cols, row)) for row in result]
        print(f"Dobijeno {len(troskovi)} troškova")
        return troskovi

    def dobij_kategorije(self) -> List[Dict]:
        result = self.db.execute_query("SELECT * FROM kategorije_troskova ORDER BY naziv")
        cols = ['id', 'naziv', 'opis']
        return [dict(zip(cols, row)) for row in result]

    def dobij_statistike(self, datum_od: str = None, datum_do: str = None) -> Dict:
        params = []
        conditions = []
        if datum_od:
            conditions.append("datum >= ?")
            params.append(datum_od)
        if datum_do:
            conditions.append("datum <= ?")
            params.append(datum_do)
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        query_kategorije = f"SELECT kategorija, status, SUM(iznos) as ukupno, COUNT(*) as broj FROM troskovi{where_clause} GROUP BY kategorija"
        result_kategorije = self.db.execute_query(query_kategorije, params if params else None)
        query_status = f"SELECT kategorija, status, SUM(iznos) as ukupno, COUNT(*) as broj FROM troskovi{where_clause} GROUP BY status"
        result_status = self.db.execute_query(query_status, params if params else None)
        query_ukupno = f"SELECT SUM(iznos) as ukupno, COUNT(*) as broj FROM troskovi{where_clause}"
        result_ukupno = self.db.execute_query(query_ukupno, params if params else None)
        statistike = {
            'po_kategorijama': [
                {'kategorija': row[0] if row and row[0] else 'Nepoznato',
                 'ukupno': float(row[2]) if row and row[2] else 0.0,
                 'broj': row[3] if row and row[3] else 0}
                for row in result_kategorije
            ],
            'po_statusu': [
                {'status': row[1] if row and row[1] else 'Nepoznato',
                 'ukupno': float(row[2]) if row and row[2] else 0.0,
                 'broj': row[3] if row and row[3] else 0}
                for row in result_status
            ],
            'ukupno': {
                'ukupno': float(result_ukupno[0][0]) if result_ukupno and len(result_ukupno) > 0 and result_ukupno[0][
                    0] is not None else 0.0,
                'broj': result_ukupno[0][1] if result_ukupno and len(result_ukupno) > 0 and result_ukupno[0][
                    1] is not None else 0
            }
        }
        print(f"Statistike: {statistike}")
        return statistike

app = Flask(__name__)
CORS(app)
db = DatabaseManager()
trosak_service = TrosakService(db)

@app.route('/api/troskovi', methods=['GET', 'POST'])
def troskovi_api():
    try:
        if request.method == 'POST':
            data = request.json
            print(f"Received expense data: {data}")
            if not data or not all(k in data for k in ['naziv', 'kategorija', 'iznos', 'datum']):
                return jsonify({'error': 'Nedostaju obavezni podaci (naziv, kategorija, iznos, datum)'}), 400
            trosak_id = trosak_service.kreiraj_trosak(
                data['naziv'], data['kategorija'], data['iznos'],
                data['datum'], data.get('opis', ''), data.get('povezano_sa')
            )
            return jsonify({'id': trosak_id, 'status': 'success'})
        else:
            kategorija = request.args.get('kategorija')
            status = request.args.get('status')
            datum_od = request.args.get('datum_od')
            datum_do = request.args.get('datum_do')
            troskovi = trosak_service.dobij_troskove(kategorija, status, datum_od, datum_do)
            return jsonify(troskovi)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': 'Greška na serveru'}), 500

@app.route('/api/troskovi/<trosak_id>', methods=['GET', 'PUT', 'DELETE'])
def trosak_api(trosak_id):
    try:
        if request.method == 'PUT':
            data = request.json
            if not data:
                return jsonify({'error': 'Nedostaju podaci'}), 400
            success = trosak_service.azuriraj_trosak(
                trosak_id,
                data.get('naziv'), data.get('kategorija'),
                data.get('iznos'), data.get('datum'),
                data.get('opis'), data.get('status'),
                data.get('povezano_sa')
            )
            return jsonify({'status': 'success' if success else 'failure'})
        elif request.method == 'DELETE':
            success = trosak_service.obrisi_trosak(trosak_id)
            return jsonify({'status': 'success' if success else 'failure'})
        else:
            trosak = trosak_service.dobij_trosak(trosak_id)
            if not trosak:
                return jsonify({'error': 'Trošak nije pronađen'}), 404
            return jsonify(trosak)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': 'Greška na serveru'}), 500

@app.route('/api/kategorije', methods=['GET'])
def kategorije_api():
    try:
        kategorije = trosak_service.dobij_kategorije()
        return jsonify(kategorije)
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': 'Greška na serveru'}), 500

@app.route('/api/troskovi/statistike', methods=['GET'])
def statistike_api():
    try:
        datum_od = request.args.get('datum_od')
        datum_do = request.args.get('datum_do')
        statistike = trosak_service.dobij_statistike(datum_od, datum_do)
        return jsonify(statistike)
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': f'Greška na serveru: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'trosak-service'})

if __name__ == "__main__":
    print("Pokretanje Trošak mikroservisa na portu 5003...")
    app.run(host='0.0.0.0', port=5003, debug=True)