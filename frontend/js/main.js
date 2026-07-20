/* ========================================================
 * 🚀 核心运行配置与安全鉴权体系
 * ======================================================== */
const API_BASE = '/api';
let currentUser = { username: '', name: '', role: '', permissions: [] }; 
let allOrdersLocal = []; 
let currentTab = 0; 
let activeKeyboardTargetId = 'materialInputUse';

// 【核心状态】存储当前被小圆筛选的日期范围
let nomiActiveFilterStart = null; 
let nomiActiveFilterEnd = null;

let nomiMaterialFilterStart = null;
let nomiMaterialFilterEnd = null;

function getRoleName(role) {
    const maps = { 'super_admin': '超级管理员', 'admin': '管理员', 'employee': '员工', 'operator': '员工' };
    return maps[role] || role;
}

function hasPerm(permKey) {
    if (currentUser.role === 'super_admin') return true;
    return currentUser.permissions && currentUser.permissions.includes(permKey);
}

function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Username': String(currentUser.username),
        'Role': String(currentUser.role)
    };
}

/* ========================================================
 * 🤖 权限引擎与基础交互 (UI级别动态屏蔽)
 * ======================================================== */
function renderUI() {
    const loginSection = document.getElementById('loginSection');
    const mainSection = document.getElementById('mainSection');
    const fabContainer = document.getElementById('fabContainer');
    
    if (!currentUser.username) {
        loginSection.classList.remove('hidden');
        mainSection.style.display = 'none';
        if(fabContainer) fabContainer.style.display = 'none';
        return;
    }

    loginSection.classList.add('hidden');
    mainSection.style.display = 'block';
    if(fabContainer) fabContainer.style.display = 'block';

    const btnOpenViewUser = document.getElementById('btnOpenViewUser');
    const fabAddOrder = document.getElementById('fabAddOrder');
    const fabAddMaterial = document.getElementById('fabAddMaterial');

    if (hasPerm('system.user_manage')) btnOpenViewUser.style.display = 'block';
    else btnOpenViewUser.style.display = 'none';

    if (hasPerm('pending.add')) fabAddOrder.style.display = 'block';
    else fabAddOrder.style.display = 'none';

    if (hasPerm('material.add')) fabAddMaterial.style.display = 'block';
    else fabAddMaterial.style.display = 'none';
}

async function handleLogin() {
    const usernameInput = document.getElementById('loginUsername').value.trim();
    const passwordInput = document.getElementById('loginPassword').value.trim();
    if (!usernameInput || !passwordInput) return alert('请填入账号密码！');

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: usernameInput, password: passwordInput })
        });
        const resData = await response.json();
        if (response.ok && resData.success) {
            currentUser = resData.user;
            if (!currentUser.permissions) currentUser.permissions = [];
            localStorage.setItem('local_user', JSON.stringify(currentUser));
            
            document.querySelectorAll('.tab-pane').forEach(el => el.dataset.hash = '');
            
            renderUI();
            switchTab(0); 
            
            setTimeout(() => {
                const speechBubble = document.getElementById('aiSpeechBubble');
                if(speechBubble) {
                    speechBubble.textContent = `欢迎回来，${currentUser.name || currentUser.username} 主人！`;
                    speechBubble.classList.add('show');
                    setTimeout(() => speechBubble.classList.remove('show'), 4000);
                }
            }, 1000);
        } else { alert(resData.message || '凭证错误，登录失败'); }
    } catch (error) { alert('本地服务端连接失败，请检查系统。'); }
}

function handleLogout() {
    currentUser = { username: '', name: '', role: '', permissions: [] };
    localStorage.removeItem('local_user');
    window.location.reload();
}

/* ========================================================
 * 📦 业务功能整合：动态数据渲染与卡片智能裂变引擎
 * ======================================================== */
