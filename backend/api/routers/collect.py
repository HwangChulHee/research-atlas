"""수집 에이전트 라우트 (LangGraph 흐름, start/resume/state)."""
import uuid

from fastapi import APIRouter, Body, HTTPException
from langgraph.types import Command

from backend.agents.collect import build_collect_graph

router = APIRouter()

# 그래프는 모듈 로드 시 1회 컴파일해 전역 보관 — 매 요청 compile하면 MemorySaver 상태가
# 초기화돼 resume이 깨진다(핵심 함정). thread_id별로 세션 격리됨.
_collect_graph = build_collect_graph()


def _interrupt_response(thread_id: str, payload: dict) -> dict:
    """interrupt payload(collect의 interrupt({...})) → stage별 프론트 응답."""
    stage = payload.get("stage")
    out = {"thread_id": thread_id, "done": False, "stage": stage}
    if stage == "interpret":
        out["topic"] = payload.get("topic", "")
        out["report"] = payload.get("status_report", "")
        out["actions"] = ["proceed", "revise", "cancel"]
    elif stage == "approve":
        out["counts"] = payload.get("counts", {})
        out["actions"] = ["proceed", "cancel"]
    elif stage == "extract_confirm":
        out["passed_count"] = payload.get("passed_count")
        out["to_extract"] = payload.get("to_extract")
        out["gate_summary"] = payload.get("gate_summary")
        out["actions"] = ["proceed", "cancel"]
    return out


def _done_response(thread_id: str, values: dict) -> dict:
    """완료 상태(values dict) → done 응답."""
    return {"thread_id": thread_id, "done": True,
            "extracted": values.get("extracted", []),
            "summary": values.get("report_text", "")}


def _to_response(thread_id: str, result: dict) -> dict:
    """그래프 invoke 결과 → 프론트용. interrupt 멈춤이면 stage별 payload, 완료면 최종 요약."""
    if "__interrupt__" in result:
        return _interrupt_response(thread_id, result["__interrupt__"][0].value)
    return _done_response(thread_id, result)


@router.post("/api/collect/start")
def collect_start(payload: dict = Body(...)):
    """수집 명령 → 첫 interrupt(해석 확인)까지 실행."""
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text 비어 있음")
    thread_id = uuid.uuid4().hex
    cfg = {"configurable": {"thread_id": thread_id}}
    result = _collect_graph.invoke({"query": text}, cfg)
    return _to_response(thread_id, result)


@router.post("/api/collect/resume")
def collect_resume(payload: dict = Body(...)):
    """결정(proceed|cancel|revise:<텍스트>) → 다음 interrupt 또는 완료까지 재개."""
    thread_id = payload.get("thread_id")
    decision = payload.get("decision")
    if not thread_id or not decision:
        raise HTTPException(400, "thread_id/decision 필요")
    cfg = {"configurable": {"thread_id": thread_id}}
    # 존재하지 않는 thread_id면 상태가 없어 조용히 새 실행처럼 돌 수 있음 → 명시적으로 거른다.
    if _collect_graph.get_state(cfg).created_at is None:
        raise HTTPException(404, "세션 없음(서버 재시작/만료) — 다시 시작하세요")
    try:
        result = _collect_graph.invoke(Command(resume=decision), cfg)
    except Exception as e:
        raise HTTPException(500, f"재개 실패(세션 만료 가능): {e}")
    return _to_response(thread_id, result)


@router.get("/api/collect/state")
def collect_state(thread_id: str):
    """thread_id 의 현재 체크포인트 상태 → start/resume 과 동일 스키마.

    프론트가 새로고침/재접속 시 카드를 복원하는 데 쓴다. get_state 반환은 invoke 의
    {"__interrupt__": [...]} 와 형식이 달라 어댑터로 맞춘다:
    - 멈춘 interrupt 는 snap.interrupts[*].value 에 있음 → _interrupt_response 로 감쌈.
    - interrupt 없고 next 없음 → 완료(snap.values 로 done 응답).
    - 세션 없음(created_at None) → 404.
    """
    cfg = {"configurable": {"thread_id": thread_id}}
    snap = _collect_graph.get_state(cfg)
    if snap.created_at is None:
        raise HTTPException(404, "세션 없음(서버 재시작/만료)")
    if snap.interrupts:
        return _interrupt_response(thread_id, snap.interrupts[0].value)
    if snap.next:
        # interrupt 없이 다음 노드 대기 = 실행 중간(예: 추출 도중 서버 재시작).
        # 카드로 복원할 안정 지점이 아님 → 만료로 취급(프론트가 thread 참조 정리). ⑤ 범위.
        raise HTTPException(404, "복원 가능한 멈춤 지점 아님(실행 중간)")
    return _done_response(thread_id, snap.values)
