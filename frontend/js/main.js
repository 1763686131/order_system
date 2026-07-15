const API_BASE = '/api';
let currentUser = { username: '', role: '', permissions: [] };
let allOrdersLocal = []; 
let currentTab = 'pending'; 
let activeKeyboardTargetId = 'materialInputUse'; 

// 🌟 全新角色名称映射：统称为“员工”
function getRoleName(role) {
    const maps = { 'super_admin': '超级管理员', 'admin': '管理员', 'employee': '员工', 'operator': '员工' };
    return maps[role] || role;
}

// 🌟 核心引擎：极速权限校验算法 (超管拥有一切，其他人看具体权限勾选)
function hasPerm(permKey) {
    if (currentUser.role === 'super_admin') return true;
    return currentUser.permissions && currentUser.permissions.includes(permKey);
}

// 🌟 权限树形配置图谱
const PERMISSIONS_CONFIG = [
    {
        group: 'order', label: '📦 订单流水线核心业务',
        children: [
            { key: 'order.add', label: '发布生成新订单' },
            { key: 'order.edit', label: '修改历史订单内容' },
            { key: 'order.complete', label: '执行标记完成业务' },
            { key: 'order.uncomplete', label: '执行撤销完成状态' },
            { key: 'order.copy', label: '一键复制物流排版' }
        ]
    },
    {
        group: 'material', label: '🛢️ 生产物料与库存业务',
        children: [
            { key: 'material.add', label: '录入原料消耗与产出' },
            { key: 'material.edit', label: '修改流水账单备注' },
            { key: 'material.edit_stock', label: '调整大盘总物理库存' }
        ]
    }
];

function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Username': String(currentUser.username),
        'Role': String(currentUser.role)
    };
}

function initFilterDates() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - 3); 
    document.getElementById('filterStartDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('filterEndDate').value = endDate.toISOString().split('T')[0];
}

function toggleMobileMenu() {
    const menu = document.getElementById('navRightMenu');
    if(menu) menu.classList.toggle('show-menu');
}
function closeMobileMenu() {
    const menu = document.getElementById('navRightMenu');
    if(menu) menu.classList.remove('show-menu');
}

function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (show) modal.classList.remove('hidden');
    else modal.classList.add('hidden');
}

function switchTab(tabName) {
    currentTab = tabName;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) btn.classList.add('active');
    });

    const orderGrid = document.getElementById('orderGrid');
    const materialWrapper = document.getElementById('materialViewWrapper');

    if (tabName === 'materials') {
        orderGrid.classList.add('hidden');
        materialWrapper.classList.remove('hidden');
        fetchMaterialRecords();
    } else {
        orderGrid.classList.remove('hidden');
        materialWrapper.classList.add('hidden');
        fetchOrders();
    }
}

function refreshDashboardData() {
    if (currentTab === 'materials') fetchMaterialRecords();
    else fetchOrders();
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

// 🌟 UI 渲染大换血：根据权限显示功能入口按钮
function renderUI() {
    const loginSection = document.getElementById('loginSection');
    const mainSection = document.getElementById('mainSection');
    const btnOpenViewUser = document.getElementById('btnOpenViewUser');
    const btnNavCreateOrder = document.getElementById('btnNavCreateOrder');
    const btnEditStockAction = document.getElementById('btnEditStockAction');
    const btnUploadMaterialAction = document.getElementById('btnUploadMaterialAction');

    if (!currentUser.username) {
        loginSection.classList.remove('hidden');
        mainSection.classList.add('hidden');
        return;
    }

    loginSection.classList.add('hidden');
    mainSection.classList.remove('hidden');

    document.getElementById('currentUsername').innerText = currentUser.username;
    document.getElementById('currentUserRoleTag').innerText = getRoleName(currentUser.role);

    // 只有超管和管理员才能看到“账户控制台”
    if (['super_admin', 'admin'].includes(currentUser.role)) btnOpenViewUser.classList.remove('hidden');
    else btnOpenViewUser.classList.add('hidden');

    // 顶部发单按钮管控
    if (hasPerm('order.add')) btnNavCreateOrder.classList.remove('hidden');
    else btnNavCreateOrder.classList.add('hidden');

    // 顶部调库按钮管控
    if (hasPerm('material.edit_stock')) btnEditStockAction.classList.remove('hidden');
    else btnEditStockAction.classList.add('hidden');
    
    // 物料录入按钮管控
    if (btnUploadMaterialAction) {
        if (hasPerm('material.add')) btnUploadMaterialAction.classList.remove('hidden');
        else btnUploadMaterialAction.classList.add('hidden');
    }
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
            // 确保没有权限数组时给个兜底空数组
            if (!currentUser.permissions) currentUser.permissions = [];
            localStorage.setItem('local_user', JSON.stringify(currentUser));
            renderUI();
            initFilterDates();
            refreshDashboardData();
        } else { alert(resData.message || '凭证错误，登录失败'); }
    } catch (error) { alert('本地服务端连接失败，请检查 Docker。'); }
}

