"""
RippleStorage 储能系统配置智能生成器
使用 LLM 或规则根据文档内容与实体信息自动生成电池、电价、负荷配置
"""

import json
import math
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime

from openai import OpenAI

from ..config import Config
from ..utils.logger import get_logger
from ..utils.locale import get_language_instruction, t
from .zep_entity_reader import EntityNode

logger = get_logger('ripplestorage.simulation_config')


@dataclass
class TimeSimulationConfig:
    total_simulation_hours: int = 24
    minutes_per_round: int = 60
    agents_per_hour_min: int = 1
    agents_per_hour_max: int = 5
    peak_hours: List[int] = field(default_factory=lambda: [9, 10, 11, 12, 13, 14, 19, 20, 21])
    peak_activity_multiplier: float = 1.5
    off_peak_hours: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6, 7])
    off_peak_activity_multiplier: float = 0.3
    morning_hours: List[int] = field(default_factory=lambda: [8])
    morning_activity_multiplier: float = 0.8
    work_hours: List[int] = field(default_factory=lambda: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18])
    work_activity_multiplier: float = 1.0


@dataclass
class EventConfig:
    initial_posts: List[Dict[str, Any]] = field(default_factory=list)
    scheduled_events: List[Dict[str, Any]] = field(default_factory=list)
    hot_topics: List[str] = field(default_factory=list)
    narrative_direction: str = ""


@dataclass
class PlatformConfig:
    platform: str
    recency_weight: float = 0.4
    popularity_weight: float = 0.3
    relevance_weight: float = 0.3
    viral_threshold: int = 10
    echo_chamber_strength: float = 0.5


@dataclass
class AgentActivityConfig:
    agent_id: int
    entity_uuid: str
    entity_name: str
    entity_type: str
    activity_level: float = 0.5
    posts_per_hour: float = 1.0
    comments_per_hour: float = 2.0
    active_hours: List[int] = field(default_factory=lambda: list(range(8, 23)))
    response_delay_min: int = 5
    response_delay_max: int = 60
    sentiment_bias: float = 0.0
    stance: str = "neutral"
    influence_weight: float = 1.0


