# import json
# from google.adk.agents.llm_agent import Agent
# from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
# # from google.adk.agents.tool import tool


# from typing import Optional, Dict, Any, Set
# from google.adk.agents.callback_context import CallbackContext
# from google.adk.models.llm_request import LlmRequest
# from google.adk.models.llm_response import LlmResponse
# from google.genai import types as genai_types 
# from google.adk.tools.base_tool import BaseTool
# from google.adk.tools.tool_context import ToolContext


# from Scrapers.entertainment_scraper import scrape_entertainment_top_n
# from Scrapers.sports_scraper import scrape_sports_top_n
# from Scrapers.international_scraper import scrape_international_top_n
# from Scrapers.national_scraper import scrape_national_top_n
# from Scrapers.states_scraper import scrape_states_top_n



# BANNED_WORDS: Set[str] = {
#     "kill yourself", "how to make a bomb", "i will kill you", "rape", 
#     "nazi", "faggot", "retard", "child porn" ,"autistic","murder"
# }

# NEWS_KEYWORDS: Set[str] = {
#     "news", "headlines", "article", "happening in", "sports", 
#     "entertainment", "politics", "business", "tech", "latest", 
#     "updates", "breaking", "tell me about", "what's new","information"
# }


# VALID_STATES: Set[str] = {
#     "mumbai", "delhi", "bengaluru", "kolkata", "chennai", "pune", 
#     "hyderabad", "ahmedabad", "maharashtra", "karnataka", 
#     "west bengal", "tamil nadu", "gujarat", "uttar pradesh", 
#     "rajasthan", "punjab", "kerala", "andhra pradesh", "goa"
# }

# MAX_ARTICLE_LIMIT: int = 20

# SCRAPER_TOOL_NAMES: Set[str] = {
#     "get_states_news", "get_national_news", "get_international_news",
#     "get_sports_news", "get_entertainment_news"
# }



# def get_states_news(state: str, limit: int = 10) -> str:
#     """Returns latest state-level news. Example: state='mumbai'"""
#     data = scrape_states_top_n(state, limit)
#     return json.dumps(data, ensure_ascii=False)

# def get_national_news(limit: int = 10) -> str:
#     """Returns latest national-level Indian news."""
#     data = scrape_national_top_n(limit)
#     return json.dumps(data, ensure_ascii=False)

# def get_international_news(limit: int = 10) -> str:
#     """Returns recent global/international news."""
#     data = scrape_international_top_n(limit)
#     return json.dumps(data, ensure_ascii=False)

# def get_sports_news(limit: int = 10) -> str:
#     """Returns top sports headlines."""
#     data = scrape_sports_top_n(limit)
#     return json.dumps(data, ensure_ascii=False)

# def get_entertainment_news(limit: int = 10) -> str:
#     """Returns latest entertainment news."""
#     data = scrape_entertainment_top_n(limit)
#     return json.dumps(data, ensure_ascii=False)



# def input_guardrail(
#     callback_context: CallbackContext, llm_request: LlmRequest
# ) -> Optional[LlmResponse]:
#     """
#     INPUT GUARDRAIL (before_model_callback)
#     1. Checks for BANNED_WORDS.
#     2. Checks for off-topic requests (missing NEWS_KEYWORDS).
#     """
#     print(f"--- Callback: input_guardrail running for agent: {callback_context.agent_name} ---")

#     last_user_message_text = ""
#     if llm_request.contents:
#         for content in reversed(llm_request.contents):
#             if content.role == 'user' and content.parts:
#                 if content.parts[0].text:
#                     last_user_message_text = content.parts[0].text.lower()
#                     break
    
#     if not last_user_message_text:
#         print("--- Callback: No user text found. Allowing. ---")
#         return None # No text to check, allow

#     # guard rail 1 - user input containing banned words
#     if any(word in last_user_message_text for word in BANNED_WORDS):
#         print(f"--- Callback: Found banned word. Blocking LLM call! ---")
#         return LlmResponse(
#             content=genai_types.Content(
#                 role="model",
#                 parts=[genai_types.Part(text="I cannot process this request due to a content policy violation.")]
#             )
#         )

#     # guard rail 2 user asking for unrelated information -
#     if not any(keyword in last_user_message_text for keyword in NEWS_KEYWORDS):
#         print(f"--- Callback: Request appears off-topic. Blocking LLM call! ---")
#         return LlmResponse(
#             content=genai_types.Content(
#                 role="model",
#                 parts=[genai_types.Part(text="I am a news assistant. I can only fetch news, headlines, and articles.")]
#             )
#         )

#     print(f"--- Callback: Input passed guardrails. Allowing LLM call. ---")
#     return None 

# def tool_guardrail(
#     tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
# ) -> Optional[Dict]:
#     """
#     TOOL GUARDRAIL (before_tool_callback)
#     1. Validates 'state' argument for 'get_states_news' tool.
#     """
#     tool_name = tool.name
#     print(f"--- Callback: tool_guardrail running for tool '{tool_name}' ---")
            
#     # guardrail 3 - making sure valid states is given.
#     if tool_name == "get_states_news":
#         state_arg = args.get("state", "").lower().strip() 
        