async function fetchOrders() {
    if (currentTab !== 0 && currentTab !== 1 && currentTab !== 2) return; 

    try {
        const response = await fetch(`${API_BASE}/orders`, { method: 'GET', headers: getHeaders() });
        const serverOrders = await response.json();
        allOrdersLocal = serverOrders;
        
        const confirmModal = document.getElementById('confirmModal');
        const shipOrderModal = document.getElementById('shipOrderModal');
        if ((confirmModal && confirmModal.style.display === 'flex') || (shipOrderModal && shipOrderModal.style.display === 'flex')) return;

        const targetContainer = document.getElementById(`tab-${currentTab}`);

        if (currentTab === 2) {
            let shippedOrders = serverOrders.filter(o => o.status === 'shipped');
            
            // 🔥 【核心范围过滤逻辑】：有范围则用范围，没范围则默认展示最近三天
            if (nomiActiveFilterStart && nomiActiveFilterEnd) {
                let startT = new Date(nomiActiveFilterStart.replace(/-/g, '/')).getTime();
                let endT = new Date(nomiActiveFilterEnd.replace(/-/g, '/')).getTime() + 86400000 - 1; 
                
                shippedOrders = shippedOrders.filter(o => {
                    let dateStr = o.shipped_date || o.completed_date || '';
                    if (!dateStr) return false;
                    let t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime();
                    return t >= startT && t <= endT;
                });
            } else {
                const now = new Date();
                const threeDaysAgo = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 2).getTime(); 
                
                shippedOrders = shippedOrders.filter(o => {
                    let dateStr = o.shipped_date || o.completed_date || '';
                    if (!dateStr) return false;
                    let t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime();
                    return t >= threeDaysAgo;
                });
            }

            const currentDataHash = JSON.stringify(shippedOrders) + "_" + nomiActiveFilterStart + "_" + nomiActiveFilterEnd;
            if (targetContainer.dataset.hash === currentDataHash) return; 
            targetContainer.dataset.hash = currentDataHash;

            if (shippedOrders.length === 0) {
                let msg = nomiActiveFilterStart ? `没有找到 ${nomiActiveFilterStart} 到 ${nomiActiveFilterEnd} 的出库记录` : `最近 3 天内暂无任何已出库的物流记录`;
                targetContainer.innerHTML = `<div style="color: #999; width:100%; text-align:center; padding:60px 20px; font-size:16px;">${msg}</div>`;
                return;
            }
            
            let groups = {};
            shippedOrders.forEach(o => {
                let day = o.shipped_date ? o.shipped_date.substring(0, 10) : (o.completed_date ? o.completed_date.substring(0, 10) : '未知日期');
                if (!groups[day]) groups[day] = []; groups[day].push(o);
            });
            
            let tHtml = '<div class="timeline-container">';
            
            // 彻底移除了“清除筛选”按钮的代码，刷新即恢复默认！

            // 🔥 完美修复：恢复按日期分组的朋友圈时间线渲染逻辑
            Object.keys(groups).sort((a, b) => b.localeCompare(a)).forEach(date => {
                tHtml += `<div class="timeline-group"><div class="timeline-date">${date}</div><div class="shipped-grid">`;
                
                groups[date].forEach(o => {
                    let isEmployee = currentUser.role === 'employee' || currentUser.role === 'operator';
                    let typeText = o.type == 1 ? '绝缘订单' : '中固订单';
                    let tagsHtml = '';
                    if (o.goods_packaging) tagsHtml += `<div class="s-tag s-tag-purple">包装:${o.goods_packaging}</div>`;
                    if (o.goods_weight) tagsHtml += `<div class="s-tag s-tag-cyan">货物总重量:${o.goods_weight}</div>`;
                    if (o.goods_quantity) tagsHtml += `<div class="s-tag s-tag-green">件数:${o.goods_quantity}</div>`;
                    
                    let detailBtnHtml = '';
                    if (hasPerm('shipped.detail')) detailBtnHtml = `<div class="s-detail-btn" onclick="openEditOrderModal(${o.id})">详情</div>`;
                    
                    tHtml += `
                    <div class="shipped-card">
                        <div class="ribbon">已出库</div>
                        <div class="shipped-left">
                            <div class="shipped-title">${o.goods_name || '无货物名称'}</div>
                            <div class="expand-list-text">展开列表</div>
                            <div class="s-tags-wrapper">${tagsHtml}</div>
                            ${o.remark ? `<div class="s-tags-wrapper"><div class="s-tag s-tag-pink">备注信息:${o.remark}</div></div>` : ''}
                            <div class="s-tags-wrapper">
                                <div class="s-tag" style="background:#f0f5ff; color:#2f54eb; border:1px solid #adc6ff;">方式: ${o.logistics_type || '未登记'}</div>
                                <div class="s-tag s-tag-pink" style="background:#e6f7ff; color:#1890ff; border:1px solid #b7e1ff;">单号/凭证: ${o.logistics_no || '暂无记录'}</div>
                            </div>
                            <div class="shipped-bottom">
                                <div><div class="s-time-label">出库发货时间</div><div class="s-time-value">${o.shipped_date || o.completed_date || '未知'}</div></div>
                                ${detailBtnHtml}
                            </div>
                        </div>
                        <div class="shipped-right">
                            <div class="s-sub-title">${typeText}</div><div class="s-main-title">${o.order_client || '未命名'}</div>
                            <div class="s-info-list">
                                <div>收货姓名：${o.receiver_name || '未填'}</div>
                                <div>联系电话：${isEmployee ? '***' : (o.receiver_phone || '未填')}</div>
                                <div style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;" title="${o.receiver_address || ''}">收货地址：${o.receiver_address || '未填'}</div>
                            </div>
                        </div>
                    </div>`;
                });
                
                tHtml += `</div></div>`;
            });
            
            tHtml += '</div>';
            targetContainer.innerHTML = tHtml;
            setTimeout(initExpandButtons, 50); 
            return;
        }

        let targetStatus = (currentTab === 1) ? 'completed' : 'pending';
        let filteredOrders = serverOrders.filter(o => o.status === 'completed' || o.status === 'pending');
        let displayedOrders = serverOrders.filter(o => o.status === targetStatus);

        if (targetStatus === 'completed') displayedOrders.sort((a, b) => (b.completed_date || '').localeCompare(a.completed_date || ''));
        else displayedOrders.sort((a, b) => (b.date || '').localeCompare(a.date || ''));

        const currentDataHash = JSON.stringify(displayedOrders);
        if (targetContainer.dataset.hash === currentDataHash) return; 
        targetContainer.dataset.hash = currentDataHash;

        if (displayedOrders.length === 0) {
            targetContainer.innerHTML = `<div style="color: #999; width:100%; text-align:center; padding:60px 20px; font-size:16px;">当前列表下无任何订单单据记录</div>`;
            return;
        }

        let html = '';
        let isMobile = window.innerWidth <= 768; 

        displayedOrders.forEach(o => {
            let isEmployee = currentUser.role === 'employee' || currentUser.role === 'operator';
            let typeName = o.type == 1 ? '绝缘订单' : '中固订单';
            let goodsLines = (o.goods_name || '').split('\n').filter(l => l.trim() !== '');

            let chunks = [];
            if (isMobile) {
                chunks = [goodsLines];
            } else {
                for (let i = 0; i < goodsLines.length; i += 12) {
                    chunks.push(goodsLines.slice(i, i + 12));
                }
                if (chunks.length === 0) chunks.push([]);
            }

            chunks.forEach((chunkLines, chunkIndex) => {
                let isFirstCard = chunkIndex === 0;
                let isSplit = chunks.length > 1;
                let partLetter = String.fromCharCode(65 + chunkIndex); 

                let compactClass = (!isMobile && chunkLines.length >= 8) ? 'compact' : '';

                if (currentTab === 0) {
                    let frontGoodsHtml = '';
                    chunkLines.forEach(line => {
                        let lineScale = calculateTextScale(line, 15);
                        let renderScale = Math.min(lineScale, 1.15); 
                        let formattedLine = line.replace(/([a-zA-Z0-9.]+)/g, `<span class="text-red-large" style="font-size: calc(var(--red-size, 42px) * ${renderScale});">$1</span>`);
                        frontGoodsHtml += `<div class="product-item" style="font-size: calc(var(--base-size, 24px) * ${renderScale}); white-space: nowrap; height: calc(var(--red-size, 42px) * 1.1); display: flex; align-items: center;">${formattedLine}</div>`;
                    });

                    let indicatorHtml = (!isMobile && isSplit) ? `<div class="card-part-indicator">${partLetter}</div>` : '';

                    let tagsHtmlStr = '';
                    let frontActs = '';
                    let backGoodsHtml = '';
                    let backActs = '';

                    if (isFirstCard) {
                        let tagsHtml = '';
                        if (o.goods_packaging) tagsHtml += `<div class="tag tag-blue">包装:${o.goods_packaging}</div>`;
                        if (o.goods_weight) tagsHtml += `<div class="tag tag-cyan">重量:${o.goods_weight}</div>`;
                        if (o.remark) tagsHtml += `<div class="tag tag-red">备注:${o.remark}</div>`;
                        if (o.goods_quantity) tagsHtml += `<div class="tag tag-green">件数:${o.goods_quantity}</div>`;

                        if (tagsHtml) {
                            tagsHtmlStr = `
                            <div class="tags-wrapper">
                                <div class="tags-label">标签&备注</div>
                                <div class="tags-container">${tagsHtml}</div>
                            </div>`;
                        }

                        if (hasPerm('pending.complete')) frontActs += `<button class="btn btn-primary" onclick="triggerStatusConfirm(${o.id}, 'completed')">确定完成</button>`;
                        if (hasPerm('pending.view_detail')) frontActs += `<button class="btn btn-default" onclick="toggleCard(this)">详情页面</button>`;

                        goodsLines.forEach(line => {
                            let lineScale = calculateTextScale(line, 15);
                            let renderScale = Math.min(lineScale, 1.15);
                            backGoodsHtml += `<div class="info-row text-red text-bold" style="font-size: calc(15px * ${renderScale}); white-space: nowrap; height: 24px; display: flex; align-items: center;">${line}</div>`;
                        });

                        if (hasPerm('pending.view_detail')) backActs += `<button class="btn btn-default" onclick="toggleCard(this)">⇦返回</button>`;
                        if (hasPerm('pending.complete')) backActs += `<button class="btn btn-primary" onclick="triggerStatusConfirm(${o.id}, 'completed')">确定完成</button>`;
                        if (hasPerm('pending.edit')) backActs += `<button class="btn btn-danger" onclick="openEditOrderModal(${o.id})">修改</button>`;
                        if (hasPerm('pending.copy')) backActs += `<button class="btn btn-success" onclick="copyOrderInfo(${o.id})">复制</button>`;
                    }

                    html += `
                    <div class="flip-container">
                      <div class="flipper ${!isFirstCard ? 'no-flip' : ''}">
                        <div class="order-card front">
                          <div class="order-title">${o.order_client || '未命名归属'}订单</div>
                          <div class="order-header"><span><strong>${typeName}</strong> 产品列表 ${!isFirstCard ? '(续集)' : ''}</span><span>${isFirstCard ? (o.date || '未知时间') : ''}</span></div>
                          
                          <div class="product-list ${compactClass}">
                            ${frontGoodsHtml || '<div class="product-item" style="color:#999;">暂无货物明细</div>'}
                            ${indicatorHtml}
                          </div>
                          
                          ${tagsHtmlStr}
                          ${isFirstCard ? `<div class="actions">${frontActs}</div>` : ''}
                        </div>
                        
                        ${isFirstCard ? `
                        <div class="order-card back">
                          <div class="order-title">${o.order_client || '未命名归属'}订单</div>
                          <div class="order-header"><span><strong>${typeName}</strong> 产品列表</span><span>${o.date || '未知时间'}</span></div>
                          <div class="product-list">
                            <div class="info-row" style="display: flex; justify-content: space-between;">
                              <span>收货姓名：${o.receiver_name || '未填'}</span>
                              <span>联系电话：${isEmployee ? '***' : (o.receiver_phone || '未填')}</span>
                            </div>
                            <div class="info-row">收货地址：${o.receiver_address || '未填'}</div>
                            <div class="info-row info-label" style="margin-top: 12px;">货物全量信息：</div>
                            ${backGoodsHtml}
                            <div style="display: flex; gap: 24px; margin-top: 16px;">
                              <div class="info-row"><span class="info-label">包装：</span>${o.goods_packaging || '无'}</div>
                              <div class="info-row"><span class="info-label">数量：</span><span class="text-red text-bold">${o.goods_weight || '无'}</span></div>
                            </div>
                            <div style="display: flex; gap: 24px;">
                              <div class="info-row"><span class="info-label">件数：</span>${o.goods_quantity || '无'}</div>
                              <div class="info-row"><span class="info-label">物流服务：</span>${isEmployee ? '***' : (o.logistics_service || '无')}</div>
                            </div>
                            ${o.remark ? `<div class="info-row"><span class="info-label">备注：</span><span class="text-red text-bold">${o.remark}</span></div>` : ''}
                          </div>
                          <div class="actions-back">${backActs}</div>
                        </div>
                        ` : `<div class="order-card back"></div>`}
                      </div>
                    </div>`;
                } 
                else if (currentTab === 1) {
                    let frontGoodsHtml = '';
                    chunkLines.forEach(line => { 
                        let lineScale = calculateTextScale(line, 15);
                        let renderScale = Math.min(lineScale, 1.15);
                        frontGoodsHtml += `<div class="info-row text-red text-bold" style="font-size: calc(var(--base-size, 24px) * ${renderScale}); white-space: nowrap; flex-shrink: 0; height: calc(var(--base-size, 24px) * 1.4); display: flex; align-items: center;">${line}</div>`; 
                    });
                    let indicatorHtml = (!isMobile && isSplit) ? `<div class="card-part-indicator" style="font-size:70px;">${partLetter}</div>` : '';

                    let cActs = '';
                    let shortDate = o.completed_date ? o.completed_date.split(' ')[0] : '未知日期';

                    if (isFirstCard) {
                        if (hasPerm('completed.uncomplete')) cActs += `<button class="btn btn-default" onclick="triggerStatusConfirm(${o.id}, 'pending')">撤销</button>`;
                        if (hasPerm('completed.ship')) cActs += `<button class="btn btn-primary" onclick="triggerShipModal(${o.id})">出库</button>`;
                        if (hasPerm('completed.delete')) cActs += `<button class="btn btn-danger" onclick="deleteOrder(${o.id})">删除</button>`;
                        if (hasPerm('completed.copy')) cActs += `<button class="btn btn-success" onclick="copyOrderInfo(${o.id})">复制</button>`;
                    }

                    html += `
                    <div class="completed-card" style="padding: 20px 24px; font-size: 15px;">
                      <div class="order-title" style="font-size: 28px; margin-bottom: 8px;">${o.order_client || '未命名归属'}订单</div>
                      <div class="order-header" style="font-size: 15px; padding-bottom: 8px; margin-bottom: 12px;">
                        <span><strong>${typeName}</strong> 发货核对明细 ${!isFirstCard ? '(续)' : ''}</span>
                        <span>${isFirstCard ? shortDate : ''}</span>
                      </div>
                      
                      <div class="product-list ${compactClass}" style="position:relative;">
                        ${isFirstCard ? `
                        <div class="info-row" style="display: flex; justify-content: space-between;">
                          <span>收货姓名：${o.receiver_name || '未填'}</span>
                          <span>电话：${isEmployee ? '***' : (o.receiver_phone || '未填')}</span>
                        </div>
                        <div class="info-row">收货地址：${o.receiver_address || '未填'}</div>
                        <div class="info-row info-label" style="margin-top: 6px;">货物信息：</div>
                        ` : ''}

                        ${frontGoodsHtml || '<div class="info-row" style="color:#999; flex-shrink: 0;">暂无货物明细</div>'}
                        ${indicatorHtml}

                        ${isFirstCard ? `
                        <div style="margin-top: auto; padding-top: 12px; display: flex; flex-direction: column; gap: 4px; flex-shrink: 0;">
                            <div style="display: flex; gap: 24px;">
                              <div class="info-row"><span class="info-label">包装：</span>${o.goods_packaging || '无'}</div>
                              <div class="info-row"><span class="info-label">数量：</span><span class="text-red text-bold">${o.goods_weight || '无'}</span></div>
                            </div>
                            <div style="display: flex; gap: 24px;">
                              <div class="info-row"><span class="info-label">件数：</span>${o.goods_quantity || '无'}</div>
                              <div class="info-row"><span class="info-label">物流：</span>${isEmployee ? '***' : (o.logistics_service || '无')}</div>
                            </div>
                            ${o.remark ? `<div class="info-row"><span class="info-label">备注信息：</span><span class="text-red text-bold">${o.remark}</span></div>` : ''}
                            <div class="info-row" style="color: #888; border-top: 1px dashed #f0f0f0; padding-top: 8px; margin-top: 4px;">
                              <span class="info-label" style="color: #333;">完成时间：</span>${o.completed_date || '未知'}
                            </div>
                        </div>
                        ` : ''}
                      </div>
                      ${isFirstCard ? `<div class="actions-back" style="margin-top: 12px; padding-top: 12px;">${cActs}</div>` : ''}
                    </div>`;
                }
            });
        });
        
        targetContainer.innerHTML = html;
        setTimeout(() => { autoFitVerticalText(); }, 50);

    } catch (error) { console.error("数据拉取引擎异常", error); }
}

