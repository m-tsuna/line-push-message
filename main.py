"""
LINE メッセージ送信プログラム（課題7：LINE Messaging API）

LINE Messaging API を使い、ターミナルで入力したメッセージを、
自分で作った LINE 公式アカウントから、自分の LINE に送る（プッシュメッセージ）。

使い方：ターミナルで  python main.py  を実行する。
"""

import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# ============================================================
# 設定（ここをまとめて書いておく）
# ============================================================

# このプログラム（main.py）が置いてあるフォルダ
BASE_DIR = Path(__file__).resolve().parent

# トークンとユーザー ID を書いておくファイルと、その中の項目名
ENV_FILE = BASE_DIR / ".env"
ENV_EXAMPLE_FILE = BASE_DIR / ".env.example"
TOKEN_NAME = "LINE_CHANNEL_ACCESS_TOKEN"
USER_ID_NAME = "LINE_USER_ID"

# ユーザー ID の形（U のあとに 0〜9・a〜f が 32 文字）
# LINE アプリの画面に出る「LINE ID」は別物なので、間違えて貼ったときに気づけるようにする
USER_ID_PATTERN = r"U[0-9a-f]{32}"

# プッシュメッセージ（ユーザー ID を指定して送る）の API の URL
PUSH_URL = "https://api.line.me/v2/bot/message/push"

# テキストメッセージ1通に書ける文字数の上限（LINE の決まり）
MAX_TEXT_LENGTH = 5000

# 無料プラン（コミュニケーションプラン）で1か月に送れる数（エラーの案内に使う）
FREE_PLAN_MONTHLY_LIMIT = 200

# LINE の返事を待つ秒数（これを過ぎたら「応答が無い」として終わる）
TIMEOUT_SECONDS = 10

# 送信前に表示するメッセージの区切り線
SEPARATOR = "-" * 26


# ============================================================
# F1 設定の読み込み
# ============================================================
def load_settings():
    """
    .env からチャネルアクセストークンとユーザー ID を読み込み、(トークン, ユーザー ID) を返す。
    .env が無い・項目が空・ユーザー ID の形が違う場合は、理由を表示して終了する（F6）。
    """
    # .env の中身を「環境変数」（プログラムが読める設定値）として読み込む
    load_dotenv(ENV_FILE)
    token = os.getenv(TOKEN_NAME, "").strip()
    user_id = os.getenv(USER_ID_NAME, "").strip()

    # 空の項目を集めて、まとめて知らせる
    missing = [name for name, value in ((TOKEN_NAME, token), (USER_ID_NAME, user_id)) if not value]
    if missing:
        show_error_and_exit(
            f"{'、'.join(missing)} が設定されていません。\n"
            f"{ENV_EXAMPLE_FILE.name} をコピーして「{ENV_FILE.name}」という名前にし、\n"
            f"チャネルアクセストークンとユーザー ID を書いてください。\n"
            f"置き場所: {BASE_DIR}"
        )
    if not re.fullmatch(USER_ID_PATTERN, user_id):
        show_error_and_exit(
            f"{USER_ID_NAME} の形が正しくありません（U で始まる 33 文字のはずです）。\n"
            "LINE Developers コンソールでチャネルを開き、「チャネル基本設定」タブの一番下にある\n"
            "「あなたのユーザー ID」をコピーしてください（LINE アプリの「LINE ID」とは別物です）。"
        )
    return token, user_id


# ============================================================
# F2 メッセージの入力
# ============================================================
def ask_message():
    """
    メッセージを1行ずつ入力してもらい、改行でつないだ文字列を返す。
    空の行（何も入力せずに Enter）で入力を終わる。
    最初の行が空なとき・文字数が上限を超えたときは、もう一度聞く。
    """
    while True:
        print("メッセージを入力してください（空の行で入力を終わります）")
        lines = []
        while True:
            line = input("> ")
            if line.strip() == "":
                if lines:
                    break
                print("メッセージが空です。メッセージを入力してください。")
                continue
            lines.append(line)

        message = "\n".join(lines)
        if len(message) <= MAX_TEXT_LENGTH:
            return message
        print(
            f"メッセージが長すぎます（{len(message)} 文字）。"
            f"LINE で1通に送れるのは {MAX_TEXT_LENGTH} 文字までです。もう一度入力してください。"
        )


# ============================================================
# F3 送信前の確認
# ============================================================
def confirm_send(message):
    """
    送信するメッセージを表示し、送ってよいか聞く。y なら True、n なら False を返す。
    """
    print()
    print("--- 送信するメッセージ ---")
    print(message)
    print(SEPARATOR)
    while True:
        answer = input("送信しますか？ (y/n): ").strip().lower()
        if answer in ("y", "n"):
            return answer == "y"
        print("y か n を入力してください。")


