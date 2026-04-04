import os
import sys
import subprocess
import json
from google import genai
from github import Github
import time
import random

REQUIRED_ENV_VARS = ["GEMINI_API_KEY", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]

def validate_environment():
    """実行時に必要な環境変数が揃っているか確認する"""
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        print(f"Error: 以下の環境変数が設定されていません: {','.join(missing)}", file=sys.stderr)
        sys.exit(1)

validate_environment()


if len(sys.argv) < 3:
    print("引数が正しくありません。例：`gemini_review.py {base_branch} {head_branch}`")
    sys.exit(1)

base_branch = sys.argv[1]
head_branch = sys.argv[2]



client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MAX_RETRIES = 3

IGNORE_EXTENSIONS = {
    '.ttf', '.woff', '.woff2', '.png', '.jpg', '.jpeg', '.gif', '.svg', 
    '.ico', '.pdf', '.zip', '.gz', '.tar', '.mp4', '.mp3', '.db', '.sqlite', '.env', ".git"
}

IGNORE_FILES = {os.path.basename(__file__), "package-lock.json", "yarn.lock"}

MAX_FILE_SIZE = 500 * 1024

context_path = "review/REVIEW_CONTEXT.md"

review_model = "gemma-4-31b-it"

appendix_themes = ("猫の豆知識", "数学の面白い概念", "物理の面白い話", "コンピュータの歴史", "任意のプログラミング言語の豆知識", "IT系の小話", "言語学の雑学", "なぞなぞまたはクイズ")

REPO_ROOT = os.path.abspath(os.getcwd())



def get_filtered_project_structure():
    raw_files = get_git_result(["git", "ls-files", "--cached", "--exclude-standard"]).split("\n")
    filtered = []

    for f in raw_files:
        if not f: continue

        _, ext = os.path.splitext(f)
        if ext.lower() in IGNORE_EXTENSIONS: continue

        if os.path.basename(f) in IGNORE_FILES: continue

        if any(secret in f for secret in ["key", "token", ".pem", ".env", ".git/", "node_modules/", "secrets/"]):
            continue
        filtered.append(f)
    return "\n".join(filtered)

def get_git_result(command_list):
    try:
        return subprocess.check_output(command_list).decode("utf-8").strip()
    except Exception:
        return ""

def read_repository_file(path: str) -> str:
    """
    リポジトリ内の指定されたファイルの全文を読み取ります。
    引数: str (ファイルパス)
    戻り値: str (ファイル内容)
    """
    abs_path = os.path.realpath(path)

    root_real_path = os.path.realpath(REPO_ROOT)

    if not abs_path.startswith(root_real_path):
        return "[TOOL ERROR!!!]Access denied. You can only read files with in the repository."

    _, ext = os.path.splitext(path)
    if ext.lower() in IGNORE_EXTENSIONS or os.path.basename(path) in IGNORE_FILES:
        return "[TOOL ERROR!!!] This file is restricted or binary."
    
    if not os.path.exists(path):
        return f"[TOOL ERROR!!!] File '{path}' not found."
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[TOOL ERROR!!!] Could not read file: {str(e)}"

def call_gemini(prompt:str, config:genai.types.GenerateContentConfigOrDict|None=None, model:str=review_model) -> str|None:
    for attempt in range(MAX_RETRIES):
        start_time = time.time()
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )
            elapsed = time.time() - start_time
            print(f"Done! ({elapsed:.1f}s)")
            return response.text
        except Exception as e:
            if "503" in str(e) and attempt < MAX_RETRIES - 1:
                print(f"Server busy, retrying in 5s ... (Attempt{attempt+1})")
                print(f"Error details: {e}")
                time.sleep(5)
                continue
            raise e

tools = [read_repository_file]
config = genai.types.GenerateContentConfig(
    tools=tools,
    automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(maximum_remote_calls=3)
)

project_structure = get_filtered_project_structure()

