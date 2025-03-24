import requests
import base64

API_URL = "https://api.cloudflare.com/client/v4/accounts/278f197da298d79eb81f06b72011bb25/ai/run/@cf/black-forest-labs/flux-1-schnell"

HEADERS = {
    "Authorization": "Bearer WTSaANr6uRslArJN6TQH_-a-Dd3B8VWYbCPzUF5J",
    "Content-Type": "application/json"
}

DATA = {
    "prompt": "Um porco espinho futuristico, com uma arma futiristica na mão e com um fone de ouvido na orelha",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 50  # Aumentei para 50 para melhor qualidade
}

try:
    response = requests.post(API_URL, json=DATA, headers=HEADERS)
    response.raise_for_status()  # Lança exceção para status de erro (4xx ou 5xx)

    result = response.json()
    image_base64 = result["result"]["image"]

    if image_base64:
        try:
            with open("porco_palmeiras_corinthians.png", "wb") as img_file:
                img_file.write(base64.b64decode(image_base64))
            print("Imagem salva como porco_palmeiras_corinthians.png")
        except Exception as e:
            print(f"Erro ao decodificar a imagem: {e}")
    else:
        print("Imagem não encontrada na resposta da API.")

except requests.exceptions.RequestException as e:
    print(f"Erro na requisição: {e}")
except KeyError:
    print("Erro: 'image' não encontrado na resposta da API.")
except Exception as e:
    print(f"Erro inesperado: {e}")