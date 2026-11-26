
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

# Configurações do QRGuard
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "chave-local-apenas-desenvolvimento"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("COOKIE_SECURE", "false").lower() == "true"
)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

BASE_URL = os.environ.get(
    "BASE_URL",
    "http://127.0.0.1:5000"
)


# CONEXÃO COM O BANCO DE DADOS
def conectar_banco():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "A variável DATABASE_URL não foi configurada."
        )

    return psycopg.connect(database_url)


# PREPARAÇÃO DO BANCO
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


# PÁGINA INICIAL
@app.route("/")
def inicio():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QRGuard</title>
</head>
<body>
    <h1>QRGuard</h1>
    <p>Proteção inteligente para seus objetos.</p>
    <a href="/login">Acessar painel administrativo</a>
</body>
</html>
"""


# LOGIN ADMINISTRATIVO
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


# PAINEL ADMINISTRATIVO
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


# CADASTRAR OBJETO
@app.route("/admin/cadastrar", methods=["POST"])
def cadastrar():
    if not session.get("administrador"):
        return redirect(url_for("login"))

    nome = request.form.get("nome", "").strip()
    numero = request.form.get("numero", "").strip()

    if not nome or not numero:
        return "Preencha o nome e o telefone.", 400

    if len(nome) > 150 or len(numero) > 40:
        return "Os dados ultrapassaram o limite permitido.", 400

    codigo = secrets.token_urlsafe(9)

    with conectar_banco() as conn:
        conn.execute("""
            INSERT INTO objetos (codigo, nome, numero)
            VALUES (%s, %s, %s)
        """, (codigo, nome, numero))

    return redirect(url_for("admin"))


# EDITAR OBJETO
@app.route("/admin/editar/<codigo>", methods=["GET", "POST"])
def editar(codigo):
    if not session.get("administrador"):
        return redirect(url_for("login"))

    with conectar_banco() as conn:
        objeto = conn.execute("""
            SELECT codigo, nome, numero
            FROM objetos
            WHERE codigo = %s
        """, (codigo,)).fetchone()

        if not objeto:
            return "Objeto não encontrado.", 404

        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            numero = request.form.get("numero", "").strip()

            if not nome or not numero:
                return "Preencha o nome e o telefone.", 400

            if len(nome) > 150 or len(numero) > 40:
                return "Os dados ultrapassaram o limite permitido.", 400

            conn.execute("""
                UPDATE objetos
                SET nome = %s, numero = %s
                WHERE codigo = %s
            """, (nome, numero, codigo))

            return redirect(url_for("admin"))

    return render_template("editar.html", objeto=objeto)


# GERAR QR CODE
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


# SAIR DO PAINEL
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# PÁGINA PÚBLICA DO QR CODE
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


# PREPARAR BANCO DE DADOS
preparar_banco()


# INICIAR A APLICAÇÃO
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
