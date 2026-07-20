/**
 * ========================================================
 * 🤖 NOMI (Xiao Yuan) 悬浮智能体驱动模块 (终极完整版)
 * ========================================================
 */

document.addEventListener('DOMContentLoaded', () => {
    const fabMain = document.getElementById('fabMain');
    const fabContainer = document.getElementById('fabContainer');
    const speechBubble = document.getElementById('aiSpeechBubble');
    const fabItemsList = document.querySelectorAll('.fab-item');

    if (!fabMain || !fabContainer) return; 

    let isDragging = false;
    let hasDragged = false; 
    let isMouseDownOnFab = false; 
    let startX, startY, initialX, initialY;
    
    // 【核心状态】日期筛选自动消失的定时器锁
    let filterTimeoutLock = null;

    // 1. 拖拽开始
    function dragStart(e) {
        if (e.type === 'touchstart') { 
            startX = e.touches[0].clientX; 
            startY = e.touches[0].clientY; 
        } else { 
            startX = e.clientX; 
            startY = e.clientY; 
        }
        initialX = fabContainer.offsetLeft; 
        initialY = fabContainer.offsetTop;
        
        isDragging = true; 
        hasDragged = false; 
        isMouseDownOnFab = true; 
        fabMain.style.transition = 'none'; 
    }

    // 2. 拖拽中
    function drag(e) {
        if (!isDragging || !isMouseDownOnFab) return;
        
        let clientX, clientY;
        if (e.type === 'touchmove') {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }

        let dx = clientX - startX;
        let dy = clientY - startY;

        if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
            hasDragged = true;
        }

        if (hasDragged) {
            e.preventDefault(); 
            let newX = initialX + dx;
            let newY = initialY + dy;
            
            let maxX = window.innerWidth - fabContainer.offsetWidth;
            let maxY = window.innerHeight - fabContainer.offsetHeight;
            
            newX = Math.max(0, Math.min(newX, maxX));
            newY = Math.max(0, Math.min(newY, maxY));

            fabContainer.style.left = newX + 'px';
            fabContainer.style.top = newY + 'px';
            fabContainer.style.right = 'auto';
            fabContainer.style.bottom = 'auto';
        }
    }

    // 3. 拖拽结束
    function dragEnd(e) {
        if (!isDragging) return;
        isDragging = false;
        isMouseDownOnFab = false;
        fabMain.style.transition = 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)';
    }

    // 监听 PC 端点击事件展开/收起菜单
    fabMain.addEventListener('click', function(e) {
        if (!hasDragged) {
            fabContainer.classList.toggle('active');
        }
    });

    // 移动端/触屏端轻触模拟 click
    let lastTapTime = 0;
    fabMain.addEventListener('touchend', function(e) {
        if (hasDragged) return; 
        const currentTime = new Date().getTime();
        const tapLength = currentTime - lastTapTime;
        if (tapLength > 0 && tapLength < 350) {
            fabContainer.classList.toggle('active');
            e.preventDefault();
            lastTapTime = 0;   
        } else {
            lastTapTime = currentTime;
        }
    });

    // 监听鼠标拖拽
    fabMain.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag, { passive: false });
    document.addEventListener('mouseup', dragEnd);

    // 监听触摸拖拽
    fabMain.addEventListener('touchstart', dragStart, { passive: false });
    document.addEventListener('touchmove', drag, { passive: false });
    document.addEventListener('touchend', dragEnd);

    // 4. 全局失焦隐藏
    function closeFabMenuOnOutsideClick(e) {
        // ① NOMI 操作菜单的失焦秒关
        if (fabContainer.classList.contains('active') && !fabContainer.contains(e.target)) {
            fabContainer.classList.remove('active');
        }

        // ② 交互气泡的失焦秒关
        if (speechBubble && speechBubble.classList.contains('show')) {
            if (speechBubble.contains(e.target)) return;
            speechBubble.classList.remove('show');
            if (filterTimeoutLock) {
                clearTimeout(filterTimeoutLock);
                filterTimeoutLock = null;
            }
        }
    }
    document.addEventListener('mousedown', closeFabMenuOnOutsideClick);
    document.addEventListener('touchstart', closeFabMenuOnOutsideClick, { passive: true });

    // 5. 点击子菜单后自动收起
    fabItemsList.forEach(item => {
        item.addEventListener('click', function() { 
            setTimeout(() => { fabContainer.classList.remove('active'); }, 100); 
        });
    });

    // ==========================================================
    // 🌟 范围日期筛选交互气泡引擎
    // ==========================================================
    function startFilterTimer() {
        if (filterTimeoutLock) clearTimeout(filterTimeoutLock);
        filterTimeoutLock = setTimeout(() => {
            speechBubble.classList.remove('show');
        }, 10000); 
    }

    function stopFilterTimer() {
        if (filterTimeoutLock) clearTimeout(filterTimeoutLock);
    }

    window.triggerDateFilterSpeech = function(filterType = 'shipped') {
        if (!speechBubble) return;

        let tipText = filterType === 'material' ? '主人，请选择要查看的【原材料】记录范围：' : '主人，请选择要查看的【出库单】范围：';

        // 🌟 核心修改区：纯净版 HTML 骨架，全面对接 nomi.css 的横向全圆角样式
        speechBubble.innerHTML = `
            <div id="nomiFilterArea" class="nomi-filter-area">
                <span class="nomi-filter-title">${tipText}</span>
                
                <div class="nomi-date-group">
                    <div class="nomi-date-pill">
                        <span class="nomi-date-label">从</span>
                        <input type="date" id="nomiFilterStart" class="nomi-date-input">
                    </div>
                    
                    <div class="nomi-date-pill">
                        <span class="nomi-date-label">至</span>
                        <input type="date" id="nomiFilterEnd" class="nomi-date-input">
                    </div>
                </div>

                <button id="btnNomiDateConfirm" class="nomi-btn-confirm">开始筛选</button>
            </div>
        `;
        
        speechBubble.classList.add('show');

        const filterArea = document.getElementById('nomiFilterArea');
        if (filterArea) {
            filterArea.addEventListener('mouseenter', stopFilterTimer);
            filterArea.addEventListener('mouseleave', startFilterTimer);
            filterArea.addEventListener('touchstart', stopFilterTimer, { passive: true });
            filterArea.addEventListener('touchend', startFilterTimer, { passive: true });
        }

        setTimeout(() => {
            const btnConfirm = document.getElementById('btnNomiDateConfirm');
            const dateStart = document.getElementById('nomiFilterStart');
            const dateEnd = document.getElementById('nomiFilterEnd');
            
            if (btnConfirm && dateStart && dateEnd) {
                btnConfirm.addEventListener('click', () => {
                    const startVal = dateStart.value;
                    const endVal = dateEnd.value;
                    
                    if (!startVal || !endVal) return alert('请完整选择开始和结束日期哦！');
                    if (startVal > endVal) return alert('开始日期不能晚于结束日期！');

                    if (filterType === 'material') {
                        if (typeof window.executeMaterialDateFilter === 'function') {
                            window.executeMaterialDateFilter(startVal, endVal);
                        }
                    } else {
                        if (typeof window.executeShippedDateFilter === 'function') {
                            window.executeShippedDateFilter(startVal, endVal);
                        }
                    }
                    
                    speechBubble.classList.remove('show');
                    stopFilterTimer();
                });
            }
        }, 50);

        startFilterTimer(); 
    };

    // ==========================================================
    // 💬 6. 定时 AI 语音闲聊气泡 (完美修复哑巴 BUG)
    // ==========================================================
    const aiPhrases = [
        "主人，我叫小圆，是你的智能小助手~", 
        "主人，今天的订单都处理完了吗？", 
        "今天又有什么新订单呀？", 
        "需要我帮你查库存吗？", 
        "闲着也是闲着，看看数据吧！", 
        "随时准备接入 AI 大脑神经~", 
        "中固的产品最近卖得很火呢！", 
        "发呆中... 随时可以戳我哦"
    ];

    function triggerAiSpeech() {
        if (hasDragged || isMouseDownOnFab) return;
        
        // 🔥 修复点 1：只要气泡现在是“显示”状态（无论是在选日期，还是正在说话），都不准打扰
        if (speechBubble.classList.contains('show')) return;

        const randomPhrase = aiPhrases[Math.floor(Math.random() * aiPhrases.length)];
        
        // 🔥 修复点 2：直接用文字覆盖掉原本气泡里残留的隐藏 HTML（清除旧表单），彻底杜绝假死
        speechBubble.textContent = randomPhrase;
        speechBubble.classList.add('show');
        
        setTimeout(() => { 
            // 🔥 修复点 3：过了 4 秒后，如果气泡里的内容还是这句话（说明中途主人没有点开表单），才自动收起它
            if (speechBubble.textContent === randomPhrase) {
                speechBubble.classList.remove('show'); 
            }
        }, 4000);
    }

    setInterval(triggerAiSpeech, 30000);
});