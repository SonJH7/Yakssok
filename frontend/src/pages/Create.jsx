import React, { useState, useRef, useEffect } from 'react';
import './Create.css';
import SelectRange from '../components/SelectRange'; 
import LinkPopup from "../components/LinkPopup";
import createLogo from "../assets/createLogo.png";
import { FRONT_BASE_URL } from '../config/front';
import { API_BASE_URL } from '../config/api';
import { useNavigate } from "react-router-dom";
import { LuMoveVertical } from "react-icons/lu";

const Create = () => {
    const navigate = useNavigate();

    const mainRef = useRef(null);
    const titleRef = useRef(null);
    const numberRef = useRef(null);
    const rangeRef = useRef(null);
    const submitRef = useRef(null);
    const [isSubmitVisible, setIsSubmitVisible] = useState(false);

    const [title, setTitle] = useState(""); 
    const [number, setNumber] = useState("0");
    const [selectedDates, setSelectedDates] = useState(new Set());
    const isFormValid = title.trim().length > 0 &&
                        Number(number) > 0 &&
                        selectedDates.size > 0;

    const [isPopupOpen, setIsPopupOpen] = useState(false);
    const [shareLink, setShareLink] = useState("");
    const [inviteCode, setInviteCode] = useState("");

    useEffect(() => {
        if (!isFormValid) {
            setIsSubmitVisible(false);
            return;
        }

        if (!submitRef.current || !mainRef.current) return;

        const observer = new IntersectionObserver(
            ([entry]) => {
                setIsSubmitVisible(entry.isIntersecting);
            },
            {
                root: mainRef.current,
                threshold: 0.6,
            }
        );

        observer.observe(submitRef.current);

        return () => observer.disconnect();
    }, [isFormValid]);

    const handleNumberChange = (e) => {
        let num = Number(e.target.value);

        if (num > 30) {
            setNumber("30"); 
            alert("약속에는 최대 30명만 참여할 수 있어요. "); 
            return; 
        }
        else if (num < 1 && num !== 0) {
            setNumber("1")
            alert("참여 인원수는 1명 이상이어야 해요. "); 
            return; 
        }
        setNumber(e.target.value); 
    }

    const getNextTarget = () => {
        if (title.trim().length === 0) return titleRef.current;
        if (Number(number) <= 0) return numberRef.current;
        if (selectedDates.size === 0) return rangeRef.current;
        return submitRef.current;
    };

    const showFloating = (title.trim().length > 0 || Number(number) > 0 || selectedDates.size > 0) && !isSubmitVisible;

    const scrollToTarget = () => {
        const target = getNextTarget();
        const container = mainRef.current;

        if (!target) return;

        if (container) {
            const containerRect = container.getBoundingClientRect();
            const targetRect = target.getBoundingClientRect();

            const top =
            container.scrollTop + (targetRect.top - containerRect.top) - 70;

            container.scrollTo({ top, behavior: "smooth" });
        } else {
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    };

    const handleSubmit = async () => {
        if (!isFormValid) return;

        const dates = [...selectedDates].sort();

        const payload = {
            name: title.trim(),
            candidate_dates: dates, 
            max_participants: Number(number),
        };

        const token = localStorage.getItem("access_token");
        if (!token) {
            alert("로그인 정보가 없습니다. 다시 로그인해주세요. ");
            navigate("/"); 
            return;
        }

        try {
            const res = await fetch(`${API_BASE_URL}/appointments/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify(payload),
            });

            if (res.status === 401 || res.status === 403) {
                localStorage.removeItem("access_token");
                alert("로그인 정보가 만료되었어요. 다시 로그인해주세요.");
                navigate("/");
                return;
            }

            if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            console.error("API error:", res.status, err);
            alert(`약속 생성 실패: ${res.status}`);
            return;
            }

            const data = await res.json();
            const inviteCode = data.invite_link;
            const inviteLink = `${FRONT_BASE_URL}/invite/${inviteCode}`;

            setInviteCode(inviteCode); 
            setShareLink(inviteLink);
            setIsPopupOpen(true);

        } catch (e) {
            console.error(e);
            alert("네트워크 오류로 약속 생성에 실패했어요.");
        }
    };


    return (
        <div className='create-container'>
            <main ref={mainRef} className='main-content'>
                <form>
                    <div ref={titleRef}>
                        <img src={createLogo} alt="logoImage" className='logoImage'/>
                        <br/>
                        <p className='request-text'>새로운 약속의 이름을 알려주세요</p>
                        <p className='input-index'>약속 이름</p>
                        <input
                            className="title-input"
                            type="text"
                            maxLength={50}
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="새로운 약속 이름"
                        />
                    </div>
                    <div ref={numberRef} className='number-input-container'>
                        <p className='request-text'>약속에 몇명의 인원이<br/>참여하나요?</p>
                        <div className='number-input'>
                            <span className='num-index-1'>참여인원</span>
                            <input
                                type="number"
                                className="number-box"
                                min="0"
                                max="30"
                                value={number}
                                onChange={handleNumberChange}
                            />
                            <span className='num-index-2'>명</span>
                        </div>
                    </div>
                    <div ref={rangeRef}>
                        <p className='request-text'>어느 기간 안에서<br/>약속을 정하면 좋을까요?</p>
                        <SelectRange value={selectedDates} onChange={setSelectedDates} />
                    </div>
                    <button
                        ref={submitRef}
                        type="button"
                        className="submit-button"
                        disabled={!isFormValid}
                        onClick={handleSubmit}
                    >
                        {isFormValid ? "약속 만들기" : "아직 비어있는 칸이 있어요"}
                    </button>
                    <LinkPopup
                        open={isPopupOpen}
                        link={shareLink}
                        inviteCode = {inviteCode}
                        onClose={() => setIsPopupOpen(false)}
                    />
                </form>
                {showFloating && (
                    <button
                        type="button"
                        className="floating-next"
                        onClick={scrollToTarget}
                    >
                        <LuMoveVertical />
                    </button>
                )}
            </main>
            
        </div>
    );
};

export default Create;
