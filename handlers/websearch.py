import requests
from config import WEB_SEARCH_API_KEY

BRAVE_SEARCH_API_URL = "https://api.search.brave.com/res/v1/web/search"

async def web_search(update, context):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/websearch <query> [options]\n\n"
            "Options:\n"
            "--fresh pd|pw|pm|py\n"
            "--country IN|US|DE\n"
            "--lang en|de|fr\n"
            "--snippets\n"
            "--count <1-20>\n"
            "--page <number>\n\n"
            "Example:\n"
            "/websearch ai trends --fresh pw --country IN --snippets"
        )
        return

    # -----------------------------
    # Parse arguments
    # -----------------------------
    args = context.args
    query_parts = []
    params = {}

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--fresh" and i + 1 < len(args):
            params["freshness"] = args[i + 1]
            i += 2
        elif arg == "--country" and i + 1 < len(args):
            params["country"] = args[i + 1]
            i += 2
        elif arg == "--lang" and i + 1 < len(args):
            params["search_lang"] = args[i + 1]
            params["ui_lang"] = args[i + 1]
            i += 2
        elif arg == "--snippets":
            params["extra_snippets"] = "true"
            i += 1
        elif arg == "--count" and i + 1 < len(args):
            params["count"] = args[i + 1]
            i += 2
        elif arg == "--page" and i + 1 < len(args):
            # Brave uses offset, not page number
            page = int(args[i + 1])
            params["offset"] = max(page - 1, 0)
            i += 2
        else:
            query_parts.append(arg)
            i += 1

    query = " ".join(query_parts)

    # Mandatory query param
    params["q"] = query

    # Defaults
    params.setdefault("count", 5)

    # -----------------------------
    # Call Brave API
    # -----------------------------
    try:
        response = requests.get(
            BRAVE_SEARCH_API_URL,
            headers={"X-Subscription-Token": WEB_SEARCH_API_KEY},
            params=params,
            timeout=15
        )

        data = response.json()
        results = data.get("web", {}).get("results", [])

        if not results:
            await update.message.reply_text("No results found.")
            return

        # -----------------------------
        # Format response
        # -----------------------------
        messages = []
        for idx, r in enumerate(results[:5], start=1):
            msg = f"{idx}. {r.get('title')}\n{r.get('url')}\n{r.get('description', '')}"

            extras = r.get("extra_snippets")
            if extras:
                snippets = "\n".join(f"• {s}" for s in extras[:2])
                msg += f"\n\nExtra snippets:\n{snippets}"

            messages.append(msg)

        await update.message.reply_text("\n\n".join(messages))

    except Exception as e:
        await update.message.reply_text(
            "Error fetching search results. Try again later."
        )
