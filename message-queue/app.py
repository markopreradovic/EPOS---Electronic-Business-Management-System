#!/usr/bin/env python3
from dbm import sqlite3

import pika
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Callable
import logging

class MessageQueueManager:
    def __init__(self, host='localhost', queue_name='epos_queue'):
        self.host = host
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.callbacks = {}
        self.setup_connection()

    def setup_connection(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            print(f"Connected to RabbitMQ at {self.host}")
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish_message(self, message_type: str, data: Dict[Any, Any],
                        routing_key: str = None):
        message = {
            'id': str(uuid.uuid4()),
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        if not routing_key:
            routing_key = self.queue_name
        self.channel.basic_publish(
            exchange='',
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                correlation_id=message['id']
            )
        )
        print(f"Published message: {message_type}")

    def register_callback(self, message_type: str, callback: Callable):
        self.callbacks[message_type] = callback

    def process_message(self, ch, method, properties, body):
        try:
            message = json.loads(body)
            message_type = message.get('type')
            if message_type in self.callbacks:
                self.callbacks[message_type](message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"Processed message: {message_type}")
            else:
                print(f"No callback for message type: {message_type}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            print(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.process_message
        )
        print("Waiting for messages...")
        self.channel.start_consuming()

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

class KlijentServiceMQ:
    def __init__(self, db_manager, mq_manager):
        self.db = db_manager
        self.mq = mq_manager
        self.mq.register_callback('create_client', self.handle_create_client)
        self.mq.register_callback('update_client', self.handle_update_client)
        self.mq.register_callback('delete_client', self.handle_delete_client)

    def handle_create_client(self, message):
        try:
            data = message['data']
            klijent_id = str(uuid.uuid4())
            datum = datetime.now().isoformat()
            postojeci = self.db.execute_query("SELECT id FROM klijenti WHERE email = ?", (data['email'],))
            if postojeci:
                self.mq.publish_message('client_creation_failed', {
                    'error': f"Klijent sa email-om {data['email']} već postoji",
                    'original_message_id': message['id']
                })
                return
            self.db.execute_query(
                "INSERT INTO klijenti (id, naziv, email, telefon, adresa, datum_kreiranja) VALUES (?, ?, ?, ?, ?, ?)",
                (klijent_id, data['naziv'], data['email'], data.get('telefon', ''), data.get('adresa', ''), datum)
            )
            self.mq.publish_message('client_created', {
                'klijent_id': klijent_id,
                'naziv': data['naziv'],
                'original_message_id': message['id']
            })
            print(f"Kreiran klijent preko MQ: {data['naziv']} sa ID: {klijent_id}")
        except Exception as e:
            self.mq.publish_message('client_creation_failed', {
                'error': str(e),
                'original_message_id': message['id']
            })

    def handle_update_client(self, message):
        try:
            data = message['data']
            klijent_id = data['klijent_id']
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE klijenti SET naziv = ?, email = ?, telefon = ?, adresa = ? WHERE id = ?",
                (data['naziv'], data['email'], data['telefon'], data['adresa'], klijent_id)
            )
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            if success:
                self.mq.publish_message('client_updated', {
                    'klijent_id': klijent_id,
                    'original_message_id': message['id']
                })
            else:
                self.mq.publish_message('client_update_failed', {
                    'error': 'Klijent nije pronađen',
                    'original_message_id': message['id']
                })
        except Exception as e:
            self.mq.publish_message('client_update_failed', {
                'error': str(e),
                'original_message_id': message['id']
            })

    def handle_delete_client(self, message):
        try:
            data = message['data']
            klijent_id = data['klijent_id']
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE klijenti SET aktivan = 0 WHERE id = ?", (klijent_id,))
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            if success:
                self.mq.publish_message('client_deleted', {
                    'klijent_id': klijent_id,
                    'original_message_id': message['id']
                })
            else:
                self.mq.publish_message('client_delete_failed', {
                    'error': 'Klijent nije pronađen',
                    'original_message_id': message['id']
                })
        except Exception as e:
            self.mq.publish_message('client_delete_failed', {
                'error': str(e),
                'original_message_id': message['id']
            })

