# Text Correction and Analysis Web Application

A comprehensive text correction tool with user authentication and history tracking, built with Flask.

## Features

- **Multi-layer Corrections:**
  - Spelling correction using Yandex Speller
  - Grammar correction with Gramformer
  - Punctuation restoration using DeepMultilingualPunctuation
  - Capitalization correction

- **User Authentication:**
  - Secure registration and login system
  - Session management

- **Correction History:**
  - Full history tracking with timestamps
  - Detailed error breakdowns
  - Original vs corrected text comparison

- **Interactive Web Interface:**
  - Real-time correction preview
  - Error type filtering
  - Detailed correction explanations

## Prerequisites

- Python 3.8+
- Java Runtime Environment (for language-tool-python)
- Basic terminal/command line knowledge

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/text-corrector.git
cd text-corrector

pip install -r requirements.txt

python app.py

Important notes:
1. The application requires Java Runtime Environment (JRE) for language-tool-python to work
2. First startup might take longer as it needs to download ML models
3. Gramformer and punctuation models require significant memory (recommended 4GB+ RAM)
4. For production use, consider:
   - Replacing SQLite with PostgreSQL/MySQL
   - Adding rate limiting
   - Implementing proper error handling
   - Using a WSGI server like Gunicorn

You might want to create a separate `LICENSE` file and adjust the repository URLs in the README to match your actual project location.

