# hallucination_guardrail.py
from crewai.tasks.hallucination_guardrail import HallucinationGuardrail
from crewai import LLM

def run_hallucination_guardrail(context: str, summary_output: str, threshold: float = 7.5):
    """
    Runs CrewAI's Hallucination Guardrail locally.
    Returns a dict with 'valid' and 'feedback'.
    """
    print("🧠 Running Hallucination Guardrail locally...")
    guardrail = HallucinationGuardrail(
        context=context,
        llm=LLM(model="gemini-2.5-flash-lite"),  
        threshold=threshold
    )

    result = guardrail(summary_output)

    feedback = getattr(result, "feedback", "No feedback provided by guardrail.")
    print(f"✅ Guardrail complete: valid={result.valid}, feedback={feedback}")

    return {"valid": result.valid, "feedback": feedback}
