🇧🇷 Português | [🇺🇸 English](ARTIGO.en-us.md)

# O que um notebook de tweets sobre covid me ensinou sobre rotulagem de sentimento

Comecei querendo só organizar um notebook bagunçado. Terminei descobrindo que os dois rotuladores de sentimento que eu estava usando concordam em pouco mais da metade dos tweets — e isso mudou o que eu acho que "análise de sentimento" realmente mede.

## De onde isso veio

O ponto de partida era `notebooks/tweetML.ipynb`: 179 mil tweets sobre COVID-19, TextBlob calculando sentimento, LDA extraindo tópicos, um Naive Bayes treinado em cima disso. Rodava célula por célula, dava resultado, e por um tempo isso foi suficiente — era um exercício de NLP, não um sistema.

O problema apareceu quando tentei reproduzir uma análise dois dias depois: refazer qualquer coisa significava rodar o notebook inteiro do início, na ordem certa, torcendo pro estado global não ter mudado de sentido no meio do caminho. Não tinha um teste sequer — mudar o pré-processamento era rezar pra os números não se moverem sem eu perceber. O `requirements.txt` listava bibliotecas que eu nem usava mais. Não tinha CI, lint ou type checking. E o resultado mais importante do notebook, a acurácia do classificador, só existia dentro da própria célula que a imprimia — se eu fechasse o Jupyter, a informação sumia com ele.

## Tirar a análise de dentro das células

A regra que me impus: nenhuma feature nova antes de a lógica existente estar coberta por teste. Mas pra testar, primeiro eu precisava ter o que testar — então quebrei o notebook em módulos, cada um com uma responsabilidade e uma fronteira de teste:

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

A mesma análise que antes vivia amarrada por variáveis globais entre células virou uma função pura, `run_pipeline(config)`: entra uma `PipelineConfig` (dataclass congelada e validada), sai um `PipelineResult` mais `reports/metrics.json`. Hoje `python src/main.py --sample 2000` roda exatamente o que o notebook rodava, só que de forma reproduzível.

O dataset tem 66 MB, então os testes não podiam depender dele nem de baixar nada. As fixtures constroem tweets sintéticos claramente positivos, negativos e neutros — "I love this amazing day", "I hate this terrible day", "The office opens at nine" — e validam sinal e fronteira: classificação pelo sinal da polaridade, coerência da matriz de confusão, determinismo com sementes fixas. O CI roda a cada commit: lint, format check, mypy (`disallow_untyped_defs`), pytest com threshold de cobertura em matrix de Python 3.11/3.12, auditoria de dependências com pip-audit, e um job de **smoke do pipeline** que roda a coisa real numa amostra de 500 tweets e confere que os relatórios saem do outro lado — teste unitário não pega "o CSV não tem a coluna `date`"; smoke pega.

A imagem Docker ficou multi-stage em `python:3.14-slim`, instalando a partir do lockfile, usuário não-root, stopwords e léxico do VADER pré-baixados no build, dataset embutido — o pipeline inteiro roda em qualquer lugar com Docker: `docker run tweet-sentiment --sample 5000`. No CI a imagem é escaneada com Trivy antes de ir pro GHCR.

## Limpando tweet de verdade, não texto genérico

O notebook original só fazia lowercase e removia stopwords — o suficiente para texto de livro, não pra tweet. URLs truncadas (`https://t.co/...`), @menções, prefixo "RT" e hashtags viravam feature da LDA e do classificador sem eu ter decidido isso conscientemente. A limpeza agora remove URLs, menções e RT explicitamente, e desembrulha `#COVID19` em `COVID19` — o texto da hashtag carrega sentido, o `#` é só pontuação atrapalhando o vetorizador.

## A descoberta que mudou o projeto: dois rotuladores, ~53% de concordância

Os rótulos de treino vinham só do TextBlob, que não foi desenhado pra social media. Adicionei o VADER como segundo rotulador — ele entende MAIÚSCULAS, "!!!" e emojis, coisas que TextBlob ignora — e uma análise de concordância entre os dois em `metrics.json`.

