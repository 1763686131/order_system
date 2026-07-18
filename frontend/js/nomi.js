/**
 * ========================================================
 * 🤖 NOMI (Xiao Yuan) 悬浮智能体驱动模块
 * ========================================================
 * 负责处理悬浮球的物理拖拽、点击展开、失焦隐藏以及定时语音气泡交互。
 * 独立组件，不依赖具体业务数据。
 */

document.addEventListener('DOMContentLoaded', () => {
    const fabMain = document.getElementById('fabMain');
    const fabContainer = document.getElementById('fabContainer');
    const speechBubble = document.getElementById('aiSpeechBubble');
    const fabItemsList = document.querySelectorAll('.fab-item');

    if (!fabMain || !fabContainer) return; // 确保 DOM 存在

    let isDragging = false;
    let hasDragged = false; 
    let isMouseDownOnFab = false; 
    let startX, startY, initialX, initialY;

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
        e.preventDefault(); 
        
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

    // ==========================================================
    // 🔥 新增：移动端专属的“双击”检测逻辑 (其他代码全是你原本的)
    // ==========================================================
    let lastTapTime = 0;
    fabMain.addEventListener('touchend', function(e) {
        if (hasDragged) return; // 如果是拖拽操作，坚决不触发双击
        
        const currentTime = new Date().getTime();
        const tapLength = currentTime - lastTapTime;
        
        // 两次轻触间隔在 350 毫秒以内，判定为双击！
        if (tapLength > 0 && tapLength < 350) {
            fabContainer.classList.toggle('active');
            e.preventDefault(); // 阻止手机浏览器弹出乱七八糟的默认行为
            lastTapTime = 0;    // 触发后重置时间
        } else {
            lastTapTime = currentTime; // 记录第一次点击的时间
        }
    });
    // ==========================================================

    // 监听PC端鼠标拖拽
    fabMain.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag, { passive: false });
    document.addEventListener('mouseup', dragEnd);

    // 监听移动端触摸拖拽
    fabMain.addEventListener('touchstart', dragStart, { passive: false });
    document.addEventListener('touchmove', drag, { passive: false });
    document.addEventListener('touchend', dragEnd);

    // 4. 全局失焦隐藏（点击 NOMI 外的区域收起菜单）
    function closeFabMenuOnOutsideClick(e) {
        if (fabContainer.classList.contains('active') && !fabContainer.contains(e.target)) {
            fabContainer.classList.remove('active');
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

    // 6. 定时 AI 语音气泡
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
        const randomPhrase = aiPhrases[Math.floor(Math.random() * aiPhrases.length)];
        speechBubble.textContent = randomPhrase;
        speechBubble.classList.add('show');
        setTimeout(() => { speechBubble.classList.remove('show'); }, 4000);
    }

    setInterval(triggerAiSpeech, 30000);
});