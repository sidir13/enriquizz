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
from fastapi.middleware.cors import CORSMiddleware
from pydantic.v1 import BaseModel, Field, validator

# ── Config ────────────────────────────────────────────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(__file__), "questions.csv")
CSV_FIELDS = [
    "id",
    "question",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "reponse_correcte",
    "manche",
]

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:4173,*",
).split(",")

ROUND3_REWARDS = {"cash": 10, "carre": 6, "duo": 2}
ROUND3_PENALTIES = {"cash": -2, "carre": -6, "duo": -8}

app = FastAPI(title="EnriQuiz Party", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────
class Question(BaseModel):
    id: int
    question: str
    options: List[str]
    reponse_correcte: str
    manche: int


class QuestionCreate(BaseModel):
    question: str
    option_a: str = ""
    option_b: str = ""
    option_c: str = ""
    option_d: str = ""
    reponse_correcte: str = ""
    manche: int = Field(..., ge=1, le=4)

    @validator("question")
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La question ne peut pas être vide")
        return v.strip()


class GamePhase(str, Enum):
    LOBBY = "lobby"
    COUNTDOWN = "countdown"
    ACTIVE = "active"
    BUZZER_LOCKED = "buzzer_locked"
    REVEAL = "reveal"
    MANCHE_END = "manche_end"
    GAME_END = "game_end"


# ── CSV helpers ───────────────────────────────────────────────────────────────
def load_questions() -> List[Question]:
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=500, detail="Fichier questions.csv introuvable")

    questions: List[Question] = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            options = [
                row.get("option_a", ""),
                row.get("option_b", ""),
                row.get("option_c", ""),
                row.get("option_d", ""),
            ]
            questions.append(
                Question(
                    id=int(row["id"]),
                    question=row["question"],
                    options=[o for o in options if o],
                    reponse_correcte=row.get("reponse_correcte", ""),
                    manche=int(row.get("manche", 1)),
                )
            )
    return questions


def append_question_to_csv(data: QuestionCreate) -> Question:
    questions = load_questions()
    next_id = max((q.id for q in questions), default=0) + 1

    row = {
        "id": str(next_id),
        "question": data.question,
        "option_a": data.option_a,
        "option_b": data.option_b,
        "option_c": data.option_c,
        "option_d": data.option_d,
        "reponse_correcte": data.reponse_correcte,
        "manche": str(data.manche),
    }

    file_exists = os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    options = [o for o in [data.option_a, data.option_b, data.option_c, data.option_d] if o]
    return Question(
        id=next_id,
        question=data.question,
        options=options,
        reponse_correcte=data.reponse_correcte,
        manche=data.manche,
    )


def questions_by_manche() -> Dict[int, List[Question]]:
    grouped: Dict[int, List[Question]] = {1: [], 2: [], 3: [], 4: []}
    for q in load_questions():
        if q.manche in grouped:
            grouped[q.manche].append(q)
    return grouped


