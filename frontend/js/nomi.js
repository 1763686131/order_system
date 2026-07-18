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

    // 2. 拖拽进行中
    function drag(e) {
        if (!isDragging) return;
        
        let clientX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
        let clientY = e.type === 'touchmove' ? e.touches[0].clientY : e.clientY;
        
        let dx = clientX - startX;
        let dy = clientY - startY;

        if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
            hasDragged = true;
        }

        if (hasDragged) {
            e.preventDefault(); 
            
            let newX = initialX + dx;
            let newY = initialY + dy;
            
            const maxX = window.innerWidth - 60;
            const maxY = window.innerHeight - 60;
            
            newX = Math.max(0, Math.min(newX, maxX));
            newY = Math.max(0, Math.min(newY, maxY));

            fabContainer.style.right = 'auto'; 
            fabContainer.style.bottom = 'auto';
            fabContainer.style.left = newX + 'px';
            fabContainer.style.top = newY + 'px';
        }
    }

    // 3. 拖拽结束 & 点击判定
    function dragEnd(e) {
        if (!isMouseDownOnFab) return;

        isDragging = false;
        fabMain.style.transition = 'opacity 0.3s ease, transform 0.2s, background 0.4s, box-shadow 0.4s';
        
        if (!hasDragged) {
            // 如果没有拖拽，说明是点击事件，切换菜单显示状态
            fabContainer.classList.toggle('active');
            if(speechBubble) speechBubble.classList.remove('show');
        }
        isMouseDownOnFab = false; 
    }

    // 事件绑定
    fabMain.addEventListener('mousedown', dragStart);
    fabMain.addEventListener('touchstart', dragStart, { passive: false });
    
    document.addEventListener('mousemove', drag, { passive: false });
    document.addEventListener('mouseup', dragEnd);
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
        if (!speechBubble) return;
        if (fabContainer.classList.contains('active') || isDragging) return;
        const randomPhrase = aiPhrases[Math.floor(Math.random() * aiPhrases.length)];
        speechBubble.textContent = randomPhrase; 
        speechBubble.classList.add('show');
        setTimeout(() => { speechBubble.classList.remove('show'); }, 4000);
    }
    
    setInterval(triggerAiSpeech, 30000);
});