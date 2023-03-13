from typing import Literal
from discord_webhook import DiscordEmbed, DiscordWebhook
import click

@click.command(help="CLI for sending message to discord.")
@click.option("--url", "-u", type=click.STRING, required=True)
@click.option("--status", "-s", type=click.STRING, required=True)
@click.option("--env", "-e", type=click.STRING, required=True)
@click.option("--repo", "-r", type=click.STRING, required=True)
@click.option("--tag", "-t", type=click.STRING, required=True)
def main(url:str, status:str, env:str, repo: str, tag: str) -> None:
    discord_client = DiscordClient(url, status, env,  repo, tag)
    discord_client.send_message()

class DiscordClient:
    def __init__(self, webhook_url, status, env, repo, tag) -> None:
        self.webhook_url = webhook_url
        self.status:Literal["true","false"] = status
        self.env:str = env
        self.repo:str = repo
        self.tag:str = tag
    
    def send_message(self) -> None:
        
        embed = self.create_embed()
        webhook = DiscordWebhook(self.webhook_url)
        webhook.add_embed(embed)
        webhook.execute()

    def create_embed(self) -> DiscordEmbed:
        status = "성공" if self.status == "true" else "실패"
        symbol = "🔔" if self.status == "true" else "❌"
        embed = DiscordEmbed(color="03b2f8")
        embed.set_author(name=self.repo)
        embed.set_title(title=f"{symbol} 릴리즈 {status} {symbol}")
        repo_name = self.repo.split("/")[1]
        embed.set_description(f"""
        **{self.env}**
        {repo_name} 의 {self.tag} 이미지 빌드 & 푸쉬가 {status}했습니다.
        결과를 확인해 주세요 ✈️
        """)

        embed.add_embed_field(
            name="Deploy",
            value=self._get_deploy_link(self.repo),
            inline=True
        )
        embed.add_embed_field(
            name="Release Note",
            value=f"[{self.tag}](https://github.com/{self.repo}/releases/tag/{self.tag})",
            inline=True
        )
        embed.add_embed_field(
            name="Actions Workflow",
            value=f"[{repo_name}](https://github.com/{self.repo}/actions)",
            inline=True
        )
        return embed


    def _get_deploy_link(self, repo: str) -> str:
        if repo == "alphaprime-dev/alphacrawler":
            return "[Airflow](https://airflow.alphasquare.co.kr/variable/list)"
        ENDPOINT = {
            "alphaprime-dev/alphasquare-main-server": "main-server-prod",
            "alphaprime-dev/alphasquare-chartgame" : "chartgame-prod",
            "alphaprime-dev/alphasquare-data-server" : "data-server-prod",
            "alphaprime-dev/alphasquare-real-trading-server" : "real-trading-prod",
            "alphaprime-dev/alphasquare-socketio-server" : "socketio-prod",
        }
        return f"[Argo CD](https://argocd.alphasquare.co.kr/applications/{ENDPOINT[repo]})"



if __name__ == "__main__":
    main()