function formatTextWithBreaks(text) {
    if (!text) return '';
    return text.replace(/\n/g, '<br>');
}

function handleLogout() {
    currentUser = { username: '', role: '', permissions: [] };
    localStorage.removeItem('local_user');
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
    renderUI();
}

async function fetchOrders() {
    if (currentTab === 'materials') return;
    try {
        const response = await fetch(`${API_BASE}/orders`, { method: 'GET', headers: getHeaders() });
        const serverOrders = await response.json();
        allOrdersLocal = serverOrders;
        
        if (!document.getElementById('statusConfirmModal').classList.contains('hidden')) return; 

        const gridContainer = document.getElementById('orderGrid');
        gridContainer.innerHTML = ''; 

        const startDateStr = document.getElementById('filterStartDate').value;
        const endDateStr = document.getElementById('filterEndDate').value;

        let filteredOrders = serverOrders.filter(order => {
            if (order.status !== currentTab) return false;
            if (order.date) {
                const orderDay = order.date.substring(0, 10); 
                if (startDateStr && orderDay < startDateStr) return false;
                if (endDateStr && orderDay > endDateStr) return false;
            }
            return true;
        });

        if (currentTab === 'completed') filteredOrders.sort((a, b) => (b.completed_date || '').localeCompare(a.completed_date || ''));
        else if (currentTab === 'pending') filteredOrders.sort((a, b) => (b.date || '').localeCompare(a.date || ''));

        if (filteredOrders.length === 0) {
            gridContainer.innerHTML = '<div style="color: #999; grid-column: 1/-1; text-align:center; padding:40px;">当前区间内无相关订单记录</div>';
            return;
        }

        filteredOrders.forEach(order => {
            const card = document.createElement('div');
            const orderType = order.type !== undefined ? order.type : 0;
            
            let cardClasses = 'order-card';
            let typeText = orderType == 1 ? '绝缘订单' : '中固订单';
            if (orderType == 1) cardClasses += ' insulation-order'; 
            else cardClasses += ' zhonggu-order';
            card.className = cardClasses;
            
            let isEmployee = currentUser.role === 'employee' || currentUser.role === 'operator';
            
            // 🌟 动态计算底部的各种操作按钮 (完全根据权限树走)
            let actionBtn = '';
            if (order.status === 'pending' && hasPerm('order.complete')) {
                actionBtn = `<button class="btn-success" onclick="triggerStatusConfirm(${order.id}, 'completed')">完成业务</button>`;
            } else if (order.status === 'completed' && hasPerm('order.uncomplete')) {
                actionBtn = `<button class="btn-outline-danger" onclick="triggerStatusConfirm(${order.id}, 'pending')" style="padding:4px 10px; font-size:12px;">设为未完成</button>`;
            }

            let superActionHtml = '';
            if (order.status !== 'completed' && hasPerm('order.edit')) {
                superActionHtml += `<button class="btn-outline-primary" style="padding:4px 10px; font-size:12px;" onclick="openEditOrderModal(${order.id})">修改</button>`;
            }
            // 🔒 铁律：只有超管才能看到删除按钮
            if (currentUser.role === 'super_admin') {
                superActionHtml += `<button class="btn-outline-danger" style="padding:4px 10px; font-size:12px;" onclick="deleteOrder(${order.id})">删除</button>`;
            }

            let copyBtnHtml = hasPerm('order.copy')
                ? `<button class="btn-outline-primary" style="padding:4px 10px; font-size:12px; margin-right:4px;" onclick="copyOrderInfo(${order.id})">📋 复制物流</button>`
                : '';

            let completedDateHtml = order.status === 'completed' && order.completed_date ? `<div class="complete-date" style="white-space: nowrap;">✔ ${order.completed_date}</div>` : '';

            let structuredDataHtml = '';
            if (order.order_client || order.receiver_name || (!isEmployee && order.receiver_phone) || order.receiver_address || order.goods_name || order.goods_weight || order.goods_quantity || order.goods_packaging || (!isEmployee && order.logistics_service) || order.remark) {
                structuredDataHtml = `<div style="margin-top: 12px; padding: 12px; background: #f8f9fb; border-radius: 6px; font-size: 13px; line-height: 2;">`;
                
                const typeLabel = orderType == 1 ? '绝缘订单' : '中固订单';
                if (order.order_client) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">${typeLabel}:</span><strong style="color:#333;">${order.order_client}</strong></div>`;
                if (order.receiver_name) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">收货姓名:</span><strong style="color:#333;">${order.receiver_name}</strong></div>`;
                if (!isEmployee && order.receiver_phone) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">收货电话:</span><strong style="color:#333;">${order.receiver_phone}</strong></div>`;
                if (order.receiver_address) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">收货地址:</span><strong style="color:#333; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; flex: 1;" title="${order.receiver_address}">${order.receiver_address}</strong></div>`;
                if (order.goods_name) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0; padding-top: 3px;">货物名称:</span><div style="color:#409EFF; font-weight:900; font-size: 18px; flex:1; line-height: 1.5; letter-spacing: 0.5px;">${formatTextWithBreaks(order.goods_name)}</div></div>`;
                if (order.goods_weight) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">货物重量:</span><strong style="color:#E6A23C;">${order.goods_weight}</strong></div>`;
                if (order.goods_quantity) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">货物数量:</span><strong style="color:#E6A23C;">${order.goods_quantity}</strong></div>`;
                if (order.goods_packaging) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">货物包装:</span><strong style="color:#333;">${order.goods_packaging}</strong></div>`;
                if (!isEmployee && order.logistics_service) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">物流服务:</span><strong style="color:#333;">${order.logistics_service}</strong></div>`;
                if (order.remark) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">备注信息:</span><strong style="color:#F56C6C;">${order.remark}</strong></div>`;
                structuredDataHtml += `</div>`;
            }

            let oldTextHtml = (!order.receiver_name && !order.goods_name && order.title)
                ? `<div style="color: #606266; font-size: 14px; margin-bottom: 4px;">${formatTextWithBreaks(order.title)}</div>` 
                : '';

            card.innerHTML = `
                <div class="card-header">
                    <span class="card-title-tag">[#${order.id}] ${typeText}</span>
                    <span class="order-time">🕐 创建: ${order.date || '未知'}</span>
                </div>
                <div class="card-body">${oldTextHtml}${structuredDataHtml}</div>
                <div class="card-footer">
                    ${completedDateHtml}
                    <div class="card-footer-right">${copyBtnHtml}${superActionHtml}${actionBtn}</div>
                </div>
            `;
            gridContainer.appendChild(card);
        });
    } catch (error) { console.error("订单数据加载失败", error); }
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
        navigator.clipboard.writeText(clipText).then(() => { alert('✅ 极简物流信息已成功复制！\n可以直接去微信粘贴转发了。'); }).catch(() => fallbackCopyTextToClipboard(clipText));
    } else fallbackCopyTextToClipboard(clipText);
}

