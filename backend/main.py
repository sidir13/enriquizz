import asyncio
import csv
import json
import os
import random
import string
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic.v1 import BaseModel, Field, validator

# ── Config ────────────────────────────────────────────────────────────────────
QUESTIONS_DIR = os.path.join(os.path.dirname(__file__), "questions")
MANCHE_CSV = {
    1: "manche1.csv",
    2: "manche2.csv",
    3: "manche3.csv",
    4: "manche4.csv",
}
STANDARD_FIELDS = [
    "id", "question", "option_a", "option_b", "option_c", "option_d", "reponse_correcte",
]
FINAL_FIELDS = ["id", "question", "reponse_correcte"]
FINAL_TIMER_SECONDS = 20
PART_REVEAL_INTERVAL = 5

ROUND2_REWARDS = {"cash": 8, "carre": 4, "duo": 2}
ROUND2_PENALTIES = {"cash": -2, "carre": -6, "duo": -8}
ORAL_BUZZER_POINTS = 10

app = FastAPI(title="EnriQuiz Party", version="2.0.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


# ── Models ────────────────────────────────────────────────────────────────────
class Question(BaseModel):
    id: int
    question: str
    parts: List[str] = []
    options: List[str] = []
    reponse_correcte: str
    manche: int


class QuestionCreate(BaseModel):
    question: str = ""
    partie1: str = ""
    partie2: str = ""
    partie3: str = ""
    option_a: str = ""
    option_b: str = ""
    option_c: str = ""
    option_d: str = ""
    reponse_correcte: str = ""
    manche: int = Field(..., ge=1, le=4)


class GamePhase(str, Enum):
    LOBBY = "lobby"
    COUNTDOWN = "countdown"
    ACTIVE = "active"
    BUZZER_LOCKED = "buzzer_locked"
    REVEAL = "reveal"
    MANCHE_END = "manche_end"
    GAME_END = "game_end"


# ── CSV helpers ───────────────────────────────────────────────────────────────
def csv_path_for_manche(manche: int) -> str:
    filename = MANCHE_CSV.get(manche)
    if not filename:
        raise HTTPException(status_code=400, detail="Manche invalide")
    return os.path.join(QUESTIONS_DIR, filename)


def _parse_standard_row(row: dict, manche: int) -> Question:
    row_id_str = row.get("id", "").strip()
    if not row_id_str:
        return None
    
    try:
        row_id = int(row_id_str)
    except ValueError:
        return None
    
    question_text = row.get("question", "").strip()
    reponse = row.get("reponse_correcte", "").strip()
    
    if not question_text or not reponse:
        return None
    
    options = [
        row.get("option_a", "").strip(),
        row.get("option_b", "").strip(),
        row.get("option_c", "").strip(),
        row.get("option_d", "").strip(),
    ]
    options_filled = [o for o in options if o]
    
    if len(options_filled) < 2:
        return None
    
    return Question(
        id=row_id,
        question=question_text,
        parts=[],
        options=options_filled,
        reponse_correcte=reponse,
        manche=manche,
    )


def split_by_periods(text: str) -> List[str]:
    """Découpe une question en parties (du début ou fin de la précédente jusqu'au prochain point)."""
    text = text.strip()
    if not text:
        return []
    segments = [s.strip() for s in text.split(".") if s.strip()]
    return [f"{s}." for s in segments]


def _parse_final_row(row: dict) -> Question:
    row_id_str = row.get("id", "").strip()
    if not row_id_str:
        return None
    
    try:
        row_id = int(row_id_str)
    except ValueError:
        return None
    
    full = row.get("question", "").strip()
    reponse = row.get("reponse_correcte", "").strip()
    
    if not full or not reponse:
        return None
    
    parts = split_by_periods(full)
    return Question(
        id=row_id,
        question=parts[0] if parts else full,
        parts=parts,
        options=[],
        reponse_correcte=reponse,
        manche=4,
    )


def load_questions_for_manche(manche: int) -> List[Question]:
    path = csv_path_for_manche(manche)
    if not os.path.exists(path):
        return []

    questions: List[Question] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                if manche == 4:
                    q = _parse_final_row(row)
                else:
                    q = _parse_standard_row(row, manche)
                
                if q:
                    questions.append(q)
            except Exception as e:
                print(f"WARNING: erreur lors du parsing de la ligne: {row}, error: {e}")
                continue
    
    return questions


def load_questions() -> List[Question]:
    all_q: List[Question] = []
    for m in MANCHE_CSV:
        all_q.extend(load_questions_for_manche(m))
    return all_q


def append_question_to_csv(data: QuestionCreate) -> Question:
    path = csv_path_for_manche(data.manche)
    existing = load_questions_for_manche(data.manche)
    next_id = max((q.id for q in existing), default=0) + 1

    os.makedirs(QUESTIONS_DIR, exist_ok=True)

    if data.manche == 4:
        full = data.question.strip() or data.partie1.strip()
        if not full:
            raise HTTPException(status_code=400, detail="Question requise pour la manche 4")
        row = {
            "id": str(next_id),
            "question": full,
            "reponse_correcte": data.reponse_correcte,
        }
        fields = FINAL_FIELDS
        parts = split_by_periods(full)
        question = Question(
            id=next_id,
            question=parts[0] if parts else full,
            parts=parts,
            options=[],
            reponse_correcte=data.reponse_correcte,
            manche=4,
        )
    else:
        if not data.question.strip():
            raise HTTPException(status_code=400, detail="Question requise")
        row = {
            "id": str(next_id),
            "question": data.question.strip(),
            "option_a": data.option_a,
            "option_b": data.option_b,
            "option_c": data.option_c,
            "option_d": data.option_d,
            "reponse_correcte": data.reponse_correcte,
        }
        fields = STANDARD_FIELDS
        options = [o for o in [data.option_a, data.option_b, data.option_c, data.option_d] if o]
        question = Question(
            id=next_id,
            question=data.question.strip(),
            parts=[],
            options=options,
            reponse_correcte=data.reponse_correcte,
            manche=data.manche,
        )

    file_exists = os.path.exists(path) and os.path.getsize(path) > 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return question


def questions_by_manche() -> Dict[int, List[Question]]:
    return {m: load_questions_for_manche(m) for m in MANCHE_CSV}


def speed_round_points(timer_total: float, time_left: float) -> int:
    """Points for round 1 (speed): faster answers score higher."""
    if timer_total <= 0:
        return 1
    ratio_left = max(0.0, min(1.0, time_left / timer_total))
    if ratio_left >= 0.8:
        return 10
    if ratio_left >= 0.6:
        return 8
    if ratio_left >= 0.4:
        return 6
    if ratio_left >= 0.2:
        return 4
    if ratio_left > 0:
        return 2
    return 1


def final_round_points(timer_total: float, elapsed: float) -> int:
    """Round 4: points start at 10 and decrease to 1 as time runs out."""
    if timer_total <= 0:
        return 1
    ratio = max(0.0, min(1.0, elapsed / timer_total))
    return max(1, min(10, int(10 - ratio * 9)))


def generate_room_code(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


# ── Game room ─────────────────────────────────────────────────────────────────
class Team:
    def __init__(self, team_id: str, name: str):
        self.team_id = team_id
        self.name = name
        self.score = 0
        self.ws: Optional[WebSocket] = None
        self.locked_out = False
        self.answered = False
        self.last_answer: Optional[str] = None
        self.last_points_awarded = 0

    def to_dict(self) -> dict:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "score": self.score,
            "locked_out": self.locked_out,
            "answered": self.answered,
            "last_points_awarded": self.last_points_awarded,
        }


class GameRoom:
    def __init__(self, room_code: str):
        self.room_code = room_code
        self.host_ws: Optional[WebSocket] = None
        self.teams: Dict[str, Team] = {}
        self.phase = GamePhase.LOBBY
        self.current_manche = 1
        self.question_index = 0
        self.timer_seconds = 10
        self.countdown_seconds = 3
        self.questions = questions_by_manche()
        self.current_question: Optional[Question] = None
        self.timer_task: Optional[asyncio.Task] = None
        self.timer_started_at: Optional[float] = None
        self.timer_remaining: float = 0.0
        self.frozen_points: Optional[int] = None
        self.buzzer_team_id: Optional[str] = None
        self.buzzer_claim: Optional[str] = None
        self.answers_this_question: Dict[str, dict] = {}
        self.show_correction: bool = False
        self.part_reveal_interval: float = PART_REVEAL_INTERVAL
        self.revealed_parts_count: int = 0
        self.frozen_revealed_parts: Optional[int] = None
        self._lock = asyncio.Lock()

    @property
    def manche_questions(self) -> List[Question]:
        return self.questions.get(self.current_manche, [])

    def get_team(self, team_id: str) -> Optional[Team]:
        return self.teams.get(team_id)

    def reset_question_state(self):
        self.buzzer_team_id = None
        self.buzzer_claim = None
        self.frozen_points = None
        self.show_correction = False
        self.revealed_parts_count = 0
        self.frozen_revealed_parts = None
        self.timer_started_at = None
        self.timer_remaining = float(self.timer_seconds)
        self.answers_this_question = {}
        for team in self.teams.values():
            team.locked_out = False
            team.answered = False
            team.last_answer = None
            team.last_points_awarded = 0

    def cancel_timer(self):
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        self.timer_task = None

    def _visible_parts_count(self) -> int:
        q = self.current_question
        if not q or not q.parts:
            return 0
        if self.current_manche != 4:
            return len(q.parts)
        if self.phase in (GamePhase.BUZZER_LOCKED, GamePhase.REVEAL):
            return self.frozen_revealed_parts or self.revealed_parts_count or 1
        if self.phase == GamePhase.ACTIVE:
            return max(1, self.revealed_parts_count)
        return len(q.parts)

    async def broadcast(self, manager: "ConnectionManager"):
        await manager.broadcast_room(self.room_code, {"type": "state", "payload": self.public_state()})

    def public_state(self, role: str = "all", team_id: Optional[str] = None) -> dict:
        q_data = None
        if self.current_question:
            q = self.current_question
            q_data = {
                "id": q.id,
                "question": q.question,
                "manche": q.manche,
            }
            if q.parts:
                visible_count = self._visible_parts_count()
                q_data["parts"] = q.parts[:visible_count]
                q_data["total_parts"] = len(q.parts)
                q_data["revealed_parts_count"] = visible_count
            if self.current_manche == 1 and role == "team":
                q_data["options"] = q.options
            elif role == "host" and self.current_manche in (1, 2, 3):
                q_data["options"] = q.options
            if role == "host" and self.show_correction:
                q_data["reponse_correcte"] = q.reponse_correcte

        buzzer_team = None
        if self.buzzer_team_id and self.buzzer_team_id in self.teams:
            t = self.teams[self.buzzer_team_id]
            buzzer_team = {"team_id": t.team_id, "name": t.name, "claim": self.buzzer_claim}

        teams_sorted = sorted(self.teams.values(), key=lambda t: -t.score)

        state = {
            "room_code": self.room_code,
            "phase": self.phase.value,
            "current_manche": self.current_manche,
            "question_index": self.question_index,
            "question_total": len(self.manche_questions),
            "timer_seconds": self.timer_seconds,
            "countdown_seconds": self.countdown_seconds,
            "timer_remaining": round(self.timer_remaining, 2),
            "frozen_points": self.frozen_points,
            "part_reveal_interval": self.part_reveal_interval,
            "current_question": q_data,
            "teams": [t.to_dict() for t in teams_sorted],
            "buzzer_team": buzzer_team,
            "answers": self.answers_this_question if role == "host" else {},
            "show_correction": self.show_correction if role == "host" else False,
            "manche_labels": {
                1: "Rapide et vif",
                2: "Duo / Carré / Cash",
                3: "Buzzer oral",
                4: "Question pour un champion",
            },
        }

        if team_id and team_id in self.teams:
            me = self.teams[team_id]
            state["my_team"] = {
                "team_id": me.team_id,
                "name": me.name,
                "score": me.score,
                "locked_out": me.locked_out,
                "answered": me.answered,
                "last_points_awarded": me.last_points_awarded,
            }
        return state

    async def set_phase(self, phase: GamePhase, manager: "ConnectionManager"):
        self.phase = phase
        await self.broadcast(manager)

    async def start_countdown(self, manager: "ConnectionManager"):
        self.cancel_timer()
        await self.set_phase(GamePhase.COUNTDOWN, manager)
        for remaining in range(self.countdown_seconds, 0, -1):
            self.timer_remaining = float(remaining)
            await self.broadcast(manager)
            await asyncio.sleep(1)
        await self.activate_question(manager)

    async def activate_question(self, manager: "ConnectionManager"):
        questions = self.manche_questions
        if self.question_index >= len(questions):
            await self.end_manche(manager)
            return

        self.current_question = questions[self.question_index]
        self.reset_question_state()
        if self.current_manche == 4:
            self.timer_seconds = FINAL_TIMER_SECONDS
            self.part_reveal_interval = PART_REVEAL_INTERVAL
        await self.set_phase(GamePhase.ACTIVE, manager)

        if self.current_manche in (1, 4):
            await self.start_timer(manager)

    async def start_timer(self, manager: "ConnectionManager"):
        self.cancel_timer()
        self.timer_started_at = time.monotonic()
        self.timer_remaining = float(self.timer_seconds)
        if self.current_manche == 4:
            self.revealed_parts_count = 1 if self.current_question and self.current_question.parts else 0
            self.frozen_revealed_parts = None
        self.timer_task = asyncio.create_task(self._timer_loop(manager))

    async def _timer_loop(self, manager: "ConnectionManager"):
        try:
            last_revealed = self.revealed_parts_count
            tick = 0
            while self.timer_remaining > 0 and self.phase == GamePhase.ACTIVE:
                await asyncio.sleep(0.1)
                elapsed = time.monotonic() - (self.timer_started_at or time.monotonic())
                self.timer_remaining = max(0.0, self.timer_seconds - elapsed)

                if self.current_manche == 4 and self.phase == GamePhase.ACTIVE:
                    self.frozen_points = final_round_points(self.timer_seconds, elapsed)
                    if self.current_question and self.current_question.parts:
                        n = len(self.current_question.parts)
                        self.revealed_parts_count = min(
                            n, 1 + int(elapsed // self.part_reveal_interval)
                        )

                tick += 1
                part_changed = (
                    self.current_manche == 4
                    and self.revealed_parts_count != last_revealed
                )
                if part_changed:
                    last_revealed = self.revealed_parts_count
                if part_changed or tick % 5 == 0:
                    await self.broadcast(manager)

            if self.phase == GamePhase.ACTIVE and self.current_manche in (1, 4):
                await self.time_up(manager)
        except asyncio.CancelledError:
            pass

    async def time_up(self, manager: "ConnectionManager"):
        self.cancel_timer()
        if self.current_manche == 1:
            await self.set_phase(GamePhase.REVEAL, manager)
        elif self.current_manche == 4:
            await self.set_phase(GamePhase.REVEAL, manager)

    async def end_manche(self, manager: "ConnectionManager"):
        self.cancel_timer()
        self.current_question = None
        if self.current_manche >= 4:
            await self.set_phase(GamePhase.GAME_END, manager)
        else:
            await self.set_phase(GamePhase.MANCHE_END, manager)

    async def next_manche(self, manager: "ConnectionManager"):
        if self.current_manche < 4:
            self.current_manche += 1
            self.question_index = 0
            self.questions = questions_by_manche()
            if self.current_manche == 4 and self.timer_seconds != FINAL_TIMER_SECONDS:
                self.timer_seconds = FINAL_TIMER_SECONDS
                self.part_reveal_interval = PART_REVEAL_INTERVAL
            await self.set_phase(GamePhase.LOBBY, manager)

    async def handle_team_answer(self, team_id: str, answer: str, manager: "ConnectionManager"):
        async with self._lock:
            if self.phase != GamePhase.ACTIVE or self.current_manche != 1:
                return
            team = self.get_team(team_id)
            if not team or team.answered:
                return

            team.answered = True
            team.last_answer = answer
            correct = answer == self.current_question.reponse_correcte
            points = 0

            if correct:
                points = speed_round_points(self.timer_seconds, self.timer_remaining)

            if correct:
                team.score += points
            team.last_points_awarded = points

            self.answers_this_question[team_id] = {
                "team_id": team_id,
                "name": team.name,
                "answer": answer,
                "correct": correct,
                "points": points,
            }
            await self.broadcast(manager)

    async def handle_buzz(self, team_id: str, claim: Optional[str], manager: "ConnectionManager"):
        async with self._lock:
            if self.phase != GamePhase.ACTIVE or self.current_manche not in (2, 3, 4):
                return
            team = self.get_team(team_id)
            if not team or team.locked_out:
                return

            if self.buzzer_team_id is not None:
                return

            self.buzzer_team_id = team_id
            self.buzzer_claim = claim if self.current_manche == 2 else None
            self.cancel_timer()

            if self.current_manche == 4:
                elapsed = time.monotonic() - (self.timer_started_at or time.monotonic())
                self.frozen_points = final_round_points(self.timer_seconds, elapsed)
                self.frozen_revealed_parts = self.revealed_parts_count or 1

            await self.set_phase(GamePhase.BUZZER_LOCKED, manager)

    async def validate_buzz(
        self,
        correct: bool,
        claim: Optional[str],
        manager: "ConnectionManager",
    ):
        async with self._lock:
            if self.phase != GamePhase.BUZZER_LOCKED or not self.buzzer_team_id:
                return

            team = self.teams[self.buzzer_team_id]

            if self.current_manche == 2:
                claim_key = (claim or self.buzzer_claim or "duo").lower()
                if claim_key not in ROUND2_REWARDS:
                    claim_key = "duo"
                if correct:
                    pts = ROUND2_REWARDS[claim_key]
                    team.score += pts
                    team.last_points_awarded = pts
                    await self.set_phase(GamePhase.REVEAL, manager)
                else:
                    pts = ROUND2_PENALTIES[claim_key]
                    team.score += pts
                    team.last_points_awarded = pts
                    team.locked_out = True
                    self.buzzer_team_id = None
                    self.buzzer_claim = None
                    other_eligible = any(
                        not t.locked_out for t in self.teams.values()
                    )
                    if other_eligible:
                        await self.set_phase(GamePhase.ACTIVE, manager)
                    else:
                        await self.set_phase(GamePhase.REVEAL, manager)

            elif self.current_manche == 3:
                if correct:
                    team.score += ORAL_BUZZER_POINTS
                    team.last_points_awarded = ORAL_BUZZER_POINTS
                    await self.set_phase(GamePhase.REVEAL, manager)
                else:
                    team.last_points_awarded = 0
                    team.locked_out = True
                    self.buzzer_team_id = None
                    other_eligible = any(not t.locked_out for t in self.teams.values())
                    if other_eligible:
                        await self.set_phase(GamePhase.ACTIVE, manager)
                    else:
                        await self.set_phase(GamePhase.REVEAL, manager)

            elif self.current_manche == 4:
                pts = self.frozen_points or 1
                if correct:
                    team.score += pts
                    team.last_points_awarded = pts
                    await self.set_phase(GamePhase.REVEAL, manager)
                else:
                    team.last_points_awarded = 0
                    team.locked_out = True
                    self.buzzer_team_id = None
                    self.frozen_points = None
                    other_eligible = any(not t.locked_out for t in self.teams.values())
                    if other_eligible:
                        await self.set_phase(GamePhase.ACTIVE, manager)
                        await self.start_timer(manager)
                    else:
                        await self.set_phase(GamePhase.REVEAL, manager)

            await self.broadcast(manager)

    async def skip_question(self, manager: "ConnectionManager"):
        self.cancel_timer()
        self.question_index += 1
        if self.question_index >= len(self.manche_questions):
            await self.end_manche(manager)
        else:
            await self.start_countdown(manager)

    async def next_question(self, manager: "ConnectionManager"):
        self.question_index += 1
        if self.question_index >= len(self.manche_questions):
            await self.end_manche(manager)
        else:
            await self.start_countdown(manager)

    async def adjust_points(self, team_id: str, delta: int, manager: "ConnectionManager"):
        team = self.get_team(team_id)
        if team:
            team.score += delta
            await self.broadcast(manager)


# ── Connection manager ────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.ws_meta: Dict[WebSocket, dict] = {}

    def create_room(self) -> GameRoom:
        for _ in range(20):
            code = generate_room_code()
            if code not in self.rooms:
                room = GameRoom(code)
                self.rooms[code] = room
                return room
        raise RuntimeError("Impossible de générer un code de salle")

    def get_room(self, code: str) -> Optional[GameRoom]:
        return self.rooms.get(code.upper())

    async def connect(self, ws: WebSocket):
        await ws.accept()
        await ws.send_json({"type": "connected"})

    def register_host(self, ws: WebSocket, room: GameRoom):
        room.host_ws = ws
        self.ws_meta[ws] = {"role": "host", "room_code": room.room_code}

    def register_team(self, ws: WebSocket, room: GameRoom, team: Team):
        team.ws = ws
        self.ws_meta[ws] = {
            "role": "team",
            "room_code": room.room_code,
            "team_id": team.team_id,
        }

    async def disconnect(self, ws: WebSocket):
        meta = self.ws_meta.pop(ws, None)
        if not meta:
            return
        room = self.rooms.get(meta["room_code"])
        if not room:
            return
        if meta["role"] == "host" and room.host_ws == ws:
            room.host_ws = None
        elif meta["role"] == "team":
            team = room.get_team(meta.get("team_id", ""))
            if team and team.ws == ws:
                team.ws = None

    async def send(self, ws: WebSocket, message: dict):
        try:
            await ws.send_json(message)
        except Exception:
            pass

    async def broadcast_room(self, room_code: str, message: dict):
        room = self.rooms.get(room_code)
        if not room:
            return
        recipients: Set[WebSocket] = set()
        if room.host_ws:
            recipients.add(room.host_ws)
        for team in room.teams.values():
            if team.ws:
                recipients.add(team.ws)

        for ws in recipients:
            meta = self.ws_meta.get(ws, {})
            if message.get("type") == "state":
                payload = room.public_state(
                    role=meta.get("role", "team"),
                    team_id=meta.get("team_id"),
                )
                await self.send(ws, {"type": "state", "payload": payload})
            else:
                await self.send(ws, message)

    async def handle_message(self, ws: WebSocket, raw: dict):
        msg_type = raw.get("type")
        meta = self.ws_meta.get(ws)

        if msg_type == "host_create":
            room = self.create_room()
            self.register_host(ws, room)
            await self.send(ws, {"type": "room_created", "room_code": room.room_code})
            await room.broadcast(self)
            return

        if msg_type == "host_rejoin":
            code = raw.get("room_code", "").upper().strip()
            room = self.get_room(code)
            if not room:
                await self.send(ws, {"type": "error", "message": "Salle introuvable"})
                return
            self.register_host(ws, room)
            await self.send(ws, {"type": "room_created", "room_code": room.room_code})
            await room.broadcast(self)
            return

        if msg_type == "team_join":
            code = raw.get("room_code", "").upper().strip()
            name = raw.get("team_name", "").strip()
            if not code or not name:
                await self.send(ws, {"type": "error", "message": "Code ou nom d'équipe manquant"})
                return
            room = self.get_room(code)
            if not room:
                await self.send(ws, {"type": "error", "message": "Salle introuvable"})
                return
            team_id = f"team_{len(room.teams) + 1}_{code}"
            team = Team(team_id, name)
            room.teams[team_id] = team
            self.register_team(ws, room, team)
            await self.send(ws, {"type": "joined", "team_id": team_id})
            await room.broadcast(self)
            return

        if msg_type == "team_rejoin":
            code = raw.get("room_code", "").upper().strip()
            team_id = raw.get("team_id", "")
            room = self.get_room(code)
            if not room:
                await self.send(ws, {"type": "error", "message": "Salle introuvable"})
                return
            team = room.get_team(team_id)
            if not team:
                await self.send(ws, {"type": "error", "message": "Équipe introuvable"})
                return
            self.register_team(ws, room, team)
            await self.send(ws, {"type": "joined", "team_id": team_id})
            await room.broadcast(self)
            return

        if not meta:
            await self.send(ws, {"type": "error", "message": "Non connecté"})
            return

        room = self.rooms.get(meta["room_code"])
        if not room:
            return

        if msg_type == "host_action" and meta["role"] == "host":
            await self._handle_host_action(room, raw, ws)
        elif msg_type == "team_answer" and meta["role"] == "team":
            await room.handle_team_answer(meta["team_id"], raw.get("answer", ""), self)
        elif msg_type == "team_buzz" and meta["role"] == "team":
            await room.handle_buzz(meta["team_id"], raw.get("claim"), self)
        elif msg_type == "ping":
            await self.send(ws, {"type": "pong"})

    async def _handle_host_action(self, room: GameRoom, raw: dict, ws: WebSocket):
        action = raw.get("action")

        if action == "set_config":
            if "timer_seconds" in raw:
                room.timer_seconds = max(5, min(60, int(raw["timer_seconds"])))
            if "countdown_seconds" in raw:
                room.countdown_seconds = max(1, min(10, int(raw["countdown_seconds"])))
            await room.broadcast(self)

        elif action == "start_game":
            room.current_manche = 1
            room.question_index = 0
            room.questions = questions_by_manche()
            await room.start_countdown(self)

        elif action == "start_countdown":
            await room.start_countdown(self)

        elif action == "next_question":
            await room.next_question(self)

        elif action == "skip_question":
            await room.skip_question(self)

        elif action == "next_manche":
            await room.next_manche(self)

        elif action == "validate_buzz":
            await room.validate_buzz(
                bool(raw.get("correct")),
                raw.get("claim"),
                self,
            )

        elif action == "adjust_points":
            team_id = raw.get("team_id")
            delta = int(raw.get("delta", 0))
            if team_id:
                await room.adjust_points(team_id, delta, self)

        elif action == "reload_questions":
            room.questions = questions_by_manche()
            await room.broadcast(self)

        elif action == "show_correction":
            room.show_correction = True
            await room.broadcast(self)


manager = ConnectionManager()


# ── REST routes ───────────────────────────────────────────────────────────────
@app.get("/api/questions", response_model=List[Question])
def get_questions():
    return load_questions()


@app.post("/api/questions", response_model=Question)
def create_question(data: QuestionCreate):
    return append_question_to_csv(data)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send(ws, {"type": "error", "message": "JSON invalide"})
                continue
            await manager.handle_message(ws, message)
    except WebSocketDisconnect:
        await manager.disconnect(ws)
    except Exception:
        await manager.disconnect(ws)


# ── Static frontend (monolithe) — MUST be registered after API / WS routes ─────
if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{catchall:path}")
    async def serve_spa(catchall: str = ""):
        if catchall.startswith("api") or catchall == "ws":
            raise HTTPException(status_code=404, detail="Not found")
        index_path = os.path.join(STATIC_DIR, "index.html")
        if not os.path.isfile(index_path):
            raise HTTPException(status_code=404, detail="Frontend not built. Run: cd frontend && npm run build")
        return FileResponse(index_path)
