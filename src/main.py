import argparse
from pathlib import Path

from config import PipelineConfig
from pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Análise de sentimento e tópicos em tweets'
    )
    parser.add_argument(
        '--input', default='data/covid19_tweets.csv', help='caminho do CSV de tweets'
    )
    parser.add_argument(
        '--output', default='reports', help='diretório de saída dos relatórios'
    )
    parser.add_argument(
        '--text-column', default='text', help='coluna com o texto do tweet'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help='tamanho da amostra (usa tudo se omitido)',
    )
    parser.add_argument(
        '--num-topics', type=int, default=5, help='número de tópicos da LDA'
    )
    parser.add_argument(
        '--num-words', type=int, default=10, help='palavras por tópico no relatório'
    )
    parser.add_argument(
        '--tune-topics',
        action='store_true',
        help='busca coerência para escolher num_topics automaticamente',
    )
    parser.add_argument(
        '--seed', type=int, default=42, help='semente aleatória (reprodutibilidade)'
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> PipelineConfig:
    return PipelineConfig(
        input_path=Path(args.input),
        output_dir=Path(args.output),
        text_column=args.text_column,
        sample_size=args.sample,
        num_topics=args.num_topics,
        num_words=args.num_words,
        tune_topics=args.tune_topics,
        random_state=args.seed,
    )


def main() -> None:
    config = build_config(parse_args())
    result = run_pipeline(config)

    print(f'Tweets analisados: {result.tweets_analyzed}')
    print()
    for index, words in enumerate(result.topics, start=1):
        print(f'Tópico #{index}: {" ".join(words)}')
    print()
    print(f'Acurácia do classificador: {result.evaluation.accuracy:.4f}')
    print()
    print(result.evaluation.classification_report)
    print(f'Relatórios salvos em: {result.output_dir.resolve()}')


if __name__ == '__main__':
    main()
