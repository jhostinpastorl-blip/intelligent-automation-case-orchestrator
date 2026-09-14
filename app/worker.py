import logging
import os
import time
from app.dispatch import get_dispatch_queue
from app.models import CaseStatus
from app.store import store
from app.telemetry import configure_telemetry, get_tracer
from app.tools import execute_tool

logger=logging.getLogger(__name__)

class ExecutionWorker:
    def run_once(self):
        dispatch=get_dispatch_queue()
        requested=dispatch.consume(timeout_seconds=1) if dispatch.brokered else None
        record=store.claim_execution(requested) if requested else store.claim_execution()
        if record is None: return False
        if record.analysis is None or record.analysis.proposed_tool is None:
            record.status=CaseStatus.FAILED; store.save(record); store.event(record,"execution_failed","No tool"); return True
        with get_tracer().start_as_current_span("execute_approved_intent") as span:
            span.set_attribute("case.id", record.case_id)
            try:
                result=execute_tool(record.analysis.proposed_tool)
            except Exception as exc:
                record.execution_result={"error":str(exc)}; record.status=CaseStatus.FAILED; store.save(record); store.event(record,"execution_failed",str(exc)); span.record_exception(exc)
            else:
                record.execution_result=result; record.status=CaseStatus.EXECUTED; store.save(record); store.event(record,"tool_executed",record.analysis.proposed_tool.tool_name)
        return True
    def run_forever(self, poll=1.0):
        while True:
            if not self.run_once(): time.sleep(poll)

def main():
    logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO")); configure_telemetry(); ExecutionWorker().run_forever(float(os.getenv("WORKER_POLL_INTERVAL_SECONDS","1")))
if __name__=="__main__": main()
