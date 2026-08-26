from flask import Flask, render_template
import qrcode
import os

app = Flask(__name__)

BASE_URL = "https://qrguard2.onrender.com"

# Cria a pasta dos QR Codes caso ela não exista
os.makedirs("qrcodes", exist_ok=True)


def gerar_qr(codigo):
    url = f"{BASE_URL}/objeto/{codigo}"

    img = qrcode.make(url)

    caminho = f"qrcodes/{codigo}.png"
    img.save(caminho)

    print(f"QR Code criado: {caminho}")
    print(f"Endereço: {url}")


@app.route("/")
def inicio():
    return "QRGuard funcionando!"


@app.route("/objeto/<codigo>")
def objeto(codigo):

    if codigo == "ABC123":
        nome = "João"
        numero = "(67) 99999-9999"

        return render_template(
            "objeto.html",
            nome=nome,
            numero=numero
        )

    return "Objeto não encontrado"


# Gera o QR Code do objeto ABC123
gerar_qr("ABC123")