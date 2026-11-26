# Complete unified logic script for History Exam System (Grade 10 & 11)

JS_LOGIC = """
    // =========================================================================
    // CONFIGURATION & CONSTANTS
    // =========================================================================
    const TARGET_SPREADSHEET_ID = "1vzUWJIdhn02Arkd4xUhAja5c26ESQMOxZZVo-8I24ys";
    const DEFAULT_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwz6rbhVgmikjN0UwYmdWcnzX1owDNKShg-o_R4ni0Q8v9UEekpPtcHFG53C6igxThV9g/exec";
    const STORAGE_SCRIPT_URL_KEY = "ol_history_unified_script_url_v1";

    // Security PIN SHA-256 Hash for '4112' (No plaintext PIN visible anywhere)
    const PIN_SHA256_HASH = "059f5e543bd484b00e235edc5083558c59d45706bd99c14422bda8868c6c6f90";

    const STORAGE_RESULTS_KEY = "ol_history_unified_results_v1";
    const STORAGE_SETTINGS_KEY = "ol_history_unified_settings_v1";
    const STORAGE_FEEDBACKS_KEY = "ol_history_unified_feedbacks_v1";
    const STORAGE_CUSTOM_QUESTIONS_PREFIX = "ol_history_custom_questions_grade_";

    function getWebAppUrl() {
        const savedUrl = (localStorage.getItem(STORAGE_SCRIPT_URL_KEY) || '').trim();
        return savedUrl || DEFAULT_WEB_APP_URL;
    }

    // Helper: SHA-256 calculation in browser
    async function sha256Hex(str) {
        const enc = new TextEncoder();
        const buf = await crypto.subtle.digest("SHA-256", enc.encode(str));
        return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
    }

    // Deep copies for factory reset
    const BACKUP_G10 = JSON.parse(JSON.stringify(GRADE_10_UNITS));
    const BACKUP_G11 = JSON.parse(JSON.stringify(GRADE_11_UNITS));

    function getActiveBank(grade) {
        return grade === "11" ? GRADE_11_UNITS : GRADE_10_UNITS;
    }

    function loadCustomQuestionsForGrade(grade) {
        try {
            const raw = localStorage.getItem(STORAGE_CUSTOM_QUESTIONS_PREFIX + grade);
            if (!raw) return;
            const saved = JSON.parse(raw);
            const bank = getActiveBank(grade);
            Object.keys(saved).forEach(k => {
                if (bank[k] && saved[k]) {
                    bank[k].questions = saved[k].questions || bank[k].questions;
                    bank[k].answerKey = saved[k].answerKey || bank[k].answerKey;
                    bank[k].totalQuestions = bank[k].questions.length;
                }
            });
        } catch (e) {
            console.warn("Failed loading custom questions for grade " + grade, e);
        }
    }

    function saveCustomQuestionsForGrade(grade) {
        try {
            const bank = getActiveBank(grade);
            const toSave = {};
            Object.keys(bank).forEach(k => {
                toSave[k] = {
                    questions: bank[k].questions,
                    answerKey: bank[k].answerKey
                };
            });
            localStorage.setItem(STORAGE_CUSTOM_QUESTIONS_PREFIX + grade, JSON.stringify(toSave));
        } catch (e) {
            console.warn("Failed saving custom questions for grade " + grade, e);
        }
    }

    // Load custom questions on startup
    loadCustomQuestionsForGrade("10");
    loadCustomQuestionsForGrade("11");

    // =========================================================================
    // APPLICATION STATE
    // =========================================================================
    let currentGrade = "10";
    let currentUnitId = 1;
    let studentInfo = { name: "", school: "", year: "2026", grade: "10" };
    let userAnswers = {};
    let isSubmitted = false;
    let timeLeft = 60 * 60;
    let timerInterval = null;
    let selectedRating = 5;
    let currentExamResultRecord = null;

    function getSettings() {
        const defaults = { examMinutes: 60 };
        try {
            const saved = JSON.parse(localStorage.getItem(STORAGE_SETTINGS_KEY));
            return saved ? { ...defaults, ...saved } : defaults;
        } catch (e) {
            return defaults;
        }
    }

    function saveSettingsObj(obj) {
        localStorage.setItem(STORAGE_SETTINGS_KEY, JSON.stringify(obj));
    }

    function getStoredResults() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_RESULTS_KEY)) || [];
        } catch (e) {
            return [];
        }
    }

    function saveStoredResults(arr) {
        localStorage.setItem(STORAGE_RESULTS_KEY, JSON.stringify(arr));
    }

    function getStoredFeedbacks() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_FEEDBACKS_KEY)) || [];
        } catch (e) {
            return [];
        }
    }

    function saveStoredFeedbacks(arr) {
        localStorage.setItem(STORAGE_FEEDBACKS_KEY, JSON.stringify(arr));
    }

    // =========================================================================
    // INITIALIZATION & DYNAMIC UI
    // =========================================================================
    window.addEventListener('DOMContentLoaded', () => {
        renderLoginUnitList("10");
        const settings = getSettings();
        document.getElementById('tp-exam-minutes').value = settings.examMinutes || 60;
        document.getElementById('tp-script-url').value = getWebAppUrl();
        setRating(5);
    });

    function onGradeRadioChange() {
        const selected = document.querySelector('input[name="selected-grade"]:checked').value;
        currentGrade = selected;
        document.getElementById('grade-badge-label').textContent = `${selected} ශ්‍රේණිය`;
        renderLoginUnitList(selected);
    }

    function renderLoginUnitList(grade) {
        const bank = getActiveBank(grade);
        const container = document.getElementById('unit-radio-grid');
        container.innerHTML = '';

        const keys = Object.keys(bank).sort((a,b) => Number(a) - Number(b));
        keys.forEach((key, index) => {
            const unit = bank[key];
            const isChecked = index === 0 ? 'checked' : '';
            const card = document.createElement('label');
            card.className = "cursor-pointer";
            card.innerHTML = `
                <input type="radio" name="selected-unit" value="${unit.id}" class="peer sr-only" ${isChecked}>
                <div class="p-3.5 rounded-xl border-2 border-slate-200 peer-checked:border-blue-600 peer-checked:bg-blue-50 hover:bg-slate-50 transition h-full">
                    <span class="text-xs font-extrabold text-blue-700 uppercase block">${unit.number} වන ඒකකය (ප්‍රශ්න ${unit.questions.length})</span>
                    <span class="text-sm font-bold text-slate-800">${unit.title}</span>
                </div>
            `;
            container.appendChild(card);
        });
    }

    function startStudentExam(event) {
        event.preventDefault();
        const nameVal = document.getElementById('student-name').value.trim();
        const schoolVal = document.getElementById('student-school').value.trim();
        const yearVal = document.getElementById('student-year').value.trim();
        const gradeVal = document.querySelector('input[name="selected-grade"]:checked').value;
        const unitRadio = document.querySelector('input[name="selected-unit"]:checked');

        if (!nameVal || !schoolVal || !yearVal || !unitRadio) {
            alert("කරුණාකර සියලුම අනිවාර්ය තොරතුරු ඇතුළත් කරන්න.");
            return;
        }

        currentGrade = gradeVal;
        currentUnitId = parseInt(unitRadio.value);
        studentInfo = { name: nameVal, school: schoolVal, year: yearVal, grade: gradeVal };

        document.getElementById('disp-name').textContent = studentInfo.name;
        document.getElementById('disp-school').textContent = studentInfo.school;
        document.getElementById('disp-year').textContent = studentInfo.year;
        document.getElementById('disp-grade').textContent = `${studentInfo.grade} ශ්‍රේණිය`;

        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('exam-screen').classList.remove('hidden');
        document.getElementById('exam-status-bar').classList.remove('hidden');

        renderUnitSwitcher();
        loadUnit(currentGrade, currentUnitId);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function returnToHome() {
        if (!isSubmitted && Object.keys(userAnswers).length > 0) {
            if (!confirm("ඔබ දැනට සපයා ඇති පිළිතුරු මැකී යනු ඇත. මුල් පිටුවට යාමට අවශ්‍යද?")) {
                return;
            }
        }
        clearInterval(timerInterval);
        document.getElementById('exam-screen').classList.add('hidden');
        document.getElementById('exam-status-bar').classList.add('hidden');
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('header-unit-label').textContent = "10 & 11 ශ්‍රේණි - ඉතිහාසය";
        document.getElementById('header-lesson-title').textContent = "මාර්ගගත බහුවරණ ඇගයීම් පද්ධතිය";
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function renderUnitSwitcher() {
        const switcher = document.getElementById('unit-switcher');
        switcher.innerHTML = '';
        document.getElementById('switcher-grade-badge').textContent = `${currentGrade} ශ්‍රේණිය`;
        const bank = getActiveBank(currentGrade);
        const keys = Object.keys(bank).sort((a,b) => Number(a) - Number(b));

        keys.forEach(k => {
            const u = bank[k];
            const btn = document.createElement('button');
            btn.type = 'button';
            const isCur = u.id === currentUnitId;
            btn.className = `px-2.5 py-1 rounded-lg text-xs font-bold transition shrink-0 ${
                isCur ? 'bg-amber-400 text-blue-950 shadow' : 'bg-blue-800 hover:bg-blue-700 text-blue-100'
            }`;
            btn.textContent = `ඒකක ${u.number}`;
            btn.title = u.title;
            btn.onclick = () => {
                if (u.id === currentUnitId) return;
                if (!isSubmitted && Object.keys(userAnswers).length > 0) {
                    if (!confirm("වෙනත් ඒකකයකට මාරු වුවහොත් දැනට සපයා ඇති පිළිතුරු මැකී යනු ඇත. ඉදිරියට යාමට අවශ්‍යද?")) return;
                }
                currentUnitId = u.id;
                renderUnitSwitcher();
                loadUnit(currentGrade, currentUnitId);
            };
            switcher.appendChild(btn);
        });
    }

    function loadUnit(grade, unitId) {
        const bank = getActiveBank(grade);
        const unit = bank[unitId];
        const settings = getSettings();

        userAnswers = {};
        isSubmitted = false;
        clearInterval(timerInterval);
        timeLeft = (settings.examMinutes || 60) * 60;

        document.getElementById('header-unit-label').textContent = `${grade} ශ්‍රේණිය - ඉතිහාසය (${unit.number} වන ඒකකය)`;
        document.getElementById('header-lesson-title').textContent = `${unit.title} (ප්‍රශ්න ${unit.questions.length})`;
        document.getElementById('banner-main-title').textContent = `අ.පො.ස. (සාමාන්‍ය පෙළ) - ${grade} ශ්‍රේණිය ඉතිහාසය`;
        document.getElementById('banner-sub-title').textContent = `${unit.number} වන ඒකකය: ${unit.title} | කාලය: මිනිත්තු ${settings.examMinutes || 60}`;
        document.getElementById('progress-text').textContent = `0 / ${unit.questions.length}`;

        document.getElementById('results-section').classList.add('hidden');
        document.getElementById('submit-box').classList.remove('hidden');

        renderNavGrid();
        renderQuestions();
        startTimer();
    }

    // =========================================================================
    // TIMER & NAVIGATION GRID
    // =========================================================================
    function startTimer() {
        updateTimerDisplay();
        timerInterval = setInterval(() => {
            if (isSubmitted) {
                clearInterval(timerInterval);
                return;
            }
            timeLeft--;
            updateTimerDisplay();
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                alert("කාලය අවසන්! ඔබගේ පිළිතුරු ස්වයංක්‍රීයව ඉදිරිපත් කෙරේ.");
                submitExam();
            }
        }, 1000);
    }

    function updateTimerDisplay() {
        const timerEl = document.getElementById('timer');
        const m = Math.floor(Math.max(0, timeLeft) / 60);
        const s = Math.max(0, timeLeft) % 60;
        timerEl.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        if (timeLeft <= 300) {
            timerEl.classList.remove('text-amber-300');
            timerEl.classList.add('text-rose-400', 'animate-pulse');
        } else {
            timerEl.classList.remove('text-rose-400', 'animate-pulse');
            timerEl.classList.add('text-amber-300');
        }
    }

    function renderNavGrid() {
        const bank = getActiveBank(currentGrade);
        const unit = bank[currentUnitId];
        const navGrid = document.getElementById('nav-grid');
        navGrid.innerHTML = '';

        unit.questions.forEach(q => {
            const btn = document.createElement('button');
            btn.id = `nav-btn-${q.id}`;
            btn.type = 'button';
            btn.className = "h-8 rounded border border-slate-300 text-xs font-bold text-slate-600 hover:bg-blue-50 transition";
            btn.textContent = q.id;
            btn.onclick = () => {
                const el = document.getElementById(`q-card-${q.id}`);
                if (el) {
                    const y = el.getBoundingClientRect().top + window.scrollY - 90;
                    window.scrollTo({ top: y, behavior: 'smooth' });
                }
            };
            navGrid.appendChild(btn);
        });
    }

    function renderQuestions() {
        const bank = getActiveBank(currentGrade);
        const unit = bank[currentUnitId];
        const container = document.getElementById('questions-container');
        container.innerHTML = '';

        unit.questions.forEach(q => {
            const card = document.createElement('div');
            card.id = `q-card-${q.id}`;
            card.className = "bg-white rounded-xl shadow-sm border border-slate-200 p-5 md:p-6 transition";

            let headerHtml = '';
            if (q.header) {
                headerHtml = `<div class="mb-3 p-3 bg-slate-50 border-l-4 border-amber-500 rounded-r-lg text-xs md:text-sm text-slate-700 leading-relaxed">${q.header}</div>`;
            }

            let optionsHtml = '';
            q.options.forEach((optText, idx) => {
                const optNum = idx + 1;
                optionsHtml += `
                    <button type="button" id="opt-${q.id}-${optNum}" onclick="selectOption(${q.id}, ${optNum})"
                        class="option-btn w-full text-left p-3.5 rounded-xl border-2 border-slate-200 flex items-start gap-3 text-sm md:text-base text-slate-800">
                        <span class="w-7 h-7 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-xs font-extrabold shrink-0 mt-0.5 text-slate-700">(${optNum})</span>
                        <span class="leading-snug">${optText}</span>
                    </button>
                `;
            });

            card.innerHTML = `
                ${headerHtml}
                <div class="flex items-start gap-3 mb-4">
                    <span class="bg-blue-900 text-white font-bold text-xs md:text-sm px-2.5 py-1 rounded-lg shrink-0 mt-0.5">${String(q.id).padStart(2, '0')}</span>
                    <h3 class="font-bold text-slate-800 text-base md:text-lg leading-snug">${q.text}</h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    ${optionsHtml}
                </div>
            `;
            container.appendChild(card);
        });
    }

    function selectOption(qId, optNum) {
        if (isSubmitted) return;
        userAnswers[qId] = optNum;

        for (let i = 1; i <= 4; i++) {
            const btn = document.getElementById(`opt-${qId}-${i}`);
            if (btn) {
                if (i === optNum) btn.classList.add('selected');
                else btn.classList.remove('selected');
            }
        }

        const navBtn = document.getElementById(`nav-btn-${qId}`);
        if (navBtn) {
            navBtn.classList.remove('border-slate-300', 'text-slate-600');
            navBtn.classList.add('bg-blue-700', 'text-white', 'border-blue-800');
        }

        const bank = getActiveBank(currentGrade);
        const unit = bank[currentUnitId];
        document.getElementById('progress-text').textContent = `${Object.keys(userAnswers).length} / ${unit.questions.length}`;
    }

    function confirmSubmit() {
        if (isSubmitted) return;
        const bank = getActiveBank(currentGrade);
        const unit = bank[currentUnitId];
        const answeredCount = Object.keys(userAnswers).length;
        const total = unit.questions.length;

        if (answeredCount < total) {
            const unanswered = total - answeredCount;
            if (!confirm(`ඔබ තවමත් ප්‍රශ්න ${unanswered} කට පිළිතුරු සපයා නොමැත. එසේ වුවද විභාගය අවසන් කිරීමට අවශ්‍යද?`)) return;
        } else {
            if (!confirm("ඔබගේ පිළිතුරු ඉදිරිපත් කර විභාගය අවසන් කිරීමට අවශ්‍යද?")) return;
        }
        submitExam();
    }

    function calculateGrade(percentage) {
        if (percentage >= 75) return "A";
        if (percentage >= 65) return "B";
        if (percentage >= 50) return "C";
        if (percentage >= 35) return "S";
        return "W";
    }

    function submitExam() {
        isSubmitted = true;
        clearInterval(timerInterval);

        const bank = getActiveBank(currentGrade);
        const unit = bank[currentUnitId];
        const total = unit.questions.length;
        let score = 0;

        unit.questions.forEach(q => {
            const correct = unit.answerKey[q.id];
            const chosen = userAnswers[q.id];
            if (chosen === correct) score++;

            const navBtn = document.getElementById(`nav-btn-${q.id}`);
            if (navBtn) {
                navBtn.className = `h-8 rounded border text-xs font-bold text-white ${
                    chosen === correct ? 'bg-emerald-600 border-emerald-700' : 'bg-rose-600 border-rose-700'
                }`;
            }
        });

        const percentage = Math.round((score / total) * 100);
        const grade = calculateGrade(percentage);

        document.getElementById('submit-box').classList.add('hidden');
        const resultsSection = document.getElementById('results-section');
        resultsSection.classList.remove('hidden');

        document.getElementById('result-unit-subtitle').textContent = `${currentGrade} ශ්‍රේණිය - ඉතිහාසය | ${unit.number} වන ඒකකය: ${unit.title}`;
        document.getElementById('res-student-name').textContent = studentInfo.name;
        document.getElementById('res-student-school').textContent = studentInfo.school;
        document.getElementById('res-student-year').textContent = studentInfo.year;
        document.getElementById('res-student-grade').textContent = `${currentGrade} ශ්‍රේණිය`;

        document.getElementById('score-text').textContent = `${score} / ${total}`;
        document.getElementById('percentage-text').textContent = `${percentage}%`;
        document.getElementById('grade-text').textContent = grade;

        renderAnswerMatrix(unit);
        renderDetailedReview(unit);

        const nowStr = new Date().toLocaleString('si-LK');
        const recordObj = {
            id: Date.now(),
            gradeLevel: currentGrade,
            name: studentInfo.name,
            school: studentInfo.school,
            year: studentInfo.year,
            unitId: unit.id,
            unitNumber: unit.number,
            unitTitle: unit.title,
            score: score,
            total: total,
            percentage: percentage,
            grade: grade,
            timestamp: nowStr,
            answers: { ...userAnswers }
        };

        currentExamResultRecord = recordObj;

        const existingResults = getStoredResults();
        existingResults.unshift(recordObj);
        saveStoredResults(existingResults);

        syncScoreToGoogleSheet(recordObj);

        // Reset feedback form for this submission
        document.getElementById('feedback-comments').value = '';
        const fbStatus = document.getElementById('feedback-status-badge');
        fbStatus.className = 'hidden';
        fbStatus.textContent = '';
        setRating(5);

        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    async function syncScoreToGoogleSheet(record) {
        const statusBadge = document.getElementById('sheet-sync-status');
        const scriptUrl = getWebAppUrl();

        if (!scriptUrl) {
            statusBadge.className = "inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300";
            statusBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i><span>පද්ධතිය තුළ සුරැකුණි (Google Sheet URL සකසා නොමැත)</span>`;
            return;
        }

        const payload = {
            action: "save_student_score",
            grade: record.gradeLevel,
            spreadsheetId: TARGET_SPREADSHEET_ID,
            timestamp: record.timestamp,
            name: record.name,
            school: record.school,
            year: record.year,
            unit: `${record.unitNumber} - ${record.unitTitle}`,
            score: record.score,
            total: record.total,
            percentage: `${record.percentage}%`,
            gradeResult: record.grade
        };

        try {
            await fetch(scriptUrl, {
                method: "POST",
                mode: "no-cors",
                headers: { "Content-Type": "text/plain;charset=utf-8" },
                body: JSON.stringify(payload)
            });

            statusBadge.className = "inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-300";
            statusBadge.innerHTML = `<i class="fa-solid fa-circle-check"></i><span>Google Sheet වෙත ලකුණු සාර්ථකව සුරැකුණි!</span>`;
        } catch (err) {
            console.error("Google Sheet sync error:", err);
            statusBadge.className = "inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold bg-rose-50 text-rose-800 border border-rose-300";
            statusBadge.innerHTML = `<i class="fa-solid fa-circle-xmark"></i><span>Google Sheet සම්බන්ධතා දෝෂයකි (දත්ත පද්ධතියේ සුරැකී ඇත)</span>`;
        }
    }

    function renderAnswerMatrix(unit) {
        const tbody = document.getElementById('answer-matrix-body');
        tbody.innerHTML = '';
        const total = unit.questions.length;
        const rowsCount = Math.ceil(total / 4);

        for (let r = 0; r < rowsCount; r++) {
            const tr = document.createElement('tr');
            for (let c = 0; c < 4; c++) {
                const qNum = r + 1 + c * rowsCount;
                if (qNum <= total) {
                    const correct = unit.answerKey[qNum];
                    const chosen = userAnswers[qNum];
                    const isOk = chosen === correct;
                    tr.innerHTML += `
                        <td class="border border-slate-300 p-1.5 font-bold bg-slate-50">${String(qNum).padStart(2, '0')}</td>
                        <td class="border border-slate-300 p-1.5 font-extrabold ${isOk ? 'text-emerald-700 bg-emerald-50' : 'text-rose-700 bg-rose-50'}">
                            ${correct} ${chosen ? (isOk ? '✓' : `(ඔබ: ${chosen})`) : '(හිස්)'}
                        </td>
                    `;
                } else {
                    tr.innerHTML += `<td class="border border-slate-300 p-1.5 bg-slate-50">-</td><td class="border border-slate-300 p-1.5">-</td>`;
                }
            }
            tbody.appendChild(tr);
        }
    }

    function renderDetailedReview(unit) {
        const container = document.getElementById('review-container');
        container.innerHTML = '';

        unit.questions.forEach(q => {
            const correct = unit.answerKey[q.id];
            const chosen = userAnswers[q.id];
            const isOk = chosen === correct;

            const card = document.createElement('div');
            card.className = `p-5 rounded-xl border-2 ${isOk ? 'border-emerald-300 bg-emerald-50/40' : 'border-rose-300 bg-rose-50/40'}`;

            let optsHtml = '';
            q.options.forEach((optText, idx) => {
                const num = idx + 1;
                let badgeClass = "bg-white border-slate-200 text-slate-700";
                let icon = "";

                if (num === correct) {
                    badgeClass = "bg-emerald-100 border-emerald-500 text-emerald-950 font-bold";
                    icon = `<i class="fa-solid fa-circle-check text-emerald-600 ml-auto"></i>`;
                } else if (num === chosen && !isOk) {
                    badgeClass = "bg-rose-100 border-rose-500 text-rose-950 font-bold";
                    icon = `<i class="fa-solid fa-circle-xmark text-rose-600 ml-auto"></i>`;
                }

                optsHtml += `
                    <div class="p-2.5 rounded-lg border ${badgeClass} flex items-center gap-2 text-xs md:text-sm">
                        <span class="font-extrabold">(${num})</span>
                        <span>${optText}</span>
                        ${icon}
                    </div>
                `;
            });

            card.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-extrabold px-2.5 py-0.5 rounded ${isOk ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white'}">
                        ප්‍රශ්න ${String(q.id).padStart(2, '0')} - ${isOk ? 'නිවැරදියි' : (chosen ? 'වැරදියි' : 'පිළිතුරු සපයා නැත')}
                    </span>
                    <span class="text-xs font-bold text-slate-600">නිවැරදි පිළිතුර: (${correct})</span>
                </div>
                <p class="font-bold text-slate-800 text-sm md:text-base mb-3">${q.text}</p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">${optsHtml}</div>
            `;
            container.appendChild(card);
        });
    }

    // =========================================================================
    // STUDENT FEEDBACK & SUGGESTIONS FEATURE (Saves to Drive / Sheet)
    // =========================================================================
    function setRating(val) {
        selectedRating = val;
        const stars = document.querySelectorAll('#star-rating-box i');
        stars.forEach(s => {
            const num = parseInt(s.getAttribute('data-star'));
            if (num <= val) {
                s.className = "fa-solid fa-star text-amber-400";
            } else {
                s.className = "fa-solid fa-star text-slate-300";
            }
        });
        document.getElementById('rating-text').textContent = `තරු 5න් ${val}ක්`;
    }

    async function submitStudentFeedback(event) {
        event.preventDefault();
        const comments = document.getElementById('feedback-comments').value.trim();
        if (!comments) {
            alert("කරුණාකර ඔබගේ අදහස් හෝ යෝජනා ඇතුළත් කරන්න.");
            return;
        }

        const btn = document.getElementById('btn-feedback-submit');
        const statusBadge = document.getElementById('feedback-status-badge');
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> සුරකිමින් පවතී...`;

        const feedbackObj = {
            id: Date.now(),
            timestamp: new Date().toLocaleString('si-LK'),
            studentName: studentInfo.name || "සිසුවා",
            studentSchool: studentInfo.school || "-",
            year: studentInfo.year || "2026",
            grade: currentGrade,
            unitNumber: currentExamResultRecord ? currentExamResultRecord.unitNumber : "-",
            unitTitle: currentExamResultRecord ? currentExamResultRecord.unitTitle : "-",
            scoreText: currentExamResultRecord ? `${currentExamResultRecord.score}/${currentExamResultRecord.total} (${currentExamResultRecord.percentage}%)` : "-",
            rating: selectedRating,
            comments: comments
        };

        // Save locally
        const feedbacks = getStoredFeedbacks();
        feedbacks.unshift(feedbackObj);
        saveStoredFeedbacks(feedbacks);

        // Sync to Google Drive / Google Sheet via Web App
        const scriptUrl = getWebAppUrl();
        const payload = {
            action: "save_student_feedback",
            grade: currentGrade,
            spreadsheetId: TARGET_SPREADSHEET_ID,
            driveFileName: "student_feedback_and_suggestions.json",
            timestamp: feedbackObj.timestamp,
            name: feedbackObj.studentName,
            school: feedbackObj.studentSchool,
            year: feedbackObj.year,
            gradeLevel: `${currentGrade} ශ්‍රේණිය`,
            unit: `${feedbackObj.unitNumber} - ${feedbackObj.unitTitle}`,
            score: feedbackObj.scoreText,
            rating: `${selectedRating} / 5 Stars`,
            comments: comments
        };

        try {
            if (scriptUrl) {
                await fetch(scriptUrl, {
                    method: "POST",
                    mode: "no-cors",
                    headers: { "Content-Type": "text/plain;charset=utf-8" },
                    body: JSON.stringify(payload)
                });
            }

            statusBadge.className = "inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg bg-emerald-100 text-emerald-900 border border-emerald-300";
            statusBadge.innerHTML = `<i class="fa-solid fa-circle-check"></i> ඔබගේ අදහස් හා යෝජනා සාර්ථකව Google Drive / Sheet වෙත සුරැකුණි! ස්තූතියි.`;
        } catch (e) {
            console.error("Feedback sync error:", e);
            statusBadge.className = "inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg bg-blue-100 text-blue-900 border border-blue-300";
            statusBadge.innerHTML = `<i class="fa-solid fa-circle-check"></i> ඔබගේ අදහස් පද්ධතිය තුළ සාර්ථකව සුරැකුණි!`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-cloud-arrow-up"></i> අදහස් හා යෝජනා Drive වෙත සුරකින්න`;
        }
    }

    // =========================================================================
    // TEACHER PIN LOGIN & SECURITY (SECURE HASH VERIFICATION)
    // =========================================================================
    function openTeacherLogin() {
        document.getElementById('teacher-pin-input').value = '';
        document.getElementById('teacher-pin-modal').classList.remove('hidden');
        setTimeout(() => document.getElementById('teacher-pin-input').focus(), 100);
    }

    function closeTeacherLogin() {
        document.getElementById('teacher-pin-modal').classList.add('hidden');
    }

    async function verifyTeacherPin() {
        const entered = document.getElementById('teacher-pin-input').value.trim();
        const enteredHash = await sha256Hex(entered);
        const settings = getSettings();
        const activeHash = settings.customPinHash || PIN_SHA256_HASH;

        if (enteredHash === activeHash) {
            closeTeacherLogin();
            openTeacherPanel();
        } else {
            alert("වැරදි රහස් අංකයකි! නැවත උත්සාහ කරන්න.");
        }
    }

    function openTeacherPanel() {
        const settings = getSettings();
        document.getElementById('tp-exam-minutes').value = settings.examMinutes || 60;
        document.getElementById('tp-script-url').value = getWebAppUrl();
        document.getElementById('teacher-panel-modal').classList.remove('hidden');
        switchTeacherTab('results');
        populateTeacherFilterUnits();
        renderTeacherTable();
    }

    function closeTeacherPanel() {
        document.getElementById('teacher-panel-modal').classList.add('hidden');
    }

    function switchTeacherTab(tabName) {
        const resTab = document.getElementById('tp-tab-results');
        const fbTab = document.getElementById('tp-tab-feedbacks');
        const edTab = document.getElementById('tp-tab-editor');

        const resBtn = document.getElementById('tp-tab-btn-results');
        const fbBtn = document.getElementById('tp-tab-btn-feedbacks');
        const edBtn = document.getElementById('tp-tab-btn-editor');

        const activeClass = "px-4 py-2.5 rounded-t-xl font-bold text-xs md:text-sm bg-white text-blue-950 border-t-2 border-x border-slate-300 -mb-px flex items-center gap-2 shadow-sm";
        const inactiveClass = "px-4 py-2.5 rounded-t-xl font-bold text-xs md:text-sm bg-slate-200/80 text-slate-600 hover:bg-white/70 border-t border-x border-transparent flex items-center gap-2 transition";

        resTab.classList.add('hidden');
        fbTab.classList.add('hidden');
        edTab.classList.add('hidden');

        resBtn.className = inactiveClass;
        fbBtn.className = inactiveClass;
        edBtn.className = inactiveClass;

        if (tabName === 'results') {
            resTab.classList.remove('hidden');
            resBtn.className = activeClass;
            renderTeacherTable();
        } else if (tabName === 'feedbacks') {
            fbTab.classList.remove('hidden');
            fbBtn.className = activeClass;
            renderTeacherFeedbacksTable();
        } else if (tabName === 'editor') {
            edTab.classList.remove('hidden');
            edBtn.className = activeClass;
            onEditorGradeChange();
        }
    }

    function saveExamSettings() {
        const mins = parseInt(document.getElementById('tp-exam-minutes').value);
        if (isNaN(mins) || mins < 5 || mins > 180) {
            alert("කරුණාකර මිනිත්තු 5 ත් 180 ත් අතර අගයක් ඇතුළත් කරන්න.");
            return;
        }
        const settings = getSettings();
        settings.examMinutes = mins;
        saveSettingsObj(settings);
        alert(`විභාග කාලය මිනිත්තු ${mins} ලෙස සුරැකුණි.`);
    }

    async function updateTeacherPin() {
        const newPin = document.getElementById('tp-new-pin').value.trim();
        if (newPin.length < 4) {
            alert("රහස් අංකය අවම වශයෙන් අක්ෂර 4 කින් යුක්ත විය යුතුය.");
            return;
        }
        const hash = await sha256Hex(newPin);
        const settings = getSettings();
        settings.customPinHash = hash;
        saveSettingsObj(settings);
        document.getElementById('tp-new-pin').value = '';
        alert("ගුරු පාලන රහස් අංකය සාර්ථකව වෙනස් කරන ලදී!");
    }

    function saveWebAppUrlSetting() {
        const val = document.getElementById('tp-script-url').value.trim();
        if (!val) {
            localStorage.removeItem(STORAGE_SCRIPT_URL_KEY);
            alert("පෙරනිමි Web App URL එක යළි සකසන ලදී.");
            return;
        }
        localStorage.setItem(STORAGE_SCRIPT_URL_KEY, val);
        alert("Google Apps Script Web App URL එක සාර්ථකව සුරැකුණි!");
    }

    function onTeacherFilterGradeChange() {
        populateTeacherFilterUnits();
        renderTeacherTable();
    }

    function populateTeacherFilterUnits() {
        const gradeVal = document.getElementById('tp-filter-grade').value;
        const unitSel = document.getElementById('tp-filter-unit');
        unitSel.innerHTML = '<option value="all">සියලුම ඒකක</option>';

        if (gradeVal === "all") {
            for (let i = 1; i <= 10; i++) unitSel.innerHTML += `<option value="10_${i}">10 ශ්‍රේණිය - ඒකක ${i}</option>`;
            for (let i = 1; i <= 8; i++) unitSel.innerHTML += `<option value="11_${i}">11 ශ්‍රේණිය - ඒකක ${i}</option>`;
        } else {
            const bank = getActiveBank(gradeVal);
            Object.keys(bank).sort((a,b) => Number(a)-Number(b)).forEach(k => {
                unitSel.innerHTML += `<option value="${gradeVal}_${bank[k].id}">${bank[k].number} වන ඒකකය - ${bank[k].title}</option>`;
            });
        }
    }

    function renderTeacherTable() {
        const allResults = getStoredResults();
        const gradeFilter = document.getElementById('tp-filter-grade').value;
        const unitFilter = document.getElementById('tp-filter-unit').value;

        const filtered = allResults.filter(r => {
            if (gradeFilter !== "all" && String(r.gradeLevel) !== gradeFilter) return false;
            if (unitFilter !== "all") {
                const parts = unitFilter.split('_');
                if (String(r.gradeLevel) !== parts[0] || String(r.unitId) !== parts[1]) return false;
            }
            return true;
        });

        document.getElementById('tp-total-students').textContent = filtered.length;
        if (filtered.length > 0) {
            const avg = Math.round(filtered.reduce((acc, cur) => acc + cur.score, 0) / filtered.length);
            const aCount = filtered.filter(r => r.grade === 'A').length;
            const maxScore = Math.max(...filtered.map(r => r.score));
            document.getElementById('tp-avg-score').textContent = `${avg} / 40`;
            document.getElementById('tp-a-count').textContent = aCount;
            document.getElementById('tp-max-score').textContent = maxScore;
        } else {
            document.getElementById('tp-avg-score').textContent = "0 / 40";
            document.getElementById('tp-a-count').textContent = "0";
            document.getElementById('tp-max-score').textContent = "0";
        }

        const tbody = document.getElementById('tp-results-body');
        tbody.innerHTML = '';

        if (filtered.length === 0) {
            tbody.innerHTML = `<tr><td colspan="11" class="p-6 text-center text-slate-400 font-medium">තවමත් ප්‍රතිඵල වාර්තා වී නොමැත.</td></tr>`;
            return;
        }

        filtered.forEach((rec, idx) => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-50";
            tr.innerHTML = `
                <td class="p-3 font-bold text-slate-500">${idx + 1}</td>
                <td class="p-3 font-bold text-slate-800">${rec.name}</td>
                <td class="p-3 text-slate-600">${rec.school}</td>
                <td class="p-3 text-slate-600">${rec.year}</td>
                <td class="p-3 font-bold text-blue-900">${rec.gradeLevel} ශ්‍රේණිය</td>
                <td class="p-3 font-semibold text-slate-700">ඒකක ${rec.unitNumber}</td>
                <td class="p-3 text-center font-extrabold text-slate-800">${rec.score} / ${rec.total}</td>
                <td class="p-3 text-center font-bold text-emerald-700">${rec.percentage}%</td>
                <td class="p-3 text-center"><span class="px-2.5 py-0.5 rounded-full text-xs font-black bg-amber-100 text-amber-900">${rec.grade}</span></td>
                <td class="p-3 text-xs text-slate-500">${rec.timestamp}</td>
                <td class="p-3 text-center space-x-1">
                    <button onclick="inspectStudentRecord(${rec.id})" class="bg-blue-100 hover:bg-blue-200 text-blue-800 px-2.5 py-1 rounded text-xs font-bold">පරීක්ෂා කරන්න</button>
                    <button onclick="deleteSingleResult(${rec.id})" class="bg-rose-100 hover:bg-rose-200 text-rose-800 px-2 py-1 rounded text-xs font-bold"><i class="fa-solid fa-trash"></i></button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    function inspectStudentRecord(recId) {
        const allResults = getStoredResults();
        const rec = allResults.find(r => r.id === recId);
        if (!rec) return;

        const bank = getActiveBank(rec.gradeLevel);
        const unit = bank[rec.unitId];
        const box = document.getElementById('tp-student-detail-box');
        const title = document.getElementById('tp-detail-title');
        const grid = document.getElementById('tp-detail-grid');

        title.textContent = `${rec.name} (${rec.school}) - ${rec.gradeLevel} ශ්‍රේණිය ඒකක ${rec.unitNumber}: ${rec.unitTitle} | ලකුණු: ${rec.score}/${rec.total}`;
        grid.innerHTML = '';

        if (unit) {
            unit.questions.forEach(q => {
                const correct = unit.answerKey[q.id];
                const chosen = rec.answers ? rec.answers[q.id] : null;
                const isOk = chosen === correct;
                const cell = document.createElement('div');
                cell.className = `p-2 rounded border text-center font-bold ${
                    isOk ? 'bg-emerald-100 border-emerald-400 text-emerald-900' : 'bg-rose-100 border-rose-400 text-rose-900'
                }`;
                cell.innerHTML = `<div>ප්‍රශ්න ${q.id}</div><div>${chosen || '-'} / (${correct})</div>`;
                grid.appendChild(cell);
            });
        }

        box.classList.remove('hidden');
        box.scrollIntoView({ behavior: 'smooth' });
    }

    function deleteSingleResult(recId) {
        if (!confirm("මෙම වාර්තාව මකා දැමීමට අවශ්‍යද?")) return;
        const updated = getStoredResults().filter(r => r.id !== recId);
        saveStoredResults(updated);
        renderTeacherTable();
    }

    function clearAllResults() {
        if (!confirm("සියලුම ශිෂ්‍ය ප්‍රතිඵල වාර්තා මකා දැමීමට අවශ්‍යද? මෙය ආපසු හැරවිය නොහැක.")) return;
        localStorage.removeItem(STORAGE_RESULTS_KEY);
        document.getElementById('tp-student-detail-box').classList.add('hidden');
        renderTeacherTable();
    }

    function exportResultsCSV() {
        const allResults = getStoredResults();
        if (allResults.length === 0) {
            alert("බාගත කිරීමට ප්‍රතිඵල වාර්තා නොමැත.");
            return;
        }
        let csv = "\\uFEFFසිසුවාගේ නම,පාසල / පන්තිය,වසර,ශ්‍රේණිය,ඒකකය,ලකුණු,මුළු ලකුණු,ප්‍රතිශතය,සාමාර්ථය,දිනය / වේලාව\\n";
        allResults.forEach(r => {
            csv += `"${r.name}","${r.school}","${r.year}","${r.gradeLevel} ශ්‍රේණිය","${r.unitNumber} - ${r.unitTitle}",${r.score},${r.total},${r.percentage}%,"${r.grade}","${r.timestamp}"\\n`;
        });
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `History_Exam_Results_${new Date().toISOString().slice(0,10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // =========================================================================
    // TEACHER PANEL FEEDBACKS TABLE
    // =========================================================================
    function renderTeacherFeedbacksTable() {
        const feedbacks = getStoredFeedbacks();
        const tbody = document.getElementById('tp-feedbacks-body');
        tbody.innerHTML = '';

        if (feedbacks.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="p-6 text-center text-slate-400 font-medium">සිසුන් විසින් ඉදිරිපත් කළ අදහස් හෝ යෝජනා තවමත් වාර්තා වී නොමැත.</td></tr>`;
            return;
        }

        feedbacks.forEach((fb, idx) => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-50";
            let starsHtml = '';
            for (let s = 1; s <= 5; s++) {
                starsHtml += s <= fb.rating 
                    ? '<i class="fa-solid fa-star text-amber-400"></i>' 
                    : '<i class="fa-solid fa-star text-slate-300"></i>';
            }
            tr.innerHTML = `
                <td class="p-3 font-bold text-slate-500">${idx + 1}</td>
                <td class="p-3 font-bold text-slate-800">${fb.studentName}</td>
                <td class="p-3 text-slate-600">${fb.studentSchool}</td>
                <td class="p-3 text-slate-700 font-semibold">${fb.grade} ශ්‍රේණිය (ඒකක ${fb.unitNumber})</td>
                <td class="p-3 text-center"><div class="inline-flex gap-1 text-sm">${starsHtml}</div></td>
                <td class="p-3 text-slate-800 max-w-xs break-words">${fb.comments}</td>
                <td class="p-3 text-xs text-slate-500">${fb.timestamp}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function exportFeedbacksCSV() {
        const feedbacks = getStoredFeedbacks();
        if (feedbacks.length === 0) {
            alert("බාගත කිරීමට අදහස් වාර්තා නොමැත.");
            return;
        }
        let csv = "\\uFEFFසිසුවාගේ නම,පාසල / පන්තිය,වසර,ශ්‍රේණිය,ඒකකය,ශ්‍රේණිගත කිරීම,අදහස් හා යෝජනා,දිනය / වේලාව\\n";
        feedbacks.forEach(f => {
            csv += `"${f.studentName}","${f.studentSchool}","${f.year}","${f.grade} ශ්‍රේණිය","${f.unitNumber} - ${f.unitTitle}","${f.rating}/5","${f.comments.replace(/"/g, '""')}","${f.timestamp}"\\n`;
        });
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `History_Student_Feedbacks_${new Date().toISOString().slice(0,10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function clearAllFeedbacks() {
        if (!confirm("සියලුම අදහස් හා යෝජනා මැකීමට අවශ්‍යද?")) return;
        localStorage.removeItem(STORAGE_FEEDBACKS_KEY);
        renderTeacherFeedbacksTable();
    }

    // =========================================================================
    // QUESTION BANK EDITOR (Grade 10 & Grade 11)
    // =========================================================================
    function onEditorGradeChange() {
        const grade = document.getElementById('qe-grade-select').value;
        const bank = getActiveBank(grade);
        const unitSel = document.getElementById('qe-unit-select');
        unitSel.innerHTML = '';
        Object.keys(bank).sort((a,b) => Number(a)-Number(b)).forEach(k => {
            unitSel.innerHTML += `<option value="${bank[k].id}">${bank[k].number} වන ඒකකය - ${bank[k].title}</option>`;
        });
        renderQuestionEditor();
    }

    function renderQuestionEditor() {
        const grade = document.getElementById('qe-grade-select').value;
        const unitId = parseInt(document.getElementById('qe-unit-select').value);
        const search = (document.getElementById('qe-search-input').value || '').trim().toLowerCase();
        const bank = getActiveBank(grade);
        const unit = bank[unitId];
        const listEl = document.getElementById('qe-questions-list');
        listEl.innerHTML = '';

        if (!unit) return;

        const filtered = unit.questions.filter(q => {
            if (!search) return true;
            return String(q.id).includes(search) ||
                q.text.toLowerCase().includes(search) ||
                q.options.some(o => o.toLowerCase().includes(search));
        });

        document.getElementById('qe-count-label').textContent = `මුළු ප්‍රශ්න: ${unit.questions.length} (පෙන්වන්නේ: ${filtered.length})`;

        filtered.forEach(q => {
            const correctAns = unit.answerKey[q.id] || 1;
            const card = document.createElement('div');
            card.className = "bg-white border border-slate-300 rounded-xl p-4 shadow-sm space-y-3";

            let optsInputs = '';
            q.options.forEach((opt, idx) => {
                const optNum = idx + 1;
                optsInputs += `
                    <div class="flex items-center gap-2">
                        <input type="radio" name="qe-ans-${grade}-${unitId}-${q.id}" ${correctAns === optNum ? 'checked' : ''}
                            onchange="updateQuestionCorrectAnswer('${grade}', ${unitId}, ${q.id}, ${optNum})"
                            class="w-4 h-4 accent-emerald-600 cursor-pointer" title="නිවැරදි පිළිතුර ලෙස තෝරන්න">
                        <span class="text-xs font-bold text-slate-600">(${optNum})</span>
                        <input type="text" value="${opt.replace(/"/g, '&quot;')}"
                            onchange="updateQuestionOptionText('${grade}', ${unitId}, ${q.id}, ${idx}, this.value)"
                            class="flex-1 px-3 py-1.5 rounded-lg border border-slate-300 text-xs md:text-sm focus:border-blue-600 outline-none">
                    </div>
                `;
            });

            card.innerHTML = `
                <div class="flex items-center justify-between gap-2 border-b pb-2">
                    <span class="bg-blue-900 text-white text-xs font-bold px-2.5 py-1 rounded">ප්‍රශ්න අංක ${String(q.id).padStart(2, '0')}</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-bold text-emerald-700">නිවැරදි පිළිතුර: (${correctAns})</span>
                        <button onclick="deleteQuestionFromUnit('${grade}', ${unitId}, ${q.id})" class="bg-rose-100 hover:bg-rose-200 text-rose-800 px-2.5 py-1 rounded text-xs font-bold">
                            <i class="fa-solid fa-trash"></i> මකන්න
                        </button>
                    </div>
                </div>
                <div>
                    <label class="text-xs font-bold text-slate-600 block mb-1">ප්‍රශ්නය:</label>
                    <textarea rows="2" onchange="updateQuestionText('${grade}', ${unitId}, ${q.id}, this.value)"
                        class="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs md:text-sm font-medium focus:border-blue-600 outline-none">${q.text}</textarea>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                    ${optsInputs}
                </div>
            `;
            listEl.appendChild(card);
        });
    }

    function triggerAutoSaveQuestions(grade) {
        saveCustomQuestionsForGrade(grade);
        const badge = document.getElementById('qe-autosave-badge');
        if (badge) {
            badge.className = "inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold bg-emerald-100 text-emerald-900 border border-emerald-300 mt-4 sm:mt-5";
            badge.innerHTML = `<i class="fa-solid fa-circle-check"></i><span>ස්වයංක්‍රීයව සුරැකුණි</span>`;
        }
    }

    function updateQuestionText(grade, unitId, qId, newText) {
        const bank = getActiveBank(grade);
        const unit = bank[unitId];
        const q = unit.questions.find(item => item.id === qId);
        if (q && newText.trim()) {
            q.text = newText.trim();
            triggerAutoSaveQuestions(grade);
        }
    }

    function updateQuestionOptionText(grade, unitId, qId, optIdx, newText) {
        const bank = getActiveBank(grade);
        const unit = bank[unitId];
        const q = unit.questions.find(item => item.id === qId);
        if (q && newText.trim()) {
            q.options[optIdx] = newText.trim();
            triggerAutoSaveQuestions(grade);
        }
    }

    function updateQuestionCorrectAnswer(grade, unitId, qId, ansNum) {
        const bank = getActiveBank(grade);
        const unit = bank[unitId];
        unit.answerKey[qId] = ansNum;
        triggerAutoSaveQuestions(grade);
        renderQuestionEditor();
    }

    function addNewQuestionToUnit() {
        const grade = document.getElementById('qe-grade-select').value;
        const unitId = parseInt(document.getElementById('qe-unit-select').value);
        const bank = getActiveBank(grade);
        const unit = bank[unitId];
        const nextId = unit.questions.length > 0 ? Math.max(...unit.questions.map(q => q.id)) + 1 : 1;

        unit.questions.push({
            id: nextId,
            text: "නව ප්‍රශ්නය මෙහි ඇතුළත් කරන්න...",
            options: ["පළමු පිළිතුර", "දෙවන පිළිතුර", "තෙවන පිළිතුර", "සිව්වන පිළිතුර"]
        });
        unit.answerKey[nextId] = 1;
        unit.totalQuestions = unit.questions.length;

        triggerAutoSaveQuestions(grade);
        renderQuestionEditor();
    }

    function deleteQuestionFromUnit(grade, unitId, qId) {
        const bank = getActiveBank(grade);
        const unit = bank[unitId];
        if (unit.questions.length <= 1) {
            alert("ඒකකයක අවම වශයෙන් එක් ප්‍රශ්නයක්වත් තිබිය යුතුය.");
            return;
        }
        if (!confirm(`ප්‍රශ්න අංක ${qId} මකා දැමීමට අවශ්‍යද?`)) return;

        const newQuestions = [];
        const newAnswerKey = {};
        let counter = 1;
        unit.questions.forEach(q => {
            if (q.id !== qId) {
                const oldAns = unit.answerKey[q.id] || 1;
                newQuestions.push({ ...q, id: counter });
                newAnswerKey[counter] = oldAns;
                counter++;
            }
        });

        unit.questions = newQuestions;
        unit.answerKey = newAnswerKey;
        unit.totalQuestions = unit.questions.length;

        triggerAutoSaveQuestions(grade);
        renderQuestionEditor();
    }

    function resetUnitQuestionsToDefault() {
        const grade = document.getElementById('qe-grade-select').value;
        const unitId = parseInt(document.getElementById('qe-unit-select').value);
        if (!confirm("මෙම ඒකකයේ ප්‍රශ්න මුල් පැවති තත්ත්වයට පත් කිරීමට අවශ්‍යද?")) return;

        const backup = grade === "11" ? BACKUP_G11 : BACKUP_G10;
        const bank = getActiveBank(grade);
        bank[unitId] = JSON.parse(JSON.stringify(backup[unitId]));

        triggerAutoSaveQuestions(grade);
        renderQuestionEditor();
    }

    async function syncEditedQuestionsToGoogleSheet(showAlertOnSuccess = false) {
        const grade = document.getElementById('qe-grade-select').value;
        const scriptUrl = getWebAppUrl();
        const bank = getActiveBank(grade);

        if (!scriptUrl) {
            if (showAlertOnSuccess) alert("Google Apps Script URL එකක් සකසා නැත.");
            return;
        }

        const payload = {
            action: "save_question_bank",
            grade: grade,
            spreadsheetId: TARGET_SPREADSHEET_ID,
            updatedAt: new Date().toLocaleString('si-LK'),
            questionBank: bank
        };

        try {
            await fetch(scriptUrl, {
                method: "POST",
                mode: "no-cors",
                headers: { "Content-Type": "text/plain;charset=utf-8" },
                body: JSON.stringify(payload)
            });
            if (showAlertOnSuccess) alert(`${grade} ශ්‍රේණියේ ප්‍රශ්න බැංකුව සාර්ථකව Google Drive සහ Sheet වෙත සුරැකුණි!`);
        } catch (e) {
            console.error("Cloud sync error:", e);
            if (showAlertOnSuccess) alert("Cloud වෙත සුරැකීමේදී දෝෂයක් ඇති විය.");
        }
    }

    function exportUpdatedHtmlFile() {
        const docHtml = "<!DOCTYPE html>\\n" + document.documentElement.outerHTML;
        const blob = new Blob([docHtml], { type: "text/html;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `History_Exam_Unified_Grades_10_and_11_${new Date().toISOString().slice(0,10)}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
"""

with open('C:/Users/manpe/.gemini/antigravity/scratch/history_exam/unified_logic.js', 'w', encoding='utf-8') as f:
    f.write(JS_LOGIC)

print("Saved unified_logic.js successfully")
