🇧🇷 Português | [🇺🇸 English](ARTIGO.en-us.md)

# De notebook a produção: produtizando um pipeline de análise de sentimento em tweets

Como um notebook exploratório de NLP virou um pipeline determinístico, testado, tipado e com CI/CD — e, no caminho, ganhou um segundo rotulador, benchmark de modelos, tendência temporal e seleção automática de tópicos.

## O ponto de partida

O projeto começou como a maioria dos projetos de ciência de dados: um Jupyter notebook (`notebooks/tweetML.ipynb`) que carregava 179 mil tweets sobre COVID-19, rodava TextBlob para sentimento, LDA para tópicos e treinava um Naive Bayes. Funcionava. E era isso.

O problema é que notebook não é artefato de engenharia. Faltava tudo o que separa uma análise exploratória de um pipeline que você colocaria a assinatura embaixo:

- Toda a lógica vivia em células — refazer a análise era rodar o notebook inteiro, do zero, com o estado global dependendo da ordem de execução
- Zero testes automatizados — mudar o pré-processamento era rezar para os números não mudarem
- `requirements.txt` sem pin de versão (e `pip install` listando bibliotecas que nem eram usadas)
- Sem CI, sem lint, sem type checking — nada
- Resultados presos em outputs de célula: a acurácia do classificador só existia dentro do notebook

Este artigo é o caminho de lá até cá.

## Primeira parada: a base (extrair, testar, automatizar)

A regra que segui: **nenhuma feature nova antes de a lógica existente estar coberta por testes.** Mas antes de testar, era preciso ter o que testar.

### Extraindo o notebook em módulos

Cada célula virou um módulo com uma responsabilidade — e uma fronteira de teste:

```
src/
├── preprocessing.py   # limpeza de texto + stopwords
├── sentiment.py       # TextBlob e rótulos
├── topics.py          # LDA
├── classifier.py      # Naive Bayes + avaliação
├── visualization.py   # histograma + wordclouds
├── pipeline.py        # orquestração
└── main.py            # CLI
```

A mesma análise que vivia em células interligadas por variáveis globais virou uma função `run_pipeline(config)` pura: entra uma `PipelineConfig` (dataclass congelada e validada), sai um `PipelineResult` + `reports/metrics.json`. A CLI de hoje (`python src/main.py --sample 2000`) roda exatamente o que o notebook rodava.

### Testes com fixtures sintéticas

O dataset tem 66 MB — testes não podem depender dele (nem do download de nada). As fixtures constroem tweets sintéticos claramente positivos, negativos e neutros ("I love this amazing day", "I hate this terrible day", "The office opens at nine") e validam sinais e fronteiras: classificação por sinal da polaridade, coerência da matriz de confusão, determinismo com sementes fixas.

### CI que roda a cada commit

Lint, format check, mypy (com `disallow_untyped_defs`), pytest com threshold de cobertura em matrix de Python 3.11/3.12, auditoria de dependências com pip-audit — e um job de **smoke do pipeline** que roda o pipeline real em uma amostra de 500 tweets e verifica que os relatórios existem. Teste de unidade não pega "o CSV não tem a coluna `date`"; smoke pega.

### Docker sem surpresas

Imagem multi-stage com `python:3.14-slim`, instalação a partir do lockfile, usuário não-root, stopwords e léxico do VADER pré-baixados no build — e o dataset embutido. O pipeline inteiro roda em qualquer lugar com Docker: `docker run tweet-sentiment --sample 5000`. No CI, a imagem é escaneada com Trivy e publicada no GHCR.

## As features: melhorar os tweets e as análises

Com a base pronta, o ataque aos problemas de qualidade que o notebook escondia.

### Limpeza específica de tweets

O notebook só fazia lowercase + stopwords. Mas tweets têm URLs truncadas (`https://t.co/...`), @menções, prefixo "RT" e hashtags — tudo isso virava feature da LDA e do classificador. A limpeza agora remove URLs, menções e RT, e desembrulha `#COVID19` em `COVID19` (o texto da hashtag é conteúdo; o `#` é pontuação).

### Dois rotuladores em vez de um

Os rótulos de treinamento vinham só do TextBlob — que não foi feito para social media. Adicionei o **VADER** como segundo rotulador (ele entende MAIÚSCULAS, "!!!" e emojis) e uma análise de concordância no `metrics.json`. O resultado é a descoberta mais interessante do projeto: **os dois concordam em apenas ~53% dos tweets**. Cada rotulador acha que o outro erra em quase metade do corpus. É a evidência mais clara de que rótulo léxico é proxy ruidosa — e o argumento central para o roadmap (anotação humana ou modelo pré-treinado).

### TF-IDF com bigramas + benchmark de modelos

`CountVectorizer` de unigramas perde "not good". A troca por `TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)` captura negações e expressões compostas. E em vez de confiar no Naive Bayes por fé, um benchmark de 4 modelos no mesmo split:

| modelo | acurácia | macro-F1 |
| --- | --- | --- |
| LinearSVC | **0,820** | **0,784** |
| LogisticRegression | 0,803 | 0,752 |
| ComplementNB | 0,729 | 0,701 |
| MultinomialNB | 0,731 | 0,651 |

O LinearSVC vence com folga. E o ComplementNB — desenhado para classes desbalanceadas — supera o MultinomialNB no macro-F1 justamente porque `negative` é minoria (o micro-average esconde isso, o macro expõe).

### A dimensão temporal que o notebook ignorava

O dataset tem coluna `date` e ela não era usada para nada. Agora o `metrics.json` resume o período coberto, o dia mais negativo e o mais positivo, e `figures/sentiment_timeline.png` plota a polaridade média diária — TextBlob e VADER lado a lado. Quando as curvas divergem em um dia, é um sinal de que ali tem conteúdo que só um dos léxicos captura.

### Tópicos sem chutar k

Escolher `num_topics=5` era arbitrário. Com `--tune-topics`, o pipeline treina LDA para k ∈ {3, 5, 7, 10} e escolhe o de maior coerência (UMass simplificada, computada sobre a própria matriz documento-termo — sem dependência extra). Na amostra de 20 mil tweets, k=3 venceu. O `metrics.json` guarda os escores de todos os candidatos para auditoria.

## Lições que o tutorial não conta

1. **Determinismo primeiro.** Semente fixa em amostragem, split e LDA significa que dois runs produzem o mesmo `metrics.json` — e o diff do metrics é a revisão de código do cientista de dados.
2. **Vulnerabilidade pode vir de onde você menos espera.** O Trivy achou CVEs no `msgpack` e `setuptools` *vendorizados dentro do pip* (e duplicados no wheel do ensurepip). Fix: remover o ensurepip da imagem e apontar o skip-dirs certo. Não foi nenhuma dependência minha.
3. **Concordância entre rotuladores é métrica de qualidade gratuita.** Antes de treinar qualquer modelo, medir o quanto duas heurísticas concordam diz muito sobre o teto do que você pode aprender.
4. **Notebook não morre.** Ele continua no repositório como registro da exploração original. O pipeline é o que o notebook *queria ser* quando crescer — e a fonte da verdade é o código testado, não o output da célula.

## Estado final

- 64 testes, 97% de cobertura, threshold de 95% bloqueando no CI
- ruff (lint + format) e mypy limpos, rodando a cada push
- CI em matrix de Python, smoke do pipeline com dados reais, imagem Docker escaneada com Trivy e publicada no GHCR
- Pipeline com dupla anotação de sentimento, benchmark de 4 modelos, tendência temporal e seleção de tópicos por coerência
- `metrics.json` reprodutível — o artefato final da análise, versionado junto com o código
