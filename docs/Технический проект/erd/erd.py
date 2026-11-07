"""ER-диаграммы базы данных R3DVIS (нотация «вороньей лапки»).

Состав сущностей и атрибутов соответствует моделям SQLAlchemy
серверной части (backend/app/*/models.py) и миграциям Alembic.

Запуск:  python3 erd.py  →  erd_*.dot, *.svg, *.png (нужен Graphviz).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).parent

# имя таблицы: (русское название, [(поле, тип, ключ)])  ключ: PK, FK, PK,FK, U
E: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "users": ("Учётная запись", [
        ("id", "UUID", "PK"), ("username", "VARCHAR(64)", "U"), ("password_hash", "VARCHAR(255)", ""),
        ("telegram_id", "BIGINT", "U"), ("is_active", "BOOLEAN", ""), ("is_admin", "BOOLEAN", ""),
        ("display_name", "VARCHAR(128)", ""), ("avatar_url", "VARCHAR(512)", ""),
        ("bind_token", "VARCHAR(64)", "U"), ("preferred_group_id", "UUID", "FK"),
        ("token_version", "INTEGER", ""), ("created_at", "TIMESTAMPTZ", "")]),
    "user_features": ("Выданная возможность", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("feature", "VARCHAR(32)", ""),
        ("enabled", "BOOLEAN", ""), ("until", "TIMESTAMPTZ", ""), ("granted_by", "UUID", "FK"),
        ("note", "TEXT", ""), ("created_at", "TIMESTAMPTZ", ""), ("updated_at", "TIMESTAMPTZ", "")]),
    "app_settings": ("Настройка", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("key", "VARCHAR(64)", ""),
        ("value", "JSONB", ""), ("updated_at", "TIMESTAMPTZ", "")]),
    "schedule_groups": ("Учебная группа", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("name", "VARCHAR(200)", ""),
        ("file_hash", "VARCHAR(64)", ""), ("parsed_at", "TIMESTAMPTZ", "")]),
    "schedule_lessons": ("Занятие", [
        ("id", "UUID", "PK"), ("group_id", "UUID", "FK"), ("day_label", "VARCHAR(100)", ""),
        ("time_slot", "VARCHAR(30)", ""), ("discipline", "VARCHAR(300)", ""),
        ("lesson_type", "VARCHAR(120)", ""), ("teacher", "VARCHAR(200)", ""),
        ("room", "VARCHAR(120)", ""), ("slot_order", "INTEGER", "")]),
    "subject_tasks": ("Домашнее задание", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("discipline", "VARCHAR(255)", ""),
        ("title", "VARCHAR(255)", ""), ("completed", "BOOLEAN", ""), ("due_date", "DATE", ""),
        ("priority", "VARCHAR(16)", ""), ("created_at", "TIMESTAMPTZ", ""), ("completed_at", "TIMESTAMPTZ", "")]),
    "projects": ("Проект", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("name", "VARCHAR(120)", ""),
        ("description", "TEXT", ""), ("sphere", "VARCHAR(30)", ""), ("color", "VARCHAR(10)", ""),
        ("created_at", "TIMESTAMPTZ", "")]),
    "tasks": ("Задача", [
        ("id", "UUID", "PK"), ("project_id", "UUID", "FK"), ("user_id", "UUID", "FK"),
        ("title", "VARCHAR(255)", ""), ("description", "TEXT", ""), ("status", "VARCHAR(20)", ""),
        ("priority", "VARCHAR(20)", ""), ("deadline", "TIMESTAMPTZ", ""),
        ("created_at", "TIMESTAMPTZ", ""), ("updated_at", "TIMESTAMPTZ", "")]),
    "subtasks": ("Подзадача", [
        ("id", "UUID", "PK"), ("task_id", "UUID", "FK"), ("title", "VARCHAR(255)", ""),
        ("done", "BOOLEAN", ""), ("order", "INTEGER", "")]),
    "task_tags": ("Метка задачи", [
        ("id", "UUID", "PK"), ("task_id", "UUID", "FK"), ("tag", "VARCHAR(50)", "")]),
    "planner_events": ("Дело планера", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("title", "VARCHAR(256)", ""),
        ("event_type", "VARCHAR(32)", ""), ("event_date", "DATE", ""), ("start_time", "TIME", ""),
        ("end_time", "TIME", ""), ("note", "VARCHAR(1024)", ""), ("reminder_minutes", "INTEGER", ""),
        ("done", "BOOLEAN", ""), ("reminder_sent", "BOOLEAN", ""), ("cal_uid", "VARCHAR(255)", ""),
        ("cal_dirty", "BOOLEAN", ""), ("created_at", "TIMESTAMPTZ", "")]),
    "reminders": ("Напоминание", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("text", "TEXT", ""),
        ("remind_at", "TIMESTAMPTZ", ""), ("repeat_rule", "VARCHAR(64)", ""),
        ("repeat_anchor", "TIMESTAMPTZ", ""), ("source", "VARCHAR(32)", ""), ("sent", "BOOLEAN", ""),
        ("created_at", "TIMESTAMPTZ", "")]),
    "workouts": ("Тренировка", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("type", "VARCHAR(16)", ""),
        ("started_at", "TIMESTAMPTZ", ""), ("ended_at", "TIMESTAMPTZ", ""), ("note", "TEXT", ""),
        ("distance_km", "NUMERIC(5,2)", ""), ("created_at", "TIMESTAMPTZ", "")]),
    "workout_exercises": ("Упражнение", [
        ("id", "UUID", "PK"), ("workout_id", "UUID", "FK"), ("name", "VARCHAR(128)", ""),
        ("sets", "JSON", "")]),
    "car_refuels": ("Заправка", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("refuel_date", "DATE", ""),
        ("liters", "NUMERIC(6,2)", ""), ("price_per_liter", "NUMERIC(7,2)", ""),
        ("total_cost", "NUMERIC(10,2)", ""), ("odometer_km", "NUMERIC(9,1)", ""),
        ("station", "VARCHAR(100)", ""), ("fuel_type", "VARCHAR(8)", ""), ("full_tank", "BOOLEAN", ""),
        ("note", "TEXT", ""), ("created_at", "TIMESTAMPTZ", "")]),
    "car_maintenance": ("Обслуживание", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("service_date", "DATE", ""),
        ("service_type", "VARCHAR(100)", ""), ("cost", "NUMERIC(10,2)", ""),
        ("km_at_service", "NUMERIC(9,1)", ""), ("next_service_km", "NUMERIC(9,1)", ""),
        ("next_service_date", "DATE", ""), ("note", "TEXT", ""), ("created_at", "TIMESTAMPTZ", "")]),
    "car_profiles": ("Автомобиль", [
        ("user_id", "UUID", "PK,FK"), ("make", "VARCHAR(60)", ""), ("model", "VARCHAR(80)", ""),
        ("year", "INTEGER", ""), ("engine", "VARCHAR(80)", ""), ("transmission", "VARCHAR(40)", ""),
        ("notes", "TEXT", ""), ("regulation", "JSONB", ""), ("regulation_at", "TIMESTAMPTZ", ""),
        ("updated_at", "TIMESTAMPTZ", "")]),
    "weekly_reports": ("Итоги недели", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("week_start", "DATE", ""),
        ("text", "TEXT", ""), ("data", "JSONB", ""), ("created_at", "TIMESTAMPTZ", "")]),
    "habit_profiles": ("Профиль привычек", [
        ("user_id", "UUID", "PK,FK"), ("data", "JSONB", ""), ("computed_at", "TIMESTAMPTZ", "")]),
    "chat_messages": ("Реплика переписки", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("role", "VARCHAR(16)", ""),
        ("content", "TEXT", ""), ("source", "VARCHAR(16)", ""), ("created_at", "TIMESTAMPTZ", "")]),
    "nudges": ("Обращение ассистента", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("kind", "VARCHAR(48)", ""),
        ("title", "VARCHAR(255)", ""), ("body", "TEXT", ""), ("reason", "TEXT", ""),
        ("payload", "JSON", ""), ("status", "VARCHAR(16)", ""), ("result", "TEXT", ""),
        ("created_at", "TIMESTAMPTZ", ""), ("responded_at", "TIMESTAMPTZ", "")]),
    "nudge_settings": ("Настройки обращений", [
        ("user_id", "UUID", "PK,FK"), ("quiet_from", "INTEGER", ""), ("quiet_to", "INTEGER", ""),
        ("daily_budget", "INTEGER", "")]),
    "nudge_mutes": ("Отключение повода", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("kind", "VARCHAR(48)", ""),
        ("muted_until", "TIMESTAMPTZ", ""), ("created_at", "TIMESTAMPTZ", "")]),
    "claude_jobs": ("Задание исполнителю", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("status", "VARCHAR(16)", ""),
        ("prompt", "TEXT", ""), ("subject", "VARCHAR(160)", ""), ("inputs", "JSONB", ""),
        ("messages", "JSONB", ""), ("container_id", "VARCHAR(128)", ""), ("result_text", "TEXT", ""),
        ("outputs", "JSONB", ""), ("cost_usd", "NUMERIC(10,4)", ""), ("error", "TEXT", ""),
        ("created_at", "TIMESTAMPTZ", ""), ("updated_at", "TIMESTAMPTZ", "")]),
    "push_devices": ("Устройство оповещений", [
        ("id", "UUID", "PK"), ("user_id", "UUID", "FK"), ("token", "VARCHAR(1024)", "U"),
        ("platform", "VARCHAR(16)", ""), ("keys", "JSON", ""), ("muted", "JSON", ""),
        ("created_at", "TIMESTAMPTZ", ""), ("last_seen", "TIMESTAMPTZ", "")]),
}

# связи: (родитель, потомок, обязательность потомка, подпись)
# many — «ноль или много» (odot+crow), one — «ноль или один» (odot+tee)
R = [
    ("users", "user_features", "many", "получает"),
    ("users", "app_settings", "many", "переопределяет"),
    ("users", "schedule_groups", "many", "загружает"),
    ("schedule_groups", "schedule_lessons", "many", "содержит"),
    ("schedule_groups", "users", "many", "выбрана основной"),
    ("users", "subject_tasks", "many", "ведёт"),
    ("users", "projects", "many", "ведёт"),
    ("projects", "tasks", "many", "включает"),
    ("tasks", "subtasks", "many", "делится на"),
    ("tasks", "task_tags", "many", "помечена"),
    ("users", "planner_events", "many", "планирует"),
    ("users", "reminders", "many", "создаёт"),
    ("users", "workouts", "many", "записывает"),
    ("workouts", "workout_exercises", "many", "включает"),
    ("users", "car_refuels", "many", "записывает"),
    ("users", "car_maintenance", "many", "записывает"),
    ("users", "car_profiles", "one", "описывает"),
    ("users", "weekly_reports", "many", "получает"),
    ("users", "habit_profiles", "one", "имеет"),
    ("users", "chat_messages", "many", "пишет"),
    ("users", "nudges", "many", "получает"),
    ("users", "nudge_settings", "one", "настраивает"),
    ("users", "nudge_mutes", "many", "отключает"),
    ("users", "claude_jobs", "many", "ставит"),
    ("users", "push_devices", "many", "регистрирует"),
]

FONT = "Liberation Sans"


def node(name: str, full: bool) -> str:
    title, cols = E[name]
    head = (f'<TR><TD BGCOLOR="#e6e6e6" COLSPAN="3"><B>{name}</B><BR/>'
            f'<FONT POINT-SIZE="10">{title}</FONT></TD></TR>')
    if not full:
        return f'"{name}" [label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5">{head}</TABLE>>];'
    rows = []
    for i, (c, t, k) in enumerate(cols):
        key = f"<B>{k}</B>" if k else " "
        cname = f"<U>{c}</U>" if "PK" in k else c
        rows.append(f'<TR><TD ALIGN="LEFT" WIDTH="38">{key}</TD><TD ALIGN="LEFT">{cname}</TD>'
                    f'<TD ALIGN="LEFT"><FONT COLOR="#444444">{t}</FONT></TD></TR>')
    return (f'"{name}" [label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">'
            f'{head}{"".join(rows)}</TABLE>>];')


def graph(fname: str, names: list[str], full: bool, rankdir: str = "LR", extra: str = "",
          left: tuple[str, ...] = ()) -> None:
    """left — сущности, которые размещаются слева от родителя (ради компактности листа)."""
    lines = [f'digraph ERD {{ graph [rankdir={rankdir}, fontname="{FONT}", nodesep=0.35, ranksep=0.9, '
             f'splines=spline, pad=0.3{extra}];',
             f'node [shape=plain, fontname="{FONT}", fontsize=11];',
             f'edge [fontname="{FONT}", fontsize=9, dir=both, color="#333333"];']
    for n in names:
        lines.append(node(n, full))
    for a, b, card, lbl in R:
        if a in names and b in names:
            tail = "teeteenone" if not (a == "schedule_groups" and b == "users") else "teeodot"
            headarrow = "crowodot" if card == "many" else "teeodot"
            if b in left:  # ребро в обратную сторону: потомок ранжируется левее родителя
                lines.append(f'"{b}" -> "{a}" [arrowtail={headarrow}, arrowhead={tail}, label="{lbl}"];')
            else:
                lines.append(f'"{a}" -> "{b}" [arrowtail={tail}, arrowhead={headarrow}, label="{lbl}"];')
    lines.append("}")
    dot = HERE / f"{fname}.dot"
    dot.write_text("\n".join(lines), encoding="utf-8")
    for fmt in ("svg", "png"):
        args = ["dot", f"-T{fmt}", str(dot), "-o", str(dot.with_suffix("." + fmt))]
        if fmt == "png":
            args.insert(1, "-Gdpi=150")
        subprocess.run(args, check=True)
    print("saved", fname)


if __name__ == "__main__":
    graph("erd_overview", list(E), full=False, rankdir="LR",
          left=("planner_events", "reminders", "workouts", "car_refuels", "car_maintenance", "car_profiles",
                "weekly_reports", "habit_profiles", "chat_messages", "claude_jobs", "push_devices"))
    graph("erd_study", ["users", "user_features", "app_settings", "schedule_groups", "schedule_lessons",
                        "subject_tasks", "projects", "tasks", "subtasks", "task_tags"], full=True)
    graph("erd_planning", ["users", "planner_events", "reminders", "workouts", "workout_exercises",
                           "car_refuels", "car_maintenance", "car_profiles", "weekly_reports"], full=True,
          left=("planner_events", "reminders", "weekly_reports"))
    graph("erd_assistant", ["users", "chat_messages", "nudges", "nudge_settings", "nudge_mutes",
                            "habit_profiles", "claude_jobs", "push_devices"], full=True,
          left=("chat_messages", "claude_jobs", "habit_profiles"))