O resultado foi a parte mais interessante do projeto inteiro: **os dois concordam em apenas ~53% dos tweets**. Quase metade do corpus, cada rotulador acha que o outro errou. Isso não é ruído de implementação — é evidência de que "sentimento léxico" é uma proxy barulhenta pro que a gente realmente quer medir, e virou o argumento central para o próximo passo natural do projeto: anotação humana ou um modelo pré-treinado, em vez de confiar cegamente em heurística de léxico.

## TF-IDF com bigramas e um benchmark de 4 modelos

`CountVectorizer` de unigrama perde negação — "not good" vira "good" pro classificador. Troquei por `TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)`, que captura negações e expressões compostas. E em vez de manter o Naive Bayes só porque já estava lá, rodei um benchmark de 4 modelos no mesmo split:

| modelo | acurácia | macro-F1 |
| --- | --- | --- |
| LinearSVC | **0,820** | **0,784** |
| LogisticRegression | 0,803 | 0,752 |
| ComplementNB | 0,729 | 0,701 |
| MultinomialNB | 0,731 | 0,651 |

LinearSVC venceu com folga. O detalhe que eu não esperava: ComplementNB — desenhado justamente para classes desbalanceadas — supera o MultinomialNB no macro-F1, porque `negative` é minoria no dataset. O micro-average esconde esse desbalanceamento; o macro expõe.

## A coluna que o notebook original ignorava

O dataset sempre teve uma coluna `date`, e ela nunca foi usada pra nada. Agora `metrics.json` resume o período coberto, aponta o dia mais negativo e o mais positivo, e `figures/sentiment_timeline.png` plota a polaridade média diária com TextBlob e VADER lado a lado. Quando as duas curvas divergem num dia específico, isso é sinal de que há conteúdo naquele dia que só um dos dois léxicos está captando corretamente.

## Tópicos sem chutar k

`num_topics=5` no notebook original era um número escolhido no escuro. Com `--tune-topics`, o pipeline treina LDA para k ∈ {3, 5, 7, 10} e escolhe o de maior coerência — UMass simplificada, calculada sobre a própria matriz documento-termo, sem dependência extra. Na amostra de 20 mil tweets, k=3 venceu. `metrics.json` guarda o escore de todos os candidatos, não só o vencedor, pra eu poder auditar a decisão depois.

## O que eu aprendi fazendo isso

Determinismo vem antes de tudo: semente fixa em amostragem, split e LDA significa que dois runs produzem o mesmo `metrics.json`, e o diff desse arquivo virou minha revisão de código de cientista de dados. Vulnerabilidade pode vir de onde você menos espera — o Trivy achou CVEs em `msgpack` e `setuptools` vendorizados *dentro do próprio pip*, duplicados no wheel do ensurepip; a correção foi remover o ensurepip da imagem e apontar o skip-dirs certo, e nenhuma delas era dependência minha. Concordância entre rotuladores é uma métrica de qualidade praticamente de graça: antes de treinar qualquer modelo, medir o quanto duas heurísticas concordam entre si já diz muito sobre o teto do que dá para aprender dali. E o notebook não morreu — ele continua no repositório como registro da exploração original; o pipeline é o que ele queria ser quando crescesse, e a fonte da verdade agora é código testado, não output de célula.

## Onde o pipeline está agora

64 testes, 97% de cobertura, threshold de 95% bloqueando no CI. `ruff` (lint + format) e `mypy` limpos a cada push, CI em matrix de Python, smoke do pipeline com dados reais, imagem Docker escaneada com Trivy e publicada no GHCR. O pipeline hoje tem anotação dupla de sentimento, benchmark de 4 modelos, tendência temporal e seleção de tópicos por coerência — e `metrics.json` é reproduzível, o artefato final da análise, versionado junto com o código.
