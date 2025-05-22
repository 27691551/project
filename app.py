from flask import Flask,render_template,request,url_for,redirect
import sqlite3


app = Flask(__name__)


DB_NAME = 'membership.db'


def get_db_connection():
    """獲取資料庫連接"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db()-> None:
    """初始化資料庫"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS members (
            iid INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            phone TEXT,
            birthdate TEXT
        )
    ''')
    c.execute('''
        INSERT OR IGNORE INTO members (username, email, password, phone, birthdate)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin', 'admin@example.com', 'admin123', '0912345678', '1990-01-01'))
    conn.commit()
    conn.close()


@app.template_filter('add_stars')
def add_stars(s: str) -> str:
    """自訂過濾器"""
    return f'★{s}★!'


@app.route("/")
def index() -> str:
    """首頁"""
    return render_template("index.html")


@app.route("/register",methods = ['GET','POST'])
def register() -> str:
    """註冊頁面"""
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')
        phone = request.form.get('phone')
        birthdate = request.form.get('birthdate')

        if not username or not email or not password:
            return render_template('error.html', message="請輸入用戶名、電子郵件和密碼")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM members WHERE username = ?", (username,))
                if c.fetchone():
                    return render_template('error.html', message="用戶名已存在")
                c.execute("INSERT INTO members (username, email, password, phone, birthdate) "
                      "VALUES (?, ?, ?, ?, ?)",
                      (username, email, password, phone, birthdate))
                conn.commit()
        except sqlite3.Error as e:
            return render_template('error.html', message=f"註冊失敗: {e}")
        return redirect(url_for('login'))
    return render_template("register.html")


@app.route("/login",methods=['GET', 'POST'])
def login() -> str:
    """登入頁面"""
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password')
        if not email or not password:
            return render_template('error.html', message="請輸入電子郵件和密碼")

        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT iid, username FROM members WHERE email=? AND password=?", (email, password))
                row = c.fetchone()
                if row:
                    iid, username = row
                    return render_template('welcome.html', iid=iid, username=username)
                else:
                    return render_template('error.html', message="電子郵件或密碼錯誤")
        except sqlite3.Error as e:
            return render_template('error.html', message=f"登入失敗: {e}")
    return render_template("login.html")
        

@app.route('/edit_profile/<int:iid>', methods=['GET', 'POST'])
def edit_profile(iid: int)-> str:
    """編輯個人資料"""
    with get_db_connection() as conn:  
        c = conn.cursor()
        if request.method == 'POST':
            email = request.form.get('email').strip()
            password = request.form.get('password')
            phone = request.form.get('phone')
            birthdate = request.form.get('birthdate')

            if not email or not password:
                return render_template('error.html', message="請輸入電子郵件和密碼")

            c.execute("SELECT * FROM members WHERE email=? AND iid!=?", (email, iid))
            if c.fetchone():
                return render_template('error.html', message="電子郵件已被使用")

            c.execute("UPDATE members SET email=?, password=?, phone=?, birthdate=? "
                      "WHERE iid=?",
                      (email, password, phone, birthdate, iid))
            conn.commit()
            c.execute("SELECT username FROM members WHERE iid=?", (iid,))
            username = c.fetchone()[0]
            return render_template('welcome.html', iid=iid, username=username)
        else:
            c.execute("SELECT * FROM members WHERE iid=?", (iid,))
            row = c.fetchone()
            if row:
                return render_template('edit_profile.html', member=row)
            return render_template('error.html', message="找不到該使用者")


@app.route("/delete/<iid>")
def delete(iid)-> str:
    """刪除使用者"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM members WHERE iid=?", (iid,))
            conn.commit()
    except sqlite3.Error as e:
        return render_template('error.html', message=f"刪除失敗: {e}")
    return redirect(url_for('index'))


init_db()


