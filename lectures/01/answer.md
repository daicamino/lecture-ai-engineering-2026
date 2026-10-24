# 第1回 解答

## 演習

- 講座に固有の質問（宿題の3レベル）へのモデルの回答（要約でよい）：AIE2026の講座において「3レベル」という言葉が出てきた場合、それは**AIを活用するスキルや、プロンプト（指示文）を出す際の「難易度・段階」を3つに分類したもの**を指している可能性が非常に高いです。AIの研修や講座では、受講者が自身のレベルや課題の難易度を段階的に理解できるように、以下のような「3つのレベル」で説明されるのが一般的です。

- 用語集の正しい意味と比べて気づいたこと：

- 表示できたトークン数（入力 / 出力）：入力トークン=22, 出力トークン=531

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：モデルの変更（AIE_MODEL 環境変数）、temperatureの変更、会話履歴機能の追加、応答時間とトークン数の比較機能の追加
- 結果：
[質問] LoRAとは何ですか？

■基礎
□モデルを変えて実行
[model] gemini-3.5-flash-lite
[トークン] 入力: 7, 出力: 564

[model] gemini-3.5-flash
[トークン] 入力: 7, 出力: 671

[model] gemini-3.8-flash
モデルが混み合っています（503）。少し待ってから再実行してください。

□temperatureを変えて実行
uv run python -m app.ask --temperature 0.0 "LoRAとは何ですか？"
[トークン] 入力: 7, 出力: 567
[トークン] 入力: 7, 出力: 553
[トークン] 入力: 7, 出力: 688

uv run python -m app.ask --temperature 0.2 "LoRAとは何ですか？
[model] gemini-3.5-flash-lite
[トークン] 入力: 7, 出力: 725
[トークン] 入力: 7, 出力: 450
[トークン] 入力: 7, 出力: 558

uv run python -m app.ask --temperature 1.2 "LoRAとは何ですか？"
[トークン] 入力: 7, 出力: 567
[トークン] 入力: 7, 出力: 683
[トークン] 入力: 7, 出力: 622

■実装
@daicamino ➜ /workspaces/lecture-ai-engineering-2026 (lec01) $ uv run python -m app.ask --temperature 0.0 "私の名前は何ですか？"
[model] gemini-3.5-flash-lite
[質問] 私の名前は何ですか？

[トークン] 入力: 6, 出力: 24
申し訳ありませんが、私にはあなたの名前がわかりません。教えていただければ、お名前でお呼びしますよ！
@daicamino ➜ /workspaces/lecture-ai-engineering-2026 (lec01) $ uv run python -m app.ask --temperature 0.0 "私の名前は太郎です"
[model] gemini-3.5-flash-lite
[質問] 私の名前は太郎です

[トークン] 入力: 6, 出力: 19
太郎さん、はじめまして！
どうぞよろしくお願いします。何かお手伝いできることはありますか？

■発展
uv run python -m app.ask \
  --compare-models gemini-3.5-flash-lite gemini-3.5-flash \
  --question "LoRAとは何ですか？" \
  --question "temperatureとは何ですか？"
[model] gemini-3.5-flash-lite
model | question | elapsed (s) | input tokens | output tokens
--- | --- | ---: | ---: | ---:
gemini-3.5-flash-lite | LoRAとは何ですか？ | 7.94 | 7 | 683
gemini-3.5-flash | LoRAとは何ですか？ | 10.03 | 7 | 653
gemini-3.5-flash-lite | temperatureとは何ですか？ | 4.36 | 6 | 306


- 気づき・疑問： temperatureの設定では、完全に揺れを制御できない。
