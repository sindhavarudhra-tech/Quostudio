import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_CONFIG = {
    "dbname": "quotation_maker",
    "user": "rudhrasindhava",
    "password": "",
    "host": "127.0.0.1",
    "port": "5432"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def init_app_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotations (
            id SERIAL PRIMARY KEY,
            client_name VARCHAR(255) NOT NULL,
            bg_image VARCHAR(255),
            preloaded_items TEXT
        )
    ''')
    # Add document_data column safely if it doesn't exist yet
    cursor.execute('ALTER TABLE quotations ADD COLUMN IF NOT EXISTS document_data TEXT;')
    conn.commit()
    cursor.close()
    conn.close()

init_app_db()

@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM items ORDER BY botanical_name ASC')
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', items=items)

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM items ORDER BY botanical_name ASC')
    items = cursor.fetchall()
    cursor.execute('SELECT * FROM quotations ORDER BY id DESC')
    quotations = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dashboard.html', items=items, quotations=quotations)

@app.route('/new_quotation', methods=['POST'])
def new_quotation():
    client_name = request.form.get('client_name', 'Untitled Client')
    selected_items = request.form.getlist('selected_items')
    preloaded_items_str = ",".join(selected_items)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO quotations (client_name, preloaded_items) VALUES (%s, %s) RETURNING id',
        (client_name, preloaded_items_str)
    )
    quote_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('editor', quote_id=quote_id))

@app.route('/delete_quote/<int:quote_id>', methods=['POST'])
def delete_quote(quote_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM quotations WHERE id = %s', (quote_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/editor/<int:quote_id>')
def editor(quote_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM quotations WHERE id = %s', (quote_id,))
    quote = cursor.fetchone()
    
    cursor.execute('SELECT * FROM items ORDER BY botanical_name ASC')
    items = cursor.fetchall()

    cursor.execute('SELECT * FROM services ORDER BY id ASC')
    services = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('editor.html', quote=quote, items=items, services=services)

# --- NEW: Background Auto-Save Route ---
@app.route('/save_quote/<int:quote_id>', methods=['POST'])
def save_quote(quote_id):
    data = request.json.get('document_data')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE quotations SET document_data = %s WHERE id = %s', (data, quote_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/upload_bg/<int:quote_id>', methods=['POST'])
def upload_bg(quote_id):
    file = request.files.get('bg_image')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE quotations SET bg_image = %s WHERE id = %s', (filename, quote_id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('editor', quote_id=quote_id))

if __name__ == '__main__':
    app.run(debug=True, port=5000)