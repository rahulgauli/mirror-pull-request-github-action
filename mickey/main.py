import os
import json
import asyncio
import subprocess
from typing import List


def run_subprocess(command: List[str], error_message: str) -> bool:
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{error_message}: {e}")
        return False

def clone_repository(repository: str) -> bool:
    return run_subprocess(
        ["git", "clone", f"https://github.com/rahulgauli/{repository}.git"],
        f"Error cloning repository {repository}"
    )

def checkout_branch(repository: str, branch_name: str) -> bool:
    os.chdir(repository)
    return run_subprocess(
        ["git", "checkout", "-b", branch_name],
        f"Error creating branch {branch_name} in {repository}"
    )

def create_workflow_dir() -> bool:
    try:
        os.makedirs(".github/workflows", exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directories: {e}")
        return False

def write_action_template(action_template: str) -> bool:
    try:
        with open(".github/workflows/new-action.yaml", "w") as f:
            f.write(action_template)
        return True
    except Exception as e:
        print(f"Error writing action template: {e}")
        return False

def git_add_commit() -> bool:
    if not run_subprocess(["git", "add", "."], "Error running git add"):
        return False
    return run_subprocess(["git", "commit", "-m", "Add new action workflow"], "Error running git commit")

def git_push(branch_name: str) -> bool:
    return run_subprocess(["git", "push", "-u", "origin", branch_name], f"Error pushing branch {branch_name}")

def create_github_pr(repository: str, branch_name: str, gh_token: str) -> bool:
    pr_command: List[str] = [
        "gh", "pr", "create",
        "--title", f"Add new action workflow for {repository}",
        "--body", "This PR adds a new action workflow.",
        "--base", "main",
        "--head", branch_name,
        "--repo", f"rahulgauli/{repository}"
    ]
    if gh_token:
        pr_command.append("--token")
        pr_command.append(gh_token)
    return run_subprocess(pr_command, f"Error creating PR for {repository}")

def cleanup_repository(repository: str) -> bool:
    os.chdir("..")
    return run_subprocess(["rm", "-rf", repository], f"Error cleaning up {repository}")


async def create_pull_request(repository: str, action_template: str, gh_token: str):
    print(f"Creating pull request for repository: {repository}")
    if not clone_repository(repository):
        print("Skipping this repository due to cloning error.")
        return
    branch_name = f"add-new-action-{repository}-{os.urandom(4).hex()}"
    if not checkout_branch(repository, branch_name):
        cleanup_repository(repository)
        return
    if not create_workflow_dir():
        cleanup_repository(repository)
        return
    if not write_action_template(action_template):
        cleanup_repository(repository)
        return
    if not git_add_commit():
        cleanup_repository(repository)
        return
    if not git_push(branch_name):
        cleanup_repository(repository)
        return
    if not create_github_pr(repository, branch_name, gh_token):
        cleanup_repository(repository)
        return
    print(f"Pull request created successfully for {repository}")
    cleanup_repository(repository)


if __name__ == "__main__":
    try:
        gh_token = os.getenv("GITHUB_PAT_TOKEN", "")
        with open("repository.json", "r") as repo:
            repositories = json.load(repo)
        with open("skeleton/new-action.yaml","r") as skeleton:
            action_template = skeleton.read()
            print(type(action_template))
        for a_repository in repositories:
            asyncio.run(create_pull_request(
                repository=a_repository,
                action_template=action_template,
                gh_token=gh_token
            ))
    except Exception as e:
        print(f"An error occurred: {e}")