#         if not state_arg:
#             print(f"--- Callback: 'get_states_news' called with no state. Blocking. ---")
#             return {
#                 "status": "error",
#                 "error_message": "You asked for state news but did not provide a state or city. Please specify one (e.g., 'news from Mumbai')."
#             }

#         if state_arg not in VALID_STATES:
#             print(f"--- Callback: Invalid state '{state_arg}'. Blocking tool. ---")
#             return {
#                 "status": "error",
#                 "error_message": f"Policy Error: I do not have news for '{args.get('state')}'. Please try a valid Indian state or major city."
#             }
    
#     print(f"--- Callback: Tool args passed guardrails. Allowing tool '{tool_name}' to run. ---")
#     return None 



# scraper_agent = Agent(
#     model="gemini-2.5-flash",
#     name="scraper_agent", 
#     description="A news assistant that fetches live scraped content.",
#     instruction=(
#         "When the user asks for news, ALWAYS call the correct tool instead of generating fake data. "
#         "Use the tools to fetch real scraped news."
#     ),
#     tools=[
#         get_states_news,
#         get_national_news,
#         get_international_news,
#         get_sports_news,
#         get_entertainment_news,
#     ],
#     output_key = "scraper_output",
    
#     before_model_callback=input_guardrail,
#     before_tool_callback=tool_guardrail
# )

# summariser_agent = Agent(
#     model="gemini-2.5-flash",
#     name="summariser_agent",
#     description="Converts raw scraped news JSON into a polished readable report.",
#     instruction=(
#         "You will receive a variable called `scraper_output` that contains a JSON list of news articles.\n"
#         "Your job is to SUMMARISE each article clearly and professionally.\n\n"
#         "Keep summaries **150-170 words max per article**.\n"
#         "Preserve all key facts: who, what, when, where, why, quotes.\n"
#         "Tone should be like a journalist writing a news digest.\n"
#         "Do NOT copy/paste full article text.\n\n"
#         "Output must contain ALL articles. Do NOT merge or skip any."
#     )
# )

# root_agent = SequentialAgent(
#     name="NewsPipeline",
#     sub_agents=[
#         scraper_agent, 
#         summariser_agent,
#     ],
#     description="Fetches news through scraping tools, then formats them into a clean report.")

# print("✅ Agents defined with Input and Tool Guardrails.")
# print(f"Scraper agent '{scraper_agent.name}' is now protected.")


import datetime
import json
import logging
from typing import Optional, Dict, Any, Set, List
from pydantic import BaseModel
from google.adk.agents import LlmAgent, Agent, SequentialAgent
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



class NewsItem(BaseModel):
    title: str
    link: str
    date: str
    author: Optional[str] = ""
    article: Optional[str] = ""




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

    if any(w in last_user_text for w in BANNED_WORDS):
        return LlmResponse(
            content=genai_types.Content(
                role="model",
                parts=[genai_types.Part(text="I cannot process this request due to a content policy violation.")]
            )
        )

    if not any(w in last_user_text for w in NEWS_KEYWORDS):
        return LlmResponse(
            content=genai_types.Content(
                role="model",
                parts=[genai_types.Part(text="I am a news assistant. I can only fetch news, headlines, and articles.")]
            )
        )

    return None




def tool_guardrail(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
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

def before_agent_callback(callback_context: CallbackContext):
    """Logs start of agent execution."""
    state = callback_context.state
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Initialize global counter
    state["run_counter"] = state.get("run_counter", 0) + 1
    state["last_agent_start"] = timestamp

    print(f"\n=== AGENT START] ===")
    print(f"Run #: {state['run_counter']}")
    print(f"Timestamp: {timestamp}")

    # Also log via logging module
    logging.info(f"Starting agent (Run #{state['run_counter']}) at {timestamp}")

    return None


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

def wrap(items: list) -> List[NewsItem]:
    return [NewsItem(**item) for item in items]


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




scraper_agent = LlmAgent(
    model="gemini-2.5-flash",
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
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback
)




summariser_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="summariser_agent",
    description="Converts structured news items into a clean markdown digest.",
    instruction=(
        "You will receive a list of `scraper_output` items, each matching this schema:\n"
        "{ title, link, date, author, article }\n\n"
        "Write a **clean markdown news report**.\n"
        "For EACH item:\n"
        "  • Print the title as a markdown H2\n"
        "  • Then show: Date | Author | Source link\n"
        "  • Then summarise ONLY the `article` field into 120–160 words\n"
        "  • Do NOT remove or merge articles\n"
        "  • No bullet dumps, no walls of text – clean readable formatting.\n\n"
        "Example Format:\n"
        "## India signs new tech deal with Japan\n"
        "**Date:** Feb 15, 2025 | **Author:** TOI Desk | [Source](https://example.com)\n\n"
        "Summary paragraph here...\n"
    ),
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback
)



root_agent = SequentialAgent(
    name="NewsPipeline",
    sub_agents=[scraper_agent, summariser_agent],
    description="Fetches scraped news → formats as a clean markdown briefing."
)

print("FINAL PIPELINE READY WITH STRUCTURED OUTPUT AND CLEAN SUMMARIES")
