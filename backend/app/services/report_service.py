from datetime import datetime
import uuid
import random
from typing import Dict, List, Any
from app.models.report import Report, reports, dimension_templates, suggestion_templates
from app.core.logging import logger

def generate_report(scene_id: int, user_id: str, messages: List[Dict[str, Any]]) -> Report:
    """生成练习报告"""
    try:
        # 创建一个唯一的报告ID
        report_id = f"report_{scene_id}_{uuid.uuid4().hex[:8]}"
        
        # 生成模拟报告数据
        report = Report(
            id=report_id,
            scene_id=scene_id,
            user_id=user_id,
            overall=random.randint(75, 95),
            dimensions={
                "languageOrganization": random.randint(70, 90),
                "persuasiveness": random.randint(70, 90),
                "fluency": random.randint(70, 90),
                "accuracy": random.randint(70, 90),
                "expression": random.randint(70, 90)
            },
            analysis={
                dimension: {
                    "score": score,
                    "content": dimension_templates[dimension]["content"]
                }
                for dimension, score in {
                    "languageOrganization": random.randint(70, 90),
                    "persuasiveness": random.randint(70, 90),
                    "fluency": random.randint(70, 90),
                    "accuracy": random.randint(70, 90),
                    "expression": random.randint(70, 90)
                }.items()
            },
            suggestions=random.sample(suggestion_templates, 3),
            created_at=datetime.now()
        )
        
        # 保存报告
        reports[report_id] = report
        
        return report
    except Exception as e:
        logger.error(f"生成报告失败: {str(e)}")
        raise

def get_report(report_id: str) -> Report:
    """获取指定ID的报告"""
    report = reports.get(report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")
    return report

def polish_text(text: str, scene_id: int) -> Dict[str, str]:
    """润色用户表达"""
    try:
        # 根据场景ID选择不同的润色模板
        polish_templates = {
            1: [  # 新客户开发
                "您好，我是XX公司的销售顾问。我们公司专注于提供高质量的销售培训解决方案，已经帮助超过1000家企业提升了30%的销售业绩。根据您的需求，我们的产品可以为您提供个性化的培训方案，帮助您的团队快速提升销售技能。",
                "感谢您的咨询。我们公司成立于2010年，专注于销售培训领域，拥有丰富的行业经验和专业的培训团队。我们的产品采用最新的AI技术，能够根据每个销售人员的表现提供个性化的改进建议，帮助团队整体提升销售能力。",
                "您提到的市场竞争问题很重要。与市场上其他产品相比，我们的优势在于更精准的数据分析和更全面的客户服务。我们的系统不仅提供培训，还能实时跟踪销售人员的表现，生成详细的报告，帮助管理层做出更明智的决策。"
            ],
            2: [  # 异议处理
                "关于价格问题，我完全理解您的考虑。我们的产品虽然初始投资较高，但长期来看，它能够帮助您的团队提高30%的销售效率，这意味着更多的收入和利润。此外，我们提供灵活的付款方案，可以根据您的预算进行调整。",
                "您提到的使用体验问题很有价值。我们最近对产品进行了全面升级，解决了之前用户反馈的问题。现在系统更加稳定，界面更加友好，而且我们提供7*24小时的技术支持，确保您在使用过程中遇到任何问题都能得到及时解决。",
                "我理解您需要时间考虑。这是一个重要的决定，确实需要慎重。不过，我想提醒您，我们目前正在进行限时优惠活动，如果您在本周内做出决定，可以享受20%的折扣。同时，我们提供30天无理由退款保证，您可以放心试用。"
            ],
            3: [  # 产品推荐
                "针对提高团队效率的需求，我推荐我们的'销售加速器'套餐。这个套餐包含完整的销售培训课程、实时表现分析工具和个性化辅导服务，能够帮助您的团队在短时间内提升销售技能和工作效率。根据我们客户的数据，使用这个套餐的团队平均在3个月内提升了25%的销售业绩。",
                "考虑到您的预算限制，我推荐我们的'基础提升'套餐。这个套餐虽然功能相对简单，但包含了最核心的销售技能培训和分析工具，性价比极高。我们还可以根据您的具体需求进行定制，确保您花的每一分钱都能带来最大的回报。",
                "对于20人的团队，我们的'团队协作'套餐是最佳选择。这个套餐专为中型团队设计，包含团队协作工具、集体培训课程和团队绩效分析报告。我们还可以为您的团队提供专属的客户经理，确保您获得最优质的服务和支持。"
            ],
            4: [  # 成交技巧
                "签合同并不仓促，而是对双方都有保障的正式承诺。我们的产品已经得到了市场的广泛认可，目前有超过1000家企业正在使用。如果您现在签约，不仅可以享受当前的优惠价格，还能立即开始使用我们的产品，帮助您的团队提升销售业绩。",
                "如果您现在决定购买，除了享受当前的折扣外，我们还可以为您提供3个月的免费技术支持服务，价值超过5000元。此外，我们还会为您的团队提供一次免费的销售技能评估，帮助您了解团队的现状和提升空间。",
                "我们对自己的产品非常有信心，因此提供30天无理由退款保证。如果您在使用过程中发现产品不符合您的需求，可以随时申请退款，我们会全额退还您的费用，没有任何附加条件。这充分体现了我们对产品质量的自信和对客户的尊重。"
            ]
        }
        
        # 选择对应场景的润色模板
        templates = polish_templates.get(scene_id, polish_templates[1])
        
        # 根据用户输入内容选择最相关的模板
        selected_template = templates[0]  # 默认使用第一个模板
        
        # 简单的关键词匹配逻辑
        keywords = {
            "价格": 0,
            "贵": 0,
            "便宜": 0,
            "优惠": 0,
            "折扣": 0,
            "公司": 1,
            "背景": 1,
            "成立": 1,
            "产品": 2,
            "特点": 2,
            "优势": 2,
            "特别": 2,
            "考虑": 3,
            "想想": 3,
            "再联系": 3,
            "签": 4,
            "合同": 4,
            "购买": 4,
            "退款": 5,
            "不满意": 5
        }
        
        # 查找匹配的关键词
        for keyword, index in keywords.items():
            if keyword in text and index < len(templates):
                selected_template = templates[index]
                break
        
        return {"polishedText": selected_template}
    except Exception as e:
        logger.error(f"润色文本失败: {str(e)}")
        raise 