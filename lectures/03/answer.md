# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：用語集の内容をもとに回答する。
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary({'query': 'LoRA'}), search_glossary({'query': 'LoRA'})
- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：make_quiz(lecture: int)
    """指定した回の用語から1つを選び、確認問題と答えを返す。

     「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    """

## 宿題

- 取り組んだレベル：基礎
- やったこと：app/agent.pyのINSTRUCTIONSに"50文字前後で回答する"という条件を追加
- 結果：output_tokensが、172から55に減少した
- 気づき・疑問： tool_callsも2から1へ減少した
