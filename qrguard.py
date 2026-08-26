from flask import Flask, render_template, request, send_file
import qrcode
import os
import random
import string
import psycopg

app = Flask(__name__)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_URL = "https://qrguard2.onrender.com"

os.makedirs("qrcodes", exist_ok=True)


# ============================================================
# BANCO DE DADOS - POSTGRESQL
# ============================================================

def conectar_banco():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL não configurada.")

    return psycopg.connect(database_url)


def criar_banco():
    conexao = conectar_banco()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS objetos (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(6) UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            numero TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conexao.commit()
    conexao.close()


criar_banco()


# ============================================================
# GERAR CÓDIGO ÚNICO
# ============================================================

def gerar_codigo():

    while True:

        codigo = "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=6
            )
        )

        conexao = conectar_banco()

        resultado = conexao.execute(
            "SELECT id FROM objetos WHERE codigo = %s",
            (codigo,)
        ).fetchone()

        conexao.close()

        if resultado is None:
            return codigo


# ============================================================
# GERAR QR CODE
# ============================================================

def gerar_qr(codigo):

    url = f"{BASE_URL}/objeto/{codigo}"

    img = qrcode.make(url)

    caminho = f"qrcodes/{codigo}.png"

    img.save(caminho)

    print(f"QR Code criado: {caminho}")
    print(f"Endereco: {url}")

    return caminho


# ============================================================
# PÁGINA INICIAL
# ============================================================

@app.route("/")
def inicio():

    return """
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

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

    background:
        linear-gradient(
            135deg,
            #07111f,
            #0d1b2f
        );

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

    box-shadow:
        0 20px 60px rgba(0,0,0,.35);
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
    line-height: 1.5;
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

    <div class="logo">
        QR<span>Guard</span>
    </div>

    <p class="subtitle">
        Proteção inteligente para seus objetos.
    </p>

    <div class="card">

        <div class="icon">
            🛡️
        </div>

        <h1>
            Proteja seus objetos
        </h1>

        <p class="description">
            Cadastre um objeto e gere um QR Code
            exclusivo para facilitar sua devolução
            caso ele seja perdido.
        </p>

        <a
            href="/cadastrar"
            class="button"
        >
            📦 Cadastrar objeto
        </a>

    </div>

    <div class="footer">
        QRGuard • Proteção inteligente para seus objetos
    </div>

</div>

</body>

</html>
"""


# ============================================================
# CADASTRO
# ============================================================