function fallbackCopyTextToClipboard(text) {
    let textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed"; textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus(); textArea.select();
    try { document.execCommand('copy'); alert('✅ 极简物流信息已成功复制！'); } 
    catch (err) { alert('⚠️ 当前浏览器不支持自动复制，请手动选中并复制。'); }
    document.body.removeChild(textArea);
}

async function fetchMaterialRecords() {
    if (currentTab !== 'materials') return;
    try {
        const response = await fetch(`${API_BASE}/materials`, { method: 'GET', headers: getHeaders() });
        const resData = await response.json();
        document.getElementById('displayTotalStock').innerText = `${resData.total_stock} kg`;

        const container = document.getElementById('materialCapsuleList');
        container.innerHTML = '';
        const startDateStr = document.getElementById('filterStartDate').value;
        const endDateStr = document.getElementById('filterEndDate').value;

        let filteredRecords = resData.records.filter(item => {
            if (item.date) {
                const day = item.date.substring(0, 10);
                if (startDateStr && day < startDateStr) return false;
                if (endDateStr && day > endDateStr) return false;
            }
            return true;
        });

        filteredRecords.sort((a, b) => (b.date || '').localeCompare(a.date || ''));

        let totalUsed = 0;
        resData.records.forEach(item => { totalUsed += parseFloat(item.used || 0); });
        const remains = parseFloat(resData.total_stock || 0) - totalUsed;
        document.getElementById('remainedMaterialCapsule').innerText = `剩余原材料：${remains.toFixed(2)} kg`;

        if (filteredRecords.length === 0) {
            container.innerHTML = '<div style="color: #999; text-align:center; padding:40px;">当前筛选区间内无原材料使用明细</div>';
            return;
        }

        filteredRecords.forEach(item => {
            const row = document.createElement('div');
            row.className = 'material-capsule-item';

            const safeRemark = item.remark ? item.remark.replace(/'/g, "&#39;") : '';
            const remarkHtml = item.remark ? `<div class="capsule-remark-box">📝 备注：${item.remark}</div>` : '';

            let actionHtml = '';
            let btnCluster = '';
            
            if (hasPerm('material.edit')) {
                btnCluster += `<button class="btn-outline-primary" style="padding:4px 10px; font-size:12px; margin-right:4px;" onclick="openEditMaterialModal(${item.id}, ${item.used}, ${item.produced}, '${safeRemark}')">修改备注</button>`;
            }
            // 🔒 铁律：只有超管才能看到删除按钮
            if (currentUser.role === 'super_admin') {
                btnCluster += `<button class="btn-outline-danger" style="padding:4px 10px; font-size:12px;" onclick="deleteMaterialRecord(${item.id})">删除</button>`;
            }
            
            if (btnCluster) {
                actionHtml = `<div class="capsule-right">${btnCluster}</div>`;
            }

            row.innerHTML = `
                <div class="capsule-left">
                    <div class="capsule-time">🕒 ${item.date}</div>
                    <div class="capsule-stats"><span class="capsule-use-tag">用料：<strong>${item.used} kg</strong></span><span class="capsule-product-tag">成品：<strong>${item.produced} kg</strong></span></div>
                    ${remarkHtml}
                </div>
                ${actionHtml}
            `;
            container.appendChild(row);
        });
    } catch (e) { console.error("获取原材料异常", e); }
}

async function uploadMaterialRecord() {
    const usedVal = parseFloat(document.getElementById('materialInputUse').value);
    const productVal = parseFloat(document.getElementById('materialInputProduct').value);
    if (isNaN(usedVal) || isNaN(productVal)) return alert('录入失败：请点击右侧虚拟键盘完整填入有效的数字！');

    try {
        const response = await fetch(`${API_BASE}/materials`, { method: 'POST', headers: getHeaders(), body: JSON.stringify({ used: usedVal, produced: productVal }) });
        if (response.ok) {
            toggleModal('uploadMaterialModal', false); 
            document.getElementById('successNotifyDetail').innerText = `物料报表数据已成功存入：\n\n🔴 消耗: ${usedVal} kg\n🟢 产出: ${productVal} kg`;
            toggleModal('uploadSuccessNotifyModal', true);
            if(currentTab === 'materials') fetchMaterialRecords();
        }
    } catch (e) {}
}

function triggerStockModifyModal() {
    document.getElementById('newStockInput').value = document.getElementById('displayTotalStock').innerText.replace(' kg', '');
    toggleModal('editTotalStockModal', true);
}

async function submitUpdateTotalStockValue() {
    const newStock = parseFloat(document.getElementById('newStockInput').value);
    if (isNaN(newStock) || newStock < 0) return alert('请输入有效的数字！');
    try {
        const response = await fetch(`${API_BASE}/materials/stock`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ total_stock: newStock }) });
        if (response.ok) { toggleModal('editTotalStockModal', false); fetchMaterialRecords(); }
    } catch (e) {}
}

