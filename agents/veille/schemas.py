from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any, Literal
import datetime

class SourceBase(BaseModel):
    name: str
    type: str
    url: str
    config: Optional[dict] = None
    active: bool = True

class SourceCreate(SourceBase):
    pass

class SourceResponse(SourceBase):
    id: int
    last_scraped: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SourceDeleteResponse(BaseModel):
    deleted_id: int
    name: str
    type: str

class ArticleTagSchema(BaseModel):
    tag: str
    confidence: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

class ArticleSummarySchema(BaseModel):
    language: str
    summary_text: str
    generated_at: datetime.datetime
    
    model_config = ConfigDict(from_attributes=True)


class ArticleUserStateSchema(BaseModel):
    is_saved: bool = False
    read_at: Optional[datetime.datetime] = None
    shared_at: Optional[datetime.datetime] = None
    share_note: Optional[str] = None

class ArticleBase(BaseModel):
    title: str
    abstract: Optional[str] = None
    authors: Optional[List[str]] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime.datetime] = None

class ArticleResponse(ArticleBase):
    id: int
    source_id: int
    collected_at: datetime.datetime
    tags: List[ArticleTagSchema] = []
    summaries: List[ArticleSummarySchema] = []
    state: ArticleUserStateSchema = Field(default_factory=ArticleUserStateSchema)
    
    model_config = ConfigDict(from_attributes=True)

class AlertRuleBase(BaseModel):
    keywords: List[str] = Field(default_factory=list, max_length=20)
    themes: List[str] = Field(default_factory=list, max_length=20)
    frequency: Literal["daily", "weekly"] = "daily"
    active: bool = True

    @staticmethod
    def _clean_terms(values: List[str]) -> List[str]:
        return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))

    def model_post_init(self, __context: Any) -> None:
        self.keywords = self._clean_terms(self.keywords)
        self.themes = self._clean_terms(self.themes)

class AlertRuleCreate(AlertRuleBase):
    pass

class AlertRuleResponse(AlertRuleBase):
    id: int
    user_id: str
    delivery_channel: str
    last_digest_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    model_config = ConfigDict(from_attributes=True)


class AlertRuleUpdate(BaseModel):
    keywords: Optional[List[str]] = Field(None, max_length=20)
    themes: Optional[List[str]] = Field(None, max_length=20)
    frequency: Optional[Literal["daily", "weekly"]] = None
    active: Optional[bool] = None


class ArticleStateUpdate(BaseModel):
    is_saved: Optional[bool] = None
    mark_read: Optional[bool] = None
    mark_shared: Optional[bool] = None
    share_note: Optional[str] = Field(None, max_length=1000)


class DigestItemResponse(BaseModel):
    article: ArticleResponse


class WatchDigestResponse(BaseModel):
    id: int
    rule_id: int
    user_id: str
    frequency: str
    period_start: datetime.datetime
    period_end: datetime.datetime
    item_count: int
    created_at: datetime.datetime
    items: List[DigestItemResponse] = []


class CollectionRunResponse(BaseModel):
    id: int
    trigger: str
    status: str
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    source_count: int
    articles_collected: int
    digests_created: int
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
