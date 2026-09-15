from korail2 import Korail, NoResultsError, TrainType

_korail = None


def find_seats(dep, arr, day, start, end, seat):
    """start~end(HHMM) 사이에 출발하는 KTX 중, 원하는 등급 좌석이 남은 열차 목록"""
    global _korail
    if _korail is None:
        _korail = Korail("", "", auto_login=False)  # 조회만 하므로 로그인 안 함

    try:
        trains = _korail.search_train(dep, arr, day, start + "00", train_type=TrainType.KTX, include_no_seats=True)
    except NoResultsError:
        return []

    found = []
    for t in trains:
        if t.dep_time[:4] > end:
            continue
        has_seat = t.has_special_seat() if seat == "특실" else t.has_general_seat()
        if has_seat:
            found.append(f"{t.dep_time[:2]}:{t.dep_time[2:4]} 출발 KTX {t.train_no}")
    return found