window.executeShippedDateFilter = function(startDate, endDate) {
    nomiActiveFilterStart = startDate;
    nomiActiveFilterEnd = endDate;
    fetchOrders(); 
};

window.executeMaterialDateFilter = function(startDate, endDate) {
    nomiMaterialFilterStart = startDate;
    nomiMaterialFilterEnd = endDate;
    fetchMaterials(); 
};

async function fetchMaterials() {
    if (currentTab !== 3) return;
    try {
        const response = await fetch(`${API_BASE}/materials`, { method: 'GET', headers: getHeaders() });
        const matData = await response.json();
        const targetContainer = document.getElementById('tab-3');
        let allRecords = matData.records || [];
        let currentStock = parseFloat(matData.total_stock) || 0;
        
        // 为了正确计算剩余库存，先按时间正序排列计算
        allRecords.sort((a, b) => a.date.localeCompare(b.date));
        allRecords.forEach(r => { 
            currentStock -= (parseFloat(r.used) || 0); 
            r.remaining = currentStock; 
        });
        
        let filteredRecords = [];

        // 【原材料范围过滤逻辑】
        if (nomiMaterialFilterStart && nomiMaterialFilterEnd) {
            let startT = new Date(nomiMaterialFilterStart.replace(/-/g, '/')).getTime();
            let endT = new Date(nomiMaterialFilterEnd.replace(/-/g, '/')).getTime() + 86400000 - 1; 
            filteredRecords = allRecords.filter(r => {
                let dateStr = r.date || '';
                if (!dateStr) return false;
                let t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime();
                return t >= startT && t <= endT;
            });
        } else {
            const now = new Date();
            const threeDaysAgo = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 2).getTime(); 
            filteredRecords = allRecords.filter(r => {
                let dateStr = r.date || '';
                if (!dateStr) return false;
                let t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime();
                return t >= threeDaysAgo;
            });
        }
        
        if (filteredRecords.length === 0) {
            let msg = nomiMaterialFilterStart ? `没有找到 ${nomiMaterialFilterStart} 到 ${nomiMaterialFilterEnd} 的原材料记录` : `最近 3 天内暂无原材料（树脂）使用记录`;
            targetContainer.innerHTML = `<div style="color: #999; width:100%; text-align:center; padding:60px 20px; font-size:16px;">${msg}</div>`;
            return;
        }
        
        let groups = {};
        filteredRecords.forEach(r => { 
            let day = r.date.substring(0, 10); 
            if (!groups[day]) groups[day] = []; 
            groups[day].push(r); 
        });
        
        let html = '<div class="timeline-container">';
        
        Object.keys(groups).sort((a, b) => b.localeCompare(a)).forEach(date => {
            html += `<div class="timeline-group"><div class="timeline-date">${date}</div><div class="timeline-items">`;
            
            // ... 上面是已有的排序和数据过滤逻辑 ...
        groups[date].sort((a, b) => b.date.localeCompare(a.date)).forEach(r => {
            let remarkText = r.remark ? r.remark : '无';
            
            html += `
            <div class="material-card" id="mat-card-${r.id}" style="box-sizing: border-box; width: 100%;">
                
                <div id="mat-view-${r.id}" style="display: flex; align-items: center; width: 100%; flex-wrap: wrap; gap: 12px; box-sizing: border-box;">
                    <div class="m-data-group">
                        <div class="m-item"><span class="m-label-black">使用树脂：</span><span class="m-val-pink">${r.used} kg</span></div>
                        <div class="m-item"><span class="m-label-black">成品：</span><span class="m-val-green">${r.produced} kg</span></div>
                        <div class="m-item"><span class="m-label-blue">剩余树脂：</span><span class="m-val-blue">${r.remaining.toFixed(1)} kg</span></div>
                    </div>
                    <div style="flex-grow: 1; min-width: 10px;"></div>
                    <div class="m-note"><span class="m-note-label">备注：</span><span class="m-note-val">${remarkText}</span></div>
                    
                    ${hasPerm('material.edit') ? `
                    <div style="margin-left: auto; padding-left: 10px;">
                        <button class="btn-default" style="padding: 6px 16px; font-size: 13px; border-radius: 20px; border: 1px solid #d9d9d9; height: 34px; font-weight: bold; cursor: pointer;" onclick="toggleInlineMatEdit(${r.id}, true)">修改</button>
                    </div>
                    ` : ''}
                </div>

                <div id="mat-edit-${r.id}" style="display: none; align-items: center; width: 100%; flex-wrap: wrap; gap: 12px; box-sizing: border-box;">
                    <div class="m-data-group" style="flex-wrap: wrap; gap: 8px;">
                        <div class="m-item" style="display: flex; align-items: center;">
                            <span class="m-label-black" style="font-size: 13px;">使用树脂：</span>
                            <input id="inline-used-${r.id}" type="number" value="${r.used}" style="width: 70px; height: 28px; padding: 0 4px; border: 1px solid #eb2f96; border-radius: 8px; outline: none; font-weight: bold; color: #eb2f96; text-align: center; background: #fff0f6;" />
                            <span class="m-val-pink" style="margin-left: 2px; font-size: 13px;">kg</span>
                        </div>
                        <div class="m-item" style="display: flex; align-items: center;">
                            <span class="m-label-black" style="font-size: 13px;">成品：</span>
                            <input id="inline-produced-${r.id}" type="number" value="${r.produced}" style="width: 70px; height: 28px; padding: 0 4px; border: 1px solid #52c41a; border-radius: 8px; outline: none; font-weight: bold; color: #52c41a; text-align: center; background: #f6ffed;" />
                            <span class="m-val-green" style="margin-left: 2px; font-size: 13px;">kg</span>
                        </div>
                        <div class="m-item" style="font-size: 13px;">
                            <span class="m-label-blue">剩余：</span>
                            <span class="m-val-blue">${r.remaining.toFixed(1)} kg</span>
                        </div>
                    </div>
                    <div style="flex-grow: 1; min-width: 10px;"></div>
                    <div class="m-note" style="display: flex; align-items: center; flex: 1; min-width: 140px; max-width: 260px;">
                        <span class="m-note-label" style="white-space: nowrap; font-size: 13px;">备注：</span>
                        <input id="inline-remark-${r.id}" type="text" value="${r.remark || ''}" placeholder="备注..." style="width: 100%; height: 28px; padding: 0 6px; border: 1px solid #b3d8ff; border-radius: 8px; outline: none; color: #111; font-size: 13px; background: #f0f7ff;" />
                    </div>
                    
                    <div style="margin-left: auto; display: flex; align-items: center; gap: 6px; padding-left: 10px;">
                        ${hasPerm('material.delete') ? `
                        <button class="btn-danger" style="padding: 4px 14px; font-size: 12px; border-radius: 20px; border: none; height: 32px; font-weight: bold; color: white; cursor: pointer;" onclick="deleteInlineMatRecord(${r.id})">删除</button>
                        ` : ''}
                        <button class="btn-default" style="padding: 4px 14px; font-size: 12px; border-radius: 20px; border: 1px solid #d9d9d9; height: 32px; font-weight: bold; cursor: pointer;" onclick="toggleInlineMatEdit(${r.id}, false)">取消</button>
                        <button class="btn-primary" style="padding: 4px 16px; font-size: 12px; border-radius: 20px; border: none; height: 32px; font-weight: bold; background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%); color: white; cursor: pointer;" onclick="submitInlineMatEdit(${r.id})">完成</button>
                    </div>
                </div>
                
            </div>`;
        });
// ... 下面保持原样 ...
            html += `</div></div>`;
        });
        html += '</div>';
        targetContainer.innerHTML = html;
        
    } catch(error) { 
        console.error('拉取原材料数据异常', error); 
    }
}

