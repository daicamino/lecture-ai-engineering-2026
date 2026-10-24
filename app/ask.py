"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --temperature 0.2 "LoRAとは何ですか？"
    uv run python -m app.ask --chat
    uv run python -m app.ask --compare-models MODEL_A MODEL_B --question "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

単発モードではツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
from dataclasses import dataclass
from time import perf_counter

from google import genai
from google.genai.chats import Chat
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


@dataclass(frozen=True)
class Measurement:
    model: str
    question: str
    answer: str
    elapsed_seconds: float
    input_tokens: int | None
    output_tokens: int | None


def ask(question: str, temperature: float | None = None) -> str:
    client = genai.Client(api_key=get_api_key())
    measurement = _measure(
        client, MODEL, question, temperature
    )
    _print_measurement(measurement)
    return measurement.answer


def _generation_config(
    temperature: float | None,
) -> types.GenerateContentConfig | None:
    if temperature is None:
        return None
    return types.GenerateContentConfig(temperature=temperature)


def _print_usage(response: types.GenerateContentResponse) -> None:
    usage = response.usage_metadata
    if usage is None:
        print("[トークン] 使用量メタデータを取得できませんでした")
    else:
        input_tokens = (
            usage.prompt_token_count
            if usage.prompt_token_count is not None
            else "不明"
        )
        output_tokens = (
            usage.candidates_token_count
            if usage.candidates_token_count is not None
            else "不明"
        )
        print(
            f"[トークン] 入力: {input_tokens}, 出力: {output_tokens}"
        )


def _measure(
    client: genai.Client,
    model: str,
    question: str,
    temperature: float | None,
) -> Measurement:
    started_at = perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=question,
        config=_generation_config(temperature),
    )
    elapsed_seconds = perf_counter() - started_at
    usage = response.usage_metadata
    return Measurement(
        model=model,
        question=question,
        answer=response.text,
        elapsed_seconds=elapsed_seconds,
        input_tokens=usage.prompt_token_count if usage else None,
        output_tokens=usage.candidates_token_count if usage else None,
    )


def _print_measurement(measurement: Measurement) -> None:
    input_tokens = (
        measurement.input_tokens
        if measurement.input_tokens is not None
        else "不明"
    )
    output_tokens = (
        measurement.output_tokens
        if measurement.output_tokens is not None
        else "不明"
    )
    print(
        f"[計測] model={measurement.model}, "
        f"応答時間={measurement.elapsed_seconds:.2f}秒, "
        f"入力トークン={input_tokens}, 出力トークン={output_tokens}"
    )


def compare(
    models: list[str],
    questions: list[str],
    temperature: float | None = None,
) -> None:
    client = genai.Client(api_key=get_api_key())
    print("model | question | elapsed (s) | input tokens | output tokens")
    print("--- | --- | ---: | ---: | ---:")
    for question in questions:
        for model in models:
            measurement = _measure(client, model, question, temperature)
            question_cell = question.replace("|", "\\|").replace("\n", " ")
            input_tokens = (
                measurement.input_tokens
                if measurement.input_tokens is not None
                else "不明"
            )
            output_tokens = (
                measurement.output_tokens
                if measurement.output_tokens is not None
                else "不明"
            )
            print(
                f"{model} | {question_cell} | "
                f"{measurement.elapsed_seconds:.2f} | "
                f"{input_tokens} | {output_tokens}"
            )
            print(f"[回答: {model} / {question_cell}]\n{measurement.answer}\n")


def run_chat(chat: Chat) -> None:
    print("会話を開始します。終了するには空行または exit を入力してください。")
    while True:
        try:
            question = input("あなた: ").strip()
        except EOFError:
            print()
            return
        if not question or question.lower() == "exit":
            return

        response = chat.send_message(question)
        print(f"回答: {response.text}\n")
        _print_usage(response)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument(
        "--temperature",
        type=float,
        help="生成時の temperature（省略時はモデルの既定値）",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="対話モードで質問を続ける（空行または exit で終了）",
    )
    parser.add_argument(
        "--compare-models",
        nargs="+",
        metavar="MODEL",
        help="指定した複数モデルで質問を実行して計測結果を比較する",
    )
    parser.add_argument(
        "--question",
        dest="questions",
        action="append",
        help="比較モードの質問。複数指定できます",
    )
    parser.add_argument("question", nargs="?")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    if args.chat and args.question is not None:
        parser.error("対話モードでは質問を指定せずに --chat を使ってください")
    if args.chat and args.compare_models:
        parser.error("--chat と --compare-models は同時に指定できません")
    if args.questions and not args.compare_models:
        parser.error("--question は --compare-models と一緒に指定してください")
    if args.compare_models and len(args.compare_models) < 2:
        parser.error("--compare-models には2つ以上のモデルが必要です")

    try:
        if args.compare_models:
            questions = list(args.questions or [])
            if args.question is not None:
                questions.insert(0, args.question)
            if not questions:
                parser.error(
                    "--compare-models を使う場合は --question で質問を指定してください"
                )
            compare(args.compare_models, questions, args.temperature)
        elif args.chat:
            client = genai.Client(api_key=get_api_key())
            chat = client.chats.create(
                model=MODEL, config=_generation_config(args.temperature)
            )
            run_chat(chat)
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question, args.temperature))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