@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():

    if request.method == "POST":

        nome = request.form["nome"]
        numero = request.form["numero"]

        codigo = gerar_codigo()

        conexao = conectar_banco()

        conexao.execute(
            """
            INSERT INTO objetos (codigo, nome, numero)
            VALUES (%s, %s, %s)
            """,
            (codigo, nome, numero)
        )

        conexao.commit()
        conexao.close()

        gerar_qr(codigo)

        return f"""
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>QRGuard — Objeto cadastrado</title>

<style>

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: Arial, Helvetica, sans-serif;

    background:
        linear-gradient(
            135deg,
            #07111f,
            #0d1b2f
        );

    min-height: 100vh;

    color: white;

    padding: 25px;
}}

.container {{
    width: 100%;
    max-width: 520px;
    margin: auto;
}}

.logo {{
    text-align: center;

    font-size: 28px;

    font-weight: 800;

    margin-bottom: 30px;
}}

.logo span {{
    color: #35a7ff;
}}

.card {{
    background: rgba(255,255,255,.07);

    border: 1px solid rgba(255,255,255,.1);

    backdrop-filter: blur(15px);

    border-radius: 25px;

    padding: 30px;

    box-shadow:
        0 20px 60px rgba(0,0,0,.35);
}}

.success {{
    width: 65px;
    height: 65px;

    background: #19c37d;

    border-radius: 50%;

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 32px;

    margin: 0 auto 20px;
}}

h1 {{
    text-align: center;

    font-size: 27px;

    margin-bottom: 10px;
}}

.subtitle {{
    text-align: center;

    color: #aeb9c9;

    margin-bottom: 28px;
}}

.info {{
    background: rgba(255,255,255,.05);

    border-radius: 15px;

    padding: 18px;

    margin-bottom: 25px;
}}

.info p {{
    margin: 8px 0;

    color: #d8e0eb;
}}

.info strong {{
    color: white;
}}

.qr {{
    background: white;

    border-radius: 18px;

    padding: 15px;

    width: fit-content;

    margin: 20px auto;
}}

.qr img {{
    width: 250px;

    max-width: 100%;

    display: block;
}}

.codigo {{
    text-align: center;

    font-size: 13px;

    color: #8f9caf;

    margin-bottom: 22px;
}}

.codigo strong {{
    color: #35a7ff;

    font-size: 18px;

    letter-spacing: 2px;
}}

.button {{
    display: block;

    width: 100%;

    padding: 15px;

    border-radius: 13px;

    text-align: center;

    text-decoration: none;

    font-weight: bold;

    margin-top: 12px;

    transition: .2s;
}}

.primary {{
    background: #168cff;

    color: white;
}}

.primary:hover {{
    background: #0878df;

    transform: translateY(-2px);
}}

.secondary {{
    background: rgba(255,255,255,.08);

    color: white;
}}

.secondary:hover {{
    background: rgba(255,255,255,.14);
}}

.footer {{
    text-align: center;

    color: #687589;

    font-size: 12px;

    margin-top: 25px;
}}

</style>

</head>

<body>

<div class="container">

    <div class="logo">
        QR<span>Guard</span>
    </div>

    <div class="card">

        <div class="success">
            ✓
        </div>

        <h1>
            Objeto cadastrado!
        </h1>

        <p class="subtitle">
            Seu QR Code está pronto para ser usado.
        </p>

        <div class="info">

            <p>
                <strong>Objeto:</strong><br>
                {nome}
            </p>

            <p>
                <strong>Telefone:</strong><br>
                {numero}
            </p>

        </div>

        <div class="qr">

            <img
                src="/qrcode/{codigo}"
                alt="QR Code do objeto"
            >

        </div>

        <div class="codigo">

            Código do objeto<br>

            <strong>
                {codigo}
            </strong>

        </div>

        <a
            href="/qrcode/{codigo}"
            download
            class="button primary"
        >
            ↓ &nbsp; Baixar QR Code
        </a>

        <a
            href="/objeto/{codigo}"
            class="button secondary"
        >
            👁 &nbsp; Ver página pública
        </a>

        <a
            href="/cadastrar"
            class="button secondary"
        >
            + &nbsp; Cadastrar outro objeto
        </a>

    </div>

    <div class="footer">
        QRGuard • Proteção inteligente para seus objetos
    </div>

</div>

</body>

</html>
"""

    # ========================================================
    # FORMULÁRIO DE CADASTRO
    # ========================================================

    return """
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>QRGuard — Cadastrar objeto</title>

<style>

* {
    box-sizing: border-box;

    margin: 0;

    padding: 0;
}

body {

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    min-height: 100vh;

    background:
        linear-gradient(
            135deg,
            #07111f,
            #0d1b2f
        );

    color: white;

    padding: 25px;
}

.container {

    max-width: 500px;

    margin: auto;
}

.logo {

    text-align: center;

    font-size: 30px;

    font-weight: 800;

    margin:
        20px
        0
        35px;
}

.logo span {

    color: #35a7ff;
}

.card {

    background:
        rgba(255,255,255,.07);

    border:
        1px solid
        rgba(255,255,255,.1);

    backdrop-filter:
        blur(15px);

    border-radius: 25px;

    padding: 30px;

    box-shadow:
        0 20px 60px
        rgba(0,0,0,.35);
}

.icon {

    width: 65px;

    height: 65px;

    background:
        rgba(22,140,255,.15);

    border-radius: 18px;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 30px;

    margin-bottom: 22px;
}

h1 {

    font-size: 28px;

    margin-bottom: 8px;
}

.subtitle {

    color: #aeb9c9;

    line-height: 1.5;

    margin-bottom: 30px;
}

label {

    display: block;

    font-size: 14px;

    font-weight: bold;

    margin-bottom: 8px;

    color: #dce5f0;
}

input {

    width: 100%;

    padding: 15px;

    border-radius: 13px;

    border:
        1px solid
        rgba(255,255,255,.12);

    background:
        rgba(0,0,0,.2);

    color: white;

    font-size: 16px;

    outline: none;

    margin-bottom: 22px;
}

input:focus {

    border-color: #168cff;

    box-shadow:
        0 0 0 3px
        rgba(22,140,255,.15);
}

input::placeholder {

    color: #687589;
}

button {

    width: 100%;

    padding: 16px;

    border: none;

    border-radius: 13px;

    background: #168cff;

    color: white;

    font-size: 16px;

    font-weight: bold;

    cursor: pointer;

    transition: .2s;
}

button:hover {

    background: #0878df;

    transform: translateY(-2px);
}

.security {

    margin-top: 22px;

    padding: 15px;

    border-radius: 13px;

    background:
        rgba(25,195,125,.08);

    border:
        1px solid
        rgba(25,195,125,.15);

    color: #9fdcc3;

    font-size: 13px;

    line-height: 1.5;
}

.footer {

    text-align: center;

    color: #687589;

    font-size: 12px;

    margin-top: 25px;
}

</style>

</head>

<body>

<div class="container">

    <div class="logo">
        QR<span>Guard</span>
    </div>

    <div class="card">

        <div class="icon">
            📦
        </div>

        <h1>
            Cadastrar objeto
        </h1>

        <p class="subtitle">

            Crie um QR Code exclusivo
            para identificar seu objeto
            e facilitar sua devolução.

        </p>

        <form method="POST">

            <label>
                Nome do objeto
            </label>

            <input
                type="text"
                name="nome"
                placeholder="Ex: Mochila preta"
                required
            >

            <label>
                Telefone para contato
            </label>

            <input
                type="text"
                name="numero"
                placeholder="Ex: (67) 99999-9999"
                required
            >

            <button type="submit">

                🔐 Criar QR Code

            </button>

        </form>

        <div class="security">

            🔒 Seus dados são utilizados apenas
            para identificar o objeto e facilitar
            o contato caso ele seja encontrado.

        </div>

    </div>

    <div class="footer">

        QRGuard • Proteção inteligente
        para seus objetos

    </div>

</div>

</body>

</html>
"""


# ============================================================
# EXIBIR QR CODE
# ============================================================

@app.route("/qrcode/<codigo>")
def qrcode_imagem(codigo):

    caminho = f"qrcodes/{codigo}.png"

    if not os.path.exists(caminho):

        return "QR Code nao encontrado", 404

    return send_file(
        caminho,
        mimetype="image/png"
    )


# ============================================================
# PÁGINA PÚBLICA DO OBJETO
# ============================================================

@app.route("/objeto/<codigo>")
def objeto(codigo):

    conexao = conectar_banco()

    dados = conexao.execute(
        """
        SELECT nome, numero
        FROM objetos
        WHERE codigo = %s
        """,
        (codigo,)
    ).fetchone()

    conexao.close()

    if dados is None:

        return "Objeto nao encontrado", 404

    return render_template(
        "objeto.html",
        nome=dados[0],
        numero=dados[1]
    )


# ============================================================
# SERVIDOR LOCAL
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )