"""
BBQ Registration App - Refactored Version
Main application entry point
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=3000)


