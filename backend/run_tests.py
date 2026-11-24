"""Run suites in separate processes so temporary environment/database settings never mix."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
for suite in ('test_regressions.py','test_meta_oauth.py','test_campaign_review.py','test_system_design.py'):
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','backend','-p',suite,'-v'],cwd=root)
    if result.returncode:raise SystemExit(result.returncode)
