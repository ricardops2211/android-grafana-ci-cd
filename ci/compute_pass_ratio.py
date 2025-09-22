#!/usr/bin/env python3
import os, sys
def main():
    try:
        total = int(os.environ.get("TOTAL", "1"))
        ok    = int(os.environ.get("OK", "0"))
        print(round((ok/total) if total>0 else 0, 3))
    except Exception:
        print("0.0"); sys.exit(0)
if __name__ == "__main__":
    main()
