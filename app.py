import pika
import json
import os # Ortam değişkenlerini okumak için 'os' kütüphanesini ekledik
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- RabbitMQ Bağlantı Ayarları ---
# Render, RabbitMQ adresini bize bir URL olarak verir. Onu ortam değişkeninden okuyoruz.
# Eğer ortamda bu değişken yoksa (yani kendi bilgisayarımızda çalıştırıyorsak), localhost'a bağlanır.
rabbitmq_url = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/%2f')
RABBITMQ_QUEUE = 'mesaj_kuyrugu'

# Pika'nın bu URL'i kullanarak bağlantı kurmasını sağlıyoruz.
url_params = pika.URLParameters(rabbitmq_url)

# --- ÜRETİCİ (PRODUCER) KISMI ---
@app.route('/gonder', methods=['POST'])
def mesaj_gonder():
    user_message = request.json
    try:
        connection = pika.BlockingConnection(url_params) # Değişti: Artık URL parametrelerini kullanıyor
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        channel.basic_publish(exchange='',
                              routing_key=RABBITMQ_QUEUE,
                              body=json.dumps(user_message))
        connection.close()
        return jsonify({"status": "ok", "message": "Mesaj başarıyla gönderildi."})
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"status": "error", "message": "Mesaj gönderilemedi."}), 500

# --- TÜKETİCİ (CONSUMER) KISMI ---
@app.route('/mesaj-al', methods=['GET'])
def mesaj_al():
    try:
        connection = pika.BlockingConnection(url_params) # Değişti: Artık URL parametrelerini kullanıyor
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        method_frame, header_frame, body = channel.basic_get(queue=RABBITMQ_QUEUE, auto_ack=True)
        connection.close()
        if method_frame:
            message_data = json.loads(body.decode('utf-8'))
            return jsonify({"status": "ok", "message": message_data})
        else:
            return jsonify({"status": "no_message", "message": None})
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"status": "error", "message": "Mesajlar alınamadı."}), 500

# --- Sunucuyu Başlatma Kısmı ---
# Bu if bloğunu SİLİYORUZ çünkü artık sunucuyu Gunicorn başlatacak.
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)