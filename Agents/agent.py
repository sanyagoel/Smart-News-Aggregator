import json
from google.adk.agents.llm_agent import Agent
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent

# from google.adk.agents.tool import tool

from Scrapers.entertainment_scraper import scrape_entertainment_top_n
from Scrapers.sports_scraper import scrape_sports_top_n
from Scrapers.international_scraper import scrape_international_top_n
from Scrapers.national_scraper import scrape_national_top_n
from Scrapers.states_scraper import scrape_states_top_n



def get_states_news(state: str, limit: int = 10) -> str:
    """Returns latest state-level news. Example: state='mumbai'"""
    data = scrape_states_top_n(state, limit)
    return json.dumps(data, ensure_ascii=False)


def get_national_news(limit: int = 10) -> str:
    """Returns latest national-level Indian news."""
    data = scrape_national_top_n(limit)
    return json.dumps(data, ensure_ascii=False)


def get_international_news(limit: int = 10) -> str:
    """Returns recent global/international news."""
    data = scrape_international_top_n(limit)
    return json.dumps(data, ensure_ascii=False)


def get_sports_news(limit: int = 10) -> str:
    """Returns top sports headlines."""
    data = scrape_sports_top_n(limit)
    return json.dumps(data, ensure_ascii=False)


def get_entertainment_news(limit: int = 10) -> str:
    """Returns latest entertainment news."""
    data = scrape_entertainment_top_n(limit)
    return json.dumps(data, ensure_ascii=False)



scraper_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="A news assistant that fetches live scraped content.",
    instruction=(
        "When the user asks for news, ALWAYS call the correct tool instead of generating fake data. "
        "Use the tools to fetch real scraped news."
    ),
    tools=[
        get_states_news,
        get_national_news,
        get_international_news,
        get_sports_news,
        get_entertainment_news,
    ],
    output_key = "scraper_output"
)

summariser_agent = Agent(
    model="gemini-2.5-flash",
    name="summariser_agent",
    description="Converts raw scraped news JSON into a polished readable report.",
    instruction=(
        "You will receive a variable called `scraper_output` that contains a JSON list of news articles.\n"
        "Your job is to SUMMARISE each article clearly and professionally.\n\n"
        "Keep summaries **150-170 words max per article**.\n"
        "Preserve all key facts: who, what, when, where, why, quotes.\n"
        "Tone should be like a journalist writing a news digest.\n"
        "Do NOT copy/paste full article text.\n\n"
        "Output must contain ALL articles. Do NOT merge or skip any."
    )
)


root_agent = SequentialAgent(
    name="NewsPipeline",
    sub_agents=[
        scraper_agent,
        summariser_agent,
    ],
    description="Fetches news through scraping tools, then formats them into a clean report.")