function triggerShipModal(orderId) {
    document.getElementById('shipTargetId').value = orderId;
    document.getElementById('shipLogisticsNo').value = ''; 
    // 每次开启弹窗默认还原勾选到第一行的“物流”选项
    const typeRadios = document.getElementsByName('shipLogisticsType');
    if (typeRadios.length > 0) typeRadios[0].checked = true;
    // 同时清空第二行独立输入框的内容
    document.getElementById('shipLogisticsTypeOther').value = '';

    document.getElementById('shipOrderModal').style.display = 'flex';
}

function closeShipModal() { document.getElementById('shipOrderModal').style.display = 'none'; }

async function submitShipOrder() {
    const id = document.getElementById('shipTargetId').value;
    let logisticsNo = document.getElementById('shipLogisticsNo').value.trim();
    if (!logisticsNo) logisticsNo = '无单号记录'; 

    // 获取单选框被选中的值
    let logisticsType = '物流';
    const typeRadios = document.getElementsByName('shipLogisticsType');
    for (let r of typeRadios) {
        if (r.checked) { logisticsType = r.value; break; }
    }
    
    // 如果选中的是第二行独立 DIV 中的“自由填写”，则抓取右侧文本框
    if (logisticsType === '自由填写') {
        const otherVal = document.getElementById('shipLogisticsTypeOther').value.trim();
        logisticsType = otherVal ? otherVal : '其它发货方式';
    }

    const currentDateTime = getCurrentDateTime();
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ 
                status: 'shipped', 
                logistics_type: logisticsType, 
                logistics_no: logisticsNo, 
                shipped_date: currentDateTime, 
                completed_date: currentDateTime 
            })
        });
        if (response.ok) { closeShipModal(); fetchOrders(); }
    } catch (e) { alert('发货出库网络通讯失败'); }
}

