from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Get from: https://github.com/settings/tokens

INPUT_FILE = "/workspaces/Resume/repos.json"
OUTPUT_FILE = "/workspaces/Resume/repos_enriched.json"

# API behavior
RATE_LIMIT_THRESHOLD = 10  # Wait when remaining requests < this
API_DELAY_SECONDS = 0.5    # Delay between API calls
MAX_CONTRIBUTORS_PAGES = 5  # Max pages to fetch (100 per page)

# Complexity scoring weights (must sum to 100)
COMPLEXITY_WEIGHTS = {
    "language_diversity": 20,
    "size": 20,
    "files": 20,
    "contributors": 20,
    "commits": 20
}

# Topic keyword mappings
TOPIC_KEYWORDS = {
    'api': ['api', 'rest', 'backend'],
    'web': ['web', 'frontend', 'website'],
    'data': ['data-science', 'analytics'],
    'ml': ['machine-learning', 'ai', 'data-science'],
    'mobile': ['mobile', 'ios', 'android'],
    'automation': ['automation', 'devops', 'ci-cd']
}