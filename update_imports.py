import os
import re

mapping = {
    'chat_engine': 'backend.models.chat_engine',
    'world_model': 'backend.models.world_model',
    'pretraining_pipeline': 'backend.models.pretraining_pipeline',
    'execution_engine': 'backend.agents.execution_engine',
    'document_parser': 'backend.utils.document_parser',
    'enterprise_platform': 'backend.services.enterprise_platform',
    'knowledge_engine': 'backend.services.knowledge_engine',
    'security_framework': 'backend.services.security_framework',
    'learning_from_experience': 'backend.memory.learning_from_experience',
    'autonomous_execution_engine': 'backend.agents.autonomous_execution_engine',
    'autonomous_research_scientist': 'backend.agents.autonomous_research_scientist',
    'ai_service': 'backend.api.ai_service',
    'chat': 'backend.api.chat',
    'api_chat_runner': 'backend.api.api_chat_runner',
    'add_route': 'backend.api.add_route',
    'agent_planner': 'backend.agents.agent_planner',
    'agent_society': 'backend.agents.agent_society',
    'multi_agent_system': 'backend.agents.multi_agent_system',
    'nexa_multi_agent': 'backend.agents.nexa_multi_agent',
    'nexa_studio': 'backend.agents.nexa_studio',
    'nexa_autonomous_platform': 'backend.agents.nexa_autonomous_platform',
    'episodic_memory_engine': 'backend.memory.episodic_memory_engine',
    'memory_engine': 'backend.memory.memory_engine',
    'nexa_memory_system': 'backend.memory.nexa_memory_system',
    'rag_engine': 'backend.rag.rag_engine',
    'retrieval_service': 'backend.rag.retrieval_service',
    'nexa_rag_platform': 'backend.rag.nexa_rag_platform',
    'vector_store': 'backend.rag.vector_store',
    'ocr_engine': 'backend.vision.ocr_engine',
    'image_pipeline': 'backend.vision.image_pipeline',
    'nexa_vision_multimodal': 'backend.vision.nexa_vision_multimodal',
    'embedding_service': 'backend.services.embedding_service',
    'multimodal_service': 'backend.services.multimodal_service',
    'ai_platform': 'backend.services.ai_platform',
    'nexa_cloud_platform': 'backend.services.nexa_cloud_platform',
    'chunk_manager': 'backend.utils.chunk_manager',
    'context_engine': 'backend.utils.context_engine',
    'filesystem_tools': 'backend.utils.filesystem_tools',
    'python_tools': 'backend.utils.python_tools',
    'terminal_tools': 'backend.utils.terminal_tools',
    'tool_manager': 'backend.utils.tool_manager',
    'tool_registry': 'backend.utils.tool_registry'
}

def update_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                new_content = content
                for old, new in mapping.items():
                    # Replace 'from old import' with 'from new import'
                    new_content = re.sub(rf'from\s+{old}(\s+import)', rf'from {new}\1', new_content)
                    # Replace 'import old' with 'import new' (be careful with word boundaries)
                    new_content = re.sub(rf'import\s+{old}(\s|$)', rf'import {new}\1', new_content)
                
                if new_content != content:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    print(f"Updated imports in {filepath}")

if __name__ == "__main__":
    update_imports('backend')
