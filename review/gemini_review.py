import os
import sys
import subprocess
import json
from google import genai
from github import Github
import time

base_branch = sys.argv[1]
head_branch = sys.argv[2]

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MAX_RETRIES = 3

IGNORE_EXTENSIONS = {
    '.ttf', '.woff', '.woff2', '.png', '.jpg', '.jpeg', '.gif', '.svg', 
    '.ico', '.pdf', '.zip', '.gz', '.tar', '.mp4', '.mp3', '.db', '.sqlite'
}

MAX_FILE_SIZE = 500 * 1024

context_path = "REVIEW_CONTEXT.md"

def get_git_result(command):
    try:
        return subprocess.check_output(command, shell=True).decode("utf-8").strip()
    except Exception:
        return ""

files = get_git_result(f"git diff --name-only origin/{base_branch}...HEAD").split("\n")

review_results = []

context_content = ""
if os.path.exists(context_path):
    with open(context_path, "r", encoding="utf-8") as f:
        context_content = f.read()

for file_path in files:
    if not file_path or not os.path.exists(file_path) or os.path.isdir(file_path):
        continue

    _, ext = os.path.splitext(file_path)
    if ext.lower() in IGNORE_EXTENSIONS:
        print(f"Skipping binary/unsupported file: {file_path}")
        continue

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        print(f"Skipping large file (>500MB): {file_path} ({file_size//1024}KB)")
        continue

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            full_content = f.read()
    except UnicodeDecodeError:
        print(f"Skipping non-UTF8 file: {file_path}")
        continue
    
    diff_content = get_git_result(f"git diff origin/{base_branch}...HEAD -- {file_path}")
    if not diff_content:
        continue

    print(f"[Reviewing] {file_path} ({file_size // 1024}KB) ... ", end="", flush=True)

    prompt = f"""
    あなたはシニアエンジニアです。プロジェクトの前提条件を理解した上で、以下のファイルのコードレビューを行ってください。

    ファイル名： {file_path}

    ### プロジェクトの前提条件
    {context_content}

    ### 修正後のファイル全文
    {full_content}

    ### 変更箇所の差分(diff)
    {diff_content}

    ### レビューの構成
    title: ~~~
    review-type: ~~~
    review-content: ~~~
    advice: ~~~

    review-type2: ~~~
    review-content2: ~~~
    advice2: ~~~
    .
    .
    .
    
    #### review-typeの例
    - バグ報告
    - セキュリティ懸念
    - パフォーマンス改善
    - 改善案
    - Pass
    など
    
    ### 指示
    - 差分箇所を中心に、バグ、セキュリティ、パフォーマンス上の懸念、改善案があれば指摘してください。
    - 特に問題がなければ<review-type>にPassとだけ書いてください。それ以外の時にPassと書くことは、レビューを無効化するのと同義であるため禁止します。
    - 指示は簡潔かつ具体的にお願いします。
    """

    for attempt in range(MAX_RETRIES):
        start_time = time.time()
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )
            elapsed = time.time() - start_time
            print(f"Done! ({elapsed:.1f}s)")
            break
        except Exception as e:
            if "503" in str(e) and attempt < MAX_RETRIES - 1:
                print(f"Server busy, rtrying in 5s ... (Attempt{attempt+1})")
                print(f"Error details: {e}")
                continue
            raise e

    time.sleep(1)

    if response.text and "Pass" not in response.text:
        review_results.append(f"### Review for `{file_path}`\n{response.text}")

if review_results:
    final_comment = "## Gemini Code Review Result\n\n" + "\n\n---\n\n".join(review_results)

    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])

    try:
        with open(os.environ["GITHUB_EVENT_PATH"], "r") as f:
            event_data = json.load(f)
            pr_number = event_data["number"]

        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(final_comment)
        print("Comment posted successfully!")
    except KeyError:
        print("Not a Pull Request event. Skipping comment.")
else:
    print("No issues found. Pass!")
