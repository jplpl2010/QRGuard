from flask import Flask, render_template, request, send_file
import qrcode
import os
import random
import string
import psycopg

app = Flask(__name__)

BASE_URL = "https://qrguard2.onrender.com"

os.makedirs("qrcodes", exist_ok=True)


# =========================
# BANCO DE DADOS
# =========================

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


# =========================
# CÓDIGO DO OBJETO
# =========================

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


# =========================
# QR CODE
# =========================

def gerar_qr(codigo):

    url = f"{BASE_URL}/objeto/{codigo}"

    img = qrcode.make(url)

    caminho = f"qrcodes/{codigo}.png"

    img.save(caminho)

    print(f"QR Code criado: {caminho}")
    print(f"Endereco: {url}")

    return caminho


# =========================
# INÍCIO
# =========================

@app.route("/")
def inicio():

    return """
    <h1>QRGuard funcionando!</h1>

    <a href="/cadastrar">
        Cadastrar objeto
    </a>
    """


# =========================
# CADASTRO
# =========================

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
        <h1>Objeto cadastrado!</h1>

        <p>
            <strong>Nome:</strong> {nome}
        </p>

        <p>
            <strong>Telefone:</strong> {numero}
        </p>

        <p>
            <strong>Codigo:</strong> {codigo}
        </p>

        <h2>QR Code</h2>

        <img
            src="/qrcode/{codigo}"
            width="300"
        >

        <br><br>

        <a href="/qrcode/{codigo}" download>
            <button>Baixar QR Code</button>
        </a>

        <br><br>

        <a href="/objeto/{codigo}">
            Ver pagina do objeto
        </a>

        <br><br>

        <a href="/cadastrar">
            Cadastrar outro objeto
        </a>
        """

    return """
    <h1>Cadastrar objeto</h1>

    <form method="POST">

        <label>Nome:</label><br>

        <input
            type="text"
            name="nome"
            required
        >

        <br><br>

        <label>Telefone:</label><br>

        <input
            type="text"
            name="numero"
            required
        >

        <br><br>

        <button type="submit">
            Cadastrar
        </button>

    </form>
    """


# =========================
# QR CODE
# =========================

@app.route("/qrcode/<codigo>")
def qrcode_imagem(codigo):

    caminho = f"qrcodes/{codigo}.png"

    if not os.path.exists(caminho):
        return "QR Code nao encontrado", 404

    return send_file(
        caminho,
        mimetype="image/png"
    )


# =========================
# OBJETO
# =========================

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


# =========================
# SERVIDOR
# =========================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )