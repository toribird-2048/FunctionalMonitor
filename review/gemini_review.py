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

context_path = "review/REVIEW_CONTEXT.md"

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
        print(f"Skipping large file (>500KB): {file_path} ({file_size//1024}KB)")
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
        あなたは技術的合理性を最優先するシニアエンジニアです。
        プロジェクトの前提条件（REVIEW_CONTEXT.md）を熟知した上で、提供された差分（diff）を厳格にレビューしてください。

        ## レビュー対象
        - ファイル名: {file_path}
        - プロジェクト背景: {context_content}

        ## 入力データ
        - ファイル全文: 
        {full_content}
        - 差分 (diff): 
        {diff_content}

        ## レビューの出力構成
        指摘事項がある場合は、必ず以下の2つのセクションに分類して出力してください。指摘がないセクションは「なし」と記載してください。
        全体を通して指摘がない場合のみ、 review-type: Pass と出力してください。

        ---

        ### 🚨 [Critical] バグ・セキュリティ・致命的欠陥
        ※動作不良、クラッシュ、セキュリティ脆弱性など、修正が必須な事項。

        - **title**: <指摘の要約>
        - **review-type**: <バグ報告 | セキュリティ懸念>
        - **review-content**: <具体的になぜ問題なのか、どのクラス/メソッドで発生しているか>
        - **advice**: <具体的な修正コード案や対策>

        ---

        ### 💡 [Advice] 改善案・パフォーマンス・保守性
        ※動作はするが、リファクタリング、効率化、運用上の懸念など、検討を推奨する事項。

        - **title**: <指摘の要約>
        - **review-type**: <パフォーマンス改善 | 改善案 | 保守性向上>
        - **review-content**: <現状の問題点と、変更によるメリット>
        - **advice**: <具体的な実装案や代替手法>

        ---

        ## 指示事項
        1. **優先順位の明確化**: 修正しないと実害が出るものは必ず [Critical] に、それ以外は [Advice] に配置してください。
        2. **場所の特定**: 行番号は使用せず、「UiControllerのcheck_alertsメソッド内」のように、構造名（クラス名やメソッド名）を用いて場所を特定してください。
        3. **文体の簡潔化**: 冗長な挨拶は不要です。事実と論理に基づき、簡潔に記述してください。
        4. **文脈の考慮**: REVIEW_CONTEXT.md に記載された既知の決定事項（例：あえてキャッシュを導入しない等）に対する重複指摘は避けてください。
    """

    for attempt in range(MAX_RETRIES):
        start_time = time.time()
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt
            )
            elapsed = time.time() - start_time
            print(f"Done! ({elapsed:.1f}s)")
            break
        except Exception as e:
            if "503" in str(e) and attempt < MAX_RETRIES - 1:
                print(f"Server busy, retrying in 5s ... (Attempt{attempt+1})")
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
