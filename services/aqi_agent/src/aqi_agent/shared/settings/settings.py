from __future__ import annotations

from pathlib import Path

from dotenv import find_dotenv
from dotenv import load_dotenv
from lite_llm import LiteLLMSetting
from opensearch import OpenSearchSettings
from pg import PostgresSettings
from pydantic_settings import BaseSettings
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import YamlConfigSettingsSource

from .answer_generator import AnswerGeneratorSettings
from .autocorrector import AutocorrectorSettings
from .fixsql_agent import FixSQLAgentSettings
from .sql_execution import SQLExecutionSettings
from .example_management import ExampleManagementSettings
from .history_retrieval import HistoryRetrievalSettings
from .human_intervent import HumanInterventSettings
from .memory_updater import MemoryUpdaterSettings
from .planner import PlannerSettings
from .redis import RedisSettings
from .rephrase_question import RephraseQuestionSettings
from .sql_generator import MatchSQLGeneratorSettings
from .sql_generator import MismatchSQLGeneratorSettings
from .table_pruner import TablePrunerSettings


load_dotenv(find_dotenv('.env'), override=True)


class Settings(BaseSettings):
    history_retrieval: HistoryRetrievalSettings
    rephrase_question: RephraseQuestionSettings
    planner: PlannerSettings
    match_sql_generator: MatchSQLGeneratorSettings
    human_intervent: HumanInterventSettings
    mismatch_sql_generator: MismatchSQLGeneratorSettings
    answer_generator: AnswerGeneratorSettings
    fixsql_agent: FixSQLAgentSettings
    sql_execution: SQLExecutionSettings
    opensearch: OpenSearchSettings
    table_pruner: TablePrunerSettings
    example_management: ExampleManagementSettings
    autocorrector: AutocorrectorSettings
    litellm: LiteLLMSetting
    postgres: PostgresSettings
    memory_updater: MemoryUpdaterSettings
    deployment_env: str
    host: str
    port: int
    redis: RedisSettings

    class Config:
        env_nested_delimiter = '__'
        yaml_file = str(Path(__file__).parent.parent.parent / 'settings.yaml')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )
