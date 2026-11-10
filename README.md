# LINE メッセージ送信プログラム（line-push-message）

LINE Messaging API を使い、ターミナルで入力したメッセージを、自分で作った LINE 公式アカウントから自分の LINE に送る Python プログラムです（プッシュメッセージ）。

## できること

- ターミナルで複数行のメッセージを入力し、確認してから自分の LINE に送る
- `.env` の設定ミス・トークンの間違い・送れる数の上限・通信の失敗などを、日本語で知らせる

## 使う技術

- Python 3（requests・python-dotenv）
- LINE Messaging API（プッシュメッセージ）

## 事前準備

1. Python 3 と、ライブラリ `requests`・`python-dotenv`（Anaconda なら最初から入っています）
   ```
   pip install requests python-dotenv
   ```
2. LINE 公式アカウントと Messaging API のチャネル（下の「秘密ファイルの用意の仕方」）
3. スマホの LINE で、作った公式アカウントを友だち追加しておく（「Messaging API 設定」タブの QR コードを読む）

## 秘密ファイル（.env）の用意の仕方

1. [LINE Official Account Manager](https://manager.line.biz/) にログインし、LINE 公式アカウントを作る
2. 「設定」→「Messaging API」→「Messaging API を利用する」で、プロバイダーを作って有効にする
3. [LINE Developers コンソール](https://developers.line.biz/console/) でできたチャネルを開く
4. `.env.example` をコピーして `.env` という名前にし、次の2つを `=` の後ろに貼る
   - `LINE_USER_ID`：「チャネル基本設定」タブの一番下にある「あなたのユーザー ID」（`U` で始まる）
   - `LINE_CHANNEL_ACCESS_TOKEN`：「Messaging API 設定」タブの一番下で発行する「チャネルアクセストークン（長期）」

`.env` は鍵なので、GitHub には載せません（`.gitignore` に書いてあります）。漏れたときは、コンソールでトークンを再発行してください。

## 使い方

```
python main.py
```

```
送り先：あなたの LINE（ユーザー ID：U1234…）
メッセージを入力してください（空の行で入力を終わります）
> こんにちは！
> Python から送っています。
>

--- 送信するメッセージ ---
こんにちは！
Python から送っています。
--------------------------
送信しますか？ (y/n): y
送信しました。スマホの LINE を確認してください。
```

- 何も入力せずに Enter を押すと、入力が終わります
- 1通に送れるのは 5000 文字までです
- 無料プランで送れるのは月 200 通までです

## ファイル

| ファイル | 内容 |
|---|---|
| `main.py` | プログラム本体 |
| `.env.example` | `.env` の書き方の見本 |
| `要件定義書.md` | 何をどう作るかを決めた文書（方式を選んだ理由もここに書いています） |
