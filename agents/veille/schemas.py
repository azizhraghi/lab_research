from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
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
    
    model_config = ConfigDict(from_attributes=True)

class AlertRuleBase(BaseModel):
    keywords: Optional[List[str]] = None
    themes: Optional[List[str]] = None
    frequency: str

class AlertRuleCreate(AlertRuleBase):
    pass

class AlertRuleResponse(AlertRuleBase):
    id: int
    user_id: str
    
    model_config = ConfigDict(from_attributes=True)