def speed_round_points(timer_total: float, time_left: float) -> int:
    """Points for round 2: faster answers score higher (20% brackets, -2 pts, min 1)."""
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
    """Round 4: points grow from 1 to 10 as time runs out."""
    if timer_total <= 0:
        return 10
    ratio = max(0.0, min(1.0, elapsed / timer_total))
    return max(1, min(10, int(1 + ratio * 9)))


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

    async def broadcast(self, manager: "ConnectionManager"):
        await manager.broadcast_room(self.room_code, {"type": "state", "payload": self.public_state()})

    def public_state(self, role: str = "all", team_id: Optional[str] = None) -> dict:
        q_data = None
        if self.current_question:
            q_data = {
                "id": self.current_question.id,
                "question": self.current_question.question,
                "manche": self.current_question.manche,
            }
            if self.current_manche in (1, 2):
                q_data["options"] = self.current_question.options
            if role == "host" or self.phase in (GamePhase.REVEAL, GamePhase.MANCHE_END, GamePhase.GAME_END):
                q_data["reponse_correcte"] = self.current_question.reponse_correcte

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
            "current_question": q_data,
            "teams": [t.to_dict() for t in teams_sorted],
            "buzzer_team": buzzer_team,
            "answers": self.answers_this_question if role == "host" else {},
            "manche_labels": {
                1: "Classique Q&R",
                2: "Partie Rapidité",
                3: "Le Big Buzzer",
                4: "Face-à-Face Final",
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
        await self.set_phase(GamePhase.ACTIVE, manager)

        if self.current_manche in (2, 4):
            await self.start_timer(manager)

    async def start_timer(self, manager: "ConnectionManager"):
        self.cancel_timer()
        self.timer_started_at = time.monotonic()
        self.timer_remaining = float(self.timer_seconds)
        self.timer_task = asyncio.create_task(self._timer_loop(manager))

    async def _timer_loop(self, manager: "ConnectionManager"):
        try:
            tick = 0
            while self.timer_remaining > 0 and self.phase == GamePhase.ACTIVE:
                await asyncio.sleep(0.1)
                elapsed = time.monotonic() - (self.timer_started_at or time.monotonic())
                self.timer_remaining = max(0.0, self.timer_seconds - elapsed)

                if self.current_manche == 4 and self.phase == GamePhase.ACTIVE:
                    self.frozen_points = final_round_points(
                        self.timer_seconds, elapsed
                    )

                tick += 1
                if tick % 5 == 0:
                    await self.broadcast(manager)

            if self.phase == GamePhase.ACTIVE and self.current_manche in (2, 4):
                await self.time_up(manager)
        except asyncio.CancelledError:
            pass

    async def time_up(self, manager: "ConnectionManager"):
        self.cancel_timer()
        if self.current_manche == 2:
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
            await self.set_phase(GamePhase.LOBBY, manager)

    async def handle_team_answer(self, team_id: str, answer: str, manager: "ConnectionManager"):
        async with self._lock:
            if self.phase != GamePhase.ACTIVE or self.current_manche not in (1, 2):
                return
            team = self.get_team(team_id)
            if not team or team.answered:
                return

            team.answered = True
            team.last_answer = answer
            correct = answer == self.current_question.reponse_correcte
            points = 0

            if self.current_manche == 1:
                points = 10 if correct else 0
            elif self.current_manche == 2:
                if correct:
                    points = speed_round_points(self.timer_seconds, self.timer_remaining)
                else:
                    points = 0

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
            if self.phase != GamePhase.ACTIVE or self.current_manche not in (3, 4):
                return
            team = self.get_team(team_id)
            if not team or team.locked_out:
                return

            if self.buzzer_team_id is not None:
                return

            self.buzzer_team_id = team_id
            self.buzzer_claim = claim if self.current_manche == 3 else None
            self.cancel_timer()

            if self.current_manche == 4:
                elapsed = time.monotonic() - (self.timer_started_at or time.monotonic())
                self.frozen_points = final_round_points(self.timer_seconds, elapsed)

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

            if self.current_manche == 3:
                claim_key = (claim or self.buzzer_claim or "duo").lower()
                if claim_key not in ROUND3_REWARDS:
                    claim_key = "duo"
                if correct:
                    pts = ROUND3_REWARDS[claim_key]
                    team.score += pts
                    team.last_points_awarded = pts
                    await self.set_phase(GamePhase.REVEAL, manager)
                else:
                    pts = ROUND3_PENALTIES[claim_key]
                    team.score += pts
                    team.last_points_awarded = pts
                    team.locked_out = True
                    self.buzzer_team_id = None
                    self.buzzer_claim = None
                    other_eligible = any(
                        not t.locked_out for tid, t in self.teams.items()
                    )
                    if other_eligible:
                        await self.set_phase(GamePhase.ACTIVE, manager)
                        if self.current_manche == 4:
                            await self.start_timer(manager)
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


manager = ConnectionManager()


# ── REST routes ───────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "EnriQuiz Party API", "version": "2.0.0"}


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