function openEditMaterialModal(id, used, produced, remark = '') {
    document.getElementById('editMaterialId').value = id;
    document.getElementById('editMaterialUse').value = used;
    document.getElementById('editMaterialProduct').value = produced;
    document.getElementById('editMaterialRemark').value = remark;
    toggleModal('editMaterialModal', true);
}

async function submitEditMaterial() {
    const id = document.getElementById('editMaterialId').value;
    const payload = {
        used: parseFloat(document.getElementById('editMaterialUse').value) || 0,
        produced: parseFloat(document.getElementById('editMaterialProduct').value) || 0,
        remark: document.getElementById('editMaterialRemark').value.trim()
    };
    try {
        const response = await fetch(`${API_BASE}/materials/${id}`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify(payload) });
        if (response.ok) { toggleModal('editMaterialModal', false); fetchMaterialRecords(); }
    } catch (e) {}
}

async function deleteMaterialRecord(id) {
    if (!confirm(`确定要物理【删除】单号为 #${id} 的流水记录吗？`)) return;
    try {
        const response = await fetch(`${API_BASE}/materials/${id}`, { method: 'DELETE', headers: getHeaders() });
        if (response.ok) fetchMaterialRecords();
    } catch (e) {}
}

function triggerStatusConfirm(orderId, targetStatus) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    document.getElementById('confirmTargetId').value = orderId;
    document.getElementById('confirmTargetStatus').value = targetStatus;
    document.getElementById('previewCardType').innerText = `[#${order.id}] ${order.type == 1 ? '绝缘订单' : '中固订单'}`;
    document.getElementById('previewCardDate').innerText = `🕒 创建: ${order.date || '未知'}`;
    document.getElementById('previewCardTitle').innerHTML = order.goods_name ? formatTextWithBreaks(order.goods_name) : formatTextWithBreaks(order.title);
    
    const tipText = document.getElementById('confirmTipText');
    const submitBtn = document.getElementById('btnConfirmSubmit');
    if (targetStatus === 'completed') { tipText.innerText = "🛑 确认将以下订单标记为【已完成】吗？"; submitBtn.className = "btn-success"; } 
    else { tipText.innerText = "⚠️ 确认将以下订单恢复为【未完成】吗？"; submitBtn.className = "btn-warning"; }
    toggleModal('statusConfirmModal', true);
}

