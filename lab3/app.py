import os
import json
import requests
from threading import Lock
from datetime import datetime, UTC

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import (create_engine, Column, Integer, String, Float, DateTime)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# --- CONFIG ---
# ЦБ РФ
CBR_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'
FETCH_INTERVAL_SECONDS = 60 # change to 60..300 (1-5 minutes)
MAX_POINTS = 20
DB_PATH = os.path.join('data', 'rates.db')

# --- Flask + SocketIO ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')
thread_lock = Lock()

# --- DB setup (SQLite + SQLAlchemy) ---
os.makedirs('data', exist_ok=True)
engine = create_engine(f'sqlite:///{DB_PATH}')
Base = declarative_base()

class RateSample(Base):
    __tablename__ = 'rate_samples'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True)
    char_code = Column(String, index=True)
    value = Column(Float)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# --- helper functions ---
def fetch_cbr_json(url=CBR_URL):
    """Возвращает распарсенный JSON с CBR API или None при ошибке."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        app.logger.warning('Failed to fetch CBR JSON: %s', e)
        return None

def save_snapshot(data):
    """Сохраняет текущие курсы в БД как одну точку (для каждой валюты отдельная запись)."""
    session = Session()
    now = datetime.now(UTC)
    samples = []
    for code, info in data.get('Valute', {}).items():
        sample = RateSample(timestamp=now, char_code=info['CharCode'], value=float(info['Value']))
        session.add(sample)
        samples.append({'char_code': info['CharCode'], 'value': float(info['Value'])})
    session.commit()

    # удалить старые точки, оставляем только последние MAX_POINTS для каждой валюты
    # это делается отдельно - более простой вариант: удаляем старые по количеству заметок на валюту
    session.close()
    return now, samples


def prune_db():
    """Оставляем в БД не более MAX_POINTS последних точек для каждой валюты."""
    session = Session()
    conn = engine.connect()
    # Получаем все distinct char_code
    codes = session.query(RateSample.char_code).distinct().all()
    for (code,) in codes:
        rows = session.query(RateSample).filter_by(char_code=code).order_by(RateSample.timestamp.desc()).all()
        if len(rows) > MAX_POINTS:
            to_delete = rows[MAX_POINTS:]
            for r in to_delete:
                session.delete(r)
    session.commit()
    session.close()


# --- scheduled job ---
def scheduled_fetch():
    data = fetch_cbr_json()
    if not data:
        return
    now, samples = save_snapshot(data)
    prune_db()
    # Emit update to connected clients: отправляем текущую таблицу и новую точку(и)
    try:
        socketio.emit('rates_snapshot', {'timestamp': now.isoformat(), 'samples': samples})
    except Exception:
        app.logger.exception('socketio emit failed')

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_fetch, 'interval', seconds=FETCH_INTERVAL_SECONDS, id='fetch_job')
scheduler.start()

# --- Flask routes ---
@app.route('/')
def index():
    return render_template('index.html')

# ЦБ РФ ручка
@app.route('/api/current')
def api_current():
    """Возвращает текущие данные из CBR (для начальной загрузки таблицы)."""
    data = fetch_cbr_json()
    if not data:
        return jsonify({'error': 'Failed to fetch data'}), 500
    # упростим: вернём список валют
    valutes = []
    for key, v in data.get('Valute', {}).items():
        valutes.append({
        'ID': v.get('ID'),
        'NumCode': v.get('NumCode'),
        'CharCode': v.get('CharCode'),
        'Nominal': v.get('Nominal'),
        'Name': v.get('Name'),
        'Value': v.get('Value'),
        'Previous': v.get('Previous')
        })
    return jsonify({'Date': data.get('Date'), 'PreviousDate': data.get('PreviousDate'), 'Valute': valutes})

@app.route('/api/history/<char_code>')
def api_history(char_code):
    """Возвращаем до MAX_POINTS точек для char_code из локальной БД."""
    session = Session()
    rows = session.query(RateSample).filter_by(char_code=char_code).order_by(RateSample.timestamp.asc()).all()
    res = [{'timestamp': r.timestamp.isoformat(), 'value': r.value} for r in rows]
    session.close()
    return jsonify(res)


# SocketIO events (optional)
@socketio.on('connect')
def handle_connect():
    app.logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    app.logger.info('Client disconnected')


if __name__ == '__main__':
    # при старте сделаем 1 раз fetch, чтобы была начальная точка
    scheduled_fetch()
    socketio.run(app, host='0.0.0.0', port=5020)