function triggerStatusConfirm(orderId, targetStatus) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    document.getElementById('confirmTargetId').value = orderId;
    document.getElementById('confirmTargetStatus').value = targetStatus;
    document.getElementById('newConfirmTitle').innerText = `${order.order_client || '未命名'}订单`;
    document.getElementById('newConfirmSubtitle').innerHTML = `单据日期 &nbsp; ${order.date || '未知时间'}`;
    
    let goodsLines = (order.goods_name || '').split('\n').filter(l => l.trim() !== '');
    let goodsHtml = '';
    goodsLines.forEach(line => {
        let lineScale = calculateTextScale(line, 15);
        let renderScale = Math.min(lineScale, 1.15);
        let formattedLine = line.replace(/([a-zA-Z0-9.]+)/g, `<span class="text-red-large" style="font-size: calc(24px * ${renderScale});">$1</span>`);
        goodsHtml += `<div class="modal-product" style="font-size: calc(16px * ${renderScale}); white-space: nowrap; height: 32px; display: flex; align-items: center;">${formattedLine}</div>`;
    });
    if (goodsHtml === '') goodsHtml = '<div class="modal-product" style="color:#999;">无详细货物内容</div>';
    
    document.getElementById('newConfirmBody').innerHTML = goodsHtml;
    const confirmBtn = document.querySelector('#confirmModal .modal-btn-confirm');
    if (targetStatus === 'pending') {
        confirmBtn.innerText = '确认撤销至未完成状态';
        confirmBtn.style.backgroundColor = '#ff4d4f'; 
    } else {
        confirmBtn.innerText = '确定完成';
        confirmBtn.style.backgroundColor = '#1890ff'; 
    }
    document.getElementById('confirmModal').style.display = 'flex';
}

