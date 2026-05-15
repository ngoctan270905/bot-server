from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from pydantic.alias_generators import to_camel
from datetime import datetime
from typing import Annotated, List, Optional
from enum import Enum

PyObjectId = Annotated[str, BeforeValidator(str)]

class DataSourceType(str, Enum):
    FILE = "File"
    TEXT = "Text"
    WEBSITE = "Website"
    QA = "QA"
    NOTION = "Notion"

class TrainingStatus(str, Enum):
    TRAINING = "Training"
    FAILED = "Failed"
    DONE = "Done"

class QASchema(BaseModel):
    question: str
    answer: str
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class NotionType(str, Enum):
    DATABASE = "database"
    PAGE = "page"

class NotionSchema(BaseModel):
    type: NotionType
    id: str
    token: str
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class UrlSourceInput(BaseModel):
    url: str
    title: str
    content: str
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class FileSourceInput(BaseModel):
    name: str
    file_path: str = Field(alias="filePath")
    number_of_characters: int = Field(alias="numberOfCharacters")
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class NotionSourceInput(BaseModel):
    name: str
    page_id: str = Field(alias="pageId")
    token: str
    number_of_characters: int = Field(alias="numberOfCharacters")
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class SourceUpsertRequest(BaseModel):
    bot_id: str = Field(alias="botId")
    existing_source_ids: List[str] = Field(default_factory=list, alias="existingSourceIds")
    texts: List[str] = Field(default_factory=list)
    fetched_urls: List[UrlSourceInput] = Field(default_factory=list, alias="fetchedUrls")
    files: List[FileSourceInput] = Field(default_factory=list)
    qnas: List[QASchema] = Field(default_factory=list)
    notions: List[NotionSourceInput] = Field(default_factory=list)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class SourceResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    type: DataSourceType
    name: str
    number_of_characters: int = Field(alias="numberOfCharacters")
    training_status: TrainingStatus = Field(alias="trainingStatus")
    file_path: Optional[str] = Field(None, alias="filePath")
    fetched_url: Optional[str] = Field(None, alias="fetchedUrl")
    text: Optional[str] = Field(None)
    qna: Optional[QASchema] = None
    notion: Optional[NotionSchema] = None
    bot_id: PyObjectId = Field(alias="botId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class TrainingHistoryResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    bot_id: PyObjectId = Field(alias="botId")
    sources_ids: List[PyObjectId] = Field(alias="sourcesIds")
    created_at: datetime = Field(alias="createdAt")
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
