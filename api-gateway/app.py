#!/usr/bin/env python3
import os
import time
import json
import uuid
from datetime import datetime, timedelta
from threading import Thread, Lock
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import pika
import redis

class APIGateway:
    def __init__(self, rabbitmq_host='localhost', redis_host='localhost'):
        self.app = Flask(__name__)
        CORS(self.app)
        self.rabbitmq_host = rabbitmq_host
        self.connection = None
        self.channel = None
        self.setup_rabbitmq()
        try:
            self.redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            self.redis_enabled = True
            print("Redis connected successfully")
        except:
            self.redis_enabled = False
            print("Redis not available, caching disabled")
        self.pending_requests = {}
        self.lock = Lock()
        self.setup_routes()
        self.start_response_consumer()

    def setup_rabbitmq(self):
        max_retries = 10
        retry_count = 0
        while retry_count < max_retries:
            try:
                credentials_options = [
                    pika.PlainCredentials(
                        os.getenv('RABBITMQ_USER', 'epos_user'),
                        os.getenv('RABBITMQ_PASSWORD', 'epos_password')
                    ),
                    pika.PlainCredentials('guest', 'guest'),
                    None
                ]
                connection_established = False
                for i, credentials in enumerate(credentials_options):
                    try:
                        print(f"Trying connection attempt {i + 1}...")
                        connection_params = pika.ConnectionParameters(
                            host=self.rabbitmq_host,
                            credentials=credentials
                        )
                        self.connection = pika.BlockingConnection(connection_params)
                        self.channel = self.connection.channel()
                        queues = ['epos_queue', 'response_queue']
                        for queue in queues:
                            self.channel.queue_declare(queue=queue, durable=True)
                        print(f"Connected to RabbitMQ at {self.rabbitmq_host}")
                        print(f"Using credentials: {credentials.username if credentials else 'anonymous'}")
                        connection_established = True
                        break
                    except Exception as e:
                        print(f"Credentials attempt {i + 1} failed: {e}")
                        continue
                if connection_established:
                    break
                else:
                    raise Exception("All credential attempts failed")
            except Exception as e:
                retry_count += 1
                print(f"Failed to connect to RabbitMQ (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    print(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("\n" + "=" * 50)
                    print("RabbitMQ Connection Failed!")
                    print("Please check:")
                    print("1. RabbitMQ is running")
                    print("2. User credentials are correct")
                    print("3. User has proper permissions")
                    print("4. Network connectivity")
                    print("=" * 50)
                    raise

    def send_message_and_wait(self, message_type: str, data: Dict[str, Any],
                              timeout: int = 30) -> Dict[str, Any]:
        if not self.connection or self.connection.is_closed:
            return {'error': 'RabbitMQ connection not available'}
        correlation_id = str(uuid.uuid4())
        message = {
            'id': correlation_id,
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with self.lock:
            self.pending_requests[correlation_id] = {
                'response': None,
                'timestamp': datetime.now()
            }
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key='epos_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    correlation_id=correlation_id,
                    reply_to='response_queue'
                )
            )
        except Exception as e:
            with self.lock:
                self.pending_requests.pop(correlation_id, None)
            return {'error': f'Failed to send message: {e}'}
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                if correlation_id in self.pending_requests:
                    response = self.pending_requests[correlation_id]['response']
                    if response is not None:
                        self.pending_requests.pop(correlation_id)
                        return response
            time.sleep(0.1)
        with self.lock:
            self.pending_requests.pop(correlation_id, None)
        return {'error': 'Request timeout'}

    def start_response_consumer(self):
        def consume_responses():
            try:
                credentials_options = [
                    pika.PlainCredentials(
                        os.getenv('RABBITMQ_USER', 'epos_user'),
                        os.getenv('RABBITMQ_PASSWORD', 'epos_password')
                    ),
                    pika.PlainCredentials('guest', 'guest'),
                    None
                ]
                consumer_connection = None
                for credentials in credentials_options:
                    try:
                        consumer_connection = pika.BlockingConnection(
                            pika.ConnectionParameters(
                                host=self.rabbitmq_host,
                                credentials=credentials
                            )
                        )
                        break
                    except:
                        continue
                if not consumer_connection:
                    print("Failed to establish consumer connection")
                    return
                consumer_channel = consumer_connection.channel()
                consumer_channel.queue_declare(queue='response_queue', durable=True)
                def process_response(ch, method, properties, body):
                    try:
                        response = json.loads(body)
                        correlation_id = properties.correlation_id
                        if correlation_id:
                            with self.lock:
                                if correlation_id in self.pending_requests:
                                    self.pending_requests[correlation_id]['response'] = response
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        print(f"Error processing response: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                consumer_channel.basic_consume(
                    queue='response_queue',
                    on_message_callback=process_response
                )
                print("Started response consumer")
                consumer_channel.start_consuming()
            except Exception as e:
                print(f"Error in response consumer: {e}")
        consumer_thread = Thread(target=consume_responses, daemon=True)
        consumer_thread.start()

    def setup_routes(self):
        @self.app.route('/api/klijenti', methods=['GET', 'POST'])
        def klijenti_api():
            if request.method == 'POST':
                data = request.json
                if not data or not all(k in data for k in ['naziv', 'email']):
                    return jsonify({'error': 'Nedostaju obavezni podaci (naziv, email)'}), 400
                response = self.send_message_and_wait('create_client', data)
                if 'error' in response:
                    return jsonify(response), 400 if 'već postoji' in response['error'] else 500
                return jsonify({'id': response.get('klijent_id'), 'status': 'success'})
            else:
                return self.get_clients()

        @self.app.route('/api/klijenti/<klijent_id>', methods=['GET', 'PUT', 'DELETE'])
        def klijent_api(klijent_id):
            if request.method == 'PUT':
                data = request.json
                if not data:
                    return jsonify({'error': 'Nedostaju podaci'}), 400
                data['klijent_id'] = klijent_id
                response = self.send_message_and_wait('update_client', data)
                if 'error' in response:
                    return jsonify(response), 404 if 'nije pronađen' in response['error'] else 500
                return jsonify({'status': 'success'})
            elif request.method == 'DELETE':
                response = self.send_message_and_wait('delete_client', {'klijent_id': klijent_id})
                if 'error' in response:
                    return jsonify(response), 404 if 'nije pronađen' in response['error'] else 500
                return jsonify({'status': 'success'})
            else:
                return self.get_client(klijent_id)

        @self.app.route('/api/fakture', methods=['POST'])
        def fakture_api():
            data = request.json
            if not data or 'klijent_id' not in data or 'stavke' not in data:
                return jsonify({'error': 'Nedostaju obavezni podaci (klijent_id, stavke)'}), 400
            if not data['stavke']:
                return jsonify({'error': 'Faktura mora imati najmanje jednu stavku'}), 400
            response = self.send_message_and_wait('create_invoice', data)
            if 'error' in response:
                return jsonify(response), 400
            return jsonify({'id': response.get('faktura_id'), 'status': 'success'})

        @self.app.route('/api/fakture/<faktura_id>', methods=['GET', 'PUT', 'DELETE'])
        def faktura_api(faktura_id):
            if request.method == 'PUT':
                data = request.json
                if not data:
                    return jsonify({'error': 'Nedostaju podaci'}), 400
                data['faktura_id'] = faktura_id
                response = self.send_message_and_wait('update_invoice', data)
                if 'error' in response:
                    return jsonify(response), 404 if 'nije pronađen' in response['error'] else 500
                return jsonify({'status': 'success'})
            elif request.method == 'DELETE':
                response = self.send_message_and_wait('delete_invoice', {'faktura_id': faktura_id})
                if 'error' in response:
                    return jsonify(response), 404 if 'nije pronađen' in response['error'] else 500
                return jsonify({'status': 'success'})
            else:
                return self.get_invoice(faktura_id)

        @self.app.route('/api/klijenti/<klijent_id>/fakture', methods=['GET'])
        def klijent_fakture_api(klijent_id):
            return self.get_client_invoices(klijent_id)

        @self.app.route('/api/troskovi', methods=['GET', 'POST'])
        def troskovi_api():
            if request.method == 'POST':
                data = request.json
                if not data or not all(k in data for k in ['naziv', 'kategorija', 'iznos', 'datum']):
                    return jsonify({'error': 'Nedostaju obavezni podaci (naziv, kategorija, iznos, datum)'}), 400
                response = self.send_message_and_wait('create_expense', data)
                if 'error' in response:
                    return jsonify(response), 400
                return jsonify({'id': response.get('trosak_id'), 'status': 'success'})
            else:
                filters = {
                    'kategorija': request.args.get('kategorija'),
                    'status': request.args.get('status'),
                    'datum_od': request.args.get('datum_od'),
                    'datum_do': request.args.get('datum_do')
                }
                return self.get_expenses(filters)

        @self.app.route('/api/troskovi/<trosak_id>', methods=['GET', 'PUT', 'DELETE'])
        def trosak_api(trosak_id):
            if request.method == 'PUT':
                data = request.json
                if not data:
                    return jsonify({'error': 'Nedostaju podaci'}), 400
                data['trosak_id'] = trosak_id
                response = self.send_message_and_wait('update_expense', data)
                if 'error' in response:
                    return jsonify(response), 404 if 'nije pronađen' in response['error'] else 500
                return jsonify({'status': 'success'})
            elif request.method == 'DELETE':
                response = self.send_message_and_wait('delete_expense', {'trosak_id': trosak_id})
                if 'error' in response:
                    return jsonify(response), 404 if 'nije pronađen' in response['error'] else 500
                return jsonify({'status': 'success'})
            else:
                return self.get_expense(trosak_id)

        @self.app.route('/api/kategorije', methods=['GET'])
        def kategorije_api():
            return self.get_categories()

        @self.app.route('/api/troskovi/statistike', methods=['GET'])
        def statistike_api():
            filters = {
                'datum_od': request.args.get('datum_od'),
                'datum_do': request.args.get('datum_do')
            }
            return self.get_statistics(filters)

        @self.app.route('/health')
        def health():
            return jsonify({
                'status': 'ok',
                'service': 'api-gateway',
                'rabbitmq_connected': self.connection and not self.connection.is_closed,
                'redis_enabled': self.redis_enabled
            })

        @self.app.route('/api/system/status')
        def system_status():
            return jsonify({
                'gateway': 'running',
                'rabbitmq': 'connected' if self.connection and not self.connection.is_closed else 'disconnected',
                'redis': 'enabled' if self.redis_enabled else 'disabled',
                'pending_requests': len(self.pending_requests),
                'timestamp': datetime.now().isoformat()
            })

    def get_clients(self):
        try:
            import requests
            response = requests.get('http://klijent-service:5001/api/klijenti')
            return jsonify(response.json())
        except:
            return jsonify({'error': 'Servis nedostupan'}), 503

    def get_client(self, klijent_id):
        try:
            import requests
            response = requests.get(f'http://klijent-service:5001/api/klijenti/{klijent_id}')
            if response.status_code == 404:
                return jsonify({'error': 'Klijent nije pronađen'}), 404
            return jsonify(response.json())
        except:
            return jsonify({'error': 'Servis nedostupan'}), 503

    def get_invoice(self, faktura_id):
        try:
            import requests
            response = requests.get(f'http://faktura-service:5002/api/fakture/{faktura_id}')
            if response.status_code == 404:
                return jsonify({'error': 'Faktura nije pronađena'}), 404
            return jsonify(response.json())
        except:
            return jsonify({'error': 'Servis nedostupan'}), 503

    def get_client_invoices(self, klijent_id):
        try:
            import requests
            response = requests.get(f'http://faktura-service:5002/api/klijenti/{klijent_id}/fakture')
            return jsonify(response.json())
        except:
            return jsonify({'error': 'Servis nedostupan'}), 503

    def get_expenses(self, filters):
        try:
            import requests
            params = {k: v for k, v in filters.items() if v}
            response = requests.get('http://trosak-service:5003/api/troskovi', params=params)
            return jsonify(response.json())
        except:
            return jsonify({'error': 'Servis nedostupan'}), 503

    def get_expense(self, trosak_id):
        try:
            import requests
            response = requests.get(f'http://trosak-service:5003/api/troskovi/{trosak_id}')
            if response.status_code == 404:
                return jsonify({'error': 'Trošak nije pronađen'}), 404
            return jsonify(response.json())
        except:
            return jsonify({'error': 'Servis nedostupan'}), 503

    def get_categories(self):
        try:
            import requests
            response = requests.get('http://trosak-service:5003/api/kategorije')
            return jsonify(response.json())
        except:
            return jsonify({'error': 'Servis nedostupan'}), 503

    def get_statistics(self, filters):
        try:
            import requests
            params = {k: v for k, v in filters.items() if v}
            response = requests.get('http://trosak-service:5003/api/troskovi/statistike', params=params)
            return jsonify(response.json())
        except:
            return jsonify({'error': 'Servis nedostupan'}), 503

    def cleanup_pending_requests(self):
        cutoff = datetime.now() - timedelta(minutes=5)
        with self.lock:
            expired = [req_id for req_id, req_data in self.pending_requests.items()
                       if req_data['timestamp'] < cutoff]
            for req_id in expired:
                self.pending_requests.pop(req_id, None)
        print(f"Cleaned up {len(expired)} expired requests")

    def run(self, host='0.0.0.0', port=8080, debug=False):
        print(f"Starting API Gateway on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    try:
        gateway = APIGateway(rabbitmq_host=rabbitmq_host, redis_host=redis_host)
        import threading
        def cleanup_task():
            while True:
                time.sleep(300)
                gateway.cleanup_pending_requests()
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        gateway.run(debug=os.getenv('DEBUG', 'false').lower() == 'true')
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Failed to start API Gateway: {e}")
        exit(1)