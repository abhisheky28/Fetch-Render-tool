# fetch_and_render.py (Flask Version)
from flask import Flask, render_template, request
from fetcher import perform_fetch_selenium

fetch_and_render = Flask(__name__)

# --- User Agent and Language Definitions (Moved from Streamlit) ---
USER_AGENTS = {
    "Googlebot (Desktop)": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Googlebot (Smartphone)": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
}
LANGUAGES = {
    "English (US)": "en-US,en;q=0.9", "English (UK)": "en-GB,en;q=0.8", "Spanish (Spain)": "es-ES,es;q=0.9",
    "French (France)": "fr-FR,fr;q=0.9", "German (Germany)": "de-DE,de;q=0.9", "Japanese (Japan)": "ja-JP,ja;q=0.9",
    "Chinese (China)": "zh-CN,zh;q=0.9", "Hindi (India)": "hi-IN,hi;q=0.9",
}

@fetch_and_render.route('/')
def index():
    """Renders the main input form."""
    return render_template('index.html', user_agents=USER_AGENTS, languages=LANGUAGES)

@fetch_and_render.route('/fetch', methods=['POST'])
def fetch():
    """Handles the form submission, calls the fetcher, and renders results."""
    # --- Get all data from the form ---
    url_input = request.form.get('url')
    user_agent_key = request.form.get('user_agent_key')
    language_key = request.form.get('language_key')
    
    # Checkboxes will not be in the form data if unchecked, so we check for their presence
    obey_robots_input = 'obey_robots' in request.form
    render_js_input = 'render_js' in request.form # Note: fetcher.py always renders JS, but we keep the logic
    headless_input = 'headless' in request.form
    
    timeout_input = int(request.form.get('timeout', 3))
    
    if not url_input or not url_input.startswith(('http://', 'https://')):
        return "Error: Please enter a valid URL starting with http:// or https://", 400

    # --- Call the existing fetcher logic ---
    results = perform_fetch_selenium(
        url=url_input,
        user_agent_key=user_agent_key,
        user_agent_string=USER_AGENTS[user_agent_key],
        headless=headless_input,
        timeout_seconds=timeout_input,
        language=LANGUAGES[language_key],
        obey_robots=obey_robots_input
    )

    if results.get("error"):
        return f"A critical error occurred: {results['error']}", 500

    # --- Render the results template with the data ---
    # We use **results to unpack the dictionary into template variables
    return render_template('results.html', url=url_input, user_agent_key=user_agent_key, **results)

if __name__ == '__main__':
    # To run: use `flask run` in terminal, or `python fetch_and_render.py`
    fetch_and_render.run(debug=True)