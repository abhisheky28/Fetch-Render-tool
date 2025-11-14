🕵️ Fetch & Render Tool
This tool provides a web interface to fetch a URL with various configurations, render the page using a real browser engine, and display the results, including HTTP headers, rendered HTML, and a full-page screenshot. It is designed to accurately simulate how a specific client, like a Googlebot, would see and render a webpage.
🌟 Features
Customizable Fetching: Configure the User-Agent, Accept-Language header, and post-load timeout.
Accurate JavaScript Rendering: Utilizes a full browser engine via Selenium to render modern, JavaScript-heavy pages.
Desktop & Mobile Simulation: Fetch pages as either a desktop or smartphone Googlebot, correctly applying device-specific properties.
Full-Page Screenshots: Intelligently scrolls the entire page and stitches together a complete, seamless screenshot, capturing all lazy-loaded content.
Robots.txt Awareness: Option to check for and report resources that would be blocked by a site's robots.txt rules.
Detailed Results: View HTTP response headers, the final rendered HTML source code, and a high-fidelity visual representation of the page.
Interactive Web UI: A user-friendly interface built with Flask for easy input and clear presentation of results.
⚙️ How It Works
The application is composed of several key Python scripts and HTML templates that work together:
Flask Web Server (app.py): This is the core of the application. It serves the main HTML form (index.html) and handles the form submission. When a URL is submitted, it gathers all the user-defined settings (User-Agent, language, etc.) and passes them to the fetching module. After the fetch is complete, it renders the results using the results.html template.
Fetcher Engine (fetcher.py): This is the powerhouse of the tool. It uses selenium-wire to launch a Chrome browser with the specified configurations. It navigates to the target URL, waits for the page to load, and then executes a sophisticated scrolling and screenshotting mechanism. It takes multiple viewport-sized screenshots while scrolling down the page until it reaches the bottom, then stitches them together to create a single, seamless image. It also captures the final rendered HTML, HTTP headers, and other diagnostic data.
HTML Templates (index.html, results.html): These files define the structure and appearance of the user interface. index.html provides the input form, and results.html presents the fetched data in a clean, tabbed layout.
Configuration (config.py): This file stores important path information, such as the project's root directory and the location for the Chrome user profile.
Chrome Profile Setup (create_master_profile.py): This is a crucial one-time setup script. It launches a Chrome browser session allowing you to log into a Google account or accept cookie banners. This browser profile is then saved and used by the fetcher to maintain a consistent session and avoid issues like CAPTCHAs.
🛠️ Setup and Installation Guide
This guide provides detailed, step-by-step instructions to get the Fetch & Render tool running on your local machine.
Prerequisites
Before you begin, ensure you have the following installed on your computer:
Python (Version 3.7 or newer): The programming language the tool is built on.
To check if you have Python, open your terminal or Command Prompt and type: python --version or python3 --version. If you don't have it, download it from the official Python website.
Google Chrome Browser: The tool uses Chrome to render pages.
You must have the standard Google Chrome browser installed. You can download it from google.com/chrome.
Step 1: Organize Your Project Files
Create a new folder on your computer to hold all the project files. For example, you can create a folder named FetchAndRenderTool. Place all the files you have into this folder:
app.py
fetcher.py
config.py
create_master_profile.py
requirements.txt
A folder named templates which contains:
index.html
results.html
Step 2: Set Up a Python Virtual Environment
Using a virtual environment is highly recommended as it keeps the project's dependencies isolated from other Python projects on your system.
Open your terminal or Command Prompt.
Navigate to your project folder using the cd command.
code
Bash
# Example:
cd C:\Users\YourName\Documents\FetchAndRenderTool
Create the virtual environment.
code
Bash
# On Windows
python -m venv venv

# On macOS or Linux
python3 -m venv venv
This will create a new venv folder inside your project directory.
Activate the virtual environment. You must do this every time you work on the project.
code
Bash
# On Windows
venv\Scripts\activate

# On macOS or Linux
source venv/bin/activate
When activated, you will see (venv) at the beginning of your terminal prompt.
Step 3: Install Required Libraries
All the necessary Python libraries are listed in the requirements.txt file.
Make sure your virtual environment is active (you see (venv) in your prompt).
Run the following command to install all dependencies at once:
code
Bash
pip install -r requirements.txt
This will download and install Selenium, Flask, Pillow, and all other required libraries into your virtual environment.
Step 4: Create the Master Chrome Profile (Important One-Time Step)
This step creates a dedicated Chrome profile that can store login sessions and cookies, which helps in fetching pages more reliably.
While still in your project directory in the terminal (with the virtual environment active), run the create_master_profile.py script:
code
Bash
python create_master_profile.py
ACTION REQUIRED: A new Chrome browser window will open. You will see instructions in your terminal. You have 90 seconds to:
Navigate to google.com.
Sign in to a Google account (e.g., rankingautomation07@gmail.com as mentioned in the original files).
Accept any cookie consent pop-ups.
When you are finished, manually close the browser window.
The script will automatically finish after 90 seconds. This process saves your session in a Chrome-Master-Profile folder, which the main tool will now use.
🚀 Running the Tool
After completing the setup, you are ready to launch the web application.
Make sure you are in the project's root directory and your virtual environment is activated ((venv) is visible in your prompt).
Run the following command to start the Flask web server:
code
Bash
flask --app app run --debug
The --debug flag enables debug mode, which is helpful for development as it automatically reloads the server when you make code changes.
Your terminal will show output indicating that the server is running. It will provide a local URL, which is typically:
http://127.0.0.1:5000
Open your regular web browser (like Chrome or Firefox) and navigate to that address. You should now see the "🕵️ Fetch & Render" interface.
📖 How to Use the Tool
URL: Enter the full URL of the webpage you want to fetch (e.g., https://www.example.com).
User Agent: Select the User-Agent you want to simulate. You can choose between a desktop or a smartphone Googlebot.
Accept-Language: Choose the language header to send with the request.
Obey robots.txt: If checked, the tool will analyze the robots.txt file and report any resources that are disallowed for the selected User-Agent.
Render JavaScript: This is always enabled to ensure the page is fully rendered.
Headless Browser: If checked, the Chrome browser will run in the background. Unchecking this is useful for debugging, as you will see the browser window open and perform the actions live.
Post-Load Timeout (s): The number of seconds the tool will wait after the page has loaded before it starts taking screenshots. This is useful for pages that load extra content after a delay.
Click FETCH: Press the button to start the process. Fetching can take some time depending on the complexity of the target page. Once complete, you will be taken to the results page.
Understanding the Results
The results page is divided into two tabs:
HTTP RESPONSE: This tab shows the HTTP status code (e.g., 200 OK) and all the response headers received from the server for the initial URL request.
RENDERED PAGE: This tab displays the final state of the page after rendering.
Rendered Source: The full HTML source code of the page after all JavaScript has been executed.
Visual Render: A complete, full-page screenshot. If a smartphone User-Agent was selected, the screenshot will be displayed within a mobile phone frame for better visualization.