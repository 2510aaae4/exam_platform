// 登入功能
function login() {
    const username = document.getElementById('username').value;
    const formData = new FormData();
    formData.append('username', username);
    
    fetch('/login', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('登入失敗：' + data.message);
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

function selectExam(examId) {
    console.log(`Attempting to load exam: ${examId}`);
    
    // 清除之前的數據
    currentExam = null;
    currentQuestion = 0;
    userAnswers = [];
    userConfidence = [];
    
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
    if (question.image) {
        console.log('Loading image:', question.image);
        const img = document.createElement('img');
        img.src = question.image;
        img.alt = '題目圖片';
        img.onerror = function() {
            console.error('Failed to load image:', this.src);
            this.style.display = 'none';
            imageContainer.innerHTML = '<div class="text-center text-muted">圖片載入失敗</div>';
        };
        imageContainer.innerHTML = '';
        imageContainer.appendChild(img);
        imageContainer.style.display = 'block';
    } else {
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
        alert('沒有選擇試卷');
        return;
    }

    // 檢查是否所有題目都已作答
    const unansweredQuestions = userAnswers.reduce((acc, ans, idx) => {
        if (ans === null) acc.push(idx + 1);
        return acc;
    }, []);

    if (unansweredQuestions.length > 0) {
        const confirm = window.confirm(`第 ${unansweredQuestions.join(', ')} 題尚未作答，確定要提交嗎？`);
        if (!confirm) return;
    }

    const data = {
        exam_id: currentExam.id,
        answers: userAnswers,
        confidence: userConfidence
    };

    fetch('/submit-exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const recordId = data.record_id;
            window.location.href = `/score-result/${recordId}`;
        } else {
            alert('提交失敗：' + (data.message || '未知錯誤'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('提交時發生錯誤');
    });
}
