
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, send_file
)
import os
import secrets
import io
import qrcode
import psycopg

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "chave-local-apenas-desenvolvimento"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

BASE_URL = os.environ.get(
    "BASE_URL",
    "http://127.0.0.1:5000"
)


def conectar_banco():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "A variável DATABASE_URL não foi configurada."
        )

    return psycopg.connect(database_url)



def preparar_banco():
    with conectar_banco() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS objetos (
                codigo TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                numero TEXT NOT NULL,
                criado_em TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            ALTER TABLE objetos
            ALTER COLUMN codigo TYPE TEXT
        """)



@app.route("/")
def inicio():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QRGuard</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: Arial, Helvetica, sans-serif;
            min-height: 100vh;
            background: linear-gradient(135deg, #07111f, #0d1b2f);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 25px;
        }

        .container {
            width: 100%;
            max-width: 500px;
            text-align: center;
        }

        .logo {
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 15px;
        }

        .logo span {
            color: #35a7ff;
        }

        .subtitle {
            color: #aeb9c9;
            font-size: 17px;
            line-height: 1.6;
            margin-bottom: 35px;
        }

        .card {
            background: rgba(255,255,255,.07);
            border: 1px solid rgba(255,255,255,.1);
            backdrop-filter: blur(15px);
            border-radius: 25px;
            padding: 35px;
            box-shadow: 0 20px 60px rgba(0,0,0,.35);
        }

        .icon {
            font-size: 50px;
            margin-bottom: 20px;
        }

        h1 {
            font-size: 26px;
            margin-bottom: 10px;
        }

        .description {
            color: #aeb9c9;
            line-height: 1.6;
            margin-bottom: 25px;
        }

        .button {
            display: block;
            width: 100%;
            padding: 16px;
            border-radius: 13px;
            background: #168cff;
            color: white;
            text-decoration: none;
            font-weight: bold;
            transition: .2s;
        }

        .button:hover {
            background: #0878df;
            transform: translateY(-2px);
        }

        .footer {
            margin-top: 25px;
            color: #687589;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">QR<span>Guard</span></div>

        <p class="subtitle">
            Proteção inteligente para seus objetos.
        </p>

        <div class="card">
            <div class="icon">🛡️</div>

            <h1>Proteja seus objetos</h1>

            <p class="description">
                Gere um QR Code exclusivo para facilitar
                a devolução dos seus objetos caso sejam perdidos.
            </p>

            <a href="/login" class="button">
                Acessar painel administrativo
            </a>
        </div>

        <div class="footer">
            QRGuard · Proteção inteligente para seus objetos
        </div>
    </div>
</body>
</html>
"""



@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        senha = request.form.get("senha", "")

        if ADMIN_PASSWORD and secrets.compare_digest(
            senha, ADMIN_PASSWORD
        ):
            session.clear()
            session["administrador"] = True
            return redirect(url_for("admin"))

        erro = "Senha incorreta ou login não configurado."

    return render_template("login.html", erro=erro)


@app.route("/admin")
def admin():
    if not session.get("administrador"):
        return redirect(url_for("login"))

    with conectar_banco() as conn:
        objetos = conn.execute("""
            SELECT codigo, nome, numero
            FROM objetos
            ORDER BY criado_em DESC
        """).fetchall()

    return render_template("admin.html", objetos=objetos)


@app.route("/admin/cadastrar", methods=["POST"])
def cadastrar():
    if not session.get("administrador"):
        return redirect(url_for("login"))

    nome = request.form.get("nome", "").strip()
    numero = request.form.get("numero", "").strip()

    if not nome or not numero:
        return "Preencha o nome e o telefone.", 400

    codigo = secrets.token_urlsafe(9)

    with conectar_banco() as conn:
        conn.execute("""
            INSERT INTO objetos (codigo, nome, numero)
            VALUES (%s, %s, %s)
        """, (codigo, nome, numero))

    return redirect(url_for("admin"))


@app.route("/qrcode/<codigo>.png")
def mostrar_qr(codigo):
    if not session.get("administrador"):
        return redirect(url_for("login"))

    with conectar_banco() as conn:
        objeto = conn.execute(
            "SELECT codigo FROM objetos WHERE codigo = %s",
            (codigo,)
        ).fetchone()

    if not objeto:
        return "Objeto não encontrado", 404

    endereco = f"{BASE_URL.rstrip('/')}/objeto/{codigo}"
    imagem = qrcode.make(endereco)

    arquivo = io.BytesIO()
    imagem.save(arquivo, format="PNG")
    arquivo.seek(0)

    return send_file(
        arquivo,
        mimetype="image/png",
        download_name=f"QRGuard-{codigo}.png"
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/objeto/<codigo>")
def objeto(codigo):
    with conectar_banco() as conn:
        resultado = conn.execute("""
            SELECT nome, numero
            FROM objetos
            WHERE codigo = %s
        """, (codigo,)).fetchone()

    if not resultado:
        return "Objeto não encontrado", 404

    nome, numero = resultado

    return render_template(
        "objeto.html",
        nome=nome,
        numero=numero
    )


preparar_banco()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
