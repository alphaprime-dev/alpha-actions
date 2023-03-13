import requests

url = "https://discord.com/api/webhooks/1062906330001723463/jFCyiTAA2Qi_427spFDTHQjQexN6d1Hwar63d2bz22xGDaBcwlm2pbHcwKnTtlw2_HxT"
data = {
  "content": None,
  "embeds": [
    {
      "title": "Release Completed",
      "description": "---\n\n[alphaprime-dev/alphaprime-api-bot] version v0.5.1 image is pushed \n\n[Go to Argo CD](https://argocd.alphasquare.co.kr/applications/data-server-prod )\n\n---",
      "color": 5795484,
      "fields": [
        {
          "name": "Environment",
          "value": "PROD",
          "inline": True
        },
        {
          "name": "Repository",
          "value": "[alphaprime-api-bot](https://github.com/alphaprime-dev/alphasquare-main-server/tree/refs/tags/v23.1.0)",
          "inline": True
        },
        {
          "name": "Release Note",
          "value": "[v0.5.1](https://github.com/alphaprime-dev/alphaprime-api-bot/releases/tag/v0.5.1)",
          "inline": True
        }
      ],
      "author": {
        "name": "alphaprime-api-bot"
      }
    }
  ],
  "attachments": []
}


res = requests.post(url, json=data)