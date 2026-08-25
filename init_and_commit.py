import os
import dulwich.porcelain as git
from dulwich.repo import Repo

repo_path = r"c:\Users\mitsu\Downloads\TriNetra AI"

# Check if .git exists, if not initialize
git_dir = os.path.join(repo_path, ".git")
if not os.path.exists(git_dir):
    repo = git.init(repo_path)
    print("Initialized new Git repository.")
else:
    repo = Repo(repo_path)
    print("Opened existing Git repository.")

# Stage all files
git.add(repo_path, paths=["."])
print("Staged all files.")

# Check status
status = git.status(repo_path)
print(f"Staged files count: {len(status.staged['add']) + len(status.staged['modify'])}")

# Commit
commit_msg = "feat: complete Phase 1 validation MVP and Phase 2 Spring Boot & React architecture"
try:
    commit_id = git.commit(
        repo_path,
        message=commit_msg.encode("utf-8"),
        author="Sanjai <sanjai@trinetra.ai>".encode("utf-8"),
        committer="Sanjai <sanjai@trinetra.ai>".encode("utf-8"),
    )
    print(f"Committed successfully: {commit_id.decode() if isinstance(commit_id, bytes) else commit_id}")
except Exception as e:
    print(f"Commit note: {e}")

# Set remote origin
config = repo.get_config()
remote_url = b"https://github.com/Sanjai-Quest/TriNetra-AI.git"
config.set((b"remote", b"origin"), b"url", remote_url)
config.set((b"remote", b"origin"), b"fetch", b"+refs/heads/*:refs/remotes/origin/*")
config.write_to_path()
print("Configured remote origin -> https://github.com/Sanjai-Quest/TriNetra-AI.git")