async function submitUpdateOrderStatus() {
    const id = document.getElementById('confirmTargetId').value;
    const status = document.getElementById('confirmTargetStatus').value;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ status: status }) });
        if (response.ok) { toggleModal('statusConfirmModal', false); fetchOrders(); }
    } catch (error) {}
}

// ============== 核心：智能运算引擎 =================
function smartParse(prefix) {
    const text = document.getElementById(`${prefix}OrderTitle`).value;
    if (!text.trim()) return alert('请先在上方输入框粘贴或填写内容，再点击识别！');
    const lines = text.split('\n').map(l => l.trim()).filter(l => l !== '');
    if (lines.length === 0) return;
    document.getElementById(`${prefix}OrderClient`).value = lines[0].replace(/[:：]$/, '').trim();
    if (lines.length > 1) {
        let line2 = lines[1];
        let phoneMatch = line2.match(/(1[3-9]\d{9}|0\d{2,3}-\d{7,8})/);
        let phone = phoneMatch ? phoneMatch[0] : '';
        let name = '', address = '';
        let strWithoutPhone = line2.replace(phone, '').replace(/(?:电话|联系方式|手机)[:：]?\s*/g, '');
        let nameMatch = strWithoutPhone.match(/(?:姓名|收货人)[:：]\s*([^\s。，,;；]{1,5})/);
        if (nameMatch) { name = nameMatch[1]; strWithoutPhone = strWithoutPhone.replace(nameMatch[0], ''); }
        else {
            let qMatch = strWithoutPhone.match(/[?？]\s*([^\s。，,;；:：]{1,4})/);
            if (qMatch) { name = qMatch[1]; strWithoutPhone = strWithoutPhone.replace(qMatch[0], ''); }
        }
        let addrMatch = strWithoutPhone.match(/(?:地址)[:：]\s*(.*)/);
        if (addrMatch) { address = addrMatch[1]; strWithoutPhone = strWithoutPhone.replace(addrMatch[0], ''); } 
        else { address = strWithoutPhone; }
        
        if (!name) {
            let parts = address.split(/[\s。，,;；]+/).filter(p => p.trim() !== '');
            let potentialName = parts.find(p => p.length >= 2 && p.length <= 4 && !/[省市区县镇村街道路号栋室楼]/.test(p));
            if (potentialName) { name = potentialName; address = address.replace(potentialName, ''); } 
            else {
                let fallbackParts = line2.split(phone);
                name = fallbackParts[0].replace(/收货人|电话|联系方式|:|：/g, '').trim();
                address = (fallbackParts[1] || '').replace(/^[。，,.;:\s]+/, '').trim();
                if (name.length > 6 && address.length <= 6) { let temp = name; name = address; address = temp; }
            }
        }
        document.getElementById(`${prefix}ReceiverName`).value = name.replace(/^[。，,;；\s]+|[。，,;；\s]+$/g, '').replace(/[?？]/g, '');
        document.getElementById(`${prefix}ReceiverPhone`).value = phone;
        document.getElementById(`${prefix}ReceiverAddress`).value = address.replace(/(?:地址)[:：]?/g, '').replace(/^[。，,;；\s]+|[。，,;；\s]+$/g, '');
    }

    if (lines.length > 2) {
        let goodsStr = lines.slice(2).join('\n');
        document.getElementById(`${prefix}GoodsName`).value = goodsStr;
        let totalWeight = 0, tempStr = goodsStr;
        let calcRegex1 = /(\d+(?:\.\d+)?)\s*(?:[A-Za-z\u4e00-\u9fa5]{0,6})?\s*([*xX✖️×\/÷])\s*(\d+(?:\.\d+)?)/g;
        let match;
        while ((match = calcRegex1.exec(tempStr)) !== null) {
            let val = /[*/÷]/.test(match[2]) ? (/[*xX✖️×]/.test(match[2]) ? parseFloat(match[1]) * parseFloat(match[3]) : parseFloat(match[1]) / parseFloat(match[3])) : 0;
            if (tempStr.substring(0, match.index).trim().endsWith('-')) totalWeight -= val; else totalWeight += val; 
            tempStr = tempStr.substring(0, match.index) + " ".repeat(match[0].length) + tempStr.substring(match.index + match[0].length);
        }
        let calcRegex2 = /([+-])\s*(\d+(?:\.\d+)?)/g;
        while ((match = calcRegex2.exec(tempStr)) !== null) {
            if (match[1] === '+') totalWeight += parseFloat(match[2]); else totalWeight -= parseFloat(match[2]);
        }
        if (totalWeight !== 0) document.getElementById(`${prefix}GoodsWeight`).value = (Math.round(totalWeight * 100) / 100) + 'kg';
        else document.getElementById(`${prefix}GoodsWeight`).value = '';
    }
}

