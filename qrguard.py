from flask import Flask, render_template, request, send_file
import qrcode
import os
import random
import string

app = Flask(__name__)

BASE_URL = "https://qrguard2.onrender.com"

os.makedirs("qrcodes", exist_ok=True)

objetos = {}


def gerar_codigo():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def gerar_qr(codigo):
    url = f"{BASE_URL}/objeto/{codigo}"

    img = qrcode.make(url)

    caminho = f"qrcodes/{codigo}.png"
    img.save(caminho)

    print(f"QR Code criado: {caminho}")
    print(f"Endereco: {url}")

    return caminho


@app.route("/")
def inicio():
    return """
    <h1>QRGuard funcionando!</h1>
    <a href="/cadastrar">Cadastrar objeto</a>
    """


@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():

    if request.method == "POST":

        nome = request.form["nome"]
        numero = request.form["numero"]

        codigo = gerar_codigo()

        objetos[codigo] = {
            "nome": nome,
            "numero": numero
        }

        gerar_qr(codigo)

        return f"""
        <h1>Objeto cadastrado!</h1>

        <p><strong>Nome:</strong> {nome}</p>
        <p><strong>Telefone:</strong> {numero}</p>
        <p><strong>Codigo:</strong> {codigo}</p>

        <h2>QR Code</h2>

        <img src="/qrcode/{codigo}" width="300">

        <br><br>

        <a href="/qrcode/{codigo}" download>
            <button>Baixar QR Code</button>
        </a>

        <br><br>

        <a href="/objeto/{codigo}">
            Ver pagina do objeto
        </a>
        """

    return """
    <h1>Cadastrar objeto</h1>

    <form method="POST">

        <label>Nome:</label><br>
        <input type="text" name="nome" required>

        <br><br>

        <label>Telefone:</label><br>
        <input type="text" name="numero" required>

        <br><br>

        <button type="submit">Cadastrar</button>

    </form>
    """


@app.route("/qrcode/<codigo>")
def qrcode_imagem(codigo):

    caminho = f"qrcodes/{codigo}.png"

    if not os.path.exists(caminho):
        return "QR Code nao encontrado", 404

    return send_file(caminho, mimetype="image/png")


@app.route("/objeto/<codigo>")
def objeto(codigo):

    if codigo not in objetos:
        return "Objeto nao encontrado", 404

    dados = objetos[codigo]

    return render_template(
        "objeto.html",
        nome=dados["nome"],
        numero=dados["numero"]
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )