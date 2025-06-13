from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Any

class Report(BaseModel):
    id: str
    scene_id: int
    user_id: str
    overall: int
    dimensions: Dict[str, int]
    analysis: Dict[str, Dict[str, Any]]
    suggestions: List[str]
    created_at: datetime

class ReportCreate(BaseModel):
    scene_id: int
    user_id: str
    messages: List[Dict[str, Any]]

class ReportResponse(BaseModel):
    report_id: str

# 存储报告的字典
reports = {}

# 维度分析模板
dimension_templates = {
    "languageOrganization": {
        "content": "您的语言组织整体较好，能够按照逻辑顺序表达自己的观点。但在某些回答中，内容结构可以更紧凑，减少不必要的铺垫。"
    },
    "persuasiveness": {
        "content": "您在阐述产品优势时的说服力有待提高。建议增加具体数据和案例支持，让客户更容易接受您的观点。"
    },
    "fluency": {
        "content": "您的语速适中，表达流畅，很少出现停顿或冗余词。在回答中，仅有少量的明显停顿，整体流利度表现良好。"
    },
    "accuracy": {
        "content": "您对产品特性的描述基本准确，能够清晰地传达核心价值。但在解释某些技术细节时有轻微的不准确。"
    },
    "expression": {
        "content": "您的语言表达整体清晰，用词专业，能够使用行业术语增强专业感。但有时用词略显重复，可以通过丰富词汇量来增加表达的多样性。"
    }
}

# 改进建议模板
suggestion_templates = [
    "在回答客户问题前，可以先简短重复一下客户的问题，表明您理解了他们的需求。",
    "增加具体案例和数据支持，提高说服力。可以准备2-3个成功案例，在合适的时机分享。",
    "适当使用反问句引导客户思考，这样的问题可以引导客户从新的角度看问题。",
    "在谈到产品优势时，可以结合客户所处的行业情况，使建议更有针对性。",
    "练习如何简洁有力地总结对话内容，在每个销售环节结束时进行小结，帮助客户和自己明确当前进展。"
] 