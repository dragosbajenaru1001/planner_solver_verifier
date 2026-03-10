Instrucțiuni de folosire (în terminalul PowerShell):

# creați un virtual environment
python -m venv venv

# activați virtual environment-ul
python . .\venv\Scripts\activate

# instalați requirements
pip install -r .\requirements.txt

# redenumiți .env.sample în .env și adăugați cheia de Groq în fișierul .env

# rulați script-ul
python .\planner_solver_verifier.py