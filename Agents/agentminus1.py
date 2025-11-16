import datetime
import json
import logging
from typing import Optional, Dict, Any, Set, List
from pydantic import BaseModel
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types as genai_types
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

 
from Scrapers.entertainment_scraper import scrape_entertainment_top_n
from Scrapers.sports_scraper import scrape_sports_top_n
from Scrapers.international_scraper import scrape_international_top_n
from Scrapers.national_scraper import scrape_national_top_n
from Scrapers.states_scraper import scrape_states_top_n



STYLE_OF_WRITING = "sarcastic"      
TARGET_LANGUAGE = "hi"               # ISO code, e.g. hi=Hindi, en=English, ta=Tamil



class NewsItem(BaseModel):
    title: str
    link: str
    date: str
    author: Optional[str] = ""
    article: Optional[str] = ""
    image_url: Optional[str] = None



BANNED_WORDS: Set[str] = {
    "kill yourself", "how to make a bomb", "i will kill you", "rape",
    "nazi", "faggot", "retard", "child assault", "autistic", "murder"
}

NEWS_KEYWORDS: Set[str] = {
    "news", "headlines", "article", "happening in", "sports",
    "entertainment", "politics", "business", "tech", "latest",
    "updates", "breaking", "tell me about", "what's new", "information"
}

VALID_STATES: Set[str] = {
    "mumbai", "delhi", "bengaluru", "kolkata", "chennai", "pune",
    "hyderabad", "ahmedabad", "maharashtra", "karnataka",
    "west bengal", "tamil nadu", "gujarat", "uttar pradesh",
    "rajasthan", "punjab", "kerala", "andhra pradesh", "goa"
}


