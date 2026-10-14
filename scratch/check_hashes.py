import hashlib
import glob
import os

baseline_dir = "backend/data"
for f in sorted(glob.glob(os.path.join(baseline_dir, "*.csv"))):
    with open(f, "rb") as fp:
        digest = hashlib.sha256(fp.read()).hexdigest()
    print(f"{os.path.basename(f)}: {digest}")
