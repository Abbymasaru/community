from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
import sqlite3
from datetime import datetime
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_change_this_123'  # CHANGE THIS in production!

# ===================== DATABASE SETUP – FORCE FRESH EVERY TIME (dev fix) =====================
DB_FILE = 'community_fresh.db'

if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print(f"Deleted old DB file: {DB_FILE}")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# === YOUR ORIGINAL TABLES (unchanged) ===
c.execute('''CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fname TEXT NOT NULL,
    lname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    gender TEXT NOT NULL,
    dob TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT NOT NULL
)''')

c.execute('''CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    heading TEXT NOT NULL,
    image_url TEXT,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')

c.execute('''CREATE TABLE likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type TEXT CHECK(type IN ('like', 'dislike')),
    UNIQUE(news_id, user_id),
    FOREIGN KEY(news_id) REFERENCES news(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')

c.execute('''CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(news_id) REFERENCES news(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')

c.execute('''CREATE TABLE reels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    video_url TEXT NOT NULL,
    caption TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')

# ===================== NEW TABLES (only additions) =====================
# Likes for reels (separate table so we don't touch your original likes table)
c.execute('''CREATE TABLE reels_likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reel_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type TEXT CHECK(type IN ('like', 'dislike')),
    UNIQUE(reel_id, user_id),
    FOREIGN KEY(reel_id) REFERENCES reels(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')

# Comments for reels (separate table)
c.execute('''CREATE TABLE reels_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reel_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(reel_id) REFERENCES reels(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')

conn.commit()
conn.close()

print(f"Fresh database created: {DB_FILE} with all tables")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

@app.context_processor
def inject_user():
    if 'user_id' in session:
        conn = get_db()
        c = conn.cursor()
        user = c.execute("SELECT fname, lname FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        conn.close()
        if user:
            return dict(current_user={'name': f"{user['fname']}"})
    return dict(current_user=None)

# ===================== ROUTES (your original routes untouched) =====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sign', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        gender = request.form['gender']
        date = request.form['date']
        password = request.form['password']

        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (fname, lname, email, gender, dob, password, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (fname, lname, email, gender, date, hash_password(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('log'))
        except sqlite3.IntegrityError:
            flash("Email already registered!", "error")
        finally:
            conn.close()

    return render_template('sign.html')

@app.route('/log', methods=['GET', 'POST'])
def log():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        c = conn.cursor()
        user = c.execute("SELECT * FROM users WHERE email = ? AND password = ?",
                         (email, hash_password(password))).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            flash("Logged in successfully!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password!", "error")

    return render_template('log.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

# ===================== UPDATED HOME (only added recent reels + likes) =====================
@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('log'))

    conn = get_db()
    c = conn.cursor()
    
    # Your original recent news (unchanged)
    recent_news = c.execute("""
        SELECT n.*, u.fname || ' ' || u.lname AS author,
               (SELECT COUNT(*) FROM likes WHERE news_id = n.id AND type = 'like') AS likes,
               (SELECT COUNT(*) FROM likes WHERE news_id = n.id AND type = 'dislike') AS dislikes
        FROM news n JOIN users u ON n.user_id = u.id 
        ORDER BY n.created_at DESC LIMIT 3
    """).fetchall()

    # NEW: Recent reels for home page
    recent_reels = c.execute("""
        SELECT r.*, u.fname || ' ' || u.lname AS author
        FROM reels r JOIN users u ON r.user_id = u.id 
        ORDER BY r.created_at DESC LIMIT 3
    """).fetchall()

    conn.close()
    return render_template('home.html', recent_news=recent_news, recent_reels=recent_reels)

# ===================== YOUR ORIGINAL NEWS ROUTE (100% unchanged) =====================
@app.route('/news', methods=['GET', 'POST'])
def news():
    if 'user_id' not in session:
        return redirect(url_for('log'))

    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        heading = request.form['heading']
        image_url = request.form.get('image_url', '')
        description = request.form['description']
        c.execute("INSERT INTO news (user_id, heading, image_url, description, created_at) VALUES (?, ?, ?, ?, ?)",
                  (session['user_id'], heading, image_url, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        flash("News added successfully!", "success")

    all_news = c.execute("""
        SELECT n.*, u.fname || ' ' || u.lname AS author,
               (SELECT COUNT(*) FROM likes WHERE news_id = n.id AND type = 'like') AS likes,
               (SELECT COUNT(*) FROM likes WHERE news_id = n.id AND type = 'dislike') AS dislikes
        FROM news n JOIN users u ON n.user_id = u.id 
        ORDER BY n.created_at DESC
    """).fetchall()

    comments_dict = {}
    for post in all_news:
        comments = c.execute("""
            SELECT c.*, u.fname || ' ' || u.lname AS author 
            FROM comments c JOIN users u ON c.user_id = u.id 
            WHERE c.news_id = ? ORDER BY c.created_at ASC
        """, (post['id'],)).fetchall()
        comments_dict[post['id']] = comments

    conn.close()
    return render_template('news.html', news_list=all_news, comments_dict=comments_dict)

# ===================== YOUR ORIGINAL COMMENT & LIKE ROUTES (unchanged) =====================
@app.route('/api/comment', methods=['POST'])
def api_add_comment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    news_id = data.get('news_id')
    comment_text = data.get('comment_text', '').strip()
    
    if not news_id or not comment_text:
        return jsonify({'error': 'Empty comment'}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO comments (news_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
              (news_id, session['user_id'], comment_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    
    new_comment = c.execute("""
        SELECT c.*, u.fname || ' ' || u.lname AS author 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        WHERE c.id = last_insert_rowid()
    """).fetchone()
    conn.close()
    
    return jsonify({
        'success': True,
        'comment': {
            'author': new_comment['author'],
            'comment_text': new_comment['comment_text'],
            'created_at': new_comment['created_at']
        }
    })

@app.route('/like/<int:news_id>/<action>')
def like(news_id, action):
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Please log in to like/dislike."})

    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO likes (news_id, user_id, type) VALUES (?, ?, ?)",
                  (news_id, session['user_id'], action))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    c.execute("SELECT COUNT(*) FROM likes WHERE news_id = ? AND type = 'like'", (news_id,))
    likes = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM likes WHERE news_id = ? AND type = 'dislike'", (news_id,))
    dislikes = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({"success": True, "likes": likes, "dislikes": dislikes})

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    conn = get_db()
    c = conn.cursor()
    c.row_factory = sqlite3.Row

    c.execute("""SELECT id, heading, description, image_url, created_at 
                 FROM news WHERE id = ?""", (news_id,))
    post = c.fetchone()

    if post is None:
        abort(404)

    c.execute("SELECT COUNT(*) FROM likes WHERE news_id = ? AND type = 'like'", (news_id,))
    likes = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM likes WHERE news_id = ? AND type = 'dislike'", (news_id,))
    dislikes = c.fetchone()[0]

    conn.close()

    return render_template('news_detail.html', post=post, likes=likes, dislikes=dislikes)

# ===================== YOUR OTHER ORIGINAL ROUTES (unchanged) =====================
@app.route('/members')
def members():
    if 'user_id' not in session:
        return redirect(url_for('log'))
    conn = get_db()
    c = conn.cursor()
    members_list = c.execute("SELECT fname || ' ' || lname AS full_name, gender, dob, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('members.html', members=members_list)

@app.route('/donate')
def donate():
    return render_template('donate.html')

@app.route('/faqs')
def faqs():
    return render_template('faqs.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/photo')
def photo():
    return render_template('photo.html')

# ===================== NEW: REEL ROUTE (updated with likes + comments) =====================
@app.route('/reel', methods=['GET', 'POST'])
def reel():
    if 'user_id' not in session:
        return redirect(url_for('log'))

    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        video_url = request.form['video_url']
        caption = request.form['caption']
        c.execute("INSERT INTO reels (user_id, video_url, caption, created_at) VALUES (?, ?, ?, ?)",
                  (session['user_id'], video_url, caption, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        flash("Reel posted successfully!", "success")

    # NEW: Fetch reels with likes and comments (for the reel.html template)
    all_reels = c.execute("""
        SELECT r.*, u.fname || ' ' || u.lname AS author,
               (SELECT COUNT(*) FROM reels_likes WHERE reel_id = r.id AND type = 'like') AS likes,
               (SELECT COUNT(*) FROM reels_likes WHERE reel_id = r.id AND type = 'dislike') AS dislikes
        FROM reels r JOIN users u ON r.user_id = u.id 
        ORDER BY r.created_at DESC
    """).fetchall()

    comments_dict = {}
    for reel in all_reels:
        comments = c.execute("""
            SELECT rc.*, u.fname || ' ' || u.lname AS author 
            FROM reels_comments rc 
            JOIN users u ON rc.user_id = u.id 
            WHERE rc.reel_id = ? ORDER BY rc.created_at ASC
        """, (reel['id'],)).fetchall()
        comments_dict[reel['id']] = comments

    conn.close()
    return render_template('reel.html', reels_list=all_reels, comments_dict=comments_dict)

# ===================== NEW: REEL LIKE ROUTE =====================
@app.route('/like_reel/<int:reel_id>/<action>')
def like_reel(reel_id, action):
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Please log in to like/dislike."})

    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO reels_likes (reel_id, user_id, type) VALUES (?, ?, ?)",
                  (reel_id, session['user_id'], action))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # already voted

    c.execute("SELECT COUNT(*) FROM reels_likes WHERE reel_id = ? AND type = 'like'", (reel_id,))
    likes = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM reels_likes WHERE reel_id = ? AND type = 'dislike'", (reel_id,))
    dislikes = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({"success": True, "likes": likes, "dislikes": dislikes})

# ===================== NEW: REEL COMMENT API =====================
@app.route('/api/reel_comment', methods=['POST'])
def api_reel_comment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    reel_id = data.get('reel_id')
    comment_text = data.get('comment_text', '').strip()
    
    if not reel_id or not comment_text:
        return jsonify({'error': 'Empty comment'}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO reels_comments (reel_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
              (reel_id, session['user_id'], comment_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    
    new_comment = c.execute("""
        SELECT rc.*, u.fname || ' ' || u.lname AS author 
        FROM reels_comments rc 
        JOIN users u ON rc.user_id = u.id 
        WHERE rc.id = last_insert_rowid()
    """).fetchone()
    conn.close()
    
    return jsonify({
        'success': True,
        'comment': {
            'author': new_comment['author'],
            'comment_text': new_comment['comment_text'],
            'created_at': new_comment['created_at']
        }
    })

# ===================== YOUR ORIGINAL PROFILE (unchanged) =====================
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('log'))

    conn = get_db()
    c = conn.cursor()

    user_news = c.execute("""
        SELECT n.*, u.fname || ' ' || u.lname AS author 
        FROM news n JOIN users u ON n.user_id = u.id 
        WHERE n.user_id = ? 
        ORDER BY n.created_at DESC
    """, (session['user_id'],)).fetchall()

    user_reels = c.execute("""
        SELECT r.*, u.fname || ' ' || u.lname AS author 
        FROM reels r JOIN users u ON r.user_id = u.id 
        WHERE r.user_id = ? 
        ORDER BY r.created_at DESC
    """, (session['user_id'],)).fetchall()

    conn.close()
    return render_template('profile.html', user_news=user_news, user_reels=user_reels)

    # ===================== NEW: INDIVIDUAL REEL DETAIL PAGE =====================
@app.route('/reel/<int:reel_id>')
def reel_detail(reel_id):
    if 'user_id' not in session:
        return redirect(url_for('log'))

    conn = get_db()
    c = conn.cursor()
    c.row_factory = sqlite3.Row

    # Get the single reel
    c.execute("""
        SELECT r.*, u.fname || ' ' || u.lname AS author
        FROM reels r 
        JOIN users u ON r.user_id = u.id 
        WHERE r.id = ?
    """, (reel_id,))
    post = c.fetchone()

    if post is None:
        abort(404)

    # Likes count
    c.execute("SELECT COUNT(*) FROM reels_likes WHERE reel_id = ? AND type = 'like'", (reel_id,))
    likes = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM reels_likes WHERE reel_id = ? AND type = 'dislike'", (reel_id,))
    dislikes = c.fetchone()[0]

    # Comments
    comments = c.execute("""
        SELECT rc.*, u.fname || ' ' || u.lname AS author 
        FROM reels_comments rc 
        JOIN users u ON rc.user_id = u.id 
        WHERE rc.reel_id = ? 
        ORDER BY rc.created_at ASC
    """, (reel_id,)).fetchall()

    conn.close()
    return render_template('reel_detail.html', 
                           post=post, 
                           likes=likes, 
                           dislikes=dislikes, 
                           comments=comments)

# Feedback / code submission (unchanged)
UPLOAD_FOLDER = "received_codes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/feedback')
def feedback_page():
    return render_template('feedback.html')

@app.route('/submit-code', methods=['POST'])
def submit_code():
    username = request.form.get('username')
    title = request.form.get('title')
    language = request.form.get('language')
    code = request.form.get('code')

    if not code or not username:
        flash("Code or username missing!", "error")
        return redirect(url_for('feedback_page'))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = {"python": "py", "html": "html", "css": "css", "javascript": "js"}.get(language, "txt")
    filename = f"{timestamp}_{username}_{language}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"=== TITLE: {title}\n")
        f.write(f"=== USER: {username}\n")
        f.write(f"=== LANGUAGE: {language}\n")
        f.write(f"=== SENT: {datetime.now()}\n")
        f.write("="*50 + "\n\n")
        f.write(code)

    flash(f"Code received successfully! Saved as {filename}", "success")
    return redirect(url_for('feedback_page'))

if __name__ == '__main__':
    app.run(debug=True)