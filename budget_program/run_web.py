"""
Quick start script for the budget web dashboard.

Run this script to start the web server:
    python run_web.py

Then open http://localhost:5000 in your browser.
"""

from web_app import app, init_db

if __name__ == "__main__":
    init_db()
    print("\n" + "="*60)
    print("Budget Dashboard is starting...")
    print("="*60)
    print("\n🌐 Open your browser and go to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server\n")
    app.run(debug=True, port=5000)
