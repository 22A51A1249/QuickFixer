"""QuickFixer Unified Enterprise Application Launcher.

Starts the FastAPI server with the built React frontend on http://127.0.0.1:8000.
"""

import sys
import os
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    import uvicorn
    from config import settings
except ImportError as e:
    print(f"Error: Missing required packages: {e}")
    print("Please activate your virtual environment: .venv\\Scripts\\Activate.ps1")
    print("And install dependencies: pip install -r requirements.txt")
    sys.exit(1)


def main():
    print("=" * 70)
    print("  QUICKFIXER - AI-Powered Enterprise IT Support & Issue Resolution")
    print("  Tagline: 'Identify. Diagnose. Resolve.'")
    print("=" * 70)

    # Check SQLite database
    print(f"[*] SQLite Database: {settings.SQLITE_DB_PATH}")
    print(f"[*] FAISS Runbooks:  {settings.KNOWLEDGE_BASE_DIR}")

    # Check frontend bundle
    dist_dir = BASE_DIR / "frontend" / "dist"
    if (dist_dir / "index.html").exists():
        print(f"[*] React Frontend:  Built and mounted from {dist_dir}")
        print("[*] Application URL: http://127.0.0.1:8000")
    else:
        print("[!] Frontend not built. Run 'npm run build' inside frontend/")
        print("[*] API Swagger Docs: http://127.0.0.1:8000/docs")

    print("\n[+] Starting FastAPI Uvicorn Server on http://127.0.0.1:8000 ...")
    print("[+] Press CTRL+C to terminate.\n")

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()

