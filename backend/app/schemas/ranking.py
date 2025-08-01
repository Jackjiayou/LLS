from pydantic import BaseModel
from typing import List, Optional

class RankingItem(BaseModel):
    user_id: int
    name: str
    avatar: Optional[str] = None
    score: float
    scenario_count: int

class CurrentUserRank(BaseModel):
    user_id: int
    name: str
    avatar: Optional[str] = None
    score: float
    scenario_count: int
    rank: int

class RankingResponse(BaseModel):
    ranking_list: List[RankingItem]
    current_user: Optional[CurrentUserRank] = None 