function validatePayload(payload) {
    if (!payload.receiver_phone || !payload.receiver_address || !payload.goods_name || !payload.goods_weight) return '【收货电话】、【地址】、【名称】、【重量】为必填项！';
    if (!/^(?:1[3-9]\d{9}|0\d{2,3}-\d{7,8})$/.test(payload.receiver_phone)) return '【收货电话】格式不正确！必须是 11位手机号或带区号的座机。';
    return null; 
}

async function createOrder() {
    const payload = {
        title: document.getElementById('newOrderTitle').value, type: parseInt(document.getElementById('newOrderType').value),
        order_client: document.getElementById('newOrderClient').value.trim(), receiver_name: document.getElementById('newReceiverName').value.trim(),
        receiver_phone: document.getElementById('newReceiverPhone').value.trim(), receiver_address: document.getElementById('newReceiverAddress').value.trim(),
        goods_name: document.getElementById('newGoodsName').value.trim(), goods_weight: document.getElementById('newGoodsWeight').value.trim(),
        goods_quantity: document.getElementById('newGoodsQuantity').value.trim(), goods_packaging: document.getElementById('newGoodsPackaging').value,
        logistics_service: document.getElementById('newLogisticsService').value, remark: document.getElementById('newOrderRemark').value.trim()
    };
    const errMsg = validatePayload(payload);
    if (errMsg) return alert('发单失败：' + errMsg);
    try {
        const response = await fetch(`${API_BASE}/orders`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(payload) });
        if (response.ok) {
            toggleModal('createOrderModal', false); 
            document.querySelectorAll('#createOrderModal input, #createOrderModal textarea').forEach(el => el.value = '');
            switchTab('pending'); 
        }
    } catch (error) { alert('发单失败'); }
}

function openEditOrderModal(orderId) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    document.getElementById('editOrderId').value = order.id;
    document.getElementById('editOrderDate').value = order.date || '';
    document.getElementById('editOrderType').value = order.type !== undefined ? order.type : 0;
    document.getElementById('editOrderTitle').value = order.title || '';
    ['OrderClient', 'ReceiverName', 'ReceiverPhone', 'ReceiverAddress', 'GoodsName', 'GoodsWeight', 'GoodsQuantity'].forEach(k => {
        document.getElementById(`edit${k}`).value = order[k.replace(/([A-Z])/g, "_$1").toLowerCase().substring(1)] || '';
    });
    document.getElementById('editGoodsPackaging').value = order.goods_packaging || '桶装';
    document.getElementById('editLogisticsService').value = order.logistics_service || '送货上门+回单拍照回传';
    document.getElementById('editOrderRemark').value = order.remark || '';
    toggleModal('editOrderModal', true);
}

async function submitEditOrder() {
    const id = document.getElementById('editOrderId').value;
    const date = document.getElementById('editOrderDate').value.trim();
    if (!date) return alert('时间不能为空！');
    const payload = {
        title: document.getElementById('editOrderTitle').value, type: parseInt(document.getElementById('editOrderType').value), date: date,
        order_client: document.getElementById('editOrderClient').value.trim(), receiver_name: document.getElementById('editReceiverName').value.trim(),
        receiver_phone: document.getElementById('editReceiverPhone').value.trim(), receiver_address: document.getElementById('editReceiverAddress').value.trim(),
        goods_name: document.getElementById('editGoodsName').value.trim(), goods_weight: document.getElementById('editGoodsWeight').value.trim(),
        goods_quantity: document.getElementById('editGoodsQuantity').value.trim(), goods_packaging: document.getElementById('editGoodsPackaging').value,
        logistics_service: document.getElementById('editLogisticsService').value, remark: document.getElementById('editOrderRemark').value.trim()
    };
    const errMsg = validatePayload(payload);
    if (errMsg) return alert('修改失败：' + errMsg);
    try {
        const response = await fetch(`${API_BASE}/orders/${id}/edit`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify(payload) });
        if (response.ok) { toggleModal('editOrderModal', false); fetchOrders(); }
    } catch (e) { alert('请求异常'); }
}

async function deleteOrder(id) {
    if (!confirm(`安全警告：确定要物理【删除】单号为 #${id} 的订单吗？`)) return;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'DELETE', headers: getHeaders() });
        if (response.ok) fetchOrders();
    } catch (e) {}
}


// =======================================================
// 🌟 核心升级：全新集中式账户与权限控制台
// =======================================================
let currentEditUser = null; // 记录当前正在编辑面板打开的用户