def input_guardrail(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    last_user_text = ""
    if llm_request.contents:
        for c in reversed(llm_request.contents):
            if c.role == "user" and c.parts and c.parts[0].text:
                last_user_text = c.parts[0].text.lower()
                break

    if not last_user_text:
        return None

    # Harmful content
    if any(w in last_user_text for w in BANNED_WORDS):
        callback_context.state["abort_pipeline"] = True  # <--- mark stop
        return LlmResponse(
            content=genai_types.Content(
                role="model",
                parts=[genai_types.Part(text="🚫 I cannot process this request due to a content policy violation.")]
            )
        )

    # Not news-related
    if not any(w in last_user_text for w in NEWS_KEYWORDS):
        callback_context.state["abort_pipeline"] = True  # <--- mark stop
        return LlmResponse(
            content=genai_types.Content(
                role="model",
                parts=[genai_types.Part(text="📰 I am a news assistant. I can only fetch news, headlines, and articles.")]
            )
        )

    return None



def tool_guardrail(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    """Ensures valid state/city input for news tools."""
    if tool.name == "get_states_news":
        state = args.get("state", "").lower().strip()
        if not state:
            return {
                "status": "error",
                "error_message": "You asked for state news but did not provide a state or city."
            }
        if state not in VALID_STATES:
            return {
                "status": "error",
                "error_message": f"Policy Error: I do not have news for '{state}'. Please try a valid Indian state or city."
            }
    return None



def wrap(items: list) -> List[NewsItem]:
    """Wraps dicts into Pydantic NewsItem, skipping entries without articles."""
    return [NewsItem(**item) for item in items if item.get("article")]


def get_states_news(state: str, limit: int = 10) -> List[NewsItem]:
    return wrap(scrape_states_top_n(state, limit))

def get_national_news(limit: int = 10) -> List[NewsItem]:
    return wrap(scrape_national_top_n(limit))

def get_international_news(limit: int = 10) -> List[NewsItem]:
    return wrap(scrape_international_top_n(limit))

def get_sports_news(limit: int = 10) -> List[NewsItem]:
    return wrap(scrape_sports_top_n(limit))

def get_entertainment_news(limit: int = 10) -> List[NewsItem]:
    return wrap(scrape_entertainment_top_n(limit))




def after_agent_callback(callback_context: CallbackContext):
    """Logs end of agent execution and duration."""
    state = callback_context.state
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Compute duration if possible
    try:
        start_str = state.get("last_agent_start")
        if start_str:
            start_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            duration = (datetime.datetime.now() - start_dt).total_seconds()
        else:
            duration = None
    except Exception:
        duration = None

    print(f"=== AGENT END ===")
    if duration is not None:
        print(f"Duration: {duration:.2f}s")
        logging.info(f"Completed agent in {duration:.2f}s")
    else:
        logging.info(f"Completed agent (no duration recorded)")

    # Record completion in state
    state["last_agent_end"] = timestamp
    state.setdefault("agent_timeline", []).append({
        "completed_at": timestamp,
        "duration_sec": duration
    })

    return None


scraper_agent = LlmAgent(
    model="gemini-2.5-flash-lite",
    name="scraper_agent",
    instruction="Always call a tool to fetch real scraped news. Never fabricate news.",
    description="Fetches real scraped news and stores structured data.",
    tools=[
        get_states_news,
        get_national_news,
        get_international_news,
        get_sports_news,
        get_entertainment_news,
    ],
    output_key="scraper_output",
    before_model_callback=input_guardrail,
    before_tool_callback=tool_guardrail,
)
# summariser_agent = LlmAgent(
#     model="gemini-2.5-flash-lite",
#     name="summariser_agent",
#     description=f"Summarises scraped articles and writes in a {STYLE_OF_WRITING} tone.",
#     instruction=(
#         f"You will receive a list of `scraper_output` items, each matching this schema:\n"
#         "{ title, link, date, author, article }\n\n"
#         f"Write a **clean markdown news report** in a **{STYLE_OF_WRITING} tone**.\n\n"
#         "CRITICAL RULES:\n"
#         "1. Output ONLY the formatted markdown — no prefatory text like 'Here’s a summary' or explanations.\n"
#         "2. For EACH item:\n"
#         "   • Print the title as a markdown H2\n"
#         "   • Then show: Date | Author | Source link\n"
#         f"   • Summarise ONLY the `article` field into 120–160 words, in {STYLE_OF_WRITING} tone.\n"
#         "3. Do NOT merge articles or skip any.\n"
#         "4. No bullet lists, no prefaces, no closing remarks.\n\n"
#         "Example Output:\n"
#         "## India signs new tech deal with Japan\n"
#         "**Date:** Feb 15, 2025 | **Author:** TOI Desk | [Source](https://example.com)\n\n"
#         f"Summary paragraph here (written in a {STYLE_OF_WRITING} tone)...\n"
#     ),
#     output_key="summary_output"
# )


summariser_agent = LlmAgent(
    model="gemini-2.5-flash-lite",
    name="summariser_agent",
    description=f"Summarises scraped articles and writes in a {STYLE_OF_WRITING} tone.",
    instruction=(
        f"You will receive a list of `scraper_output` items, each matching this schema:\n"
        "{ title, link, date, author, article, image_url }\n\n"
        f"Write a **clean markdown news report** in a **{STYLE_OF_WRITING} tone**.\n\n"
        "CRITICAL RULES:\n"
        "1. Output ONLY the formatted markdown — no prefatory text like 'Here’s a summary' or explanations.\n"
        "2. For EACH item:\n"
        "   • Print the title as a markdown H2\n"
        "   • Then show: Date | Author | Source link | Image Link \n"
        "   • If `image_url` is available, do NOT embed the image — just print the link as:\n"
        "     **Image:** image_url\n"
        f"   • Summarise ONLY the `article` field into 120–160 words, in {STYLE_OF_WRITING} tone.\n"
        "3. Do NOT merge articles or skip any.\n"
        "4. No bullet lists, no prefaces, no closing remarks.\n\n"
        "Example Output:\n"
        "## India signs new tech deal with Japan\n"
        "**Date:** Feb 15, 2025 | **Author:** TOI Desk | [Source](https://example.com) | [Image](https://example.com/image.jpg)\n\n"
        f"Summary paragraph here (written in a {STYLE_OF_WRITING} tone)...\n"
    ),
    output_key="summary_output",
)




multilingual_agent = LlmAgent(
    name="MultilingualTranslatorAgent",
    model="gemini-2.5-flash-lite",
    instruction=(
        "Use the **entire text** from the 'summary_output' variable as your translation source.\n"
        "Do not summarize, skip, or shorten it.\n"
        f"You are a multilingual translator. Translate the markdown text found in 'summary_output' "
        f"into **{TARGET_LANGUAGE}** (ISO 639-1 code). "
        "Preserve Markdown formatting.\n\n"
        "Rules:\n"
        "- Do not translate URLs, code blocks, or text inside backticks.\n"
        "- Preserve names, dates, and quoted entities.\n"
        "- Keep the same structure, spacing, and formatting.\n"
        "- Output ONLY the translated text (no explanations).\n"
    ),
    output_key="translated_text",
)



root_agent = SequentialAgent(
    name="NewsPipeline",
    sub_agents=[scraper_agent, summariser_agent, multilingual_agent],
    description=f"Fetches scraped news → Summarises in {STYLE_OF_WRITING} tone → Translates to {TARGET_LANGUAGE.upper()}."
)

print(f"FINAL PIPELINE READY — Style: {STYLE_OF_WRITING} | Language: {TARGET_LANGUAGE.upper()}")
