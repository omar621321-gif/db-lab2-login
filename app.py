import os
from functools import wraps

import bcrypt
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "registration"),
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def require_login(view_function):
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    return wrapped


def valid_email(value):
    return "@" in value and "." in value.split("@")[-1]


def validate_register(name, email, password, confirm_password):
    if not name:
        return "Name is required"
    if not email:
        return "Email is required"
    if not password:
        return "Password is required"
    if not confirm_password:
        return "Confirm password is required"
    if password != confirm_password:
        return "Passwords do not match"
    return None


def validate_login(email, password):
    if not email:
        return "Email is required"
    if not password:
        return "Password is required"
    return None


def validate_title(title):
    if not title:
        return "Title is required"
    if len(title) > 200:
        return "Title is too long"
    return None


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("todos"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    error = validate_register(name, email, password, confirm_password)
    if error:
        return render_template(
            "register.html",
            error=error,
            name=name,
            email=email,
        )

    # Lab asks for password hashing with bcrypt/Argon2.
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()

        # Required lab query:
        # INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?);
        query = """
            INSERT INTO users (email, name, password_hash)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (email, name, password_hash))
        db.commit()

        new_user_id = cursor.lastrowid
        session["user_id"] = new_user_id
        session["user_name"] = name
        return redirect(url_for("todos"))

    except mysql.connector.Error as err:
        if err.errno == 1062:
            return render_template(
                "register.html",
                error="Email Already Exists",
                name=name,
                email=email,
            )
        return render_template("error.html", message="Something went wrong. Please try again.")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    error = validate_login(email, password)
    if error:
        return render_template("login.html", error=error, email=email)

    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Required lab query:
        # SELECT user_id, name, password_hash FROM users WHERE email = ?;
        cursor.execute(
            """
            SELECT user_id, name, password_hash
            FROM users
            WHERE email = %s
            """,
            (email,),
        )
        user = cursor.fetchone()

        if not user:
            return render_template(
                "login.html",
                error="Invalid email or password",
                email=email,
            )

        stored_hash = user["password_hash"].encode("utf-8")
        if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return render_template(
                "login.html",
                error="Invalid email or password",
                email=email,
            )

        session["user_id"] = user["user_id"]
        session["user_name"] = user["name"]
        return redirect(url_for("todos"))

    except mysql.connector.Error:
        return render_template("error.html", message="Something went wrong. Please try again.")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/todos", methods=["GET", "POST"])
@require_login
def todos():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        error = validate_title(title)
        if error:
            todos_list = get_todos_for_user(session["user_id"])
            return render_template(
                "todos.html",
                todos=todos_list,
                error=error,
                new_title=title,
            )

        db = None
        cursor = None
        try:
            db = get_db()
            cursor = db.cursor()

            # Required lab query:
            # INSERT INTO todos (user_id, title) VALUES (?, ?);
            cursor.execute(
                "INSERT INTO todos (user_id, title) VALUES (%s, %s)",
                (session["user_id"], title),
            )
            db.commit()
            return redirect(url_for("todos"))
        except mysql.connector.Error:
            return render_template(
                "error.html",
                message="Something went wrong. Please try again.",
            )
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    todos_list = get_todos_for_user(session["user_id"])
    return render_template("todos.html", todos=todos_list)


def get_todos_for_user(user_id):
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Required lab query:
        # SELECT todo_id, title, is_done, created_at
        # FROM todos WHERE user_id = ? ORDER BY todo_id DESC;
        cursor.execute(
            """
            SELECT todo_id, title, is_done, created_at
            FROM todos
            WHERE user_id = %s
            ORDER BY todo_id DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.route("/todos/<int:todo_id>/edit", methods=["POST"])
@require_login
def edit_todo(todo_id):
    title = request.form.get("title", "").strip()
    error = validate_title(title)
    if error:
        todos_list = get_todos_for_user(session["user_id"])
        return render_template(
            "todos.html",
            todos=todos_list,
            error=error,
            edit_id=todo_id,
        )

    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()

        # Required lab query:
        # UPDATE todos SET title = ? WHERE todo_id = ? AND user_id = ?;
        cursor.execute(
            """
            UPDATE todos
            SET title = %s
            WHERE todo_id = %s AND user_id = %s
            """,
            (title, todo_id, session["user_id"]),
        )
        db.commit()
        return redirect(url_for("todos"))
    except mysql.connector.Error:
        return render_template(
            "error.html",
            message="Something went wrong. Please try again.",
        )
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.route("/todos/<int:todo_id>/toggle", methods=["POST"])
@require_login
def toggle_todo(todo_id):
    is_done = 1 if request.form.get("is_done") == "1" else 0

    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()

        # Required lab query:
        # UPDATE todos SET is_done = ? WHERE todo_id = ? AND user_id = ?;
        cursor.execute(
            """
            UPDATE todos
            SET is_done = %s
            WHERE todo_id = %s AND user_id = %s
            """,
            (is_done, todo_id, session["user_id"]),
        )
        db.commit()
        return redirect(url_for("todos"))
    except mysql.connector.Error:
        return render_template(
            "error.html",
            message="Something went wrong. Please try again.",
        )
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
@require_login
def delete_todo(todo_id):
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()

        # Required lab query:
        # DELETE FROM todos WHERE todo_id = ? AND user_id = ?;
        cursor.execute(
            """
            DELETE FROM todos
            WHERE todo_id = %s AND user_id = %s
            """,
            (todo_id, session["user_id"]),
        )
        db.commit()
        return redirect(url_for("todos"))
    except mysql.connector.Error:
        return render_template(
            "error.html",
            message="Something went wrong. Please try again.",
        )
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, port=port)