async function openViewUserModal() { 
    toggleModal('viewUserModal', true); 
    document.getElementById('userDetailPanel').style.display = 'none';
    await refreshUserList(); 
}

async function refreshUserList() {
    try {
        const response = await fetch(`${API_BASE}/users`, { method: 'GET', headers: getHeaders() });
        const users = await response.json();
        const container = document.getElementById('userListContainer');
        container.innerHTML = '';
        
        users.forEach(user => {
            const row = document.createElement('div');
            row.className = 'user-list-item';
            if (currentEditUser && currentEditUser.username === user.username) row.classList.add('active');
            
            // 权限防御：超管看一切；管理员只能看普通员工
            if (currentUser.role === 'admin' && user.role !== 'employee' && user.role !== 'operator') {
                return; // 不渲染
            }

            let roleName = getRoleName(user.role);
            let color = user.role === 'super_admin' ? '#F56C6C' : (user.role === 'admin' ? '#E6A23C' : '#67C23A');
            
            row.innerHTML = `<div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size: 15px; font-weight: bold; color: #303133;">👤 ${user.username}</span>
                <span style="font-size: 12px; background: ${color}20; color: ${color}; padding: 2px 8px; border-radius: 12px;">${roleName}</span>
            </div>`;
            row.onclick = () => loadUserDetail(user);
            container.appendChild(row);
        });
    } catch (e) {}
}

function prepareCreateUser() {
    currentEditUser = null;
    document.querySelectorAll('.user-list-item').forEach(el => el.classList.remove('active'));
    document.getElementById('userDetailPanel').style.display = 'block';
    document.getElementById('detailTitle').innerText = "✨ 新建系统账户";
    
    document.getElementById('detailUsername').value = '';
    document.getElementById('detailUsername').disabled = false;
    document.getElementById('detailPassword').value = '';
    
    document.getElementById('btnUpdatePwd').style.display = 'none';
    document.getElementById('btnDeleteUser').style.display = 'none';
    document.getElementById('btnSaveUser').style.display = 'inline-block';
    
    document.getElementById('detailRole').style.display = 'inline-block';
    document.getElementById('detailRoleText').style.display = 'none';
    
    // 渲染完全空白的权限树
    renderPermissionTree([]);
}

