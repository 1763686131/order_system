/**
 * ========================================================
 * 🤖 NOMI (Xiao Yuan) 悬浮智能体驱动模块 (终极完整版)
 * 包含：拖拽引擎、智能路由权限防误触、双开快捷筛选日历
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

    // ==========================================================
    // 🌟 新增智能微引擎：根据当前活动页面动态控制菜单权限（防误触）
    // ==========================================================
    function updateNomiMenuVisibility() {
        const items = document.querySelectorAll('.fab-item');
        let btnOrder = null;
        let btnMaterial = null;

        // 识别按钮
        items.forEach(item => {
            if (item.textContent.includes('录入订单') || item.textContent.includes('订单信息')) {
                btnOrder = item;
            }
            if (item.textContent.includes('录入原材料') || item.textContent.includes('原材料数据')) {
                btnMaterial = item;
            }
        });

        // 识别当前激活的页面
        let isUncompletedPage = false;
        let isMaterialPage = false;
        const allTabs = document.querySelectorAll('.tab-btn, .nav-link, .tab, .nav-item');
        allTabs.forEach(tab => {
            if (tab.classList.contains('active')) {
                if (tab.textContent.includes('未完成')) {
                    isUncompletedPage = true;
                } else if (tab.textContent.includes('原材料')) {
                    isMaterialPage = true;
                }
            }
        });

        // 动态隐藏/显示逻辑
        if (isUncompletedPage) {
            if (btnOrder) btnOrder.style.display = 'block';
            if (btnMaterial) btnMaterial.style.display = 'none';
        } else if (isMaterialPage) {
            if (btnOrder) btnOrder.style.display = 'none';
            if (btnMaterial) btnMaterial.style.display = 'block';
        } else {
            if (btnOrder) btnOrder.style.display = 'none';
            if (btnMaterial) btnMaterial.style.display = 'none';
        }
    }

    // 监听 PC 端点击事件展开/收起菜单
    fabMain.addEventListener('click', function(e) {
        if (!hasDragged) {
            fabContainer.classList.toggle('active');
            if (fabContainer.classList.contains('active')) {
                updateNomiMenuVisibility();
            }
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
            if (fabContainer.classList.contains('active')) {
                updateNomiMenuVisibility();
            }
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
        if (fabContainer.classList.contains('active') && !fabContainer.contains(e.target)) {
            fabContainer.classList.remove('active');
        }

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
    // 🌟 范围日期筛选交互气泡引擎 (已升级: 纯净大药丸 + 最近一周)
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

        let tipText = filterType === 'material' ? '主人，请选择要查看的【原材料】范围：' : '主人，请选择要查看的【出库单】范围：';

        // 纯净 HTML 骨架，样式全部移交 nomi.css 接管
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

                <div class="nomi-btn-group">
                    <button id="btnNomiPastWeek" class="nomi-btn-secondary">最近一周</button>
                    <button id="btnNomiDateConfirm" class="nomi-btn-confirm">开始筛选</button>
                </div>
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
            const btnPastWeek = document.getElementById('btnNomiPastWeek');
            const dateStart = document.getElementById('nomiFilterStart');
            const dateEnd = document.getElementById('nomiFilterEnd');
            
            // 提炼执行筛选逻辑
            const executeFilter = (startVal, endVal) => {
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
            };

            // 按钮 A：常规确认筛选
            if (btnConfirm && dateStart && dateEnd) {
                btnConfirm.addEventListener('click', () => {
                    const startVal = dateStart.value;
                    const endVal = dateEnd.value;
                    
                    if (!startVal || !endVal) return alert('请完整选择开始和结束日期哦！');
                    if (startVal > endVal) return alert('开始日期不能晚于结束日期！');

                    executeFilter(startVal, endVal);
                });
            }

            // 按钮 B：一键拉取最近一周数据
            if (btnPastWeek) {
                btnPastWeek.addEventListener('click', () => {
                    const formatDate = (d) => {
                        const y = d.getFullYear();
                        const m = String(d.getMonth() + 1).padStart(2, '0');
                        const date = String(d.getDate()).padStart(2, '0');
                        return `${y}-${m}-${date}`;
                    };

                    const today = new Date();
                    const sevenDaysAgo = new Date();
                    sevenDaysAgo.setDate(today.getDate() - 6); // 包含今天一共 7 天

                    const startVal = formatDate(sevenDaysAgo);
                    const endVal = formatDate(today);

                    executeFilter(startVal, endVal);
                });
            }
        }, 50);

        startFilterTimer(); 
    };

    // ==========================================================
    // 💬 6. 定时 AI 语音闲聊气泡
    // ==========================================================
    const aiPhrases = [
        "主人，我叫小圆，是你的智能小助手~", 
        "主人，今天的订单都处理完了吗？", 
        "今天又有什么新订单呀？", 
        "需要我帮你查库存吗？", 
        "闲着也是闲着，看看数据吧！", 
        "随时准备接入 AI 大脑神经~", 
        "累了就休息一下，喝口水吧~", 
        "中固的产品最近卖得很火呢！", 
        "发呆中... 随时可以戳我哦"
    ];

    function triggerAiSpeech() {
        if (hasDragged || isMouseDownOnFab) return;
        
        if (speechBubble.classList.contains('show')) return;

        const randomPhrase = aiPhrases[Math.floor(Math.random() * aiPhrases.length)];
        
        speechBubble.textContent = randomPhrase;
        speechBubble.classList.add('show');
        
        setTimeout(() => { 
            if (speechBubble.textContent === randomPhrase) {
                speechBubble.classList.remove('show'); 
            }
        }, 4000);
    }

    setInterval(triggerAiSpeech, 30000);
});


// 1. 点击小圆菜单中的“搜索订单”唤醒全屏虚化搜索弹窗
document.getElementById('btn-search-order')?.addEventListener('click', function(e) {
    e.stopPropagation();
    
    // 收起小圆菜单
    const fabMenu = document.querySelector('.fab-menu');
    if (fabMenu) fabMenu.classList.remove('active');
    
    // 恢复小圆表情
    const nomiFace = document.querySelector('.nomi-face');
    if (nomiFace) nomiFace.classList.remove('omg');
    
    // 展出全屏虚化搜索弹窗
    const searchModal = document.getElementById('searchOrderModal');
    if (searchModal) {
        searchModal.style.display = 'flex';
        // 自动聚焦到椭圆输入框
        setTimeout(() => {
            document.getElementById('searchInput')?.focus();
        }, 150);
    }
});

// 2. 关闭搜索弹窗
function closeSearchModal() {
    const searchModal = document.getElementById('searchOrderModal');
    if (searchModal) {
        searchModal.style.display = 'none';
        // 清空输入框与搜索结果
        const input = document.getElementById('searchInput');
        if (input) input.value = '';
        const results = document.getElementById('searchResults');
        if (results) results.innerHTML = '';
    }
}

// 3. 点击全屏虚化背景区域自动关闭弹窗
document.getElementById('searchOrderModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeSearchModal();
    }
});

// 4. 按下键盘 ESC 键快捷关闭搜索
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeSearchModal();
    }
});


// ================= 全局辅助函数 =================
// 搜索关键字高级高亮引擎（支持多关键字）
function highlightKeyword(text, keywordString) {
    if (!text || !keywordString) return text;
    const keywords = keywordString.trim().split(/\s+/).filter(k => k);
    if (keywords.length === 0) return text;
    const escapedKeywords = keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const regex = new RegExp(`(${escapedKeywords.join('|')})`, 'gi');
    return text.replace(regex, '<span class="highlight-matched">$1</span>');
}

// 工业级局部复制单号引擎 (保留给左侧物流单号用)
window.copySearchLogisticsNo = function(e, logNo) {
    // ...(这部分保留你之前的代码，或者用下面的简化版)
    e.stopPropagation();
    const btn = e.target;
    const originalText = btn.innerText;
    const showSuccess = () => {
        btn.innerText = '✓ 已复制';
        btn.style.background = '#22c55e'; btn.style.color = '#ffffff'; btn.style.borderColor = '#22c55e';
        setTimeout(() => { btn.innerText = originalText; btn.style.background = ''; btn.style.color = ''; btn.style.borderColor = ''; }, 2000);
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(logNo).then(showSuccess);
};

// 【新增】一键复制完整订单信息引擎
window.copyFullOrderInfo = function(e, encodedText) {
    e.stopPropagation(); // 阻止事件冒泡
    const btn = e.target;
    const originalText = btn.innerText;
    
    // 把转码后的字符串还原成带换行符的原始文本
    const textToCopy = decodeURIComponent(encodedText);

    const showSuccess = () => {
        btn.innerText = '✓ 复制成功';
        btn.style.background = '#3b82f6'; // 复制成功变科技蓝
        btn.style.color = '#ffffff';
        btn.style.borderColor = '#3b82f6';
        setTimeout(() => {
            btn.innerText = originalText;
            btn.style.background = '';
            btn.style.color = '';
            btn.style.borderColor = '';
        }, 2000);
    };

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(textToCopy).then(showSuccess).catch(err => {
            console.error('复制失败:', err);
            alert('复制失败，请手动操作');
        });
    } else {
        // 兼容模式
        let textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        textArea.style.position = "fixed"; textArea.style.opacity = "0";
        document.body.appendChild(textArea); textArea.focus(); textArea.select();
        try { document.execCommand('copy'); showSuccess(); } catch (err) {}
        textArea.remove();
    }
};

// 【新增】专属搜索结果的回单预览引擎（照搬状态 C 逻辑，并优化了索引方式）
window.viewSearchReceipt = function(e, orderId, imgUrl) {
    e.stopPropagation(); // 阻止事件冒泡

    // 1. 获取弹窗实体 (你的出库订单管理弹窗)
    const modal = document.getElementById('shippedOrderActionModal');
    if (!modal) {
        alert('系统错误：未找到回单操作弹窗！');
        return;
    }

    // 获取内部各个节点
    const title = modal.querySelector('.modal-title') || modal.querySelector('h2');
    const subtitle = modal.querySelector('.modal-subtitle') || modal.querySelector('p');
    const auditContent = document.getElementById('auditContent');
    const receiptContent = document.getElementById('receiptContent');

    const btnAuditRevoke = document.getElementById('btnAuditRevoke');
    const btnAuditConfirm = document.getElementById('btnAuditConfirm');
    const btnReceiptUpload = document.getElementById('btnReceiptUpload');
    const btnReceiptDelete = document.getElementById('btnReceiptDelete');
    
    const btnRealDelete = document.getElementById('btnRealDeleteReceipt');
    const btnDownload = document.getElementById('btnDownloadReceipt');

    const preview = document.getElementById('receiptImagePreview');
    const prompt = document.getElementById('receiptUploadPrompt');

    // 2. 完全照搬你的【状态 C：view_receipt】逻辑
    if (title) title.innerText = '回单凭证详情';
    if (subtitle) subtitle.innerText = '您可以查看大图、下载图片或从系统中彻底删除该回单';

    if (auditContent) auditContent.style.display = 'none';
    if (receiptContent) receiptContent.style.display = 'flex';

    if (btnAuditRevoke) btnAuditRevoke.style.display = 'none';
    if (btnAuditConfirm) btnAuditConfirm.style.display = 'none';
    if (btnReceiptUpload) btnReceiptUpload.style.display = 'none';
    if (btnReceiptDelete) btnReceiptDelete.style.display = 'none'; // 隐藏前端清空按钮

    // 唤醒【下载图片】按钮
    if (btnDownload) btnDownload.style.display = 'inline-block';

    // 🛡️ 权限控制：针对“真删除”
    if (typeof hasPerm === 'function' && hasPerm('shipped.delete_receipt')) {
        if (btnRealDelete) btnRealDelete.style.display = 'inline-block';
    } else {
        if (btnRealDelete) btnRealDelete.style.display = 'none';
    }

    // 3. 🎯 核心优化：抛弃 allOrdersLocal 遍历，直接使用传过来的 imgUrl！
    if (imgUrl) {
        if (preview) {
            preview.src = imgUrl;
            preview.style.display = 'block';
        }
        if (prompt) prompt.style.display = 'none';
    }

    // 4. 关键：把当前点击的 orderId 存入全局变量
    // 这是为了让你弹窗里的【彻底删除】和【下载】按钮，知道是在操作哪笔订单
    window.currentActionOrderId = orderId;
    window.currentOrderId = orderId; 

    // 5. 显示弹窗，并强行提升 CSS 层级（防止被全屏搜索框的黑屏遮挡）
    modal.style.display = 'flex';
    modal.style.zIndex = '10000'; 
};

// ================= 全局搜索状态变量 (用于分页引擎) =================
window.globalFilteredSearchData = []; // 存放过滤并排序好的所有数据
window.globalSearchKeyword = '';      // 存放当前搜索的关键字
window.searchRenderIndex = 0;         // 记录当前已经渲染了多少条
const SEARCH_PAGE_SIZE = 10;          // 每次点击加载的数量

// ================= 执行搜索 (主数据获取引擎) =================
function performSearch() {
    const input = document.getElementById('searchInput');
    const keywordString = input ? input.value.trim() : '';
    if (!keywordString) return;
    
    const resultsContainer = document.getElementById('searchResults');
    if (resultsContainer) {
        
        // 1. 渲染优雅的 Loading 动画
        resultsContainer.innerHTML = `
            <div style="text-align: center; padding: 60px 0; color: #ffffff;">
                <div class="search-loading-spinner" style="display:inline-block; width:28px; height:28px; border:3px solid rgba(255,255,255,0.2); border-top-color:#ffffff; border-radius:50%; animation:spin 0.8s linear infinite; margin-bottom:12px;"></div>
                <div style="font-size: 15px; letter-spacing: 1px; opacity: 0.9;">正在检索数据库，请稍候...</div>
            </div>
            <style>@keyframes spin { 100% { transform: rotate(360deg); } }</style>
        `;
        
        // 2. 发起 API 请求获取全量数据
        fetch('/api/orders', {
            method: 'GET',
            headers: {
                'Username': typeof currentUser !== 'undefined' ? String(currentUser.username) : '',
                'Role': typeof currentUser !== 'undefined' ? String(currentUser.role) : ''
            }
        })
        .then(response => response.json())
        .then(res => {
            const dbData = Array.isArray(res) ? res : (res.data || []);

            // 3. 多关键字联合过滤 (AND 匹配)
            const searchTerms = keywordString.toLowerCase().split(/\s+/).filter(k => k);
            
            let filteredData = dbData.filter(item => {
                const combinedCoreString = `${item.order_client || ''} ${item.receiver_name || ''} ${item.receiver_phone || ''} ${item.logistics_no || ''}`.toLowerCase();
                return searchTerms.every(term => combinedCoreString.includes(term));
            });

            // 4. 按时间倒序排序 (最新在最上面)
            filteredData.sort((a, b) => {
                const timeA = new Date(a.shipped_date || a.completed_date || a.date || 0).getTime();
                const timeB = new Date(b.shipped_date || b.completed_date || b.date || 0).getTime();
                return timeB - timeA;
            });

            // 5. 【核心】：将清洗好的数据存入全局变量，将渲染权交接给分页引擎
            window.globalFilteredSearchData = filteredData;
            window.globalSearchKeyword = keywordString;
            window.searchRenderIndex = 0;

            resultsContainer.innerHTML = ''; // 清空 Loading 提示
            
            if (filteredData.length === 0) {
                // 修改为白色字体，加强对比度
                resultsContainer.innerHTML = `
                    <div style="text-align: center; color: #ffffff; margin-top: 60px;">
                        <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.8;">📭</div>
                        <div style="font-size: 18px; font-weight: 500;">未找到与 "<span style="color:#ef4444; font-weight:bold;">${keywordString}</span>" 相关的核心订单信息</div>
                        <div style="font-size: 14px; margin-top: 8px; opacity: 0.6;">(仅支持搜索：订单名、收件人、电话、物流单号)</div>
                    </div>
                `;
            } else {
                // 触发分页渲染引擎的第一次加载
                renderSearchPage();
            }
        })
        .catch(error => {
            console.error('搜索拉取数据库失败:', error);
            resultsContainer.innerHTML = `
                <div style="text-align: center; color: #ef4444; margin-top: 60px;">
                    <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                    <div style="font-size: 18px;">网络异常，无法连接到数据库</div>
                </div>
            `;
        });
    }
}

// ================= 增量分页渲染引擎 (含4行自动分列与三大彩色标签) =================
window.renderSearchPage = function() {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;

    // 1. 移除旧的“加载更多”按钮
    const oldLoadMoreBtn = document.getElementById('loadMoreSearchBtnContainer');
    if (oldLoadMoreBtn) {
        oldLoadMoreBtn.remove();
    }

    const keywordString = window.globalSearchKeyword;
    
    // 2. 切片：从全局数据中切出 10 条
    const dataToRender = window.globalFilteredSearchData.slice(
        window.searchRenderIndex, 
        window.searchRenderIndex + SEARCH_PAGE_SIZE
    );
    
    let htmlString = '';

    // 3. 开始渲染这 10 条卡片
    dataToRender.forEach((item, index) => {
        const titleText = `${item.order_client || '未知订单'} - ${item.receiver_name || '未知收件人'}`;
        const highlightedTitle = highlightKeyword(titleText, keywordString);

        let logisticsHtml = '';
        if (item.logistics_no) {
            const highlightedLogNo = highlightKeyword(item.logistics_no, keywordString);
            logisticsHtml = `
                <div class="logistics-badge">
                    <span class="log-no-text">单号：${highlightedLogNo}</span>
                    <button class="btn-copy-log" onclick="copySearchLogisticsNo(event, '${item.logistics_no}')">复制</button>
                </div>
            `;
        }
        
        // 基础信息：电话与地址
        let infoArr = [];
        if (item.receiver_phone) infoArr.push(`电话：${item.receiver_phone}`);
        if (item.receiver_address) infoArr.push(`地址：${item.receiver_address}`);
        const highlightedInfo = highlightKeyword(infoArr.join(' | '), keywordString);

        // ================= 🎯 亮点 1：三大属性彩色标签组装 =================
        let tagsHtml = '';
        let tagsList = [];
        if (item.goods_weight && item.goods_weight.trim() !== '') {
            const highlightedWeight = highlightKeyword(item.goods_weight, keywordString);
            tagsList.push(`<span class="goods-tag tag-weight">重量/数量：${highlightedWeight}</span>`);
        }
        if (item.goods_quantity && item.goods_quantity.trim() !== '') {
            const highlightedQty = highlightKeyword(item.goods_quantity, keywordString);
            tagsList.push(`<span class="goods-tag tag-quantity">件数：${highlightedQty}</span>`);
        }
        if (item.goods_packaging && item.goods_packaging.trim() !== '') {
            const highlightedPkg = highlightKeyword(item.goods_packaging, keywordString);
            tagsList.push(`<span class="goods-tag tag-packaging">包装：${highlightedPkg}</span>`);
        }
        if (tagsList.length > 0) {
            tagsHtml = `<div class="goods-info-tags">${tagsList.join('')}</div>`;
        }

        // ================= 🎯 亮点 2：货物明细每 4 行自动横向切列 =================
        let goodsColumnsHtml = '';
        if (item.goods_name && item.goods_name.trim() !== '') {
            // 按换行符切分为数组，并过滤掉空行
            const lines = item.goods_name.split('\n').map(l => l.trim()).filter(l => l);
            
            if (lines.length > 0) {
                const chunkSize = 4; // 每列最多 4 行
                const columns = [];
                
                // 每 4 行切片为一列
                for (let i = 0; i < lines.length; i += chunkSize) {
                    columns.push(lines.slice(i, i + chunkSize));
                }

                // 渲染各列
                const colsInnerHtml = columns.map(colLines => {
                    const colContent = colLines.map(line => highlightKeyword(line, keywordString)).join('<br>');
                    return `<div class="goods-column">${colContent}</div>`;
                }).join('');

                goodsColumnsHtml = `
                    <div class="goods-columns-wrapper">
                        <div class="goods-columns-header">货物明细：</div>
                        <div class="goods-columns-flex">
                            ${colsInnerHtml}
                        </div>
                    </div>
                `;
            }
        }

        // 组装左侧内部 HTML
        let leftContentHtml = '';
        if (highlightedInfo) leftContentHtml += `<div style="font-size: 15px; margin-top: 4px;">${highlightedInfo}</div>`;
        if (tagsHtml) leftContentHtml += tagsHtml;             // 渲染彩色标签
        if (goodsColumnsHtml) leftContentHtml += goodsColumnsHtml; // 渲染多列货物

        // 状态与时间映射
        let statusText = "未知状态";
        let statusClass = "status-pending"; 
        let borderColor = "#94a3b8"; 
        let displayDate = item.shipped_date || item.completed_date || item.date || "暂无时间";

        if (item.status === 'shipped' || item.status === 'completed') {
            statusText = item.status === 'shipped' ? "已出库" : "已完成";
            statusClass = "status-completed"; 
            borderColor = "#22c55e"; 
        } else if (item.status === 'pending') {
            statusText = "未完成"; 
            statusClass = "status-pending"; 
            borderColor = "#ef4444"; 
        }

        // 组装剪贴板全量复制模板
        const typeText = (item.type == 1) ? '绝缘订单' : '中固订单';
        const shortGoodsName = (item.goods_name || '').replace(/\n/g, ' ').trim(); 
        
        let clipText = `【${typeText}】\n`;
        clipText += `姓名：${item.receiver_name || ''}\n`;
        clipText += `电话：${item.receiver_phone || ''}\n`;
        clipText += `地址：${item.receiver_address || ''}\n`;
        clipText += `名称：${shortGoodsName}\n`;
        clipText += `重量：${item.goods_weight || ''}\n`;
        clipText += `件数：${item.goods_quantity || ''}\n`;
        clipText += `包装：${item.goods_packaging || ''}\n`;
        clipText += `服务：${item.logistics_service || ''}\n`;
        clipText += `备注：${item.remark || ''}\n`;

        const safeClipText = encodeURIComponent(clipText);

        // 回单按钮判定
        let receiptBtnHtml = '';
        if (item.receipt_img_url && item.receipt_img_url.trim() !== '') {
            receiptBtnHtml = `<button class="btn-action-sm" onclick="viewSearchReceipt(event, ${item.id}, '${item.receipt_img_url}')">回单</button>`;
        }

        const delay = (index % SEARCH_PAGE_SIZE) * 0.05; 
        
        htmlString += `
            <div class="search-result-item" style="animation-delay: ${delay}s; border-left-color: ${borderColor}; align-items: flex-start;">
                <div class="item-left" style="flex: 1; padding-right: 20px;">
                    <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                        <div class="item-title">${highlightedTitle}</div>
                        ${logisticsHtml}
                    </div>
                    <div class="item-subtitle" style="line-height: 1.6;">
                        ${leftContentHtml}
                    </div>
                </div>
                
                <div class="item-right" style="min-width: 220px; display: flex; flex-direction: column; align-items: flex-end; margin-top: 4px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button class="btn-action-sm" onclick="copyFullOrderInfo(event, '${safeClipText}')">复制</button>
                        ${receiptBtnHtml}
                        <span class="item-status ${statusClass}">${statusText}</span>
                    </div>
                    <div class="item-date" style="margin-top: 12px;">时间: ${displayDate}</div>
                </div>
            </div>
        `;
    });

    // 4. 更新渲染索引
    window.searchRenderIndex += dataToRender.length;

    // 5. 判定加载更多按钮
    if (window.searchRenderIndex < window.globalFilteredSearchData.length) {
        const remaining = window.globalFilteredSearchData.length - window.searchRenderIndex;
        htmlString += `
            <div id="loadMoreSearchBtnContainer" style="text-align: center; margin-top: 24px; margin-bottom: 24px;">
                <button onclick="renderSearchPage()" style="background: #f8fafc; border: 1px solid #cbd5e1; color: #3b82f6; padding: 10px 32px; border-radius: 30px; font-size: 15px; font-weight: bold; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.1);" onmouseover="this.style.background='#e2e8f0'" onmouseout="this.style.background='#f8fafc'">
                    ⬇️ 点击加载更多 (还有 ${remaining} 条未展示)
                </button>
            </div>
        `;
    } else {
        htmlString += `
            <div style="text-align: center; color: #ffffff; margin-top: 24px; margin-bottom: 24px; font-size: 14px; opacity: 0.7; letter-spacing: 1px;">
                到底啦！已加载所有 ${window.globalFilteredSearchData.length} 条相关数据...
            </div>
        `;
    }

    resultsContainer.insertAdjacentHTML('beforeend', htmlString);
};