"""
RippleStorage 储能系统组件 Profile 生成器
将 Zep 图谱中的实体映射为储能系统的控制组件/设备 Agent
"""

import json
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI
from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger
from ..utils.locale import get_language_instruction, t
from .zep_entity_reader import EntityNode, ZepEntityReader

logger = get_logger('ripplestorage.oasis_profile')


@dataclass
class OasisAgentProfile:
    user_id: int
    user_name: str
    name: str
    bio: str
    persona: str
    karma: int = 1000
    friend_count: int = 100
    follower_count: int = 150
    statuses_count: int = 500
    age: Optional[int] = None
    gender: Optional[str] = None
    mbti: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None
    interested_topics: List[str] = field(default_factory=list)
    source_entity_uuid: Optional[str] = None
    source_entity_type: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def to_reddit_format(self) -> Dict[str, Any]:
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "created_at": self.created_at,
        }
        for k in ["age", "gender", "mbti", "country", "profession", "interested_topics"]:
            v = getattr(self, k)
            if v:
                profile[k] = v
        return profile

    def to_twitter_format(self) -> Dict[str, Any]:
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "created_at": self.created_at,
        }
        for k in ["age", "gender", "mbti", "country", "profession", "interested_topics"]:
            v = getattr(self, k)
            if v:
                profile[k] = v
        return profile

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id, "user_name": self.user_name, "name": self.name,
            "bio": self.bio, "persona": self.persona, "karma": self.karma,
            "friend_count": self.friend_count, "follower_count": self.follower_count,
            "statuses_count": self.statuses_count, "age": self.age, "gender": self.gender,
            "mbti": self.mbti, "country": self.country, "profession": self.profession,
            "interested_topics": self.interested_topics,
            "source_entity_uuid": self.source_entity_uuid,
            "source_entity_type": self.source_entity_type,
            "created_at": self.created_at,
        }


class OasisProfileGenerator:
    COMPONENT_ROLES = {
        "ems": "能量管理系统 (EMS) - 负责全局优化调度",
        "bms": "电池管理系统 (BMS) - 负责电芯监控与安全",
        "pcs": "储能变流器 (PCS) - 负责功率转换",
        "load": "负荷预测 Agent - 负责用电需求预测",
        "grid": "电网交互 Agent - 负责并离网策略",
        "default": "储能协同组件 - 参与系统控制",
    }

    def __init__(self, api_key=None, base_url=None, model_name=None, zep_api_key=None, graph_id=None):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME
        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.zep_api_key = zep_api_key or Config.ZEP_API_KEY
        self.zep_client = None
        self.graph_id = graph_id
        if self.zep_api_key:
            try:
                self.zep_client = Zep(api_key=self.zep_api_key)
            except Exception as e:
                logger.warning(f"Zep 客户端初始化失败: {e}")

    def _map_entity_to_role(self, entity: EntityNode) -> str:
        name = entity.name.lower()
        etype = (entity.get_entity_type() or "").lower()
        if "电" in name or "battery" in name or "cell" in name or "储能" in name:
            return "bms"
        if "变流" in name or "pcs" in name or "逆变" in name or "inverter" in name:
            return "pcs"
        if "负荷" in name or "load" in name or "用电" in name or "需求" in name:
            return "load"
        if "电网" in name or "grid" in name or "电力" in name:
            return "grid"
        if "管理" in name or "ems" in name or "控制" in name or "调度" in name:
            return "ems"
        # 基于 entity type 索引映射
        type_map = {
            "student": "load", "professor": "load", "person": "load",
            "organization": "ems", "company": "ems", "university": "grid",
            "governmentagency": "grid", "mediaoutlet": "pcs",
        }
        return type_map.get(etype, "default")

    def generate_profile_from_entity(self, entity: EntityNode, user_id: int, use_llm: bool = True) -> OasisAgentProfile:
        role_key = self._map_entity_to_role(entity)
        role_desc = self.COMPONENT_ROLES.get(role_key, self.COMPONENT_ROLES["default"])
        name = entity.name
        user_name = f"{role_key.upper()}_{user_id:03d}"

        if use_llm:
            bio, persona = self._generate_with_llm(name, entity, role_desc)
        else:
            bio = f"{role_desc} | 实体: {name}"
            persona = f"作为 {role_desc}，我基于实体 '{name}' 的信息参与 RippleStorage 储能系统的协同优化。我的目标是提升系统安全性与经济性。"

        return OasisAgentProfile(
            user_id=user_id,
            user_name=user_name,
            name=name,
            bio=bio,
            persona=persona,
            karma=random.randint(500, 5000),
            friend_count=random.randint(50, 500),
            follower_count=random.randint(100, 1000),
            statuses_count=random.randint(100, 2000),
            profession=role_desc.split("-")[0].strip(),
            interested_topics=["储能优化", "峰谷套利", "需量管理", "电池安全"],
            source_entity_uuid=entity.uuid,
            source_entity_type=entity.get_entity_type() or "Component",
        )

    def _generate_with_llm(self, name: str, entity: EntityNode, role_desc: str) -> tuple:
        try:
            prompt = (
                f"将实体 '{name}' 转化为 RippleStorage 工商业储能系统中的一个数字孪生组件。\n"
                f"角色定位: {role_desc}\n"
                f"实体摘要: {entity.summary or 'N/A'}\n"
                f"请返回 JSON: {{\"bio\": \"50字内的组件简介\", \"persona\": \"100字内的组件人设与职责\"}}"
            )
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个储能系统数字孪生建模专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300,
            )
            content = resp.choices[0].message.content or ""
            import re
            m = re.search(r'\{.*?\}', content, re.DOTALL)
            if m:
                data = json.loads(m.group())
                return data.get("bio", ""), data.get("persona", "")
        except Exception as e:
            logger.warning(f"LLM 生成组件人设失败: {e}")
        bio = f"{role_desc} | 实体: {name}"
        persona = f"作为 {role_desc}，我基于实体 '{name}' 参与 RippleStorage 储能协同优化。"
        return bio, persona

    def generate_profiles_from_entities(
        self,
        entities: List[EntityNode],
        use_llm: bool = True,
        progress_callback=None,
        graph_id: str = None,
        parallel_count: int = 3,
        realtime_output_path: str = None,
        output_platform: str = "reddit"
    ) -> List[OasisAgentProfile]:
        profiles = []
        for i, entity in enumerate(entities):
            profile = self.generate_profile_from_entity(entity, user_id=i, use_llm=use_llm)
            profiles.append(profile)
            if progress_callback:
                progress_callback(i + 1, len(entities), f"已生成组件: {profile.name} ({profile.profession})")
            if realtime_output_path and output_platform == "reddit":
                self._append_realtime(realtime_output_path, profile)
        return profiles

    def _append_realtime(self, path: str, profile: OasisAgentProfile):
        try:
            data = []
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            data.append(profile.to_reddit_format())
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"实时保存失败: {e}")

    def save_profiles(self, profiles: List[OasisAgentProfile], file_path: str, platform: str = "reddit"):
        if platform == "twitter":
            import csv
            if not profiles:
                return
            sample = profiles[0].to_twitter_format()
            fieldnames = list(sample.keys())
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for p in profiles:
                    writer.writerow(p.to_twitter_format())
        else:
            data = [p.to_reddit_format() for p in profiles]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