function closeModal() { document.getElementById('confirmModal').style.display = 'none'; }

async function submitUpdateOrderStatus() {
    const id = document.getElementById('confirmTargetId').value;
    const status = document.getElementById('confirmTargetStatus').value;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ status: status }) });
        if (response.ok) { closeModal(); fetchOrders(); }
    } catch (error) { alert("流转操作异常"); }
}

async function deleteOrder(id) {
    if (!confirm(`严重安全警告：您确定要彻底物理删除这条订单记录吗？此操作无法撤销！`)) return;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'DELETE', headers: getHeaders() });
        if (response.ok) fetchOrders();
    } catch (e) {}
}

function copyOrderInfo(orderId) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    
    let isEmployee = currentUser.role === 'employee' || currentUser.role === 'operator';
    const typeText = (order.type == 1) ? '绝缘订单' : '中固订单';
    let nameLimit = (order.type == 1) ? 8 : 5;
    let shortGoodsName = (order.goods_name || '').replace(/\n/g, '').trim().substring(0, nameLimit);
    
    let clipText = `【${typeText}】\n`;
    if (order.receiver_name) clipText += `姓名：${order.receiver_name}\n`;
    if (!isEmployee && order.receiver_phone) clipText += `电话：${order.receiver_phone}\n`;
    if (order.receiver_address) clipText += `地址：${order.receiver_address}\n`;
    if (shortGoodsName) clipText += `名称：${shortGoodsName}\n`;
    if (order.goods_weight) clipText += `重量：${order.goods_weight}\n`;
    if (order.goods_quantity) clipText += `件数：${order.goods_quantity}\n`;
    if (order.goods_packaging) clipText += `包装：${order.goods_packaging}\n`;
    if (!isEmployee && order.logistics_service) clipText += `服务：${order.logistics_service}\n`;
    if (order.remark) clipText += `备注：${order.remark}\n`;

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(clipText).then(() => { alert('✅ 极简物流信息已成功复制！'); }).catch(() => fallbackCopyTextToClipboard(clipText));
    } else fallbackCopyTextToClipboard(clipText);
}

async function createOrder() {
    const payload = {
        title: document.getElementById('newOrderTitle').value, 
        type: parseInt(document.getElementById('newOrderType').value),
        order_client: document.getElementById('newOrderClient').value.trim(), 
        receiver_name: document.getElementById('newReceiverName').value.trim(),
        receiver_phone: document.getElementById('newReceiverPhone').value.trim(), 
        receiver_address: document.getElementById('newReceiverAddress').value.trim(),
        goods_name: document.getElementById('newGoodsName').value.trim(), 
        goods_weight: document.getElementById('newGoodsWeight').value.trim(),
        goods_quantity: document.getElementById('newGoodsQuantity').value.trim(), 
        goods_packaging: document.getElementById('newGoodsPackaging').value,
        logistics_service: document.getElementById('newLogisticsService').value, 
        remark: document.getElementById('newOrderRemark').value.trim()
    };
    const errMsg = validatePayload(payload);
    if (errMsg) return alert('发单失败：' + errMsg);
    try {
        const response = await fetch(`${API_BASE}/orders`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(payload) });
        if (response.ok) {
            toggleModal('createOrderModal', false); 
            document.querySelectorAll('#createOrderModal input, #createOrderModal textarea').forEach(el => el.value = '');
            switchTab(0); 
        }
    } catch (error) {}
}

