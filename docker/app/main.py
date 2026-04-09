import os
import time
import logging
import psycopg2
from flask import Flask, jsonify

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# DB helper
def get_connection():
    """
    Devuelve una conexión a Postgres.
    Reintenta hasta 10 veces con 2s de espera.
    """
    db_url = os.environ.get("DATABASE_URL")
    for attempt in range(1, 11):
        try:
            conn = psycopg2.connect(db_url)
            return conn
        except psycopg2.OperationalError as e:
            logger.warning("DB not ready (attempt %d/10): %s", attempt, e)
            time.sleep(2)
    raise RuntimeError("Could not connect to the DB after 10 attemps.")


def init_db():
    """
    Crea la tabla items si no existe e inserta datos de ejemplo
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        );
    """)
    # Evita duplicados en cada arranque
    cur.execute("SELECT COUNT(*) FROM items;")
    if cur.fetchone()[0] == 0:
        for item in ["Docker", "Ansible", "Terraform", "Kubernetes"]:
            cur.execute("INSERT INTO items (name) VALUES (%s);", (item,))
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Database initialised.")


# Endpoints
@app.route("/health")
def health():
    """Health check: lo usan Docker, el pipeline y los balanceadores de carga"""
    return jsonify({"status": "ok"}), 200


@app.route("/items")
def get_items():
    """Devuelve todos los items almacenados en la DB"""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM items ORDER BY id;")
            rows = cur.fetchall()
        conn.close()
        return jsonify([{"id": r[0], "name": r[1]} for r in rows]), 200
    except Exception as exc:
        logger.error("Error fetching items: %s", exc)
        return jsonify({"error": "Database error"}), 500


@app.route("/items/<int:item_id>")
def get_item(item_id):
    """Devuelve un item por ID."""
    if item_id <= 0:
        return jsonify({"error": "Invalid ID"}), 400
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM items WHERE id = %s;", (item_id,))
            row = cur.fetchone()
        conn.close()
        if row is None:
            return jsonify({"error": "Item not found"}), 404
        return jsonify({"id": row[0], "name": row[1]}), 200
    except Exception as exc:
        logger.error("Error fetching item %d: %s", item_id, exc)
        return jsonify({"error": "Database error"}), 500


@app.route("/")
def index():
    """Landing page"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DevOps Lab</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-950 text-white min-h-screen flex flex-col items-center justify-center p-8">
    <div class="w-full max-w-lg">
        <h1 class="text-3xl font-bold mb-2">🚀 DevOps Lab</h1>
        <p class="text-gray-400 mb-8">Flask · PostgreSQL · Docker · Ansible · Terraform</p>

        <div class="bg-gray-800 rounded-xl p-6 mb-6">
            <h2 class="text-lg font-semibold mb-4">Stack items from Postgres</h2>
            <ul id="items" class="space-y-2 text-gray-300">
                <li class="text-gray-500 italic">Loading...</li>
            </ul>
        </div>

        <div class="bg-gray-800 rounded-xl p-6">
            <h2 class="text-lg font-semibold mb-2">API Health</h2>
            <span id="health" class="text-gray-500 italic">Checking...</span>
        </div>
    </div>

    <script>
        fetch('/items')
            .then(r => r.json())
            .then(data => {
                const ul = document.getElementById('items');
                ul.innerHTML = data.map(i =>
                    `<li class="flex items-center gap-2">
                        <span class="w-6 h-6 bg-indigo-600 rounded text-xs flex items-center justify-center">${i.id}</span>
                        ${i.name}
                    </li>`
                ).join('');
            });

        fetch('/health')
            .then(r => r.json())
            .then(data => {
                const el = document.getElementById('health');
                el.innerHTML = `<span class="text-green-400 font-semibold">● ${data.status}</span>`;
            });
    </script>
</body>
</html>"""


# Arranque
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
