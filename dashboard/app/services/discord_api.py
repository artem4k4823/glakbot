"""Тонкая обёртка над Discord REST API от имени бота (токен BOT_TOKEN).

Дашборд выдаёт роли и пишет в ЛС напрямую через REST, поэтому решение по анкете
применяется мгновенно и не требует, чтобы бот опрашивал базу данных.
"""
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from app.config import settings

API_BASE = "https://discord.com/api/v10"
TEXT_CHANNEL_TYPES = {0, 5}  # обычный текстовый и канал объявлений

_ERROR_HINTS = {
    10007: "Пользователь уже покинул сервер.",
    10011: "Роль не найдена — выберите её заново в настройках анкеты.",
    50001: "У бота нет доступа к этому ресурсу.",
    50013: "У бота не хватает прав: нужно право «Управлять ролями», "
           "а роль бота должна стоять в списке выше выдаваемой роли.",
}


class DiscordAPIError(Exception):
    def __init__(self, status: int, code: Optional[int], message: str):
        self.status = status
        self.code = code
        super().__init__(_ERROR_HINTS.get(code, f"Discord API ошибка {status}: {message}"))


async def _request(method: str, path: str, *, reason: str | None = None, json: Any = None) -> Any:
    headers = {"Authorization": f"Bot {settings.BOT_TOKEN}"}
    if reason:
        headers["X-Audit-Log-Reason"] = quote(reason[:512])

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.request(method, f"{API_BASE}{path}", headers=headers, json=json)

    if resp.status_code >= 400:
        try:
            body = resp.json()
        except ValueError:
            body = {}
        raise DiscordAPIError(resp.status_code, body.get("code"), body.get("message", resp.text))

    return resp.json() if resp.content else None


async def get_guild_name(guild_id: str) -> str:
    try:
        guild = await _request("GET", f"/guilds/{guild_id}")
        return guild.get("name", "сервер")
    except (DiscordAPIError, httpx.HTTPError):
        return "сервер"


async def get_guild_roles(guild_id: str) -> List[Dict]:
    """Роли сервера, которые бот теоретически может выдать (без @everyone и ролей интеграций), сверху вниз."""
    try:
        roles = await _request("GET", f"/guilds/{guild_id}/roles")
    except (DiscordAPIError, httpx.HTTPError):
        return []
    roles = [r for r in roles if r["id"] != guild_id and not r.get("managed")]
    return sorted(roles, key=lambda r: r.get("position", 0), reverse=True)


async def get_guild_text_channels(guild_id: str) -> List[Dict]:
    try:
        channels = await _request("GET", f"/guilds/{guild_id}/channels")
    except (DiscordAPIError, httpx.HTTPError):
        return []
    channels = [c for c in channels if c.get("type") in TEXT_CHANNEL_TYPES]
    return sorted(channels, key=lambda c: c.get("position", 0))


async def add_member_role(guild_id: str, user_id: str, role_id: str, reason: str) -> None:
    await _request("PUT", f"/guilds/{guild_id}/members/{user_id}/roles/{role_id}", reason=reason)


async def send_dm(user_id: str, embed: Dict[str, Any]) -> bool:
    """Отправляет пользователю ЛС. False — если ЛС закрыты или произошла ошибка."""
    try:
        channel = await _request("POST", "/users/@me/channels", json={"recipient_id": user_id})
        await _request("POST", f"/channels/{channel['id']}/messages", json={"embeds": [embed]})
        return True
    except (DiscordAPIError, httpx.HTTPError):
        return False


async def mark_review_message(channel_id: str, message_id: str, status_text: str, color: int) -> None:
    """Перекрашивает уведомление в канале модерации и пишет итог в футер. Ошибки игнорируются."""
    try:
        message = await _request("GET", f"/channels/{channel_id}/messages/{message_id}")
        embeds = message.get("embeds") or []
        if not embeds:
            return
        embeds[0]["color"] = color
        embeds[0]["footer"] = {"text": status_text}
        await _request("PATCH", f"/channels/{channel_id}/messages/{message_id}", json={"embeds": embeds})
    except (DiscordAPIError, httpx.HTTPError):
        pass
