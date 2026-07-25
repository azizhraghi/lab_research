# -*- coding: utf-8 -*-
from __future__ import annotations                   
from pydantic import BaseModel, Field                
from typing import Optional                           
from datetime import datetime, timezone              
from uuid import uuid4    


class Paper(BaseModel):
    """represents a scientific paper discovered by the veille agent"""

    id: str                                           
    title: str                                       
    authors: str                                      
    summary: str                                      
    plain_summary: Optional[str] = None               
    topic: Optional[str] = None                       
    source: str                                       
    discovered_at: datetime = Field(                 
        default_factory=lambda: datetime.now(timezone.utc)
    )

class ArticleDiscoveredPayload(BaseModel):
    """the payload attached to an article.discovered event
    this is what the bibliometrie agent will receive"""

    paper_id: str                                     
    title: str                                        
    authors: str                                      
    topic: str                                       
    plain_summary: str                                
    source: str                                       
    discovered_at: str                                