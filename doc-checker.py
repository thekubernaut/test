#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
# OpenAI support (optional)
# import openai
import ollama
from github import Github
from git import Repo
import json

# Configuration
DOC_PATHS = ["docs/", "README.md"]  # Add more documentation paths as needed
LLM_BACKEND = 'ollama'  # Only Ollama is supported by default
MODEL = os.getenv('LLM_MODEL', 'llama2')  # For Ollama: 'llama2', 'mistral', etc.
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

def get_pull_request_info() -> Dict:
    """Get information about the current pull request from GitHub Actions environment."""
    event_path = os.getenv('GITHUB_EVENT_PATH')
    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH not found")
    
    with open(event_path, 'r') as f:
        event_data = json.load(f)
    
    return {
        'repo': event_data['repository']['full_name'],
        'pr_number': event_data['number'],
        'base_sha': event_data['pull_request']['base']['sha'],
        'head_sha': event_data['pull_request']['head']['sha']
    }

def get_code_diff(base_sha: str, head_sha: str) -> str:
    """Get the git diff between base and head commits."""
    repo = Repo('.')
    diff = repo.git.diff(base_sha, head_sha)
    return diff

def read_documentation() -> Dict[str, str]:
    """Read all documentation files."""
    docs = {}
    for doc_path in DOC_PATHS:
        path = Path(doc_path)
        if path.is_file():
            docs[str(path)] = path.read_text()
        elif path.is_dir():
            for doc_file in path.rglob('*.md'):
                docs[str(doc_file)] = doc_file.read_text()
    return docs

# OpenAI support (optional)
"""
def analyze_with_openai(diff: str, doc_content: str) -> str:
    # Use OpenAI to analyze documentation.
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = f"""
    # Analyze if the following documentation needs to be updated based on these code changes.
    # If the documentation is already accurate or the changes don't affect it, return the original documentation.
    # If updates are needed, provide the updated documentation.
    
    # Code changes:
    # {diff}
    
    # Documentation to check:
    # {doc_content}
    
    # Return only the updated documentation if changes are needed, or the original if no changes are required.
    # """
    
    # response = client.chat.completions.create(
    #     model=MODEL,
    #     messages=[
    #         {"role": "system", "content": "You are a documentation expert. Analyze if documentation needs updates based on code changes."},
    #         {"role": "user", "content": prompt}
    #     ],
    #     temperature=0.3
    # )
    
    # return response.choices[0].message.content
"""

def analyze_with_ollama(diff: str, doc_content: str) -> str:
    """Use Ollama to analyze documentation."""
    client = ollama.Client(host=OLLAMA_HOST)
    
    prompt = f"""
    Analyze if the following documentation needs to be updated based on these code changes.
    If the documentation is already accurate or the changes don't affect it, return the original documentation.
    If updates are needed, provide the updated documentation.
    
    Code changes:
    {diff}
    
    Documentation to check:
    {doc_content}
    
    Return only the updated documentation if changes are needed, or the original if no changes are required.
    """
    
    response = client.generate(
        model=MODEL,
        prompt=prompt,
        system="You are a documentation expert. Analyze if documentation needs updates based on code changes.",
        temperature=0.3
    )
    
    return response.response

def analyze_documentation(diff: str, docs: Dict[str, str]) -> Dict[str, str]:
    """Analyze if documentation needs updates based on code changes."""
    updated_docs = {}
    
    for doc_path, doc_content in docs.items():
        updated_content = analyze_with_ollama(diff, doc_content)
        
        if updated_content != doc_content:
            updated_docs[doc_path] = updated_content
    
    return updated_docs

def create_pull_request(updated_docs: Dict[str, str], pr_info: Dict):
    """Create a new branch, commit changes, and open a pull request."""
    if not updated_docs:
        print("No documentation updates needed.")
        return
    
    # Create a new branch
    branch_name = f"docs-update-{pr_info['pr_number']}"
    repo = Repo('.')
    repo.git.checkout('-b', branch_name)
    
    # Commit changes
    for doc_path, content in updated_docs.items():
        with open(doc_path, 'w') as f:
            f.write(content)
        repo.git.add(doc_path)
    
    repo.git.commit('-m', f"Update documentation based on PR #{pr_info['pr_number']}")
    repo.git.push('origin', branch_name)
    
    # Create pull request
    github = Github(os.getenv('GITHUB_TOKEN'))
    repo = github.get_repo(pr_info['repo'])
    pr = repo.create_pull(
        title=f"Documentation updates for PR #{pr_info['pr_number']}",
        body="This PR contains documentation updates based on recent code changes.",
        head=branch_name,
        base="main"
    )
    print(f"Created PR #{pr.number}")

def main():
    try:
        # Get pull request information
        pr_info = get_pull_request_info()
        
        # Get code changes
        diff = get_code_diff(pr_info['base_sha'], pr_info['head_sha'])
        
        # Read documentation
        docs = read_documentation()
        
        # Analyze documentation
        updated_docs = analyze_documentation(diff, docs)
        
        # Create pull request if needed
        create_pull_request(updated_docs, pr_info)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 