function loadUserDetail(user) {
    currentEditUser = user;
    document.querySelectorAll('.user-list-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    document.getElementById('userDetailPanel').style.display = 'block';
    document.getElementById('detailTitle').innerText = `⚙️ 配置用户：${user.username}`;
    
    document.getElementById('detailUsername').value = user.username;
    document.getElementById('detailUsername').disabled = true; // 修改模式下不可改名
    document.getElementById('detailPassword').value = user.password;
    
    document.getElementById('btnUpdatePwd').style.display = 'inline-block';
    document.getElementById('btnSaveUser').style.display = 'inline-block';
    
    // 🔒 删除按钮控制：只有超管，且不能删超管自己
    if (currentUser.role === 'super_admin' && user.role !== 'super_admin') {
        document.getElementById('btnDeleteUser').style.display = 'inline-block';
    } else {
        document.getElementById('btnDeleteUser').style.display = 'none';
    }
    
    // 角色控制
    const roleSelect = document.getElementById('detailRole');
    const roleText = document.getElementById('detailRoleText');
    if (user.role === 'super_admin') {
        roleSelect.style.display = 'none';
        roleText.style.display = 'inline-block';
        roleText.innerText = '最高级安全守护者 (不可更改)';
        document.getElementById('permissionsWrapper').style.display = 'none'; // 超管无需配置权限
    } else {
        roleSelect.style.display = 'inline-block';
        roleText.style.display = 'none';
        roleSelect.value = (user.role === 'operator') ? 'employee' : user.role;
        document.getElementById('permissionsWrapper').style.display = 'block';
        
        // Admin 看别人，强行锁定角色框
        if (currentUser.role === 'admin') roleSelect.disabled = true;
        else roleSelect.disabled = false;
        
        renderPermissionTree(user.permissions || []);
    }
}

// 动态渲染交互式权限树控件
function renderPermissionTree(userPerms) {
    let treeHtml = '';
    PERMISSIONS_CONFIG.forEach(group => {
        treeHtml += `<div class="perm-group">
            <label><input type="checkbox" class="perm-parent" data-group="${group.group}" onchange="toggleGroupPerms(this)"> ${group.label}</label>
            <div class="perm-children">`;
        
        let allChecked = true;
        let hasChildren = false;

        group.children.forEach(child => {
            hasChildren = true;
            let isChecked = userPerms.includes(child.key) ? 'checked' : '';
            if (!userPerms.includes(child.key)) allChecked = false;
            
            // 🔒 权限控制降维打击：如果当前操作者是 admin，且他自己都没这个权限，强行锁死复选框不让发给别人
            let disabledStr = '';
            let labelClass = '';
            if (currentUser.role === 'admin' && !hasPerm(child.key)) {
                disabledStr = 'disabled title="您自己未拥有此权限，无法授予他人"';
                labelClass = 'disabled-perm';
                isChecked = ''; // 强行拉空
            }
            
            treeHtml += `<label class="${labelClass}"><input type="checkbox" class="perm-cb" value="${child.key}" data-group="${group.group}" onchange="checkParentPerm(this)" ${isChecked} ${disabledStr}> ${child.label}</label>`;
        });
        
        treeHtml += `</div></div>`;
    });
    
    document.getElementById('permTreeContainer').innerHTML = treeHtml;
    // 渲染完后初始化一下父框的状态
    document.querySelectorAll('.perm-cb').forEach(cb => checkParentPerm(cb, false));
}

function toggleGroupPerms(parentCb) {
    const group = parentCb.dataset.group;
    const cbs = document.querySelectorAll(`.perm-cb[data-group="${group}"]:not([disabled])`);
    cbs.forEach(cb => cb.checked = parentCb.checked);
}

function checkParentPerm(childCb, cascade = true) {
    const group = childCb.dataset.group;
    const cbs = document.querySelectorAll(`.perm-cb[data-group="${group}"]`);
    const parentCb = document.querySelector(`.perm-parent[data-group="${group}"]`);
    // 只要该组有一个被勾上，父类就呈勾选状态
    parentCb.checked = Array.from(cbs).some(cb => cb.checked);
}

// 收集已勾选的权限树叶子节点
function getSelectedPermissions() {
    const perms = [];
    document.querySelectorAll('.perm-cb:checked').forEach(cb => perms.push(cb.value));
    return perms;
}

// 大一统的保存按钮：新建用户 或 保存权限配置
async function saveUserData() {
    if (!currentEditUser) {
        // ========== 场景 A: 新建账户 ==========
        const u = document.getElementById('detailUsername').value.trim();
        const p = document.getElementById('detailPassword').value.trim();
        const r = document.getElementById('detailRole').value;
        if (!u || !p) return alert('账号密码不能为空！');
        
        const payload = { username: u, password: p, role: r, permissions: getSelectedPermissions() };
        try {
            const res = await fetch(`${API_BASE}/users`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(payload) });
            if (res.ok) { alert('✨ 新系统账户创建并赋权成功！'); refreshUserList(); prepareCreateUser(); }
            else alert('账户名称已存在或无权限！');
        } catch(e) { alert('网络异常'); }
        
    } else {
        // ========== 场景 B: 保存已有用户的权限和角色 ==========
        // 如果是超级管理员，可能还顺手改了别人的角色
        if (currentUser.role === 'super_admin' && currentEditUser.role !== 'super_admin') {
            // 目前没有单独的更新角色接口，如果有需求后续可以在后端加上。当前我们着重于更新它的权限。
        }
        
        const payload = { permissions: getSelectedPermissions() };
        try {
            const res = await fetch(`${API_BASE}/users/${currentEditUser.username}/permissions`, { 
                method: 'PUT', headers: getHeaders(), body: JSON.stringify(payload) 
            });
            if (res.ok) { alert(`✅ 已成功更新 ${currentEditUser.username} 的模块访问权限！`); refreshUserList(); }
        } catch(e) { alert('更新权限失败'); }
    }
}

async function updateUserPassword() {
    if (!currentEditUser) return;
    const p = document.getElementById('detailPassword').value.trim();
    if(!p) return alert('密码不能为空');
    try { 
        const res = await fetch(`${API_BASE}/users/${currentEditUser.username}/password`, { 
            method: 'PUT', headers: getHeaders(), body: JSON.stringify({ password: p }) 
        }); 
        if (res.ok) alert('✅ 密码重置成功！');
    } catch(e) {}
}

async function deleteCurrentUser() {
    if (!currentEditUser) return;
    if (!confirm(`💣 严重警告：确定要彻底物理删除账户 [${currentEditUser.username}] 吗？`)) return;
    try { 
        const res = await fetch(`${API_BASE}/users/${currentEditUser.username}`, { method: 'DELETE', headers: getHeaders() }); 
        if (res.ok) { document.getElementById('userDetailPanel').style.display = 'none'; refreshUserList(); }
    } catch(e) {}
}

window.onload = function() {
    const savedUser = localStorage.getItem('local_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        if (!currentUser.permissions) currentUser.permissions = [];
        renderUI();
        initFilterDates();
        switchTab('pending');
        setInterval(function() {
            refreshDashboardData();
            if (!document.getElementById('viewUserModal').classList.contains('hidden')) refreshUserList();
        }, 3000); 
    } else { renderUI(); }
};