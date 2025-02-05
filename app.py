from flask import Flask, render_template, request, jsonify, g, redirect, url_for, session
from pyaspeller import YandexSpeller
from deepmultilingualpunctuation import PunctuationModel
from gramformer import Gramformer
import language_tool_python
import re
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'corrections.db' 

# SQLite database setup
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                corrected_output TEXT NOT NULL,
                total_errors INTEGER,
                capitalization_errors INTEGER,
                spelling_errors INTEGER,
                grammar_errors INTEGER,
                punctuation_errors INTEGER,
                detailed_errors TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

         # Add a users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        db.commit()

# Save data to SQLite
def save_correction_to_db(user_input, corrected_output, counts, corrections):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO corrections 
        (user_input, corrected_output, total_errors, capitalization_errors,
         spelling_errors, grammar_errors, punctuation_errors, detailed_errors)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_input,
        corrected_output,
        counts['all'],
        counts['capitalization'],
        counts['spelling'],
        counts['grammar'],
        counts['punctuation'],
        json.dumps(corrections)
    ))
    db.commit()

# Initialize modules
speller = YandexSpeller()
punctuation_model = PunctuationModel()
gf = Gramformer(models=1)
tool = language_tool_python.LanguageTool('en-US')

# Correction functions
def correct_spelling(text):
    corrected_text = speller.spelled(text)
    corrections = []

    original_words = text.split()
    corrected_words = corrected_text.split()

    for original, corrected in zip(original_words, corrected_words):
        if original != corrected:
            corrections.append((original, corrected))

    return corrections, corrected_text

def correct_punctuation(text):
    corrected_text = punctuation_model.restore_punctuation(text)
    corrections = []

    original_words = text.split()
    corrected_words = corrected_text.split()

    for original, corrected in zip(original_words, corrected_words):
        if original != corrected:
            corrections.append((original, corrected))

    return corrections, corrected_text

def correct_grammar(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    corrections = []
    corrected_text_list = []

    for sentence in sentences:
        corrected_sentence = gf.correct(sentence)
        if isinstance(corrected_sentence, set):
            corrected_sentence = next(iter(corrected_sentence))

        corrected_text_list.append(corrected_sentence)
        original_words = sentence.split()
        corrected_words = corrected_sentence.split()

        i, j = 0, 0
        while i < len(original_words) or j < len(corrected_words):
            if i < len(original_words) and j < len(corrected_words):
                if original_words[i] != corrected_words[j]:
                    # Condition 1: Word modified
                    if original_words[i] not in corrected_words[j:]:
                        corrections.append((original_words[i], corrected_words[j]))
                        i += 1
                        j += 1
                    # Condition 2: New word added
                    else:
                        corrections.append((" ", corrected_words[j]))
                        j += 1
                else:
                    i += 1
                    j += 1
            elif j < len(corrected_words): 
                # Condition 2: New word added
                corrections.append((" ", corrected_words[j]))
                j += 1
            else:
                # Condition 3: Word removed
                corrections.append((original_words[i], " "))
                i += 1

    corrected_text = " ".join(corrected_text_list)
    return corrections, corrected_text

def correct_capitalization(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    corrections = []
    corrected_sentences = []

    for sentence in sentences:
        if not sentence:
            continue

        words = sentence.split()
        first_word = words[0]
        if first_word[0].islower():
            corrected_word = first_word.capitalize()
            corrections.append((first_word, corrected_word))
            words[0] = corrected_word

        sentence = " ".join(words)
        matches = tool.check(sentence)
        for match in matches:
            if match.replacements:
                start, end = match.offset, match.offset + match.errorLength
                incorrect_text = sentence[start:end]
                suggested_replacement = match.replacements[0]
                corrections.append((incorrect_text, suggested_replacement))
                sentence = sentence[:start] + suggested_replacement + sentence[end:]

        corrected_sentences.append(sentence)

    corrected_text = " ".join(corrected_sentences)
    return corrections, corrected_text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/correct', methods=['POST'])
def correct_text():
    text = request.form['text']
    corrections = {
        "all": [],
        "capitalization": [],
        "spelling": [],
        "grammar": [],
        "punctuation": []
    }
    counts = {
        "capitalization": 1,
        "spelling": 1,
        "grammar": 1,
        "punctuation": 1,
        "all": 0
    }

    # Apply corrections in order
    spell_corrections, text = correct_spelling(text)
    corrections["spelling"].extend(spell_corrections)
    counts["spelling"] = len(spell_corrections)

    punct_corrections, text = correct_punctuation(text)
    corrections["punctuation"].extend(punct_corrections)
    counts["punctuation"] = len(punct_corrections)

    grammar_corrections, text = correct_grammar(text)
    corrections["grammar"].extend(grammar_corrections)
    counts["grammar"] = len(grammar_corrections)

    capital_corrections, text = correct_capitalization(text)
    corrections["capitalization"].extend(capital_corrections)
    counts["capitalization"] = len(capital_corrections)

    # Combine all corrections and calculate total errors
    for key in corrections:
        if key != "all":
            corrections["all"].extend(corrections[key])

    counts["all"] = counts["capitalization"] + counts["spelling"] + counts["grammar"] + counts["punctuation"]

    save_correction_to_db(request.form['text'], text, counts, corrections)

    return jsonify({
        'corrections': corrections,
        'counts': counts,
        'corrected_text': text
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and user[2] == password: 
            session['username'] = user[1] 
            return redirect(url_for('view_corrections'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        db.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/view-corrections',  methods=['GET'])
def view_corrections():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, user_input, created_at 
        FROM corrections 
        ORDER BY created_at ASC
    ''')
    rows = cursor.fetchall()
    return render_template('view_corrections.html', rows=rows, username=session.get('username'))

@app.route('/correction-details/<int:correction_id>')
def correction_details(correction_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM corrections WHERE id = ?', (correction_id,))
    correction = cursor.fetchone()
    
    if correction:
        return jsonify({
            'detailed_errors': json.loads(correction[8])
        })
    
    return jsonify({'error': 'Correction not found'}), 404

@app.route('/correction-description/<int:correction_id>')
def correction_description(correction_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM corrections WHERE id = ?', (correction_id,))
    correction = cursor.fetchone()
    
    if not correction:
        return "Correction not found", 404

    # Parse the detailed errors from JSON
    detailed_errors = json.loads(correction[8]) if correction[8] else {}

    return render_template('description.html', 
        correction={
            'id': correction[0],
            'original': correction[1],
            'corrected': correction[2],
            'counts': {
                'total': correction[3],
                'capitalization': correction[4],
                'spelling': correction[5],
                'grammar': correction[6],
                'punctuation': correction[7]
            },
            'details': detailed_errors
        }
    )

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ""
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime(format)

if __name__ == "__main__":
    init_db()   
    app.run(debug=True)
 