import asyncio
import json
import os
import random
import sqlite3
import urllib.parse
import urllib.request

from quart import Quart, render_template, request, redirect, session, url_for, jsonify
from spacy.tokens import Doc
import spacy
from uuid import uuid4

from backend.Getanswer import register_ask_route


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def load_dotenv():
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_dotenv()

app = Quart(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.secret_key = os.getenv("APP_SECRET_KEY", "dev-secret-key")

DATABASE_PATH = os.path.join(BASE_DIR, "app.db")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000").rstrip("/")

nlp = spacy.load("en_core_web_sm")


def make_chat(title="New chat"):
    return {"id": uuid4().hex, "title": title, "history": []}


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_sub TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            avatar_url TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL DEFAULT 'New chat',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
        );
        """
    )
    connection.commit()
    connection.close()


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    connection = get_db_connection()
    user = connection.execute(
        "SELECT id, email, name, avatar_url FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    connection.close()
    return dict(user) if user else None


def get_session_chats():
    chats = session.get("chats")
    if chats:
        return chats

    chat = make_chat()
    session["chats"] = [chat]
    session["active_chat_id"] = chat["id"]
    return session["chats"]


def save_session_chats(chats, active_chat_id):
    session["chats"] = chats
    session["active_chat_id"] = active_chat_id


def find_chat(chats, chat_id):
    for chat in chats:
        if chat["id"] == chat_id:
            return chat
    return None


def build_chat_title(question):
    cleaned = " ".join(question.strip().split())
    if not cleaned:
        return "New chat"
    return cleaned[:40] + ("..." if len(cleaned) > 40 else "")


def get_db_chats(user_id):
    connection = get_db_connection()
    chat_rows = connection.execute(
        """
        SELECT id, title
        FROM chats
        WHERE user_id = ?
        ORDER BY updated_at DESC, created_at DESC
        """,
        (user_id,),
    ).fetchall()

    chats = []
    for chat_row in chat_rows:
        message_rows = connection.execute(
            """
            SELECT question, answer_json
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_row["id"],),
        ).fetchall()
        chats.append(
            {
                "id": chat_row["id"],
                "title": chat_row["title"],
                "history": [
                    [message_row["question"], json.loads(message_row["answer_json"])]
                    for message_row in message_rows
                ],
            }
        )

    connection.close()
    return chats


def create_db_chat(user_id, title="New chat"):
    chat_id = uuid4().hex
    connection = get_db_connection()
    connection.execute(
        """
        INSERT INTO chats (id, user_id, title)
        VALUES (?, ?, ?)
        """,
        (chat_id, user_id, title),
    )
    connection.commit()
    connection.close()
    return chat_id


def ensure_db_chat(user_id):
    chats = get_db_chats(user_id)
    if chats:
        return chats

    create_db_chat(user_id)
    return get_db_chats(user_id)


def append_db_message(user_id, chat_id, question, answer):
    connection = get_db_connection()
    chat_row = connection.execute(
        "SELECT id, title FROM chats WHERE id = ? AND user_id = ?",
        (chat_id, user_id),
    ).fetchone()
    if chat_row is None:
        connection.close()
        return None

    connection.execute(
        """
        INSERT INTO messages (chat_id, question, answer_json)
        VALUES (?, ?, ?)
        """,
        (chat_id, question, json.dumps(answer)),
    )

    next_title = chat_row["title"]
    if next_title == "New chat" and question.strip():
        next_title = build_chat_title(question)

    connection.execute(
        """
        UPDATE chats
        SET title = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        """,
        (next_title, chat_id, user_id),
    )
    connection.commit()
    connection.close()
    return next_title


def find_or_create_user(profile):
    connection = get_db_connection()
    row = connection.execute(
        """
        SELECT id
        FROM users
        WHERE google_sub = ?
        """,
        (profile["sub"],),
    ).fetchone()

    if row is None:
        cursor = connection.execute(
            """
            INSERT INTO users (google_sub, email, name, avatar_url)
            VALUES (?, ?, ?, ?)
            """,
            (profile["sub"], profile["email"], profile["name"], profile.get("picture")),
        )
        user_id = cursor.lastrowid
    else:
        user_id = row["id"]
        connection.execute(
            """
            UPDATE users
            SET email = ?, name = ?, avatar_url = ?
            WHERE id = ?
            """,
            (profile["email"], profile["name"], profile.get("picture"), user_id),
        )

    connection.commit()
    connection.close()
    return user_id


