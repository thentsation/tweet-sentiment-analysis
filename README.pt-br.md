[🇧🇷 Português](README.pt-br.md) | [🇺🇸 English](README.md)

# Análise de Sentimento e Modelagem de Tópicos em Tweets sobre COVID-19

[![Python CI](https://github.com/ntsation/tweet-sentiment-analysis/actions/workflows/pipeline_python.yaml/badge.svg)](https://github.com/ntsation/tweet-sentiment-analysis/actions/workflows/pipeline_python.yaml)

Pipeline de NLP que combina **análise de sentimento (TextBlob)**, **modelagem de tópicos (LDA)** e um **classificador Naive Bayes** sobre ~179 mil tweets sobre a pandemia de COVID-19.

> Versão em português deste artigo. [Leia em inglês](README.md).

## TL;DR

- **Dataset**: 179.108 tweets de julho/agosto de 2020 (`data/covid19_tweets.csv`)
- **Sentimento**: polaridade via TextBlob (positivo / negativo / neutro)
- **Tópicos**: LDA com 5 tópicos — máscaras, vacinas, boletins de casos, lockdown
- **Classificador**: MultinomialNB com **84,5% de acurácia** no conjunto de teste
- **Engenharia**: código 100% tipado (mypy strict), 99% de cobertura, CI com ruff + pytest + mypy + pip-audit + smoke do pipeline

## Contexto

Este repositório nasceu como um notebook exploratório (`notebooks/tweetML.ipynb`) e foi **produtizado**: toda a lógica foi extraída para um pacote Python testável, determinístico e executável via CLI, com a mesma qualidade de engenharia esperada de um serviço em produção.

## O pipeline

```mermaid
flowchart LR
    A["CSV<br/>covid19_tweets.csv"] --> B["load_data<br/>amostragem determinística"]
    B --> C["preprocessing<br/>lowercase + stopwords NLTK"]
    C --> D["sentiment<br/>polaridade TextBlob"]
    C --> E["topics<br/>LDA (scikit-learn)"]
    D --> F["classifier<br/>MultinomialNB"]
    D --> G["reports/<br/>figuras + metrics.json"]
    E --> G
    F --> G
```

1. **Carga e amostragem** — leitura do CSV, remoção de nulos e amostragem opcional com semente fixa (`random_state=42`) para reprodutibilidade
2. **Pré-processamento** — lowercase e remoção de stopwords do NLTK
3. **Sentimento** — polaridade do TextBlob no texto limpo; rótulos derivados do sinal (`>0` positivo, `<0` negativo, `=0` neutro)
4. **Tópicos** — `CountVectorizer` (max 3.000 features) + `LatentDirichletAllocation` com 5 componentes
5. **Classificador** — `MultinomialNB` treinado sobre os rótulos de sentimento, com split 80/20 estratificado por semente fixa
6. **Relatórios** — histograma de polaridade, word clouds por tópico e `metrics.json` com tópicos, acurácia, matriz de confusão e classification report

## Resultados

### Tópicos identificados pela LDA

| Tópico | Palavras mais relevantes | Interpretação |
| --- | --- | --- |
| 1 | covid19, people, mask, like, amp, know, good, realdonaldtrump, masks, year | Uso de máscaras / opinião pública |
| 2 | covid19, pandemic, vaccine, health, amp, coronavirus, world, trump, says, virus | Vacina e políticas de saúde |
| 3 | covid19, covid, 19, coronavirus, 2020, spread, news, august, latest, daily | Boletins e notícias diárias |
| 4 | cases, covid19, new, deaths, total, india, positive, coronavirus, reported, 24 | Números de casos e mortes |
| 5 | covid19, amp, day, home, safe, lockdown, week, stay, work, 000 | Lockdown e isolamento |

### Classificador Naive Bayes

Acurácia de **0,845** sobre 35.822 tweets de teste:

| classe | precision | recall | f1-score | support |
| --- | --- | --- | --- | --- |
| negative | 0,75 | 0,66 | 0,70 | 5.724 |
| neutral | 0,87 | 0,90 | 0,88 | 16.180 |
| positive | 0,85 | 0,86 | 0,86 | 13.918 |

A classe `negative` é a mais difícil — coerente com o fato de os rótulos serem derivados da polaridade do TextBlob (proxy ruidosa), não de anotação humana.

## Produtização

O que foi feito para transformar o notebook em um projeto apresentável:

| Prática | Detalhe |
| --- | --- |
| Código tipado | `mypy` com `disallow_untyped_defs` em todo o `src/` |
| Testes unitários | 41 testes, **99% de cobertura**, fixtures sintéticas (não dependem do CSV de 66 MB) |
| Determinismo | Sementes fixas em amostragem, LDA e split; dois runs produzem o mesmo `metrics.json` |
| Lint e formato | `ruff` via pre-commit e CI |
| CI (GitHub Actions) | ruff + pytest matrix (3.11/3.12) + mypy + pip-audit + **smoke do pipeline em amostra real** |
| Docker | Imagem multi-stage non-root com dataset embutido, scan Trivy e publicação no GHCR |
| Dependências | Pins exatos, lockfile universal (`uv pip compile`) regenerado semanalmente por workflow |
| Dependabot | Atualizações diárias de dependências e actions |
| Release | python-semantic-release com versionamento semântico no `main` |

## Como usar

```bash
make install          # cria .venv e instala dependências
make run              # executa o pipeline em 2.000 tweets (SAMPLE=2000)
make run-full         # executa em todos os ~179 mil tweets
make test             # suite de testes
make coverage         # testes com relatório de cobertura
make lint             # ruff check
make format           # ruff format
make typecheck        # mypy
```

Ou diretamente pela CLI:

```bash
python src/main.py --sample 5000 --num-topics 5 --output reports
```

Saída em `reports/`:

- `metrics.json` — tópicos, acurácia, matriz de confusão, classification report e configuração do run
- `figures/sentiment_distribution.png` — distribuição da polaridade
- `figures/wordclouds/wordcloud_topic_N.png` — word cloud por tópico

### Docker

A imagem é multi-stage (builder + runtime non-root), instala a partir do lockfile, pré-baixa as stopwords do NLTK e embute o dataset — rodando o pipeline completo em qualquer lugar com Docker:

```bash
make docker-build
make docker-run                                     # amostra de 2.000 tweets, relatórios em ./reports
docker run --rm -v $(pwd)/reports:/app/reports tweet-sentiment --sample 5000   # argumentos da CLI via args
```

Ou via Compose: `docker compose up --build`.

No CI, a imagem é construída, escaneada com **Trivy** (CRITICAL/HIGH falham o build) e publicada no **GHCR** com tags de versão, `latest` e SHA a cada push no `main`/release.

## Estrutura do repositório

```
├── src/
│   ├── main.py            # CLI (argparse)
│   ├── pipeline.py        # orquestração + metrics.json
│   ├── config.py          # PipelineConfig (dataclass congelada e validada)
│   ├── preprocessing.py   # stopwords NLTK + limpeza
│   ├── sentiment.py       # TextBlob + rótulos
│   ├── topics.py          # LDA + top palavras por tópico
│   ├── classifier.py      # Naive Bayes + avaliação
│   └── visualization.py   # histograma + word clouds
├── tests/                 # unitários + end-to-end com fixtures sintéticas
├── notebooks/             # notebook exploratório original
├── data/                  # dataset (179.108 tweets)
├── config/                # requirements pinados + lockfile
├── docker/                # Dockerfile multi-stage
└── .github/workflows/     # CI, Docker CI/CD, lockfile semanal, release
```

## Roadmap

- [ ] Persistir o modelo treinado (joblib) e expor inferência como serviço
- [ ] Substituir a proxy do TextBlob por rótulos anotados ou modelo pré-treinado
- [ ] Coleta incremental de dados (streaming) e reprodutibilidade via DVC
