import urllib.request
import urllib.parse


url = "https://discord.com/api/webhooks/1062906330001723463/jFCyiTAA2Qi_427spFDTHQjQexN6d1Hwar63d2bz22xGDaBcwlm2pbHcwKnTtlw2_HxT"
data = {
    "content": "test github actions",
    "embeds": None,
    "attachments": []
}

req = urllib.request.Request(
    url=url, 
    data=urllib.parse.urlencode(data).encode("utf-8"), 
    method="POST"
)

res = urllib.request.urlopen(req)