def exchange_google_code(code, redirect_uri):
    payload = urllib.parse.urlencode(
        {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode()
    request_object = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request_object, timeout=20) as response:
        return json.load(response)


def fetch_google_profile(access_token):
    request_object = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(request_object, timeout=20) as response:
        return json.load(response)


def build_state(chats, active_chat):
    return {
        "chats": chats,
        "active_chat_id": active_chat["id"],
        "active_chat": active_chat,
        "history": active_chat["history"],
    }


async def wants_json():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def build_guest_state(requested_chat_id=None):
    chats = get_session_chats()
    active_chat_id = requested_chat_id or session.get("active_chat_id") or chats[0]["id"]
    active_chat = find_chat(chats, active_chat_id)

    if active_chat is None:
        active_chat = chats[0]
        active_chat_id = active_chat["id"]

    save_session_chats(chats, active_chat_id)
    return build_state(chats, active_chat)


def build_user_state(user_id, requested_chat_id=None):
    chats = ensure_db_chat(user_id)
    active_chat_id = requested_chat_id or session.get("active_chat_id")
    active_chat = find_chat(chats, active_chat_id) if active_chat_id else None

    if active_chat is None:
        active_chat = chats[0]
        active_chat_id = active_chat["id"]

    session["active_chat_id"] = active_chat_id
    return build_state(chats, active_chat)


init_db()


@app.route("/")
async def home():
    current_user = get_current_user()
    if request.args.get("fresh") == "1" and current_user is None:
        session.pop("chats", None)
        session.pop("active_chat_id", None)

    requested_chat_id = request.args.get("chat")
    if current_user is None:
        state = build_guest_state(requested_chat_id)
    else:
        state = build_user_state(current_user["id"], requested_chat_id)
    if await wants_json():
        return jsonify(state)
    return await render_template(
        "index.html",
        **state,
        current_user=current_user,
        google_login_ready=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
    )


@app.route("/auth/google")
async def auth_google():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        return redirect(url_for("home"))

    oauth_state = uuid4().hex
    session["oauth_state"] = oauth_state
    query = urllib.parse.urlencode(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": f"{BASE_URL}/auth/google/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "state": oauth_state,
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@app.route("/auth/google/callback")
async def auth_google_callback():
    if request.args.get("state") != session.get("oauth_state"):
        return redirect(url_for("home"))

    code = request.args.get("code")
    if not code:
        return redirect(url_for("home"))

    try:
        token_payload = await asyncio.to_thread(
            exchange_google_code,
            code,
            f"{BASE_URL}/auth/google/callback",
        )
        profile = await asyncio.to_thread(
            fetch_google_profile,
            token_payload["access_token"],
        )
    except Exception:
        return redirect(url_for("home"))

    session.pop("oauth_state", None)
    session.pop("chats", None)
    session.pop("active_chat_id", None)
    session["user_id"] = find_or_create_user(profile)
    return redirect(url_for("home"))


@app.route("/logout", methods=["POST"])
async def logout():
    session.pop("user_id", None)
    session.pop("active_chat_id", None)
    return redirect(url_for("home"))


@app.route("/chats/new", methods=["POST"])
async def new_chat():
    current_user = get_current_user()
    if current_user is None:
        chats = get_session_chats()
        chat = make_chat()
        chats.insert(0, chat)
        save_session_chats(chats, chat["id"])
        state = build_state(chats, chat)
    else:
        chat_id = create_db_chat(current_user["id"])
        state = build_user_state(current_user["id"], chat_id)
    if await wants_json():
        return jsonify(state)
    return redirect(url_for("home", chat=state["active_chat_id"]))


@app.route("/chat/<chat_id>")
async def select_chat(chat_id):
    current_user = get_current_user()
    if current_user is None:
        chats = get_session_chats()
        active_chat = find_chat(chats, chat_id)
        if active_chat is None:
            active_chat = chats[0]
            chat_id = active_chat["id"]
        save_session_chats(chats, chat_id)
        state = build_state(chats, active_chat)
    else:
        state = build_user_state(current_user["id"], chat_id)
    if await wants_json():
        return jsonify(state)
    return redirect(url_for("home", chat=state["active_chat_id"]))



register_ask_route(app, {
    "nlp": nlp,
    "get_current_user": get_current_user,
    "get_session_chats": get_session_chats,
    "find_chat": find_chat,
    "build_user_state": build_user_state,
    "save_session_chats": save_session_chats,
    "build_state": build_state,
    "append_db_message": append_db_message,
    "wants_json": wants_json,
    "build_chat_title": build_chat_title,
})


if __name__ == "__main__":
    app.run()
