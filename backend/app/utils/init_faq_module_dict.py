"""
初始化常见问题模块字典工具

本模块用于在应用启动时自动创建常见问题模块字典（如果不存在）。
字典编码: FAQ_MODULE

作者: Auto
创建时间: 2024
"""

from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.app.models import Project, Dictionary, DictionaryValue
from backend.app.schemas import DictionaryCreate, DictionaryValueCreate


def init_faq_module_dictionary():
    """
    初始化常见问题模块字典
    
    如果字典不存在，则创建字典和预定义的字典值。
    如果字典已存在，则跳过创建。
    """
    db: Session = SessionLocal()
    try:
        # 检查字典是否已存在
        existing_dict = db.query(Dictionary).filter(Dictionary.code == "FAQ_MODULE").first()
        
        if existing_dict:
            print(f"常见问题模块字典已存在，ID: {existing_dict.id}")
            return existing_dict.id
        
        # 获取第一个项目，如果没有项目则创建一个默认项目
        project = db.query(Project).first()
        if not project:
            print("未找到项目，创建默认项目...")
            project = Project(
                name="系统默认项目",
                manager="系统管理员",
                contact_info="系统",
                description="系统默认项目，用于存储系统级字典"
            )
            db.add(project)
            db.flush()
            print(f"已创建默认项目，ID: {project.id}")
        
        # 创建字典
        dictionary = Dictionary(
            project_id=project.id,
            name="常见问题模块",
            code="FAQ_MODULE",
            description="常见问题所属模块字典，用于分类管理常见问题"
        )
        db.add(dictionary)
        db.flush()
        
        # 创建预定义的字典值
        module_values = [
            {"key": "1", "value": "患者管理", "description": "患者相关常见问题模块", "order_index": 1},
            {"key": "2", "value": "医嘱管理", "description": "医嘱相关常见问题模块", "order_index": 2},
            {"key": "3", "value": "收费管理", "description": "收费相关常见问题模块", "order_index": 3},
            {"key": "4", "value": "药品管理", "description": "药品相关常见问题模块", "order_index": 4},
            {"key": "5", "value": "检验检查", "description": "检验检查相关常见问题模块", "order_index": 5},
            {"key": "6", "value": "系统设置", "description": "系统设置相关常见问题模块", "order_index": 6},
            {"key": "7", "value": "报表统计", "description": "报表统计相关常见问题模块", "order_index": 7},
            {"key": "8", "value": "其他", "description": "其他类别常见问题模块", "order_index": 8},
        ]
        
        for value_data in module_values:
            dict_value = DictionaryValue(
                dictionary_id=dictionary.id,
                key=value_data["key"],
                value=value_data["value"],
                description=value_data["description"],
                order_index=value_data["order_index"]
            )
            db.add(dict_value)
        
        db.commit()
        print(f"已创建常见问题模块字典，ID: {dictionary.id}，包含 {len(module_values)} 个字典值")
        return dictionary.id
        
    except Exception as e:
        db.rollback()
        print(f"初始化常见问题模块字典失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # 直接运行此脚本时，初始化字典
    init_faq_module_dictionary()