files = get_git_result(["git", "diff", "--name-only", f"origin/{base_branch}...HEAD"]).split("\n")

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
    
    diff_content = get_git_result(["git", "diff", f"origin/{base_branch}...HEAD", "--", file_path])
    if not diff_content:
        continue

    print(f"[Reviewing] {file_path} ({file_size // 1024}KB) ... ", end="", flush=True)

    prompt = f"""
        あなたは技術的合理性を最優先するシニアエンジニアです。
        プロジェクトの前提条件（REVIEW_CONTEXT.md）を熟知した上で、提供された差分（diff）を厳格にレビューしてください。

        ## プロジェクト背景
        {context_content}
        
        ## リポジトリ内の全ファイル構造
        {project_structure}

        ## レビュー対象
        - ファイル名:
        {file_path}
        - ファイル全文: 
        {full_content}
        - 差分 (diff): 
        {diff_content}

        ## レビューの出力構成
        指摘事項がある場合は、必ず以下の2つのセクションに分類して出力してください。指摘がないセクションは「なし」と記載してください。
        全体を通して指摘がない場合のみ、 review-type: Pass と出力してください。

        ---

        ## 🚨 [Critical] バグ・セキュリティ・致命的欠陥
        ※動作不良、クラッシュ、セキュリティ脆弱性など、修正が必須な事項。

        ### <指摘の要約>
        - **review-type**: <バグ報告 | セキュリティ懸念>
        - **review-content**: <具体的になぜ問題なのか、どのクラス/メソッドで発生しているか>
        - **advice**: <具体的な修正コード案や対策>
        - **commit-message**: <この修正のみを適用する場合のGitコミットメッセージの提案(Conventional Commits形式)>


        ---

        ## 💡 [Advice] 改善案・パフォーマンス・保守性
        ※動作はするが、リファクタリング、効率化、運用上の懸念など、検討を推奨する事項。

        ## <指摘の要約>
        - **review-type**: <パフォーマンス改善 | 改善案 | 保守性向上>
        - **review-content**: <現状の問題点と、変更によるメリット>
        - **advice**: <具体的な実装案や代替手法>
        - **commit-message**: <この改善のみを適用する場合のGitコミットメッセージの提案(Conventional Commits形式)>

        ---

        ## 指示事項
        1. **優先順位の明確化**: 修正しないと実害が出るものは必ず [Critical] に、それ以外は [Advice] に配置してください。
        2. **場所の特定**: 行番号は使用せず、「UiControllerのcheck_alertsメソッド内」のように、構造名（クラス名やメソッド名）を用いて場所を特定してください。
        3. **文体の簡潔化**: 冗長な挨拶は不要です。事実と論理に基づき、簡潔に記述してください。
        4. **文脈の考慮**: REVIEW_CONTEXT.md に記載された既知の決定事項（例：あえてキャッシュを導入しない等）に対する重複指摘は避けてください。
        5. **関連ファイルの取得**: レビュー対象のファイルが依存、または関係している他のファイルの内容を確認する必要がある場合は、`read_repository_file`関数を使用して中身を確認した上で判断してください。
        6. **コミットメッセージの質**: `fix：read_repository_file におけるパス探索の問題を解決` のように、プレフィックス（fix, refactor, featなど）を適切に使い、簡潔に記述してください。プレフィックス以外は日本語とします。
    """

    response = call_gemini(prompt, config=config)

    time.sleep(1)

    if response and "Pass" not in response:
        review_results.append(f"### Review for `{file_path}`\n{response}")

if review_results:
    full_review_summary = "\n\n".join(review_results)
    theme = random.choice(appendix_themes)
    appendix_prompt = f"""
    あなたは技術に精通しつつ、ユーモアのあるシニアエンジニアです。
    すでにAIによるコードレビューは終わっており、このコーナーはAIコードレビューの最後に付け足される付録コーナーです。
    テーマはランダムに選ばれます。今回のテーマは{theme}です。
    数行程度のテーマに従ったコンテンツを書いてください。

    以下は小話の参考にできる今回なされたレビューの一覧です。
    {full_review_summary}
    """

    appendix_text = call_gemini(appendix_prompt)

    if appendix_text is None:
        appendix_text = "残念！付録の生成に失敗しました。"

    final_comment = (
        "## Gemini Code Review Result\n\n" + 
        "\n\n---\n\n".join(review_results) +
        "\n\n" + f"## 付録(テーマ:{theme})" +
        "\n\n" + appendix_text
    )

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
