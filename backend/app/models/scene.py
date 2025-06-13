from pydantic import BaseModel
from typing import List, Optional

class Scene(BaseModel):
    id: int
    name: str
    description: str
    goal: str
    icon: str

class Question(BaseModel):
    id: int
    sceneId: int
    text: str
    voiceUrl: str
    duration: str

# 场景数据
scenes = [
    {
        "id": 0,
        "name": "核苷酸产品介绍",
        "description": "你是一位珍奥双迪的保健品销售，正在对保健品持怀疑态度且较为节俭的中老年客户，重点推广核苷酸产品",
        "goal": "通过科学依据和产品优势打消客户疑虑，促使选择购买珍奥的核苷酸产品。",
        "icon": "/static/scene1.png"
    },
    {
        "id": 1,
        "name": "新客户开发",
        "description": "针对首次接触的潜在客户，学习如何有效地介绍产品和建立信任。本场景模拟与一位对产品完全陌生的客户进行初次沟通，你需要通过有效的自我介绍和产品展示，引起客户的兴趣。",
        "goal": "学习如何快速建立与新客户的信任关系，引起客户对产品的兴趣，为后续的深入交流奠定基础。",
        "icon": "/static/scene1.png"
    },
    {
        "id": 2,
        "name": "异议处理",
        "description": "学习如何面对客户提出的各种异议，并有效地进行回应。在销售过程中，客户常常会提出各种疑问和异议，本场景将帮助你学习如何处理这些问题，并将潜在的阻碍转化为销售机会。",
        "goal": "掌握处理客户异议的技巧，将异议转化为销售机会，提高客户的购买意愿。",
        "icon": "/static/scene2.png"
    },
    {
        "id": 3,
        "name": "产品推荐",
        "description": "根据客户需求，推荐最合适的产品，提高销售成功率。本场景模拟客户已经表明了自己的需求，你需要基于这些需求，向客户推荐最合适的产品。",
        "goal": "学习如何精准分析客户需求，进行有针对性的产品推荐，提高客户满意度和购买几率。",
        "icon": "/static/scene3.png"
    },
    {
        "id": 4,
        "name": "成交技巧",
        "description": "学习如何引导客户做出购买决定，顺利完成销售。本场景模拟客户已经对产品有较高兴趣，但尚未做出购买决定的情况，你需要运用成交技巧，促使客户完成购买。",
        "goal": "掌握成交的时机把握和话术技巧，提高成交率，顺利完成销售过程。",
        "icon": "/static/scene4.png"
    }
]

# 问题数据
questions = {
    0: [  # 核苷酸产品介绍
        {
            "id": 1,
            "sceneId": 0,
            "text": "我现在很年轻，平常很注重食疗，现在身体状态很不错，我现在真的需要保健吗？",
            "voiceUrl": "/static/audio/scene1-q1.mp3",
            "duration": "5"
        },
        {
            "id": 2,
            "sceneId": 0,
            "text": "这个产品我吃完以后能有什么效果或者改善呢？",
            "voiceUrl": "/static/audio/scene1-q2.mp3",
            "duration": "4"
        },
        {
            "id": 3,
            "sceneId": 0,
            "text": "我有很多保健品的选择，为什么要选择你们的核苷酸呢？",
            "voiceUrl": "/static/audio/scene1-q3.mp3",
            "duration": "5"
        }
    ],
    1: [  # 新客户开发
        {
            "id": 1,
            "sceneId": 1,
            "text": "您好，听说贵公司有一些不错的产品，能简单介绍一下吗？",
            "voiceUrl": "/static/audio/scene1-q1.mp3",
            "duration": "5"
        },
        {
            "id": 2,
            "sceneId": 1,
            "text": "我还不太了解你们公司的背景，能告诉我你们公司的情况吗？",
            "voiceUrl": "/static/audio/scene1-q2.mp3",
            "duration": "4"
        },
        {
            "id": 3,
            "sceneId": 1,
            "text": "市场上类似的产品很多，贵公司的产品有什么特别之处吗？",
            "voiceUrl": "/static/audio/scene1-q3.mp3",
            "duration": "5"
        }
    ],
    2: [  # 异议处理
        {
            "id": 4,
            "sceneId": 2,
            "text": "这个价格对我来说有点高，能便宜一些吗？",
            "voiceUrl": "/static/audio/scene2-q1.mp3",
            "duration": "3"
        },
        {
            "id": 5,
            "sceneId": 2,
            "text": "我以前用过类似的产品，但效果不太理想，为什么我要选择你们的呢？",
            "voiceUrl": "/static/audio/scene2-q2.mp3",
            "duration": "6"
        },
        {
            "id": 6,
            "sceneId": 2,
            "text": "我需要考虑一下，可以过几天再联系你吗？",
            "voiceUrl": "/static/audio/scene2-q3.mp3",
            "duration": "4"
        }
    ],
    3: [  # 产品推荐
        {
            "id": 7,
            "sceneId": 3,
            "text": "我需要一个能提高团队效率的工具，你们有什么推荐？",
            "voiceUrl": "/static/audio/scene3-q1.mp3",
            "duration": "4"
        },
        {
            "id": 8,
            "sceneId": 3,
            "text": "我预算有限，有什么性价比高的选择吗？",
            "voiceUrl": "/static/audio/scene3-q2.mp3",
            "duration": "3"
        },
        {
            "id": 9,
            "sceneId": 3,
            "text": "我们团队有20人，有适合团队使用的套餐吗？",
            "voiceUrl": "/static/audio/scene3-q3.mp3",
            "duration": "4"
        }
    ],
    4: [  # 成交技巧
        {
            "id": 10,
            "sceneId": 4,
            "text": "我对产品很满意，但现在签合同是不是太仓促了？",
            "voiceUrl": "/static/audio/scene4-q1.mp3",
            "duration": "4"
        },
        {
            "id": 11,
            "sceneId": 4,
            "text": "如果我现在决定购买，有什么优惠吗？",
            "voiceUrl": "/static/audio/scene4-q2.mp3",
            "duration": "3"
        },
        {
            "id": 12,
            "sceneId": 4,
            "text": "购买后如果不满意，能退款吗？",
            "voiceUrl": "/static/audio/scene4-q3.mp3",
            "duration": "3"
        }
    ]
} 