function openEditOrderModal(orderId) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    document.getElementById('editOrderId').value = order.id;
    document.getElementById('editOrderDate').value = order.date || '';
    document.getElementById('editOrderType').value = order.type !== undefined ? order.type : 0;
    document.getElementById('editOrderTitle').value = order.title || '';
    
    ['OrderClient', 'ReceiverName', 'ReceiverPhone', 'ReceiverAddress', 'GoodsName', 'GoodsWeight', 'GoodsQuantity'].forEach(k => {
        const el = document.getElementById(`edit${k}`);
        if (el) el.value = order[k.replace(/([A-Z])/g, "_$1").toLowerCase().substring(1)] || '';
    });
    
    document.getElementById('editGoodsPackaging').value = order.goods_packaging || '桶装';
    document.getElementById('editLogisticsService').value = order.logistics_service || '送货上门+回单拍照回传';
    document.getElementById('editOrderRemark').value = order.remark || '';
    
    const delBtn = document.getElementById('btnDeleteOrderInEdit');
    if (delBtn) {
        if (hasPerm('pending.delete') || hasPerm('completed.delete')) delBtn.style.display = 'inline-block';
        else delBtn.style.display = 'none';
    }
    toggleModal('editOrderModal', true);
}

async function submitEditOrder() {
    const id = document.getElementById('editOrderId').value;
    const date = document.getElementById('editOrderDate').value.trim();
    if (!date) return alert('时间不能为空！');
    const payload = {
        title: document.getElementById('editOrderTitle').value, 
        type: parseInt(document.getElementById('editOrderType').value), 
        date: date,
        order_client: document.getElementById('editOrderClient').value.trim(), 
        receiver_name: document.getElementById('editReceiverName').value.trim(),
        receiver_phone: document.getElementById('editReceiverPhone').value.trim(), 
        receiver_address: document.getElementById('editReceiverAddress').value.trim(),
        goods_name: document.getElementById('editGoodsName').value.trim(), 
        goods_weight: document.getElementById('editGoodsWeight').value.trim(),
        goods_quantity: document.getElementById('editGoodsQuantity').value.trim(), 
        goods_packaging: document.getElementById('editGoodsPackaging').value,
        logistics_service: document.getElementById('editLogisticsService').value, 
        remark: document.getElementById('editOrderRemark').value.trim()
    };
    const errMsg = validatePayload(payload);
    if (errMsg) return alert('修改失败：' + errMsg);
    try {
        const response = await fetch(`${API_BASE}/orders/${id}/edit`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify(payload) });
        if (response.ok) { toggleModal('editOrderModal', false); fetchOrders(); }
    } catch (e) { alert('请求异常'); }
}

async function deleteOrderInEdit() {
    const id = document.getElementById('editOrderId').value;
    if (!id) return;
    if (!confirm('安全警告：您确定要彻底物理删除这条订单记录吗？此操作无法撤销！')) return;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'DELETE', headers: getHeaders() });
        if (response.ok) { toggleModal('editOrderModal', false); fetchOrders(); }
    } catch (e) { alert('物理删除请求异常'); }
}

function openUploadMaterialModal() {
    toggleModal('uploadMaterialModal', true);
    setActiveKeyboardTarget('materialInputUse');
    document.getElementById('materialInputUse').value = '';
    document.getElementById('materialInputProduct').value = '';
}

function setActiveKeyboardTarget(id) {
    activeKeyboardTargetId = id;
    document.querySelectorAll('.keyboard-target').forEach(el => el.classList.remove('active-target'));
    document.getElementById(id).classList.add('active-target');
}

function pressKey(key) {
    const targetInput = document.getElementById(activeKeyboardTargetId);
    let currentVal = targetInput.value;
    if (key === 'clear') targetInput.value = '';
    else if (key === 'backspace') targetInput.value = currentVal.substring(0, currentVal.length - 1);
    else if (key === '.') { if (!currentVal.includes('.')) targetInput.value = currentVal + '.'; }
    else targetInput.value = currentVal + key;
}

async function uploadMaterialRecord() {
    const usedVal = parseFloat(document.getElementById('materialInputUse').value);
    const productVal = parseFloat(document.getElementById('materialInputProduct').value);
    if (isNaN(usedVal) || isNaN(productVal)) return alert('录入失败：请完整输入耗材与产出量！');

    try {
        const response = await fetch(`${API_BASE}/materials`, { method: 'POST', headers: getHeaders(), body: JSON.stringify({ used: usedVal, produced: productVal }) });
        if (response.ok) {
            toggleModal('uploadMaterialModal', false); 
            document.getElementById('successNotifyDetail').innerText = `物料报表已存入：\n消耗: ${usedVal} kg\n产出: ${productVal} kg`;
            toggleModal('uploadSuccessNotifyModal', true);
            if (currentTab === 3) fetchMaterials();
        }
    } catch (e) {}
}

function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (show) modal.classList.remove('hidden');
    else modal.classList.add('hidden');
}

function switchTab(index) {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => item.classList.remove('active'));
  navItems[index].classList.add('active');

  const tabPanes = document.querySelectorAll('.tab-pane');
  tabPanes.forEach(pane => pane.classList.remove('active'));
  document.getElementById('tab-' + index).classList.add('active');

  currentTab = index;
  
  if (index === 0 || index === 1 || index === 2) fetchOrders();
  else if (index === 3) fetchMaterials();
  if (index === 2) initExpandButtons(); 
  
  if (index === 2) {
      if (typeof window.triggerDateFilterSpeech === 'function') window.triggerDateFilterSpeech('shipped');
  } else if (index === 3) {
      if (typeof window.triggerDateFilterSpeech === 'function') window.triggerDateFilterSpeech('material');
  }

  setTimeout(() => { autoFitVerticalText(); }, 50);
}

function toggleCard(btn) {
  const flipper = btn.closest('.flipper');
  if (flipper) {
      flipper.classList.toggle('flipped');
      setTimeout(() => { autoFitVerticalText(); }, 350); 
  }
}

