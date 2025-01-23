// 登入功能
function login() {
    const username = document.getElementById('username').value;
    
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${encodeURIComponent(username)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/';
        } else {
            alert(data.message || '登入失敗');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('登入時發生錯誤');
    });
}

// 檢查登入狀態
window.onload = function() {
    const username = localStorage.getItem('username');
    if (username) {
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('userInfo').style.display = 'block';
        document.getElementById('userDisplay').textContent = username;
    }
}

// 模擬作題相關功能
let currentExam = null;
let currentQuestion = 0;
let userAnswers = [];
let userConfidence = [];
let startTime = null;
let timerInterval = null;
let examDuration = 0;

// 開始計時器
function startTimer() {
    startTime = new Date();
    timerInterval = setInterval(updateTimer, 1000);
}

// 更新計時器顯示
function updateTimer() {
    if (!startTime) return;
    
    const now = new Date();
    const diff = Math.floor((now - startTime) / 1000);
    examDuration = diff;
    
    const hours = Math.floor(diff / 3600);
    const minutes = Math.floor((diff % 3600) / 60);
    const seconds = diff % 60;
    
    const timerDisplay = document.getElementById('timer');
    timerDisplay.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

// 停止計時器
function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function selectExam(examId) {
    console.log(`Attempting to load exam: ${examId}`);
    
    // 清除之前的數據
    currentExam = null;
    currentQuestion = 0;
    userAnswers = [];
    userConfidence = [];
    
    // 重置計時器
    if (timerInterval) {
        stopTimer();
    }
    startTimer();
    
    // 清除顯示
    document.getElementById('questionContent').innerHTML = '';
    document.getElementById('options').innerHTML = '';
    document.getElementById('questionImage').innerHTML = '';
    document.getElementById('questionSelector').innerHTML = '';
    
    fetch(`/load-exam/${examId}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('Response:', response);
        return response.json().then(data => {
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            return data;
        });
    })
    .then(data => {
        console.log('Received data:', data);
        
        if (!data.success) {
            throw new Error(data.error || '無法載入試卷，請稍後再試');
        }
        
        if (!data.questions || !Array.isArray(data.questions) || data.questions.length === 0) {
            throw new Error('試卷格式錯誤或內容為空');
        }
        
        console.log(`Successfully loaded exam with ${data.questions.length} questions`);
        
        currentExam = {
            id: examId,
            questions: data.questions
        };
        currentQuestion = 0;
        userAnswers = new Array(data.questions.length).fill(null);
        userConfidence = new Array(data.questions.length).fill(null);
        
        // 初始化題號選擇器
        const selector = document.getElementById('questionSelector');
        selector.innerHTML = '';
        for (let i = 0; i < data.questions.length; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `第 ${i + 1} 題`;
            selector.appendChild(option);
        }
        
        showQuestion();
        
        // 關閉模態框
        const modal = bootstrap.Modal.getInstance(document.getElementById('examSelector'));
        if (modal) {
            modal.hide();
        }
    })
    .catch(error => {
        console.error('Error in selectExam:', error);
        alert(error.message || '載入試卷時發生錯誤');
        
        // 重新顯示模態框
        const modal = new bootstrap.Modal(document.getElementById('examSelector'));
        modal.show();
    });
}

function showQuestion() {
    if (!currentExam || !currentExam.questions || currentQuestion >= currentExam.questions.length) {
        console.error('Invalid exam state:', { currentExam, currentQuestion });
        return;
    }
    
    const question = currentExam.questions[currentQuestion];
    console.log('Showing question:', question);
    
    // 更新題號
    document.getElementById('questionNumber').textContent = `第 ${currentQuestion + 1} 題`;
    
    // 顯示題目內容
    const contentElement = document.getElementById('questionContent');
    contentElement.innerHTML = question.content || '題目內容載入錯誤';
    
    // 顯示選項
    const optionsContainer = document.getElementById('options');
    optionsContainer.innerHTML = '';
    
    if (Array.isArray(question.options)) {
        question.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.className = `btn option-btn ${userAnswers[currentQuestion] === index ? 'selected' : ''}`;
            button.textContent = option;
            button.onclick = () => selectAnswer(index);
            optionsContainer.appendChild(button);
        });
    }
    
    // 顯示圖片
    const imageContainer = document.getElementById('questionImage');
    imageContainer.innerHTML = ''; // 清空容器
    
    if (question.image) {
        console.log('Question has image:', question.image);
        const img = document.createElement('img');
        img.src = question.image;
        img.alt = `第 ${question.number} 題圖片`;
        img.className = 'img-fluid'; // 使圖片響應式
        
        // 添加載入事件處理
        img.onload = function() {
            console.log('Image loaded successfully:', question.image);
            imageContainer.style.display = 'block';
        };
        
        img.onerror = function() {
            console.error('Failed to load image:', question.image);
            this.style.display = 'none';
            imageContainer.innerHTML = `
                <div class="alert alert-warning">
                    圖片載入失敗 (${question.number}.png)
                    <br>
                    路徑: ${question.image}
                </div>`;
        };
        
        imageContainer.appendChild(img);
    } else {
        console.log('No image for question:', question.number);
        imageContainer.style.display = 'none';
    }
    
    // 更新題目選單
    const selector = document.getElementById('questionSelector');
    if (selector) {
        selector.value = currentQuestion;
    }
    
    // 更新把握度按鈕狀態
    updateConfidenceButtons();
}

function selectAnswer(answerIndex) {
    userAnswers[currentQuestion] = answerIndex;
    
    // 更新所有選項按鈕的樣式
    const buttons = document.getElementById('options').getElementsByTagName('button');
    Array.from(buttons).forEach((button, index) => {
        button.className = `btn option-btn ${index === answerIndex ? 'selected' : ''}`;
    });
}

function nextQuestion() {
    if (!currentExam || currentQuestion >= currentExam.questions.length - 1) return;
    currentQuestion++;
    showQuestion();
}

function previousQuestion() {
    if (!currentExam || currentQuestion <= 0) return;
    currentQuestion--;
    showQuestion();
}

// 更新題號選擇器的事件處理
document.getElementById('questionSelector')?.addEventListener('change', function() {
    currentQuestion = parseInt(this.value);
    showQuestion();
});

function setConfidence(level) {
    userConfidence[currentQuestion] = level;
    
    // 更新按鈕樣式
    document.querySelectorAll('.confidence-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.classList.contains(`confidence-${level}`)) {
            btn.classList.add('active');
        }
    });
}

function updateConfidenceButtons() {
    const currentLevel = userConfidence[currentQuestion];
    document.querySelectorAll('.confidence-btn').forEach(btn => {
        btn.classList.remove('active');
        if (currentLevel && btn.classList.contains(`confidence-${currentLevel}`)) {
            btn.classList.add('active');
        }
    });
}

function submitExam() {
    if (!currentExam) {
        alert('請先選擇試卷');
        return;
    }

    // 檢查是否有未作答的題目
    const unansweredQuestions = userAnswers.map((ans, idx) => ans === null ? idx + 1 : null).filter(q => q !== null);
    if (unansweredQuestions.length > 0) {
        const confirm = window.confirm(`第 ${unansweredQuestions.join(', ')} 題尚未作答，確定要交卷嗎？`);
        if (!confirm) {
            return;
        }
    }

    // 停止計時器
    stopTimer();

    // 準備提交數據
    const data = {
        examId: currentExam.id,
        answers: userAnswers,
        confidence: userConfidence.length > 0 ? userConfidence : null,  // 如果沒有設置把握度，傳送 null
        examDuration: examDuration
    };

    console.log('Submitting exam data:', data);  

    fetch('/submit-exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Server response:', data);  
        if (data.success) {
            window.location.href = `/score-result/${data.recordId}`;
        } else {
            alert('提交失敗：' + (data.error || '未知錯誤'));
            // 如果提交失敗，繼續計時
            startTimer();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('提交時發生錯誤');
        // 如果提交失敗，繼續計時
        startTimer();
    });
}
