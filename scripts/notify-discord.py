from typing import Annotated, Literal

import typer
from discord_webhook import DiscordEmbed, DiscordWebhook

app = typer.Typer(help="CLI for sending message to discord.")


@app.command()
def main(
    webhook_url: Annotated[str, typer.Option("--webhook_url", "-w")],
    status: Annotated[str, typer.Option("--status", "-s")],
    env: Annotated[str, typer.Option("--env", "-e")],
    repo: Annotated[str, typer.Option("--repo", "-r")],
    related_link: Annotated[str, typer.Option("--related_link", "-l")],
    tag: Annotated[str, typer.Option("--tag", "-t")],
) -> None:
    discord_client = DiscordClient(webhook_url, status, env, repo, related_link, tag)
    discord_client.send_message()


class DiscordClient:
    def __init__(self, webhook_url, status, env, repo, related_link, tag) -> None:
        self.webhook_url = webhook_url
        self.status: Literal["true", "false"] = status
        self.env: str = env
        self.repo: str = repo
        self.related_link: str = related_link
        self.tag: str = tag

    def send_message(self) -> None:
        embed = self.create_embed()
        webhook = DiscordWebhook(self.webhook_url)
        webhook.add_embed(embed)
        webhook.execute()

    def create_embed(self) -> DiscordEmbed:
        if self.status == "true":
            status, symbol, color = "성공", "🔔", "03b2f8"
        else:
            status, symbol, color = "실패", "❌", "ff0000"
        embed = DiscordEmbed(color=color)
        embed.set_author(name=self.repo)
        embed.set_title(title=f"{symbol} 릴리즈 {status} {symbol}")
        repo_name = self.repo.split("/")[1]
        embed.set_description(f"""
        **{self.env}**
        {repo_name} 의 {self.tag} 이미지 빌드 & 푸쉬가 {status}했습니다.
        결과를 확인해 주세요 ✈️
        """)

        embed.add_embed_field(name="Deploy", value=self.related_link, inline=True)
        embed.add_embed_field(
            name="Release Note",
            value=f"[{self.tag}](https://github.com/{self.repo}/releases/tag/{self.tag})",
            inline=True,
        )
        embed.add_embed_field(
            name="Actions Workflow",
            value=f"[{repo_name}](https://github.com/{self.repo}/actions)",
            inline=True,
        )
        return embed


if __name__ == "__main__":
    app()
