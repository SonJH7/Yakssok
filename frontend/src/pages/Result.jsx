import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import "./Result.css";
import { API_BASE_URL } from "../config/api";

/* 
  추천 결과 페이지
  - 약속 정보(기간) 표시
  - 세부정보 필터링 기능
  - 추천 결과 표시

*/

const NOT_FOUND = {
  OK: "ok",
  NOT_FOUND: "not found",
};

const Result = () => {
  const { inviteCode } = useParams();

  // 사용자 입력
  const [durationHours, setDurationHours] = useState(""); // 약속 소요 시간(시간 단위)
  const [startHour, setStartHour] = useState(""); // 시간대 시작 시각
  const [endHour, setEndHour] = useState(""); // 시간대 종료 시각

  // 로딩, 에러
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingOptimal, setLoadingOptimal] = useState(false);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(NOT_FOUND.OK);

  // 약속 정보, 추천 결과
  const [detail, setDetail] = useState(null);
  const [optimal, setOptimal] = useState(null);

  // 로그인 토큰
  const accessToken = localStorage.getItem("access_token");

  // 날짜 정규화
  const normalizeDateStr = (raw) => {
    const onlyDate = String(raw).split("T")[0];
    const [y, m, d] = onlyDate.split("-").map(Number);
    return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
  };

  // 로컬 날짜
  const makeLocalDate = (dateStr) => {
    const [y, m, d] = dateStr.split("-").map(Number);
    return new Date(y, m - 1, d);
  };

  // 날짜, 시간 형식 통일
  const formatDate = (dateStr) => {
    const [_, m, d] = dateStr.split("-").map(Number);
    return `${m}월 ${d}일`;
  };

  const formatDay = (dateStr) => {
    const date = makeLocalDate(dateStr);
    const days = ["일", "월", "화", "수", "목", "금", "토"];
    return `${days[date.getDay()]}요일`;
  };

  const formatTime = (hhmm) => {
    const [hh, mm] = String(hhmm).split(":").map(Number);
    const h = Number.isFinite(hh) ? hh : 0;
    const m = Number.isFinite(mm) ? mm : 0;
    return `${String(h).padStart(2, "0")}시 ${String(m).padStart(2, "0")}분`;
  };

  const pad2 = (v) => String(v).padStart(2, "0");

  // 입력
  const isDigitsOnly = (s) => /^\d*$/.test(String(s));

  const parseIntOrNull = (s) => {
    if (s === "") return null;
    if (!isDigitsOnly(s)) return null;
    const n = Number(s);
    if (!Number.isInteger(n)) return null;
    return n;
  };

  const isInRange = (n, min, max) => n !== null && n >= min && n <= max;

  const commitNumericField = (rawValue, { min, max, setState }) => {
    const v = String(rawValue);

    if (v === "") {
      setState("");
      return;
    }

    if (!isDigitsOnly(v)) return;

    const n = parseIntOrNull(v);
    if (!isInRange(n, min, max)) return;

    setState(v);
  };

  const handleDurationHoursChange = (value) => {
    commitNumericField(value, { min: 1, max: 24, setState: setDurationHours });
  };

  const handleStartHourChange = (value) => {
    commitNumericField(value, { min: 0, max: 23, setState: setStartHour });
  };

  const handleEndHourChange = (value) => {
    commitNumericField(value, { min: 1, max: 24, setState: setEndHour });
  };

  // 입력값 유효성 확인
  const durationInt = useMemo(
    () => parseIntOrNull(durationHours),
    [durationHours]
  );
  const startInt = useMemo(() => parseIntOrNull(startHour), [startHour]);
  const endInt = useMemo(() => parseIntOrNull(endHour), [endHour]);

  const isDurationEntered = durationInt !== null && durationInt > 0;
  const isTimeRangeSelected = startInt !== null && endInt !== null;

  // 소요시간(분)
  const minDurationMinutes = useMemo(() => {
    if (!isDurationEntered) return 0;
    return durationInt * 60;
  }, [isDurationEntered, durationInt]);

  const timeRangeStart = useMemo(() => {
    if (startInt === null) return null;
    return `${pad2(startInt)}:00`;
  }, [startInt]);

  const timeRangeEnd = useMemo(() => {
    if (endInt === null) return null;
    return `${pad2(endInt)}:00`;
  }, [endInt]);

  // 시간대 유효성 확인
  const isTimeRangeValid = useMemo(() => {
    if (!isDurationEntered || !isTimeRangeSelected) return false;
    if (endInt <= startInt) return false;
    return (endInt - startInt) * 60 >= minDurationMinutes;
  }, [
    isDurationEntered,
    isTimeRangeSelected,
    startInt,
    endInt,
    minDurationMinutes,
  ]);

  const timeRangeError = useMemo(() => {
    if (!isDurationEntered || !isTimeRangeSelected) return "";

    if (endInt <= startInt) return "종료 시각은 시작 시각보다 늦어야 해요.";
    if ((endInt - startInt) * 60 < minDurationMinutes)
      return "시간대는 소요시간보다 길어야 해요.";

    return "";
  }, [
    isDurationEntered,
    isTimeRangeSelected,
    startInt,
    endInt,
    minDurationMinutes,
  ]);

  // 약속 정보 불러오기
  const fetchDetail = useCallback(async (code) => {
    if (!code) return;

    setLoadingDetail(true);
    setError("");
    setNotFound(NOT_FOUND.OK);

    try {
      const res = await fetch(`${API_BASE_URL}/appointments/${code}/detail`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });

      if (res.status === 404) {
        setNotFound(NOT_FOUND.NOT_FOUND);
        setDetail(null);
        return;
      }

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text);
      }

      const data = await res.json();
      setDetail(data);
    } catch {
      setError("약속 정보를 불러오지 못했어요.");
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  // 추천 결과 불러오기
  const fetchOptimal = useCallback(
    async ({ code, token, minDuration, rangeStart, rangeEnd }) => {
      if (!code) return;

      setLoadingOptimal(true);
      setError("");
      setNotFound(NOT_FOUND.OK);

      try {
        const url = new URL(
          `${API_BASE_URL}/appointments/${code}/optimal-times`
        );
        url.searchParams.set("min_duration_minutes", String(minDuration));
        url.searchParams.set("time_range_start", String(rangeStart));
        url.searchParams.set("time_range_end", String(rangeEnd));

        const res = await fetch(url.toString(), {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(`optimal-times 실패: ${res.status} ${text}`);
        }

        const data = await res.json();
        setOptimal(data);
      } catch (e) {
        setError(e?.message || "추천 결과 불러오기 실패");
      } finally {
        setLoadingOptimal(false);
      }
    },
    []
  );

  // 추천 결과 리스트
  const optimalList = useMemo(() => optimal?.optimal_times || [], [optimal]);

  // 초대코드 변경 시 입력값 초기화
  useEffect(() => {
    setDurationHours("");
    setStartHour("");
    setEndHour("");
    setOptimal(null);
    setError("");
    setDetail(null);

    setNotFound(accessToken ? NOT_FOUND.OK : NOT_FOUND.LOGIN_REQUIRED);
  }, [inviteCode, accessToken]);

  // 약속 정보 로딩
  useEffect(() => {
    if (!inviteCode) return;
    fetchDetail(inviteCode);
  }, [inviteCode, fetchDetail]);

  // 추천 결과 로딩 (디바운스)
  const debounceRef = useRef(null);

  useEffect(() => {
    if (!inviteCode) return;
    if (
      notFound === NOT_FOUND.LOGIN_REQUIRED ||
      notFound === NOT_FOUND.NOT_FOUND
    )
      return;

    // 입력이 불완전/유효하지 않으면 호출 X
    if (!isTimeRangeValid) {
      setOptimal(null);
      return;
    }

    if (!timeRangeStart || !timeRangeEnd) {
      setOptimal(null);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(() => {
      fetchOptimal({
        code: inviteCode,
        token: accessToken,
        minDuration: minDurationMinutes,
        rangeStart: timeRangeStart,
        rangeEnd: timeRangeEnd,
      });
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [
    inviteCode,
    accessToken,
    notFound,
    isTimeRangeValid,
    minDurationMinutes,
    timeRangeStart,
    timeRangeEnd,
    fetchOptimal,
  ]);

  // 달력 렌더링
  const daysForGrid = useMemo(() => {
    if (!detail?.dates) return [];

    return detail.dates.map((d) => {
      const dateStr = normalizeDateStr(d.date);
      const date = makeLocalDate(dateStr);

      return {
        key: dateStr,
        dateStr,
        day: date.getDate(),
        dayOfWeek: date.getDay(),
        selectedDay: true,
      };
    });
  }, [detail]);

  const calendarCells = useMemo(() => {
    if (!daysForGrid.length) return [];

    const sorted = [...daysForGrid].sort((a, b) =>
      a.dateStr.localeCompare(b.dateStr)
    );

    const firstDateStr = sorted[0].dateStr;
    const lastDateStr = sorted[sorted.length - 1].dateStr;

    const firstdate = makeLocalDate(firstDateStr);
    const lastdate = makeLocalDate(lastDateStr);

    const start = new Date(firstdate);
    start.setDate(start.getDate() - start.getDay());

    const end = new Date(lastdate);
    end.setDate(end.getDate() + (6 - end.getDay()));

    const rangeMap = new Map(sorted.map((d) => [d.dateStr, d.selectedDay]));

    const cells = [];
    const cur = new Date(start);

    while (cur <= end) {
      const yyyy = cur.getFullYear();
      const mm = String(cur.getMonth() + 1).padStart(2, "0");
      const dd = String(cur.getDate()).padStart(2, "0");
      const dateStr = `${yyyy}-${mm}-${dd}`;

      cells.push({
        key: dateStr,
        dateStr,
        day: cur.getDate(),
        dayOfWeek: cur.getDay(),
        selectedDay: rangeMap.get(dateStr) === true,
      });

      cur.setDate(cur.getDate() + 1);
    }

    return cells;
  }, [daysForGrid]);

  const monthText = useMemo(() => {
    if (!daysForGrid.length) return "";
    const date = makeLocalDate(daysForGrid[0].dateStr);
    return `${date.getMonth() + 1}월`;
  }, [daysForGrid]);

  if (notFound === NOT_FOUND.NOT_FOUND) {
    const Type = "존재하지 않는 약속이에요.";
    const Text = "삭제된 약속이거나 잘못된 초대코드일 수 있어요.";

    return (
      <div className="resultPage">
        <div className="resultContainer">
          <div className="errorType">{Type}</div>
          <div className="errorText">{Text}</div>
        </div>
      </div>
    );
  }
  return (
    <div className="resultPage">
      <div className="resultContainer">
        {/* 약속 범위 */}
        <div className="rangeContainer">
          <div className="rangeText">약속 범위</div>
          <div className="weekContainer">
            <div className="monthText">{monthText}</div>

            <div className="weekGrid">
              {loadingDetail}

              {!loadingDetail && daysForGrid.length === 0}

              {!loadingDetail &&
                calendarCells.map((cell) => (
                  <div
                    key={cell.key}
                    className={`dayCell ${cell.selectedDay ? "selected" : ""}`}
                  >
                    <div
                      className={`dayText
                        ${cell.dayOfWeek === 0 ? "sunday" : ""}
                        ${cell.dayOfWeek === 6 ? "saturday" : ""}`}
                    >
                      {cell.day}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>

        {/* 추가 설정 */}
        <div className="addSetting">
          <div className="noticeText">
            약속 시간을
            <br />더 구체적으로 골라볼까요?
          </div>

          <div className="setText">
            <label>
              약속에는&nbsp;
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={durationHours}
                onChange={(e) => handleDurationHoursChange(e.target.value)}
                placeholder="1"
                className="setInput"
              />
              시간 소요돼요.
            </label>

            <br />

            <label>
              시간대는&nbsp;
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={startHour}
                onChange={(e) => handleStartHourChange(e.target.value)}
                placeholder="0"
                className="setInput"
              />
              &nbsp;시 부터&nbsp;
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={endHour}
                onChange={(e) => handleEndHourChange(e.target.value)}
                placeholder="0"
                className="setInput"
              />
              &nbsp;시 사이면 좋겠어요.
            </label>

            {!timeRangeError && (
              <div className="errorText">* 시간은 24시간 형식이에요.</div>
            )}
            {timeRangeError && (
              <div className="errorText">* {timeRangeError}</div>
            )}
          </div>
        </div>

        {/* 추천 날짜 */}
        <div className="resultContent">
          {!isDurationEntered || !isTimeRangeSelected ? (
            <div className="noticeText">
              소요시간과 시간대를 입력하면 추천 시간대가 나타나요.
            </div>
          ) : (
            <>
              <div className="noticeText">
                약속하기 좋은 날짜
                <br />
                약쏙이 골라봤어요.
              </div>

              <div className="resultList">
                <>
                  {loadingOptimal}

                  {!loadingOptimal && !error && optimalList.length === 0 && (
                    <div>추천 가능한 날짜가 없어요.</div>
                  )}

                  {!loadingOptimal &&
                    optimalList.slice(0, 5).map((item, index) => (
                      <div
                        key={`${item.date}-${item.start_time}-${index}`}
                        className="resultCard"
                      >
                        <div className="resultNum">{index + 1}</div>

                        <div className="resultText">
                          <div className="resultDate">
                            {formatDate(item.date)} {formatDay(item.date)}
                          </div>
                          <div className="resultTime">
                            {formatTime(item.start_time)} ~{" "}
                            {formatTime(item.end_time)}
                          </div>
                        </div>
                      </div>
                    ))}
                </>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Result;