@dataclass
class SimulationParameters:
    simulation_id: str
    project_id: str
    graph_id: str
    simulation_requirement: str
    time_config: TimeSimulationConfig = field(default_factory=TimeSimulationConfig)
    agent_configs: List[AgentActivityConfig] = field(default_factory=list)
    event_config: EventConfig = field(default_factory=EventConfig)
    twitter_config: Optional[PlatformConfig] = None
    reddit_config: Optional[PlatformConfig] = None
    llm_model: str = ""
    llm_base_url: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_reasoning: str = ""
    # RippleStorage 新增字段
    battery_config: Dict[str, Any] = field(default_factory=dict)
    tariff_config: Dict[str, Any] = field(default_factory=dict)
    load_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "time_config": asdict(self.time_config),
            "agent_configs": [asdict(a) for a in self.agent_configs],
            "event_config": asdict(self.event_config),
            "twitter_config": asdict(self.twitter_config) if self.twitter_config else None,
            "reddit_config": asdict(self.reddit_config) if self.reddit_config else None,
            "llm_model": self.llm_model,
            "llm_base_url": self.llm_base_url,
            "generated_at": self.generated_at,
            "generation_reasoning": self.generation_reasoning,
            "battery_config": self.battery_config,
            "tariff_config": self.tariff_config,
            "load_config": self.load_config,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class SimulationConfigGenerator:
    MAX_CONTEXT_LENGTH = 50000
    AGENTS_PER_BATCH = 15

    def __init__(self, api_key=None, base_url=None, model_name=None):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME
        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate_config(
        self,
        simulation_id: str,
        project_id: str,
        graph_id: str,
        simulation_requirement: str,
        document_text: str,
        entities: List[EntityNode],
        enable_twitter: bool = True,
        enable_reddit: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> SimulationParameters:
        logger.info(f"开始生成储能配置: simulation_id={simulation_id}, 实体数={len(entities)}")

        num_batches = math.ceil(len(entities) / self.AGENTS_PER_BATCH)
        total_steps = 3 + num_batches
        current_step = 0

        def report_progress(step: int, message: str):
            nonlocal current_step
            current_step = step
            if progress_callback:
                progress_callback(step, total_steps, message)
            logger.info(f"[{step}/{total_steps}] {message}")

        context = self._build_context(simulation_requirement, document_text, entities)

        # 步骤1: 时间配置
        report_progress(1, t('progress.generatingTimeConfig'))
        time_config = TimeSimulationConfig(
            total_simulation_hours=24,
            minutes_per_round=60,
        )

        # 步骤2: 事件配置（保持兼容，置空）
        report_progress(2, t('progress.generatingEventConfig'))
        event_config = EventConfig()

        # 步骤3-N: Agent 配置（映射为储能系统组件）
        all_agent_configs = []
        for batch_idx in range(num_batches):
            start_idx = batch_idx * self.AGENTS_PER_BATCH
            end_idx = min(start_idx + self.AGENTS_PER_BATCH, len(entities))
            batch_entities = entities[start_idx:end_idx]
            report_progress(3 + batch_idx, t('progress.generatingAgentConfig', start=start_idx + 1, end=end_idx, total=len(entities)))
            batch_configs = self._generate_agent_configs_batch(batch_entities, start_idx)
            all_agent_configs.extend(batch_configs)

        # 生成平台配置（保持兼容）
        report_progress(total_steps, t('progress.generatingPlatformConfig'))
        twitter_config = PlatformConfig(platform="twitter") if enable_twitter else None
        reddit_config = PlatformConfig(platform="reddit") if enable_reddit else None

        # 生成储能核心配置（电池、电价、负荷）
        battery_cfg, tariff_cfg, load_cfg = self._generate_energy_configs(context, simulation_requirement, entities)

        reasoning = (
            f"时间配置: 24小时仿真, 60分钟/轮 | "
            f"组件配置: 生成 {len(all_agent_configs)} 个储能系统组件 | "
            f"电池容量: {battery_cfg.get('capacity_kwh', 2000)}kWh | "
            f"电价策略: 峰={tariff_cfg.get('peak_price', 1.2)}元, 谷={tariff_cfg.get('valley_price', 0.3)}元"
        )

        return SimulationParameters(
            simulation_id=simulation_id,
            project_id=project_id,
            graph_id=graph_id,
            simulation_requirement=simulation_requirement,
            time_config=time_config,
            agent_configs=all_agent_configs,
            event_config=event_config,
            twitter_config=twitter_config,
            reddit_config=reddit_config,
            llm_model=self.model_name,
            llm_base_url=self.base_url,
            generation_reasoning=reasoning,
            battery_config=battery_cfg,
            tariff_config=tariff_cfg,
            load_config=load_cfg,
        )

    def _build_context(self, simulation_requirement: str, document_text: str, entities: List[EntityNode]) -> str:
        entity_summary = self._summarize_entities(entities)
        parts = [f"## 模拟需求\n{simulation_requirement}", f"\n## 实体信息 ({len(entities)}个)\n{entity_summary}"]
        current_length = sum(len(p) for p in parts)
        remaining = self.MAX_CONTEXT_LENGTH - current_length - 500
        doc_snippet = document_text[:max(0, remaining)] if document_text else ""
        if doc_snippet:
            parts.append(f"\n## 文档节选\n{doc_snippet}")
        return "\n".join(parts)

    def _summarize_entities(self, entities: List[EntityNode]) -> str:
        lines = []
        for e in entities[:30]:
            t = e.get_entity_type() or "Unknown"
            lines.append(f"- {e.name} ({t}): {e.summary[:80] if e.summary else 'N/A'}")
        return "\n".join(lines)

    def _generate_agent_configs_batch(self, batch_entities: List[EntityNode], start_idx: int) -> List[AgentActivityConfig]:
        configs = []
        for i, entity in enumerate(batch_entities):
            configs.append(AgentActivityConfig(
                agent_id=start_idx + i,
                entity_uuid=entity.uuid,
                entity_name=entity.name,
                entity_type=entity.get_entity_type() or "Component",
                activity_level=0.7,
                posts_per_hour=1.0,
                comments_per_hour=0.5,
                active_hours=list(range(0, 24)),
                response_delay_min=5,
                response_delay_max=30,
                sentiment_bias=0.0,
                stance="neutral",
                influence_weight=1.0,
            ))
        return configs

    def _generate_energy_configs(self, context: str, requirement: str, entities: List[EntityNode]) -> tuple:
        """生成电池、电价、负荷配置。优先使用规则默认值，LLM 做简单推理覆盖。"""
        # 默认值
        battery = {
            "capacity_kwh": 2000,
            "max_charge_kw": 1000,
            "max_discharge_kw": 1000,
            "efficiency": 0.92,
            "initial_soc": 0.2,
            "min_soc": 0.1,
            "max_soc": 0.95,
        }
        tariff = {
            "peak_price": 1.2,
            "valley_price": 0.3,
            "flat_price": 0.8,
            "peak_hours": [9, 10, 11, 12, 13, 14, 19, 20, 21],
            "valley_hours": [0, 1, 2, 3, 4, 5, 6, 7],
        }
        load_cfg = {
            "base_load_kw": 500,
            "peak_load_kw": 2000,
        }

        # 尝试用 LLM 提取关键参数（轻量级调用）
        try:
            prompt = (
                "根据以下工商业储能项目信息，提取三个核心参数，以 JSON 返回，不要额外解释:\n"
                "{\"battery_capacity_kwh\": 整数, \"peak_price\": 数字, \"peak_load_kw\": 整数}\n\n"
                f"项目需求: {requirement[:500]}\n"
                f"实体信息: {self._summarize_entities(entities[:10])}"
            )
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个储能系统参数提取助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=200,
            )
            content = resp.choices[0].message.content or ""
            # 尝试解析 JSON
            import re
            m = re.search(r'\{.*?\}', content, re.DOTALL)
            if m:
                data = json.loads(m.group())
                if "battery_capacity_kwh" in data:
                    battery["capacity_kwh"] = max(100, int(data["battery_capacity_kwh"]))
                    battery["max_charge_kw"] = battery["capacity_kwh"] // 2
                    battery["max_discharge_kw"] = battery["capacity_kwh"] // 2
                if "peak_price" in data:
                    tariff["peak_price"] = float(data["peak_price"])
                if "peak_load_kw" in data:
                    load_cfg["peak_load_kw"] = max(100, int(data["peak_load_kw"]))
                    load_cfg["base_load_kw"] = load_cfg["peak_load_kw"] // 4
        except Exception as e:
            logger.warning(f"LLM 提取储能参数失败，使用默认值: {e}")

        return battery, tariff, load_cfg
