from app.ai.client import client, MODEL_DEPLOYMENT


def test_web_search():
    try:
        response = client.responses.create(
            model=MODEL_DEPLOYMENT,
            tools=[
                {
                    "type": "web_search"
                }
            ],
            input=(
                "Search the web for the official YouTube page for "
                "Markiplier's Drunk Minecraft #1. "
                "Return the URL and the title of the page you found."
            )
        )

        print("\n===== RESPONSE =====")
        print(response.output_text)

        print("\n===== RAW OUTPUT ITEMS =====")
        for item in response.output:
            print(item)

    except Exception as e:
        print("\n===== ERROR =====")
        print(type(e).__name__)
        print(str(e))


if __name__ == "__main__":
    test_web_search()