# ============================================================
# F4 送信
# ============================================================
def push_message(token, user_id, message):
    """
    プッシュメッセージの API で、ユーザー ID の人（自分）にテキストメッセージを送る。

    - トークンは「Authorization: Bearer トークン」というヘッダーで渡す
    - 中身は JSON で送る。to が送り先、messages が送るメッセージの一覧（最大5件。今回は1件）
    - 成功すると HTTP 200 が返る。失敗は 400・401 などのステータスと、中身の message で理由が返る
    """
    response = requests.post(
        PUSH_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "to": user_id,
            "messages": [{"type": "text", "text": message}],
        },
        timeout=TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        show_error_and_exit(explain_line_error(response))


# ============================================================
# F5 結果の表示
# ============================================================
def show_result():
    """
    送れたことを表示する。
    （LINE の API では、送ったメッセージの中身を読み返せないので、スマホで確かめてもらう）
    """
    print("送信しました。スマホの LINE を確認してください。")


# ============================================================
# F6 エラー表示
# ============================================================
def show_error_and_exit(message):
    """
    原因が分かる日本語のエラーメッセージを表示して、プログラムを終了する。
    """
    print(f"エラー: {message}", file=sys.stderr)
    sys.exit(1)


def explain_line_error(response):
    """
    LINE が返した失敗の返事（HTTP のステータスと、中身の message）を、日本語の説明に直して返す。
    """
    # LINE は失敗の理由を {"message": "...", "details": [...]} の形で返す
    # （JSON でない返事が来ることもあるので、そのときは理由なしとする）
    try:
        body = response.json()
    except ValueError:
        body = {}
    reason = body.get("message", "")
    for detail in body.get("details", []):
        reason += f"（{detail.get('property', '')}: {detail.get('message', '')}）"
    detail_text = f"詳細: HTTP {response.status_code} {reason}".rstrip()

    # トークンが正しくない・再発行されて古くなった
    if response.status_code == 401:
        return (
            "チャネルアクセストークンが正しくありません。\n"
            f"{ENV_FILE.name} の {TOKEN_NAME} が、LINE Developers コンソールの「Messaging API 設定」タブにある\n"
            "チャネルアクセストークン（長期）と同じか確認してください。再発行した場合はトークンが変わります。\n"
            + detail_text
        )
    # 送り先や中身が正しくない
    if response.status_code == 400:
        return (
            "LINE がメッセージを受け付けませんでした。\n"
            f"{ENV_FILE.name} の {USER_ID_NAME} が、このチャネルの「チャネル基本設定」タブにある\n"
            "「あなたのユーザー ID」と同じか確認してください（別のチャネルのユーザー ID では送れません）。\n"
            + detail_text
        )
    # 月の上限を超えた・短い時間に送りすぎた
    if response.status_code == 429:
        return (
            "送れる数の上限を超えました。次のどちらかです。\n"
            f"  ・無料プランで今月送れる {FREE_PLAN_MONTHLY_LIMIT} 通を使い切った（来月まで待つ）\n"
            "  ・短い時間に送りすぎた（少し待ってからやり直す）\n"
            + detail_text
        )
    return "LINE への送信に失敗しました。\n" + detail_text


# ============================================================
# メインの処理（上の関数を順番に呼ぶ）
# ============================================================
def main():
    """
    プログラム全体の流れ：
    設定の読み込み → メッセージの入力 → 送信前の確認 → 送信 → 結果の表示
    """
    try:
        # F1 設定の読み込み（入力より先に確かめる）
        token, user_id = load_settings()
        # ユーザー ID は全部は出さず、最初の5文字だけ見せる
        print(f"送り先：あなたの LINE（ユーザー ID：{user_id[:5]}…）")

        # F2 メッセージの入力
        message = ask_message()

        # F3 送信前の確認
        if not confirm_send(message):
            print("送信をやめました。")
            return

        # F4 送信
        push_message(token, user_id, message)

        # F5 結果の表示
        show_result()

    except requests.Timeout:
        # 決めた秒数のうちに LINE から返事が無かった（F6）
        show_error_and_exit(
            f"LINE から {TIMEOUT_SECONDS} 秒たっても応答がありませんでした。時間をおいてやり直してください。\n"
            "（届いている場合もあるので、スマホの LINE を確認してください）"
        )
    except requests.RequestException as error:
        # インターネットにつながらない など（F6）
        # エラーの文字列をそのまま出すと送り先の情報まで出ることがあるので、種類の名前だけを出す
        show_error_and_exit(
            "LINE につながりませんでした。インターネット接続を確認してください。\n"
            f"詳細: {type(error).__name__}"
        )
    except (KeyboardInterrupt, EOFError):
        # Ctrl + C で途中でやめた場合
        print("\n中断しました。")
        sys.exit(1)


# このファイルを直接実行したときだけ main() を動かす
if __name__ == "__main__":
    main()