class FakturaServiceMQ:
    def __init__(self, db_manager, mq_manager):
        self.db = db_manager
        self.mq = mq_manager
        self.mq.register_callback('create_invoice', self.handle_create_invoice)
        self.mq.register_callback('update_invoice', self.handle_update_invoice)
        self.mq.register_callback('client_deleted', self.handle_client_deleted)

    def handle_create_invoice(self, message):
        try:
            data = message['data']
            stavke = data['stavke']
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
                (faktura_id, data['klijent_id'], broj_fakture, datum, ukupan_iznos, "kreirana")
            )
            for stavka in stavke:
                stavka_id = str(uuid.uuid4())
                ukupno = float(stavka['kolicina']) * float(stavka['cijena'])
                self.db.execute_query(
                    "INSERT INTO stavke (id, faktura_id, naziv, kolicina, cijena, ukupno) VALUES (?, ?, ?, ?, ?, ?)",
                    (stavka_id, faktura_id, stavka['naziv'],
                     float(stavka['kolicina']), float(stavka['cijena']), ukupno)
                )
            self.mq.publish_message('invoice_created', {
                'faktura_id': faktura_id,
                'broj_fakture': broj_fakture,
                'klijent_id': data['klijent_id'],
                'iznos': ukupan_iznos,
                'original_message_id': message['id']
            })
            self.mq.publish_message('create_expense', {
                'naziv': f'Materijal za fakturu {broj_fakture}',
                'kategorija': 'materijal',
                'iznos': ukupan_iznos * 0.6,
                'datum': datum.split('T')[0],
                'opis': f'Automatski kreiran trošak za fakturu {broj_fakture}',
                'povezano_sa': faktura_id
            })
            print(f"Kreirana faktura preko MQ: {broj_fakture}")
        except Exception as e:
            self.mq.publish_message('invoice_creation_failed', {
                'error': str(e),
                'original_message_id': message['id']
            })

    def handle_client_deleted(self, message):
        try:
            klijent_id = message['data']['klijent_id']
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE fakture SET status = 'otkazana' WHERE klijent_id = ? AND status != 'placena'",
                (klijent_id,)
            )
            updated_count = cursor.rowcount
            conn.commit()
            conn.close()
            if updated_count > 0:
                print(f"Otkazano {updated_count} faktura za obrisanog klijenta")
        except Exception as e:
            print(f"Greška pri otkazivanju faktura: {e}")

class TrosakServiceMQ:
    def __init__(self, db_manager, mq_manager):
        self.db = db_manager
        self.mq = mq_manager
        self.mq.register_callback('create_expense', self.handle_create_expense)
        self.mq.register_callback('invoice_created', self.handle_invoice_created)

    def handle_create_expense(self, message):
        try:
            data = message['data']
            trosak_id = str(uuid.uuid4())
            datum_kreiranja = datetime.now().isoformat()
            kategorije = self.db.execute_query("SELECT id FROM kategorije_troskova WHERE id = ?", (data['kategorija'],))
            if not kategorije:
                raise ValueError(f"Neispravna kategorija: {data['kategorija']}")
            self.db.execute_query(
                """INSERT INTO troskovi
                   (id, naziv, kategorija, iznos, datum, opis, status, povezano_sa, datum_kreiranja)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (trosak_id, data['naziv'], data['kategorija'], float(data['iznos']),
                 data['datum'], data.get('opis', ''), 'planiran', data.get('povezano_sa'), datum_kreiranja)
            )
            self.mq.publish_message('expense_created', {
                'trosak_id': trosak_id,
                'naziv': data['naziv'],
                'iznos': data['iznos'],
                'original_message_id': message.get('id')
            })
            print(f"Kreiran trošak preko MQ: {data['naziv']} - {data['iznos']} KM")
        except Exception as e:
            self.mq.publish_message('expense_creation_failed', {
                'error': str(e),
                'original_message_id': message.get('id')
            })

    def handle_invoice_created(self, message):
        try:
            data = message['data']
            faktura_id = data['faktura_id']
            broj_fakture = data['broj_fakture']
            iznos = float(data['iznos'])
            transport_iznos = iznos * 0.1
            self.mq.publish_message('create_expense', {
                'naziv': f'Transport za {broj_fakture}',
                'kategorija': 'transport',
                'iznos': transport_iznos,
                'datum': datetime.now().strftime('%Y-%m-%d'),
                'opis': f'Automatski kreiran trošak transporta za fakturu {broj_fakture}',
                'povezano_sa': faktura_id
            })
        except Exception as e:
            print(f"Greška pri kreiranju automatskih troškova: {e}")

if __name__ == "__main__":
    mq = MessageQueueManager()
    mq.publish_message('create_client', {
        'naziv': 'Test Company d.o.o.',
        'email': 'test@company.com',
        'telefon': '+387 51 123 456',
        'adresa': 'Test adresa 123, Banja Luka'
    })
    mq.publish_message('create_invoice', {
        'klijent_id': 'some-client-id',
        'stavke': [
            {'naziv': 'Usluga 1', 'kolicina': 2, 'cijena': 100},
            {'naziv': 'Usluga 2', 'kolicina': 1, 'cijena': 50}
        ]
    })
    print("Poruke poslane u queue")