from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    input_path: Path = Path('data/covid19_tweets.csv')
    output_dir: Path = Path('reports')
    text_column: str = 'text'
    num_topics: int = 5
    num_words: int = 10
    max_features: int = 3000
    test_size: float = 0.2
    random_state: int = 42
    sample_size: int | None = None

    def __post_init__(self) -> None:
        if not 0 < self.test_size < 1:
            raise ValueError('test_size deve estar entre 0 e 1 exclusivo')
        if self.num_topics < 2:
            raise ValueError('num_topics deve ser no mínimo 2')
        if self.max_features < 10:
            raise ValueError('max_features deve ser no mínimo 10')
        if self.sample_size is not None and self.sample_size <= 0:
            raise ValueError('sample_size deve ser positivo quando informado')
