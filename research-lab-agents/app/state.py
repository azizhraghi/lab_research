"""
Instances partagees de l'application : un seul bus, un seul agent MIS,
un seul Orchestrateur, un seul Agent Qualite, crees une fois et reutilises partout.
"""
import os
from dotenv import load_dotenv
from app.agents.mis_agent import MISAgent
from app.agents.orchestrateur_agent import OrchestratorAgent
from app.agents.qualite_agent import QualiteAgent
from app.core.event_bus import EventBus, InMemoryEventBus, KafkaEventBus, RedisEventBus

load_dotenv()


def creer_event_bus() -> EventBus:
    type_bus = os.getenv("EVENT_BUS_TYPE", "memory")
    if type_bus == "kafka":
        print("[state] EventBus : Kafka")
        return KafkaEventBus()
    if type_bus == "redis":
        print("[state] EventBus : Redis")
        return RedisEventBus()
    print("[state] EventBus : InMemory")
    return InMemoryEventBus()

event_bus = creer_event_bus()
mis_agent = MISAgent(name="mis", event_bus=event_bus)
orchestrator_agent = OrchestratorAgent(name="orchestrateur", event_bus=event_bus)
qualite_agent = QualiteAgent(name="qualite", event_bus=event_bus)