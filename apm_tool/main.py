import asyncio
from apm_tool.orchestrator import Orchestrator

if __name__ == "__main__":
    print("APM Tool started")
    orchestrator = Orchestrator()
    try:
        asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        orchestrator.shutdown()
