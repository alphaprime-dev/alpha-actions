from discord_webhook import DiscordEmbed, DiscordWebhook
import click

@click.command(help="CLI for sending message to discord.")
@click.option("--repo", "-f", type=click.STRING, required=True)
@click.option("--tag", "-f", type=click.STRING, required=True)
@click.option("--env", "-f", type=click.STRING, required=True)
def main(env:str, repo: str, tag: str) -> None:
    webhook_url = "https://discord.com/api/webhooks/1062906330001723463/jFCyiTAA2Qi_427spFDTHQjQexN6d1Hwar63d2bz22xGDaBcwlm2pbHcwKnTtlw2_HxT" # noqa
    discord_client = DiscordClient(webhook_url, env, repo, tag)
    discord_client.send_message()

class DiscordClient:
    def __init__(self, webhook_url, env, repo, tag) -> None:
        self.webhook_url = webhook_url
        self.env = env
        self.repo = repo
        self.tag = tag
    
    def send_message(self) -> None:
        embed = self.create_embed(self.env, self.repo, self.tag)
        webhook = DiscordWebhook(self.webhook_url)
        webhook.add_embed(embed)
        webhook.execute()

    def create_embed(self, env:str, repo: str, tag: str) -> DiscordEmbed:
        embed = DiscordEmbed(color="03b2f8")
        embed.set_author(name=repo)
        embed.set_title(title="🔔 릴리즈 완료 🔔")
        embed.set_description(self._get_description(env, repo, tag))
        
        embed.add_embed_field(
            name="Deploy",
            value=self._get_deploy_link(repo),
            inline=True
        )
        embed.add_embed_field(
            name="Release Note",
            value=f"[{tag}](https://github.com/{repo}/releases/tag/{tag})",
            inline=True
        )
        embed.add_embed_field(
            name="Repository",
            value=f"[{repo}](https://github.com/{repo})",
            inline=True
        )
        return embed


    def _get_description(self, env: str, repo: str, tag: str) -> str:
        return f"""
        **{env}**
        {repo.split("/")[1]} 의 {tag} 이미지가 빌드 & 푸쉬 되었습니다.
        Deploy를 진행해주세요 ✈️
        """

    def _get_deploy_link(self, repo: str) -> str:
        if repo == "alphacrawler":
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
