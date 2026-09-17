import os
import json
import time
import urllib.request
import urllib.parse

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

API = f"https://api.telegram.org/bot{TOKEN}"

users = {}


def telegram(method, data=None):
    data = data or {}
    encoded = urllib.parse.urlencode(data).encode("utf-8")

    request = urllib.request.Request(
        f"{API}/{method}",
        data=encoded
    )

    with urllib.request.urlopen(request, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def send_message(chat_id, text):
    telegram("sendMessage", {
        "chat_id": chat_id,
        "text": text
    })


def start_search(chat_id):
    users[chat_id] = {
        "step": "city",
        "search": {}
    }

    send_message(
        chat_id,
        "🏠 Neue Wohnungssuche\n\n"
        "In welcher Stadt suchst du eine Wohnung?"
    )


def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text == "/start":
        send_message(
            chat_id,
            "👋 Willkommen!\n\n"
            "Ich helfe dir, schnell passende Wohnungen zu finden.\n\n"
            "Befehle:\n"
            "/search – Suche erstellen\n"
            "/settings – Suche anzeigen\n"
            "/stop – Suche pausieren\n"
            "/test – Testwohnung senden\n"
            "/help – Hilfe dir"
        )
        return

    if text == "/help":
        send_message(
            chat_id,
            "🆘 Hilfe dir\n\n"
            "/search – neue Suche erstellen\n"
            "/settings – aktuelle Suche anzeigen\n"
            "/stop – Suche pausieren\n"
            "/test – Testbenachrichtigung senden"
        )
        return

    if text == "/search":
        start_search(chat_id)
        return

    if text == "/settings":
        user = users.get(chat_id)

        if not user or not user.get("search"):
            send_message(chat_id, "ℹ️ Du hast noch keine Suche erstellt.")
            return

        search = user["search"]

        send_message(
            chat_id,
            "🔎 Deine Suche:\n\n"
            f"🏙 Stadt: {search.get('city', 'Egal')}\n"
            f"💶 Max. Warmmiete: {search.get('rent', 'Egal')}\n"
            f"🛏 Zimmer: {search.get('rooms', 'Egal')}\n"
            f"📐 Mindestgröße: {search.get('size', 'Egal')}\n"
            f"📍 Stadtteile: {search.get('districts', 'Egal')}\n"
            f"📅 Einzug: {search.get('move_in', 'Egal')}"
        )
        return

    if text == "/stop":
        if chat_id in users:
            users[chat_id]["active"] = False

        send_message(chat_id, "⏸️ Deine Wohnungssuche wurde pausiert.")
        return

    if text == "/test":
        send_message(
            chat_id,
            "🏠 TEST – Neue Wohnung gefunden!\n\n"
            "📍 Hamburg, Altona\n"
            "💶 950 € Warmmiete\n"
            "🛏 3 Zimmer\n"
            "📐 72 m²\n\n"
            "🔗 https://example.com/wohnung"
        )
        return

    user = users.get(chat_id)

    if not user:
        send_message(
            chat_id,
            "Schreibe /search, um eine Wohnungssuche zu erstellen."
        )
        return

    step = user["step"]

    if step == "city":
        user["search"]["city"] = text
        user["step"] = "rent"
        send_message(chat_id, "💶 Wie hoch darf die maximale Warmmiete sein?\n\nBeispiel: 1100")
        return

    if step == "rent":
        user["search"]["rent"] = text
        user["step"] = "rooms"
        send_message(chat_id, "🛏 Wie viele Zimmer suchst du?\n\nBeispiel: 3")
        return

    if step == "rooms":
        user["search"]["rooms"] = text
        user["step"] = "size"
        send_message(chat_id, "📐 Wie groß soll die Wohnung mindestens sein?\n\nBeispiel: 60")
        return

    if step == "size":
        user["search"]["size"] = text
        user["step"] = "districts"
        send_message(
            chat_id,
            "📍 Welche Stadtteile kommen infrage?\n\n"
            "Du kannst mehrere nennen, z. B. Altona, Eimsbüttel.\n"
            "Oder schreibe: Egal"
        )
        return

    if step == "districts":
        user["search"]["districts"] = text
        user["step"] = "move_in"
        send_message(
            chat_id,
            "📅 Wann möchtest du einziehen?\n\n"
            "Beispiel: Ab sofort\n"
            "Oder ein Datum wie: 01.10.2026"
        )
        return

    if step == "move_in":
        user["search"]["move_in"] = text
        user["step"] = None
        user["active"] = True

        search = user["search"]

        send_message(
            chat_id,
            "✅ Suche gespeichert!\n\n"
            f"🏙 Stadt: {search['city']}\n"
            f"💶 Max. Warmmiete: {search['rent']} €\n"
            f"🛏 Zimmer: {search['rooms']}\n"
            f"📐 Mindestgröße: {search['size']} m²\n"
            f"📍 Stadtteile: {search['districts']}\n"
            f"📅 Einzug: {search['move_in']}\n\n"
            "🔔 Deine Suche ist aktiv.\n\n"
            "Sobald wir eine passende Testwohnung finden, "
            "kann der Bot dich benachrichtigen."
        )
        return


def main():
    print("🤖 Wohnung-Bot startet...")

    offset = None

    while True:
        try:
            data = {
                "timeout": 30
            }

            if offset is not None:
                data["offset"] = offset

            result = telegram("getUpdates", data)

            if not result.get("ok"):
                time.sleep(3)
                continue

            for update in result.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")

                if message:
                    try:
                        handle_message(message)
                    except Exception as error:
                        print("Fehler:", error)

        except Exception as error:
            print("Verbindungsfehler:", error)
            time.sleep(5)


if __name__ == "__main__":
    main()
