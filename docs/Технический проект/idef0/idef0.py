"""Генератор диаграмм IDEF0 технического проекта R3DVIS.

Бланк и обозначения — по Р 50.1.028-2001 (рамка с шапкой и подвалом,
функциональные блоки с номером в правом нижнем углу, стрелки ICOM
с ортогональной трассировкой). Координаты задаются вручную: так проще
добиться читаемой раскладки, чем автоматической укладкой.

Запуск:  python3 idef0.py   →  *.svg и *.png рядом со скриптом
(для PNG нужен rsvg-convert).
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "'Liberation Sans', Arial, sans-serif"
AUTHOR = "Головёшкин А.Е."
PROJECT = "R3DVIS — персональный ассистент студента"
DATE = "07.11.2026"


class Diagram:
    def __init__(self, node: str, title: str, number: int, context: str,
                 w: int = 1600, h: int = 1060, head: int = 100, foot_h: int = 80):
        self.node, self.title, self.number, self.context = node, title, number, context
        self.W, self.H, self.HEAD, self.FOOT = w, h, head, h - foot_h
        self.items: list[str] = []

    # ---------- примитивы ----------
    def text(self, x, y, lines, size=13, anchor="start", weight="normal", bg=False):
        if isinstance(lines, str):
            lines = lines.split("\n")
        if bg:  # белая подложка, чтобы подпись читалась поверх линий
            w = max(len(t) for t in lines) * size * 0.55 + 6
            x0 = {"start": x - 3, "middle": x - w / 2, "end": x - w + 3}[anchor]
            hh = len(lines) * (size + 2) + 3
            self.items.append(f'<rect x="{x0:.0f}" y="{y - size:.0f}" width="{w:.0f}" height="{hh}" fill="#fff"/>')
        spans = "".join(
            f'<tspan x="{x}" dy="{0 if i == 0 else size + 2}">{escape(t)}</tspan>'
            for i, t in enumerate(lines))
        self.items.append(
            f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}" font-family="{FONT}">{spans}</text>')

    def line(self, x1, y1, x2, y2, w=1):
        self.items.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000" stroke-width="{w}"/>')

    def rect(self, x, y, w, h, fill="none", sw=1):
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#000" stroke-width="{sw}"/>')

    # ---------- элементы IDEF0 ----------
    def box(self, x, y, w, h, name, num):
        """Функциональный блок: рамка, название, номер блока."""
        self.items.append(f'<rect x="{x+3}" y="{y+3}" width="{w}" height="{h}" fill="#bdbdbd"/>')
        self.rect(x, y, w, h, fill="#fff", sw=1.6)
        lines = name.split("\n")
        y0 = y + h / 2 - (len(lines) - 1) * 8 + 2
        self.text(x + w / 2, y0, lines, size=14, anchor="middle")
        self.text(x + w - 5, y + h - 5, num, size=12, anchor="end", weight="bold")

    def arrow(self, pts, head=True, code=None):
        d = " ".join(f"{x},{y}" for x, y in pts)
        self.items.append(f'<polyline points="{d}" fill="none" stroke="#000" stroke-width="1.3"/>')
        if head:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            if x1 == x2:
                s = 1 if y2 > y1 else -1
                tri = [(x2, y2), (x2 - 4.5, y2 - 12 * s), (x2 + 4.5, y2 - 12 * s)]
            else:
                s = 1 if x2 > x1 else -1
                tri = [(x2, y2), (x2 - 12 * s, y2 - 4.5), (x2 - 12 * s, y2 + 4.5)]
            self.items.append('<polygon points="%s" fill="#000"/>' % " ".join(f"{a},{b}" for a, b in tri))
        if code:
            (x0, y0) = pts[0] if code[0] in "ICM" else pts[-1]
            if code[0] == "I":
                self.text(x0 + 4, y0 + 15, code, size=12, weight="bold")
            elif code[0] == "O":
                self.text(x0 - 4, y0 + 15, code, size=12, anchor="end", weight="bold")
            elif code[0] == "C":
                self.text(x0 - 4, y0 + 15, code, size=12, anchor="end", weight="bold")
            else:
                self.text(x0 - 4, y0 - 6, code, size=12, anchor="end", weight="bold")

    def dot(self, x, y):
        self.items.append(f'<circle cx="{x}" cy="{y}" r="3" fill="#000"/>')

    # ---------- бланк ----------
    def _frame(self):
        W, H, HEAD, FOOT = self.W, self.H, self.HEAD, self.FOOT
        L, t = self.line, self.text
        self.rect(1, 1, W - 2, H - 2, sw=1.6)
        L(0, HEAD, W, HEAD, 1.6)
        L(0, FOOT, W, FOOT, 1.6)
        c1, c2, c3, c4, c5 = (int(W * k) for k in (0.16, 0.50, 0.66, 0.79, 0.88))
        for x in (c1, c2, c3, c4, c5):
            L(x, 0, x, HEAD)
        for y in (25, 50, 75):
            L(c2, y, c4, y)
        t(6, 18, "ИСПОЛЬЗУЕТСЯ В:", size=12)
        t(c1 / 2, 58, ["Технический", "проект"], size=12, anchor="middle")
        t(c1 + 6, 18, f"АВТОР:  {AUTHOR}", size=12)
        t(c1 + 6, 42, f"ПРОЕКТ: {PROJECT}", size=12)
        t(c1 + 6, 66, f"ДАТА:      {DATE}", size=12)
        t(c1 + 6, 90, "ЗАМЕЧАНИЯ: 1 2 3 4 5 6 7 8 9 10", size=12)
        for i, s in enumerate(("РАБОЧАЯ ВЕРСИЯ", "ЭСКИЗ", "РЕКОМЕНДОВАНО", "ПУБЛИКАЦИЯ")):
            t(c2 + 6, 18 + 25 * i, s, size=12)
        self.rect(c2 + 150, 7, 12, 12, fill="#000")
        t(c3 + 6, 18, "ЧИТАТЕЛЬ", size=12)
        t(c4 - 6, 18, "ДАТА", size=12, anchor="end")
        t(c5 + 6, 18, "КОНТЕКСТ:", size=12)
        self._context(c5)
        L(int(W * 0.18), FOOT, int(W * 0.18), H)
        L(int(W * 0.82), FOOT, int(W * 0.82), H)
        t(8, FOOT + 22, "УЗЕЛ:", size=12)
        t(int(W * 0.09), FOOT + 55, self.node, size=18, anchor="middle", weight="bold")
        t(int(W * 0.18) + 8, FOOT + 22, "НАЗВАНИЕ:", size=12)
        t(W / 2, FOOT + 55, self.title, size=18, anchor="middle", weight="bold")
        t(int(W * 0.82) + 8, FOOT + 22, "НОМЕР:", size=12)
        t(int(W * 0.91), FOOT + 55, f"{self.number}", size=18, anchor="middle", weight="bold")

    def _context(self, c5):
        x0, w = c5 + 10, self.W - c5 - 20
        c = self.context
        if c == "top":
            self.text(x0 + w / 2, 66, "ВЕРХ", size=15, anchor="middle", weight="bold")
        elif c.startswith("child:"):  # родитель — диаграмма декомпозиции с n блоками
            n, k = map(int, c.split(":")[1].split("/"))
            step = w // (n + 1)
            for i in range(n):
                self.rect(x0 + i * step, 34 + i * 9, step - 6, 10, fill="#000" if i + 1 == k else "none")
        else:  # декомпозиция контекстного блока
            self.rect(x0 + w / 2 - 25, 45, 50, 20, fill="#000")
            self.text(x0 + w / 2, 88, "A-0", size=12, anchor="middle")

    def save(self, name: str):
        self._frame()
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{self.H}" '
               f'viewBox="0 0 {self.W} {self.H}"><rect width="{self.W}" height="{self.H}" fill="#fff"/>'
               + "".join(self.items) + "</svg>")
        out = Path(__file__).with_name(name)
        out.with_suffix(".svg").write_text(svg, encoding="utf-8")
        subprocess.run(["rsvg-convert", "-z", "1.6", "-o", str(out.with_suffix(".png")),
                        str(out.with_suffix(".svg"))], check=True)
        print("saved", out.with_suffix(".png").name)


# =====================================================================
#  A-0. Контекстная диаграмма
# =====================================================================
def context_diagram():
    d = Diagram("A-0", "Вести учебные и личные дела студента", 1, "top", w=1500, h=1000)
    bx, by, bw, bh = 520, 380, 440, 250
    d.box(bx, by, bw, bh, "Вести учебные и личные\nдела студента", "A0")

    ins = ["Файл расписания, опубликованный\nколледжем в сообществе VK (xlsx)",
           "Вопросы, фразы и данные,\nвводимые пользователем",
           "События внешнего календаря\n(Яндекс Календарь)",
           "Учебные материалы и файлы\nк заданиям исполнителю"]
    for i, lbl in enumerate(ins, 1):
        y = by + 55 * i - 15
        d.arrow([(0, y), (bx, y)], code=f"I{i}")
        d.text(30, y - 24, lbl)

    ctl = ["Техническое\nзадание,\nтребования\nFR, NFR, CON",
           "Настройки\nвладельца:\nтихие часы,\nлимиты,\nпромты,\nправила плана",
           "Формат файла\nрасписания\nколледжа",
           "Запрет\nпередачи\nданных\nтретьих лиц;\nмосковское\nвремя"]
    for i, lbl in enumerate(ctl, 1):
        x = bx + 60 + 105 * (i - 1)
        d.arrow([(x, d.HEAD), (x, by)], code=f"C{i}")
        d.text(x + 6, 150, lbl)

    mech = ["Владелец\nв роли\nпользователя\nи оператора",
            "Серверная\nчасть и БД:\nFastAPI,\nPostgreSQL,\nRedis, Celery",
            "Бот aiogram\nи языковая\nмодель\n(GPTunnel)",
            "Внешние\nсервисы: VK,\nCalDAV,\nTelegram,\nClaude Code"]
    for i, lbl in enumerate(mech, 1):
        x = bx + 50 + 110 * (i - 1)
        d.arrow([(x, d.FOOT), (x, by + bh)], code=f"M{i}")
        d.text(x + 6, by + bh + 40, lbl)

    outs = ["Сводка дня, расписание,\nсвободные окна и план недели",
            "Уведомления и сводки\n(Telegram, push-оповещения)",
            "События, выгруженные\nво внешний календарь",
            "Ответы ассистента\nи результаты заданий"]
    for i, lbl in enumerate(outs, 1):
        y = by + 55 * i - 10
        d.arrow([(bx + bw, y), (d.W, y)], code=f"O{i}")
        d.text(bx + bw + 30, y - 24, lbl)

    d.text(30, 830, "Цель моделирования: определить состав функций системы R3DVIS")
    d.text(30, 848, "и потоки данных между ней и внешней средой.")
    d.text(30, 875, "Точка зрения: владелец системы (студент).")
    d.save("A-0_context")


# =====================================================================
#  A0. Декомпозиция контекстного блока
# =====================================================================
def decomposition_a0():
    d = Diagram("A0", "Вести учебные и личные дела студента", 2, "a0", w=1700, h=1080)
    W = d.W
    B = {1: (110, 160), 2: (360, 275), 3: (610, 390), 4: (860, 505), 5: (1110, 620), 6: (1360, 735)}
    BW, BH = 180, 80
    names = {1: "Актуализировать\nучебное\nрасписание", 2: "Вести учебные\nи личные\nзаписи",
             3: "Планировать\nдень и неделю", 4: "Обработать\nобращение\nк ассистенту",
             5: "Оповещать\nпользователя", 6: "Синхронизировать\nс внешним\nкалендарём"}
    for k, (x, y) in B.items():
        d.box(x, y, BW, BH, names[k], f"A{k}")

    def top(k): return B[k][1]
    def bot(k): return B[k][1] + BH
    def left(k): return B[k][0]
    def right(k): return B[k][0] + BW

    # ---- управление ----
    # C1 ТЗ → все блоки (шина y=118)
    d.arrow([(140, d.HEAD), (140, top(1))], code="C1")
    for k in (2, 3, 4, 5, 6):
        x = left(k) + 25
        d.arrow([(140, 125), (x, 125), (x, top(k))])
    d.dot(140, 125)
    d.text(146, 156, "ТЗ, требования", size=12)
    # C2 Настройки владельца → A3, A4, A5 (шина y=140)
    d.arrow([(340, d.HEAD), (340, 145), (left(3) + 60, 145), (left(3) + 60, top(3))], code="C2")
    for k in (4, 5):
        x = left(k) + 60
        d.arrow([(left(3) + 60, 145), (x, 145), (x, top(k))])
    d.dot(left(3) + 60, 145)
    d.text(346, 141, "Настройки владельца", size=12)
    # C3 Формат файла → A1
    d.arrow([(265, d.HEAD), (265, top(1))], code="C3")
    d.text(271, 157, "Формат файла", size=12, bg=True)
    # C4 Запрет передачи данных третьих лиц → A4
    d.arrow([(right(4) - 30, d.HEAD), (right(4) - 30, top(4))], code="C4")
    d.text(right(4) - 24, 372, "Запрет передачи\nданных третьих лиц", size=12, bg=True)

    # ---- входы ----
    d.arrow([(0, 190), (left(1), 190)], code="I1")
    d.text(18, 185, "Файл расписания", size=12)
    # I2 → A2 и A4
    d.arrow([(0, 300), (left(2), 300)], code="I2")
    d.text(70, 295, "Вопросы, фразы, данные", size=12)
    d.arrow([(50, 300), (50, 540), (left(4), 540)])
    d.dot(50, 300)
    d.text(400, 535, "Вопросы и фразы", size=12)
    # I4 → A4
    d.arrow([(0, 565), (left(4), 565)], code="I4")
    d.text(400, 560, "Материалы и файлы к заданиям", size=12)
    # I3 → A6
    d.arrow([(0, 795), (left(6), 795)], code="I3")
    d.text(400, 790, "События внешнего календаря", size=12)

    # ---- интерконнекты ----
    # A1 → A3, A6: занятия группы
    d.arrow([(right(1), 180), (580, 180), (580, 410), (left(3), 410)])
    d.arrow([(580, 180), (1310, 180), (1310, 755), (left(6), 755)])
    d.dot(580, 180)
    d.text(300, 176, "Занятия группы", size=12)
    # A1 → A5: изменения расписания
    d.arrow([(right(1), 220), (1085, 220), (1085, 640), (left(5), 640)])
    d.text(300, 216, "Изменения расписания", size=12, bg=True)
    # A2 → A3: записи пользователя
    d.arrow([(right(2), 295), (595, 295), (595, 440), (left(3), 440)])
    # A2 → A5: напоминания и сроки
    d.arrow([(right(2), 320), (1070, 320), (1070, 662), (left(5), 662)])
    # A2 → A6: дела планера
    d.arrow([(right(2), 340), (1330, 340), (1330, 775), (left(6), 775)])
    d.text(600, 291, "Задания, дела, напоминания, показатели", size=12, bg=True)
    d.text(1335, 335, "Дела\nпланера", size=12, bg=True)
    # A3 → O1, A4, A5
    d.arrow([(right(3), 405), (W, 405)], code="O1")
    d.text(1420, 400, "Сводка дня, план недели", size=12, bg=True)
    d.arrow([(right(3), 450), (830, 450), (830, 520), (left(4), 520)])
    d.arrow([(830, 450), (1055, 450), (1055, 685), (left(5), 685)])
    d.dot(830, 450)
    d.text(800, 446, "Свободные окна, предложения", size=12, bg=True)
    # A4 → O4
    d.arrow([(right(4), 530), (W, 530)], code="O4")
    d.text(1420, 525, "Ответы, результаты заданий", size=12, bg=True)
    # A4 → A2 (обратная связь снизу): команды изменения данных
    d.arrow([(right(4), 572), (1045, 572), (1045, 850), (340, 850), (340, 330), (left(2), 330)])
    d.text(560, 846, "Команды изменения данных, сформированные ассистентом", size=12, bg=True)
    # A5 → O2
    d.arrow([(right(5), 655), (W, 655)], code="O2")
    d.text(1420, 650, "Уведомления и сводки", size=12, bg=True)
    # A6 → O3
    d.arrow([(right(6), 760), (W, 760)], code="O3")
    d.text(1555, 755, "События\nкалендаря", size=12, bg=True)
    # A6 → A2 (обратная связь): изменения дел из календаря
    d.arrow([(right(6), 800), (1600, 800), (1600, 870), (320, 870), (320, 350), (left(2), 350)])
    d.text(1000, 866, "Изменения дел, внесённые во внешнем календаре", size=12, bg=True)

    # ---- механизмы ----
    bus = {1: 905, 2: 925, 3: 945, 4: 965}
    use = {1: (2, 4), 2: (1, 2, 3, 5, 6), 3: (1, 4, 5), 4: (1, 4, 5, 6)}
    labels = {1: "Владелец", 2: "Серверная часть и БД", 3: "Бот и языковая модель",
              4: "Внешние сервисы (VK, CalDAV, Telegram, Claude Code)"}
    for m, y in bus.items():
        x0 = 40 + 30 * (m - 1)
        xs = [left(k) + 30 + 40 * (m - 1) for k in use[m]]
        d.arrow([(x0, d.FOOT), (x0, y), (max(xs), y)], head=False, code=f"M{m}")
        for x, k in zip(xs, use[m]):
            d.arrow([(x, y), (x, bot(k))])
            if x != max(xs):
                d.dot(x, y)
        d.text(165, y - 4, labels[m], size=12, bg=True) if m == 1 else d.text(
            {2: 640, 3: 1130, 4: 1150}[m], y - 4, labels[m], size=12, bg=True)
    d.save("A0_decomposition")


# =====================================================================
#  A1. Актуализировать учебное расписание
# =====================================================================
def decomposition_a1():
    d = Diagram("A1", "Актуализировать учебное расписание", 3, "child:6/1", w=1600, h=1000)
    W = d.W
    B = {1: (130, 170), 2: (390, 300), 3: (650, 430), 4: (910, 560), 5: (1170, 690)}
    BW, BH = 190, 85
    names = {1: "Опросить\nисточник\nпубликации", 2: "Разобрать\nфайл\nрасписания",
             3: "Заменить дни\nрасписания\nв хранилище", 4: "Сравнить снимки\nи сформировать\nсообщения",
             5: "Выгрузить\nзанятия во\nвнешний календарь"}
    for k, (x, y) in B.items():
        d.box(x, y, BW, BH, names[k], f"A1{k}")

    def top(k): return B[k][1]
    def bot(k): return B[k][1] + BH
    def left(k): return B[k][0]
    def right(k): return B[k][0] + BW

    # управление
    d.arrow([(170, d.HEAD), (170, top(1))], code="C1")
    d.text(176, 125, "Регламент опроса: 8:00, 12:00, 16:00, 18:00;\nпубликации за 7 дней", size=12)
    d.arrow([(left(2) + 50, d.HEAD), (left(2) + 50, top(2))], code="C2")
    d.text(left(2) + 56, 260, "Формат файла\nколледжа", size=12, bg=True)
    d.arrow([(left(3) + 50, d.HEAD), (left(3) + 50, top(3))], code="C3")
    d.text(left(3) + 56, 275, "Правило замены\nдней целиком", size=12, bg=True)
    d.arrow([(left(5) + 50, d.HEAD), (left(5) + 50, top(5))], code="C4")
    d.text(left(5) + 56, 620, "Удалять только\nсвои события", size=12, bg=True)

    # входы
    d.arrow([(0, 205), (left(1), 205)], code="I1")
    d.text(18, 200, "Публикации сообщества", size=12)
    d.arrow([(0, 335), (left(2), 335)], code="I2")
    d.text(18, 330, "Файл, загруженный вручную", size=12)

    # интерконнекты
    d.arrow([(right(1), 210), (360, 210), (360, 320), (left(2), 320)])
    d.text(330, 206, "Файл xlsx", size=12, bg=True)
    d.arrow([(right(1), 240), (1360, 240), (1360, 530), (W, 530)], code="O4")
    d.text(1365, 260, "Отказ: файл\nуже загружен,\nисточник\nнедоступен", size=12, bg=True)
    d.arrow([(right(2), 330), (620, 330), (620, 460), (left(3), 460)])
    d.text(590, 326, "Группы и занятия", size=12, bg=True)
    d.arrow([(right(2), 370), (880, 370), (880, 585), (left(4), 585)])
    d.text(700, 366, "Ошибка разбора", size=12, bg=True)
    d.arrow([(right(3), 455), (W, 455)], code="O1")
    d.text(1420, 450, "Занятия группы", size=12, bg=True)
    d.arrow([(right(3), 490), (895, 490), (895, 610), (left(4), 610)])
    d.text(902, 535, "Снимки до\nи после", size=12, bg=True)
    d.arrow([(895, 490), (1140, 490), (1140, 720), (left(5), 720)])
    d.dot(895, 490)
    d.text(1000, 486, "Занятия выбранной группы", size=12, bg=True)
    d.arrow([(right(4), 590), (W, 590)], code="O2")
    d.text(1380, 585, "Сообщения об изменениях", size=12, bg=True)
    d.arrow([(right(5), 730), (W, 730)], code="O3")
    d.text(1400, 725, "События календаря", size=12, bg=True)

    # механизмы
    d.arrow([(60, d.FOOT), (60, 860), (left(4) + 60, 860)], head=False, code="M1")
    for k in (1, 4):
        d.arrow([(left(k) + 60, 860), (left(k) + 60, bot(k))])
        if k != 4:
            d.dot(left(k) + 60, 860)
    d.text(400, 856, "Бот: модуль опроса VK и сравнения снимков", size=12, bg=True)
    d.arrow([(90, d.FOOT), (90, 885), (left(5) + 80, 885)], head=False, code="M2")
    for k in (2, 3, 5):
        d.arrow([(left(k) + 80, 885), (left(k) + 80, bot(k))])
        if k != 5:
            d.dot(left(k) + 80, 885)
    d.text(560, 881, "Серверная часть: разбор, хранилище, синхронизация", size=12, bg=True)
    d.arrow([(120, d.FOOT), (120, 905), (left(5) + 130, 905)], head=False, code="M3")
    for k in (1, 5):
        d.arrow([(left(k) + 130, 905), (left(k) + 130, bot(k))])
        if k != 5:
            d.dot(left(k) + 130, 905)
    d.text(700, 901, "VK API, Яндекс Календарь (CalDAV)", size=12, bg=True)
    d.save("A1_decomposition")


# =====================================================================
#  A4. Обработать обращение к ассистенту
# =====================================================================
def decomposition_a4():
    d = Diagram("A4", "Обработать обращение к ассистенту", 4, "child:6/4", w=1600, h=1000)
    W = d.W
    B = {1: (150, 180), 2: (470, 330), 3: (790, 480), 4: (1110, 630)}
    BW, BH = 210, 95
    names = {1: "Принять обращение\nи собрать\nконтекст", 2: "Определить\nдействие языковой\nмоделью",
             3: "Выполнить\nинструмент через\nпрограммный\nинтерфейс", 4: "Сформировать\nи сохранить\nответ"}
    for k, (x, y) in B.items():
        d.box(x, y, BW, BH, names[k], f"A4{k}")

    def top(k): return B[k][1]
    def bot(k): return B[k][1] + BH
    def left(k): return B[k][0]
    def right(k): return B[k][0] + BW

    # управление
    d.arrow([(200, d.HEAD), (200, top(1))], code="C1")
    d.text(206, 150, "Не более 10 последних реплик", size=12, bg=True)
    d.arrow([(left(2) + 60, d.HEAD), (left(2) + 60, top(2))], code="C2")
    d.text(left(2) + 66, 220, "Промты prompt.jarvis,\nprompt.inbox; модель\nllm.model", size=12, bg=True)
    d.arrow([(left(3) + 60, d.HEAD), (left(3) + 60, top(3))], code="C3")
    d.text(left(3) + 66, 300, "Проверка владельца\nи выданных\nвозможностей;\nзапрет передачи\nданных третьих лиц", size=12, bg=True)
    d.arrow([(left(4) + 60, d.HEAD), (left(4) + 60, top(4))], code="C4")
    d.text(left(4) + 66, 560, "Удаление служебных\nидентификаторов", size=12, bg=True)

    # входы
    d.arrow([(0, 215), (left(1), 215)], code="I1")
    d.text(18, 210, "Вопрос или фраза", size=12)
    d.arrow([(0, 250), (left(1), 250)], code="I2")
    d.text(18, 245, "Переписка из БД", size=12)

    # интерконнекты
    d.arrow([(right(1), 230), (430, 230), (430, 365), (left(2), 365)])
    d.text(380, 226, "Запрос с контекстом", size=12, bg=True)
    d.arrow([(right(2), 360), (750, 360), (750, 510), (left(3), 510)])
    d.text(700, 356, "Вызов инструмента\nс параметрами", size=12, bg=True)
    d.arrow([(right(2), 400), (1070, 400), (1070, 670), (left(4), 670)])
    d.text(880, 396, "Текст ответа", size=12, bg=True)
    # обратная связь: результат инструмента → A42 (снизу)
    d.arrow([(right(3), 550), (1030, 550), (1030, 760), (520, 760), (520, bot(2))])
    d.text(640, 756, "Результат инструмента (до 8 раундов)", size=12, bg=True)
    d.arrow([(right(3), 505), (W, 505)], code="O1")
    d.text(1260, 500, "Команды изменения данных (в A2)", size=12, bg=True)
    d.arrow([(right(4), 660), (W, 660)], code="O2")
    d.text(1350, 655, "Ответ пользователю", size=12, bg=True)
    d.arrow([(right(4), 700), (W, 700)], code="O3")
    d.text(1350, 695, "Сохранённая переписка", size=12, bg=True)

    # механизмы
    d.arrow([(60, d.FOOT), (60, 860), (left(4) + 60, 860)], head=False, code="M1")
    for k in (1, 4):
        d.arrow([(left(k) + 60, 860), (left(k) + 60, bot(k))])
        if k != 4:
            d.dot(left(k) + 60, 860)
    d.text(300, 856, "Серверная часть (модуль assistant)", size=12, bg=True)
    d.arrow([(90, d.FOOT), (90, 885), (left(3) + 100, 885)], head=False, code="M2")
    for k in (1, 2, 3):
        d.arrow([(left(k) + 100, 885), (left(k) + 100, bot(k))])
        if k != 3:
            d.dot(left(k) + 100, 885)
    d.text(260, 881, "Бот: llm.py, tools.py (58 инструментов)", size=12, bg=True)
    d.arrow([(120, d.FOOT), (120, 910), (left(2) + 150, 910), (left(2) + 150, bot(2))], code="M3")
    d.text(250, 906, "Языковая модель (GPTunnel)", size=12, bg=True)
    d.save("A4_decomposition")


if __name__ == "__main__":
    context_diagram()
    decomposition_a0()
    decomposition_a1()
    decomposition_a4()
