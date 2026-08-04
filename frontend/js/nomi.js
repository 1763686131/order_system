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

// ================= 执行搜索 (带右侧操作矩阵与回单智能显隐) =================
function performSearch() {
    const input = document.getElementById('searchInput');
    const keywordString = input ? input.value.trim() : '';
    if (!keywordString) return;
    
    const resultsContainer = document.getElementById('searchResults');
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
        
        // 模拟数据库请求延迟
        setTimeout(() => {
            // 补充了 receipt_img_url 字段的模拟数据
            const dbData = [
                {
                    "id": 7,
                    "status": "shipped",
                    "type": 0,
                    "shipped_date": "2026-07-20 16:58",
                    "logistics_no": "123456",
                    "order_client": "万可订单",
                    "receiver_name": "黄叶",
                    "receiver_phone": "19016926866",
                    "receiver_address": "湖北省黄冈市黄州区禹王街道桓武路16号",
                    "goods_name": "阻燃剂  12450kg\n阻燃剂  12450kg\n阻燃剂  12450kg",
                    "goods_weight": "100kg",
                    "goods_quantity": "20件",
                    "goods_packaging": "桶装",
                    "logistics_service": "送货上门+回单拍照回传",
                    "remark": "无",
                    "receipt_img_url": "" // 模拟没有回单数据（空值）
                },
                {
                    "id": 8,
                    "status": "pending",
                    "type": 0,
                    "date": "2026-08-04 09:12", 
                    "logistics_no": "", 
                    "order_client": "中固测试单",
                    "receiver_name": "张老板",
                    "receiver_phone": "13800138000",
                    "receiver_address": "广东省深圳市南山区",
                    "goods_name": "绝缘体 200件\n耗材配件 50件",
                    "goods_weight": "50kg",
                    "goods_quantity": "5件",
                    "goods_packaging": "木箱",
                    "logistics_service": "物流自提",
                    "remark": "",
                    "receipt_img_url": null // 模拟没有回单数据（null）
                },
                {
                    "id": 28,
                    "status": "shipped",
                    "type": 1,
                    "date": "2026-07-23 09:29",
                    "completed_date": "2026-08-04 11:41",
                    "shipped_date": "2026-08-04 11:41",
                    "logistics_no": "三志物流-4444444",
                    "order_client": "张三",
                    "receiver_name": "李四",
                    "receiver_phone": "18888888888",
                    "receiver_address": "北京市东城区东长安街天安门广场",
                    "goods_name": "棒棒糖",
                    "goods_weight": "10kg",
                    "goods_quantity": "1件",
                    "goods_packaging": "桶装",
                    "logistics_service": "送货上门+回单拍照回传",
                    "remark": "加急",
                    "receipt_img_url": "/uploads/2026-08/张三订单_李四_2026-08-04_BF6A.jpg" // 模拟存在回单图片
                }
            ];

            const searchTerms = keywordString.toLowerCase().split(/\s+/).filter(k => k);
            
            const filteredData = dbData.filter(item => {
                const combinedCoreString = `${item.order_client || ''} ${item.receiver_name || ''} ${item.receiver_phone || ''} ${item.logistics_no || ''}`.toLowerCase();
                return searchTerms.every(term => combinedCoreString.includes(term));
            });

            let htmlString = '';
            
            if (filteredData.length === 0) {
                htmlString = `
                    <div style="text-align: center; color: #94a3b8; margin-top: 60px;">
                        <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;">📭</div>
                        <div style="font-size: 18px;">未找到与 "<span style="color:#ef4444">${keywordString}</span>" 相关的核心订单信息</div>
                    </div>
                `;
            } else {
                filteredData.forEach((item, index) => {
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
                    
                    let infoArr = [];
                    if (item.receiver_phone) infoArr.push(`电话：${item.receiver_phone}`);
                    if (item.receiver_address) infoArr.push(`地址：${item.receiver_address}`);
                    const highlightedInfo = highlightKeyword(infoArr.join(' | '), keywordString);

                    let goodsText = item.goods_name ? `货物明细：\n${item.goods_name.trim()}` : '';
                    const highlightedGoods = highlightKeyword(goodsText, keywordString).replace(/\n/g, '<br>');

                    let leftContentHtml = '';
                    if (highlightedInfo) leftContentHtml += `<div style="font-size: 15px; margin-top: 4px;">${highlightedInfo}</div>`;
                    if (highlightedGoods) leftContentHtml += `<div style="margin-top: 10px; padding: 10px 14px; background: rgba(241, 245, 249, 0.8); border-radius: 8px; border: 1px solid #e2e8f0; color: #475569; font-size: 14.5px;">${highlightedGoods}</div>`;
                    
                    let statusText = "未知状态";
                    let statusClass = "status-pending"; 
                    let borderColor = "#94a3b8"; 
                    let displayDate = item.shipped_date || item.completed_date || item.date || "暂无时间";

                    if (item.status === 'shipped' || item.status === 'completed') {
                        statusText = item.status === 'shipped' ? "已出库" : "已完成";
                        statusClass = "status-completed"; borderColor = "#22c55e"; 
                    } else if (item.status === 'pending') {
                        statusText = "未完成"; statusClass = "status-pending"; borderColor = "#ef4444"; 
                    }

                    // 组装全量复制模板
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

                    // ================= 亮点：回单按钮智能判定 =================
                    let receiptBtnHtml = '';
                    // 只有当 receipt_img_url 存在且不为空字符串时，才渲染回单按钮
                    if (item.receipt_img_url && item.receipt_img_url.trim() !== '') {
                        receiptBtnHtml = `<button class="btn-action-sm" onclick="event.stopPropagation(); alert('唤起回单预览：${item.receipt_img_url}')">回单</button>`;
                    }

                    const delay = (index + 1) * 0.1;
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
                                    ${receiptBtnHtml} <span class="item-status ${statusClass}" style="margin-left: 4px;">${statusText}</span>
                                </div>
                                <div class="item-date" style="margin-top: 12px;">时间: ${displayDate}</div>
                            </div>
                        </div>
                    `;
                });
                
                htmlString += `
                    <div style="text-align: center; color: #94a3b8; margin-top: 20px; font-size: 14px;">
                        没有更多数据了...
                    </div>
                `;
            }
            resultsContainer.innerHTML = htmlString;
        }, 300);
    }
}