import calendar
import os
import time
from datetime import date, datetime, timedelta, timezone
from datetime import time as clock

from dotenv import load_dotenv

import korail_client
import storage
import telegram_notify

KST = timezone(timedelta(hours=9))
CHECK_SEATS = False  # 빈자리 조회. 코레일 매크로 차단(MACRO ERROR)으로 막혀 있어서 꺼둠
HELP = (
    "사용법\n"
    "/등록 서울 부산 20260920 0900-1200 일반실\n"
    "/목록\n"
    "/삭제 번호"
)


def open_time(ride):
    """코레일 예매 오픈 시각: 승차일 1개월 전 07:00"""
    y, m = (ride.year, ride.month - 1) if ride.month > 1 else (ride.year - 1, 12)
    day = min(ride.day, calendar.monthrange(y, m)[1])
    return datetime.combine(date(y, m, day), clock(7), KST)


def describe(w):
    return f"{w['id']}번 {w['dep']}→{w['arr']} {w['date']} {w['start']}-{w['end']} {w['seat']}"


def register(data, args):
    try:
        dep, arr, day, span, seat = args
        start, end = span.split("-")
        ride = datetime.strptime(day, "%Y%m%d").date()
        datetime.strptime(start, "%H%M")
        datetime.strptime(end, "%H%M")
        if seat not in ("일반실", "특실") or start > end:
            raise ValueError
    except ValueError:
        return "형식이 맞지 않아요.\n" + HELP

    w = {
        "id": data["next_id"],
        "dep": dep, "arr": arr, "date": day, "start": start, "end": end, "seat": seat,
        "had_seat": False,
        "open_notified": datetime.now(KST) >= open_time(ride),
    }
    data["next_id"] += 1
    data["watches"].append(w)
    return "등록했어요\n" + describe(w)


def handle_commands(data):
    for u in telegram_notify.get_updates(data["last_update_id"] + 1):
        data["last_update_id"] = u["update_id"]
        msg = u.get("message") or {}
        if str(msg.get("chat", {}).get("id")) != os.environ["TELEGRAM_CHAT_ID"]:
            continue
        parts = msg.get("text", "").split()
        if not parts:
            continue

        cmd, args = parts[0], parts[1:]
        if cmd == "/등록":
            reply = register(data, args)
        elif cmd == "/목록":
            reply = "\n".join(describe(w) for w in data["watches"]) or "등록된 조건이 없어요"
        elif cmd == "/삭제" and args:
            before = len(data["watches"])
            data["watches"] = [w for w in data["watches"] if str(w["id"]) != args[0]]
            reply = "삭제했어요" if len(data["watches"]) < before else "그 번호는 없어요"
        else:
            reply = HELP
        telegram_notify.send(reply)


def check(data):
    now = datetime.now(KST)
    for w in list(data["watches"]):
        ride = datetime.strptime(w["date"], "%Y%m%d").date()
        if ride < now.date():
            data["watches"].remove(w)
            continue
        if now < open_time(ride):
            continue

        if not w["open_notified"]:
            telegram_notify.send("🔔 예매가 열렸어요\n" + describe(w))
            w["open_notified"] = True

        if not CHECK_SEATS:
            continue
        try:
            seats = korail_client.find_seats(w["dep"], w["arr"], w["date"], w["start"], w["end"], w["seat"])
        except Exception as e:
            print(f"{w['id']}번 조회 실패: {e}")
            continue
        if seats and not w["had_seat"]:
            telegram_notify.send("🎫 빈자리가 생겼어요\n" + describe(w) + "\n" + "\n".join(seats) + "\n코레일톡에서 직접 예매하세요")
        w["had_seat"] = bool(seats)
        time.sleep(1)  # 코레일 서버 부담 줄이기: 조회 사이 1초


if __name__ == "__main__":
    load_dotenv()
    data = storage.load()
    handle_commands(data)
    check(data)
    storage.save(data)
