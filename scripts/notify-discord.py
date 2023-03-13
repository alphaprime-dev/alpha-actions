import requests


url = "https://discord.com/api/webhooks/1062906330001723463/jFCyiTAA2Qi_427spFDTHQjQexN6d1Hwar63d2bz22xGDaBcwlm2pbHcwKnTtlw2_HxT"
data = {
    "content": "test github actions",
    "embeds": None,
    "attachments": []
}

res = requests.post(url, json=data)