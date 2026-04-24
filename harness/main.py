import asyncio
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import structlog
import llm_client
import sparql_client

load_dotenv()

log = structlog.get_logger()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def setup_hook():
    await bot.tree.sync()
    log.info("bot.synced")


@bot.event
async def on_ready():
    log.info("bot.ready", user=str(bot.user))


@bot.tree.command(name="ping", description="Check Discord, OpenRouter, and Oxigraph reachability")
async def ping(interaction: discord.Interaction):
    sid = str(interaction.id)
    bound = log.bind(session_id=sid, adapter="discord")
    await interaction.response.defer(thinking=True)
    bound.info("ping.received")

    lines = []

    # Discord leg: if we got here, it's up
    lines.append("✓ Discord auth")

    # OpenRouter leg
    try:
        _, model, latency = await llm_client.complete("reply with one word: ok")
        lines.append(f"✓ OpenRouter — model: {model}, latency: {latency}ms")
        bound.info("llm.checked", model=model, latency_ms=latency)
    except Exception as e:
        lines.append(f"✗ OpenRouter — {type(e).__name__}: check OPENROUTER_API_KEY")
        bound.error("llm.failed", error=str(e))

    # Oxigraph leg
    try:
        result, latency = await sparql_client.run_ask(sparql_client.HEALTH_ASK)
        lines.append(f"✓ Oxigraph — latency: {latency}ms")
        bound.info("sparql.checked", latency_ms=latency, result=result)
    except Exception as e:
        lines.append(f"✗ Oxigraph — {type(e).__name__}: check OXIGRAPH_ENDPOINT")
        bound.error("sparql.failed", error=str(e))

    await interaction.followup.send("\n".join(lines))


if __name__ == "__main__":
    sparql_client.OXIGRAPH_ENDPOINT = os.environ.get("OXIGRAPH_ENDPOINT", "http://localhost:7878")
    bot.run(os.environ["DISCORD_BOT_TOKEN"])