function autoFitVerticalText() {
    if (window.innerWidth <= 768) return; 

    document.querySelectorAll('.front .product-list, .completed-card .product-list').forEach(list => {
        let baseSize = list.classList.contains('compact') ? 16 : 24; 
        let redSize = list.classList.contains('compact') ? 26 : 42; 
        let gap = list.classList.contains('compact') ? 8 : 16;

        list.style.gap = gap + 'px';
        list.style.setProperty('--base-size', baseSize + 'px');
        list.style.setProperty('--red-size', redSize + 'px');

        void list.offsetHeight; 

        let loop = 0;
        while (list.scrollHeight > list.clientHeight && baseSize > 14 && loop < 10) {
            baseSize -= 1;
            redSize -= 1.5;
            gap = Math.max(4, gap - 1);
            
            list.style.gap = gap + 'px';
            list.style.setProperty('--base-size', baseSize + 'px');
            list.style.setProperty('--red-size', redSize + 'px');
            
            void list.offsetHeight; 
            loop++;
        }
    });
}

window.addEventListener('resize', () => {
    initExpandButtons();
    if (currentTab === 0 || currentTab === 1) autoFitVerticalText();
});

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
        } else expandBtn.textContent = '展开列表';
      } else expandBtn.style.display = 'none';

      if (!expandBtn.dataset.bound) {
        expandBtn.dataset.bound = "true";
        expandBtn.addEventListener('click', function() {
          if (title.classList.contains('expanded')) { title.classList.remove('expanded'); expandBtn.textContent = '展开列表'; } 
          else { title.classList.add('expanded'); expandBtn.textContent = '收起列表'; }
        });
      }
    }
  });
}

window.addEventListener('load', initExpandButtons);

// ========================================================
// 🖱️ 多维滚动与触摸事件强化映射
// ========================================================
// 1. 强制 Tab 0 (未完成) 和 Tab 1 (已完成) 横向排列并响应横向滚轮
document.querySelectorAll('#tab-0, #tab-1').forEach(container => {
    container.addEventListener('wheel', function(e) {
        if (e.deltaY !== 0) {
            e.preventDefault(); 
            this.scrollLeft += e.deltaY; // 把上下滚轮映射成左右滑动
        }
    }, { passive: false });
});

// 2. 强制 Tab 2 (已出库) 和 Tab 3 (原材料) 顺畅响应垂直滚轮与触屏拖拽
document.querySelectorAll('#tab-2, #tab-3').forEach(container => {
    // 滚轮控制上下滑动
    container.addEventListener('wheel', function(e) {
        if (e.deltaY !== 0) {
            this.scrollTop += e.deltaY;
        }
    }, { passive: true });
    
    // 触屏控制上下滑动 (针对手机端体验优化)
    let startY;
    container.addEventListener('touchstart', function(e) {
        startY = e.touches[0].pageY;
    }, { passive: true });
    
    container.addEventListener('touchmove', function(e) {
        if (!startY) return;
        const y = e.touches[0].pageY;
        const walk = (startY - y);
        this.scrollTop += walk; // 根据手指滑动距离强制上下移动
        startY = y;
    }, { passive: true });
});

/* ========================================================
 * 🔄 系统初始化启动挂载点
 * ======================================================== */
window.onload = function() {
    const savedUser = localStorage.getItem('local_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        if (!currentUser.permissions) currentUser.permissions = [];
        renderUI();
        switchTab(0);

        setInterval(function() {
            const editModal = document.getElementById('editOrderModal');
            const shipModal = document.getElementById('shipOrderModal');
            
            if (document.querySelector('.flipper.flipped') || 
                document.getElementById('confirmModal').style.display === 'flex' ||
                (shipModal && shipModal.style.display === 'flex') ||
                (editModal && !editModal.classList.contains('hidden'))) {
                return;
            }
            
            if (currentTab === 0) fetchOrders();
            if (typeof refreshUserList === 'function' && !document.getElementById('viewUserModal').classList.contains('hidden')) refreshUserList();
            
        }, 3000); 

    } else renderUI(); 
};

// ========================================================
// 📦 原材料【行内就地编辑与删除】控制引擎
// ========================================================
function toggleInlineMatEdit(id, isEditing) {
    const viewBlock = document.getElementById(`mat-view-${id}`);
    const editBlock = document.getElementById(`mat-edit-${id}`);
    if (viewBlock && editBlock) {
        if (isEditing) {
            viewBlock.style.display = 'none';
            editBlock.style.display = 'flex'; // 🚀 确保是 flex 横向排版
        } else {
            viewBlock.style.display = 'flex'; // 🚀 确保是 flex 横向排版
            editBlock.style.display = 'none';
        }
    }
}

async function submitInlineMatEdit(id) {
    const usedInput = document.getElementById(`inline-used-${id}`);
    const producedInput = document.getElementById(`inline-produced-${id}`);
    const remarkInput = document.getElementById(`inline-remark-${id}`);
    
    if (!usedInput || !producedInput) return;
    
    const usedVal = parseFloat(usedInput.value);
    const prodVal = parseFloat(producedInput.value);
    const remarkVal = remarkInput ? remarkInput.value.trim() : '';
    
    if (isNaN(usedVal) || isNaN(prodVal)) {
        return alert('保存失败：消耗量与产出量必须输入有效的数字！');
    }

    try {
        const response = await fetch(`${API_BASE}/materials/${id}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({
                used: usedVal,
                produced: prodVal,
                remark: remarkVal
            })
        });
        
        if (response.ok) {
            // 保存成功后重载数据实现就地刷新与库存重算
            fetchMaterials();
        } else {
            alert('修改失败：底层鉴权拦截或服务器异常');
        }
    } catch (e) {
        alert('网络通讯异常，保存失败');
    }
}

async function deleteInlineMatRecord(id) {
    if (!confirm('安全警告：您确定要彻底物理删除这条原材料使用流水记录吗？\n删除后所有剩余树脂库存将自动动态重算，此操作不可撤销！')) return;
    
    try {
        const response = await fetch(`${API_BASE}/materials/${id}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        
        if (response.ok) {
            fetchMaterials(); // 重新拉取，卡片物理消失，库存重新洗牌
        } else {
            alert('删除失败：底层权限不足');
        }
    } catch (e) {
        alert('网络通讯异常，删除失败');
    }
}