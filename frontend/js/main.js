// Tab 切换逻辑
function switchTab(index) {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => item.classList.remove('active'));
  navItems[index].classList.add('active');

  const tabPanes = document.querySelectorAll('.tab-pane');
  tabPanes.forEach(pane => pane.classList.remove('active'));
  document.getElementById('tab-' + index).classList.add('active');

  if (index === 2) { initExpandButtons(); }
}

function toggleCard() {
  const flipper = document.getElementById('cardFlipper');
  flipper.classList.toggle('flipped');
}

function openModal() { document.getElementById('confirmModal').style.display = 'flex'; }
function closeModal() { document.getElementById('confirmModal').style.display = 'none'; }
function finalSubmit() { alert('订单已确认完成！'); closeModal(); }

// 超长文字截断检测
function initExpandButtons() {
  const containers = document.querySelectorAll('#tab-2 .shipped-left');
  containers.forEach(container => {
    const title = container.querySelector('.shipped-title');
    const expandBtn = container.querySelector('.expand-list-text');

    if (title && expandBtn) {
      const isExpanded = title.classList.contains('expanded');
      title.classList.remove('expanded');

      if (title.scrollWidth > title.clientWidth) {
        expandBtn.style.display = 'block'; 
        if (isExpanded) {
          title.classList.add('expanded');
          expandBtn.textContent = '收起列表';
        } else {
          expandBtn.textContent = '展开列表';
        }
      } else {
        expandBtn.style.display = 'none';
      }

      if (!expandBtn.dataset.bound) {
        expandBtn.dataset.bound = "true";
        expandBtn.addEventListener('click', function() {
          if (title.classList.contains('expanded')) {
            title.classList.remove('expanded'); 
            expandBtn.textContent = '展开列表';
          } else {
            title.classList.add('expanded'); 
            expandBtn.textContent = '收起列表';
          }
        });
      }
    }
  });
}

window.addEventListener('load', initExpandButtons);
window.addEventListener('resize', initExpandButtons);

/* ================= AI悬浮智能体拖拽、点击、全局失焦 ================= */
const fabMain = document.getElementById('fabMain');
const fabContainer = document.getElementById('fabContainer');

let isDragging = false;
let hasDragged = false; 
let isMouseDownOnFab = false; 
let startX, startY, initialX, initialY;

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

function dragEnd(e) {
  if (!isMouseDownOnFab) return;

  isDragging = false;
  fabMain.style.transition = 'opacity 0.3s ease, transform 0.2s, background 0.4s, box-shadow 0.4s';
  
  if (!hasDragged) {
    fabContainer.classList.toggle('active');
    // 点击后如果有气泡在显示，立马藏起来
    document.getElementById('aiSpeechBubble').classList.remove('show');
  }
  isMouseDownOnFab = false; 
}

if(fabMain) {
    fabMain.addEventListener('mousedown', dragStart);
    fabMain.addEventListener('touchstart', dragStart, { passive: false });
}
document.addEventListener('mousemove', drag, { passive: false });
document.addEventListener('mouseup', dragEnd);
document.addEventListener('touchmove', drag, { passive: false });
document.addEventListener('touchend', dragEnd);

// 全局失焦：点击空白处收起菜单
function closeFabMenuOnOutsideClick(e) {
  if (fabContainer && fabContainer.classList.contains('active') && !fabContainer.contains(e.target)) {
    fabContainer.classList.remove('active');
  }
}
document.addEventListener('mousedown', closeFabMenuOnOutsideClick);
document.addEventListener('touchstart', closeFabMenuOnOutsideClick, { passive: true });

// 点击功能菜单后自动收起
const fabItemsList = document.querySelectorAll('.fab-item');
fabItemsList.forEach(item => {
  item.addEventListener('click', function() {
    setTimeout(() => { fabContainer.classList.remove('active'); }, 100);
  });
});

/* ================= AI自言自语（气泡对话框）逻辑 ================= */
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

const speechBubble = document.getElementById('aiSpeechBubble');

function triggerAiSpeech() {
  // 智能判断：如果主人正在展开菜单，或者正在拖拽我，就乖乖闭嘴不打扰
  if (!fabContainer || !speechBubble) return;
  if (fabContainer.classList.contains('active') || isDragging) return;

  // 随机抽选一句话
  const randomPhrase = aiPhrases[Math.floor(Math.random() * aiPhrases.length)];
  speechBubble.textContent = randomPhrase;
  
  // 显示气泡
  speechBubble.classList.add('show');

  // 4秒后自动消失
  setTimeout(() => {
    speechBubble.classList.remove('show');
  }, 4000);
}

// 刚打开页面 5 秒后，先打个招呼
setTimeout(triggerAiSpeech, 5000);

// 为了方便你预览，设定为每隔 30 秒自言自语一次
setInterval(triggerAiSpeech, 30000);