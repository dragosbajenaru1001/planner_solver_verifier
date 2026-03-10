"""
Prompt Chaining: Planner → Solver → Verifier
Exemplu educativ pentru curs AI - Dragos

Fiecare agent are un rol specializat si primeste
output-ul agentului anterior ca input (chaining).
"""

from groq import Groq
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

load_dotenv()

client = Groq()

# ── configurare ──────────────────────────────────────────────────────────────

# citeste GROQ_API_KEY din environment
MODEL = "llama-3.3-70b-versatile"

# ── system prompts specializate ───────────────────────────────────────────────

PLANNER_SYSTEM = """Ești un PLANNER AI. Rolul tău este să analizezi problema
și să creezi un plan de rezolvare structurat.

Răspunde cu:
1. Tipul problemei identificate
2. Pașii necesari pentru rezolvare (numerotați, clari)
3. Formule sau cunoștințe necesare
4. Estimarea dificultății: Ușor / Mediu / Avansat

NU rezolva problema. Doar planifică."""

SOLVER_SYSTEM = """Ești un SOLVER AI. Primești problema originală ȘI planul
creat de Planner.

Urmează planul pas cu pas:
- Arată fiecare pas din calcul/raționament
- Fii explicit și detaliat
- Oferă un răspuns final clar, marcat cu: RĂSPUNS FINAL: ..."""

VERIFIER_SYSTEM = """Ești un VERIFIER AI. Primești problema originală și
soluția dată de Solver.

Rolul tău:
1. Verifică dacă soluția este corectă logic și numeric
2. Identifică eventuale erori
3. Oferă un verdict explicit: ✅ CORECT sau ❌ INCORECT
4. Dacă există erori, explică și dă răspunsul corect."""

# ── funcție helper ────────────────────────────────────────────────────────────

def call_agent(agent_name: str, system_prompt: str, user_message: str) -> str:
    """Apelează Claude cu un system prompt specific și returnează răspunsul."""
    print(f"\n{'='*60}")
    print(f"  {agent_name}")
    print(f"{'='*60}")

    response = client.chat.completions.create(
        messages=[
            # Set an optional system message. This sets the behavior of the
            # assistant and can be used to provide specific instructions for
            # how it should behave throughout the conversation.
            {
                "role": "system",
                "content": system_prompt
            },
            # Set a user message for the assistant to respond to.
            {
                "role": "user",
                "content": user_message,
            }
        ],

        # The language model which will generate the completion.
        model=MODEL
    )

    result = response.choices[0].message.content

    console = Console()
    console.print(Panel(Markdown(result), title=agent_name, expand=False))
    return result

# ── lanțul principal ──────────────────────────────────────────────────────────

def run_chain(problem: str) -> dict:
    """
    Rulează lanțul complet: Planner → Solver → Verifier.
    
    Fiecare etapă primește output-ul etapei anterioare → prompt chaining.
    """
    print(f"\n📋 PROBLEMĂ: {problem}")

    # ── ETAPA 1: PLANNER ──────────────────────────────────────────────────────
    plan = call_agent(
        agent_name="🗺️  ETAPA 1: PLANNER",
        system_prompt=PLANNER_SYSTEM,
        user_message=f"Problemă de rezolvat: {problem}"
    )

    # ── ETAPA 2: SOLVER ───────────────────────────────────────────────────────
    # Chaining: Solver primeste problema + planul Planner-ului
    solution = call_agent(
        agent_name="⚙️  ETAPA 2: SOLVER",
        system_prompt=SOLVER_SYSTEM,
        user_message=(
            f"Problema originală: {problem}\n\n"
            f"Planul Planner-ului:\n{plan}"
        )
    )

    # ── ETAPA 3: VERIFIER ─────────────────────────────────────────────────────
    # Chaining: Verifier primeste problema + solutia Solver-ului
    verdict = call_agent(
        agent_name="✅  ETAPA 3: VERIFIER",
        system_prompt=VERIFIER_SYSTEM,
        user_message=(
            f"Problema originală: {problem}\n\n"
            f"Soluția Solver-ului:\n{solution}"
        )
    )

    print(f"\n{'='*60}")
    print("  🏁 LANȚ COMPLET")
    print(f"{'='*60}\n")

    return {"plan": plan, "solution": solution, "verdict": verdict}

# ── exemple ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    problems = [
        # Matematică
        "Un tren pleacă din București la 08:30 cu 120 km/h. "
        "Alt tren pleacă din Constanța (225 km distanță) la 09:00 cu 90 km/h. "
        "Unde și când se întâlnesc?",

        # Logică
        "O parolă validă trebuie să aibă minim 8 caractere, "
        "cel puțin o literă mare, o cifră și un simbol special. "
        "Este parola 'Hello1!' validă?",
    ]

    # Rulează primul exemplu (comentează/decomentează pentru altele)
    result = run_chain(problems[0])
    # result = run_chain(problems[1])