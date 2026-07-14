const API_BASE = '/api';
let currentUser = { username: '', role: '' };
let allOrdersLocal = []; 
let currentTab = 'pending'; 
let activeKeyboardTargetId = 'materialInputUse'; 

function getRoleName(role) {
    const maps = { 'super_admin': '超级管理员', 'admin': '管理员', 'operator': '操作员' };
    return maps[role] || role;
}

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

function renderUI() {
    const loginSection = document.getElementById('loginSection');
    const mainSection = document.getElementById('mainSection');
    const btnOpenAddUser = document.getElementById('btnOpenAddUser');
    const btnOpenViewUser = document.getElementById('btnOpenViewUser');
    const btnNavCreateOrder = document.getElementById('btnNavCreateOrder');
    const btnEditStockAction = document.getElementById('btnEditStockAction');

    if (!currentUser.username) {
        loginSection.classList.remove('hidden');
        mainSection.classList.add('hidden');
        return;
    }

    loginSection.classList.add('hidden');
    mainSection.classList.remove('hidden');

    document.getElementById('currentUsername').innerText = currentUser.username;
    document.getElementById('currentUserRoleTag').innerText = getRoleName(currentUser.role);

    if (currentUser.role === 'super_admin') {
        btnOpenAddUser.classList.remove('hidden');
        btnOpenViewUser.classList.remove('hidden');
        btnNavCreateOrder.classList.remove('hidden');
        btnEditStockAction.classList.remove('hidden');
    } else if (currentUser.role === 'admin') {
        btnOpenAddUser.classList.add('hidden');
        btnOpenViewUser.classList.add('hidden');
        btnNavCreateOrder.classList.remove('hidden');
        btnEditStockAction.classList.remove('hidden');
    } else {
        btnOpenAddUser.classList.add('hidden');
        btnOpenViewUser.classList.add('hidden');
        btnNavCreateOrder.classList.add('hidden');
        btnEditStockAction.classList.add('hidden');
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
    currentUser = { username: '', role: '' };
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

        if (currentTab === 'completed') {
            filteredOrders.sort((a, b) => (b.completed_date || '').localeCompare(a.completed_date || ''));
        } else if (currentTab === 'pending') {
            filteredOrders.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
        }

        if (filteredOrders.length === 0) {
            gridContainer.innerHTML = '<div style="color: #999; grid-column: 1/-1; text-align:center; padding:40px;">当前区间内无相关订单记录</div>';
            return;
        }

        filteredOrders.forEach(order => {
            const card = document.createElement('div');
            const orderType = order.type !== undefined ? order.type : 0;
            
            let cardClasses = 'order-card';
            let typeText = '未知';
            if (orderType == 1) {
                cardClasses += ' insulation-order'; typeText = '绝缘订单';
            } else {
                cardClasses += ' zhonggu-order'; typeText = '中固订单';
            }
            card.className = cardClasses;
            
            let isOperator = currentUser.role === 'operator';
            let isActionHidden = (isOperator && order.status === 'completed');
            
            let actionBtn = '';
            if (!isActionHidden) {
                if (order.status === 'pending') {
                    actionBtn = `<button class="btn-success" onclick="triggerStatusConfirm(${order.id}, 'completed')">完成业务</button>`;
                } else {
                    actionBtn = `<button class="btn-outline-danger" onclick="triggerStatusConfirm(${order.id}, 'pending')" style="padding:4px 10px; font-size:12px;">设为未完成</button>`;
                }
            }

            let superActionHtml = '';
            if (currentUser.role === 'super_admin') {
                const editBtnHtml = order.status === 'completed' 
                    ? '' : `<button class="btn-outline-primary" style="padding:4px 10px; font-size:12px;" onclick="openEditOrderModal(${order.id})">修改</button>`;
                superActionHtml = `${editBtnHtml}<button class="btn-outline-danger" style="padding:4px 10px; font-size:12px;" onclick="deleteOrder(${order.id})">删除</button>`;
            }

            // 🌟 如果是操作员，直接不生成复制按钮，隐藏保护到底
            let copyBtnHtml = !isOperator 
                ? `<button class="btn-outline-primary" style="padding:4px 10px; font-size:12px; margin-right:4px;" onclick="copyOrderInfo(${order.id})">复制</button>`
                : '';

            let completedDateHtml = order.status === 'completed' && order.completed_date ? `<div class="complete-date" style="white-space: nowrap;">✔ ${order.completed_date}</div>` : '';

            let structuredDataHtml = '';
            if (order.order_client || order.receiver_name || (!isOperator && order.receiver_phone) || order.receiver_address || order.goods_name || order.goods_weight || order.goods_quantity || order.goods_packaging || (!isOperator && order.logistics_service) || order.remark) {
                structuredDataHtml = `<div style="margin-top: 12px; padding: 12px; background: #f8f9fb; border-radius: 6px; font-size: 13px; line-height: 2;">`;
                
                const typeLabel = orderType == 1 ? '绝缘订单' : '中固订单';
                if (order.order_client) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">${typeLabel}:</span><strong style="color:#333;">${order.order_client}</strong></div>`;
                if (order.receiver_name) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">收货姓名:</span><strong style="color:#333;">${order.receiver_name}</strong></div>`;
                if (!isOperator && order.receiver_phone) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">收货电话:</span><strong style="color:#333;">${order.receiver_phone}</strong></div>`;
                if (order.receiver_address) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">收货地址:</span><strong style="color:#333; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; flex: 1;" title="${order.receiver_address}">${order.receiver_address}</strong></div>`;
                if (order.goods_name) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0; padding-top: 3px;">货物名称:</span><div style="color:#409EFF; font-weight:900; font-size: 18px; flex:1; line-height: 1.5; letter-spacing: 0.5px;">${formatTextWithBreaks(order.goods_name)}</div></div>`;
                if (order.goods_weight) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">货物重量:</span><strong style="color:#E6A23C;">${order.goods_weight}</strong></div>`;
                if (order.goods_quantity) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">货物数量:</span><strong style="color:#E6A23C;">${order.goods_quantity}</strong></div>`;
                if (order.goods_packaging) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">货物包装:</span><strong style="color:#333;">${order.goods_packaging}</strong></div>`;
                if (!isOperator && order.logistics_service) structuredDataHtml += `<div style="display:flex;"><span style="color:#909399; width: 75px; flex-shrink: 0;">物流服务:</span><strong style="color:#333;">${order.logistics_service}</strong></div>`;
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
                <div class="card-body">
                    ${oldTextHtml}
                    ${structuredDataHtml}
                </div>
                <div class="card-footer">
                    ${completedDateHtml}
                    <div class="card-footer-right">${copyBtnHtml}${superActionHtml}${actionBtn}</div>
                </div>
            `;
            gridContainer.appendChild(card);
        });
    } catch (error) { console.error("订单数据加载失败", error); }
}

// 🌟🌟🌟 更新：一键生成并复制微信转发格式的物流信息 🌟🌟🌟
function copyOrderInfo(orderId) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    
    let isOperator = currentUser.role === 'operator';
    const typeText = (order.type == 1) ? '绝缘订单' : '中固订单';
    
    // 核心要求：绝缘订单截取 1-8 个字，中固订单截取 1-5 个字
    let nameLimit = (order.type == 1) ? 8 : 5;
    let shortGoodsName = (order.goods_name || '').replace(/\n/g, '').trim().substring(0, nameLimit);
    
    let clipText = `【${typeText}】\n`;
    if (order.receiver_name) clipText += `姓名：${order.receiver_name}\n`;
    if (!isOperator && order.receiver_phone) clipText += `电话：${order.receiver_phone}\n`;
    if (order.receiver_address) clipText += `地址：${order.receiver_address}\n`;
    
    if (shortGoodsName) clipText += `名称：${shortGoodsName}\n`;
    
    // 核心要求：数量和重量分开两排渲染
    if (order.goods_weight) clipText += `重量：${order.goods_weight}\n`;
    if (order.goods_quantity) clipText += `件数：${order.goods_quantity}\n`;
    
    if (order.goods_packaging) clipText += `包装：${order.goods_packaging}\n`;
    if (!isOperator && order.logistics_service) clipText += `服务：${order.logistics_service}\n`;
    if (order.remark) clipText += `备注：${order.remark}\n`;

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(clipText).then(() => {
            alert('✅ 极简物流信息已成功复制！\n可以直接去微信粘贴转发了。');
        }).catch(() => fallbackCopyTextToClipboard(clipText));
    } else {
        fallbackCopyTextToClipboard(clipText);
    }
}

function fallbackCopyTextToClipboard(text) {
    let textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.width = "2em";
    textArea.style.height = "2em";
    textArea.style.padding = "0";
    textArea.style.border = "none";
    textArea.style.outline = "none";
    textArea.style.boxShadow = "none";
    textArea.style.background = "transparent";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        document.execCommand('copy');
        alert('✅ 极简物流信息已成功复制！\n可以直接去微信粘贴转发了。');
    } catch (err) {
        alert('⚠️ 当前浏览器不支持自动复制，请手动选中并复制。');
    }
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
            if (currentUser.role === 'super_admin' || currentUser.role === 'admin') {
                actionHtml = `
                    <div class="capsule-right">
                        <button class="btn-outline-primary" style="padding:4px 10px; font-size:12px;" onclick="openEditMaterialModal(${item.id}, ${item.used}, ${item.produced}, '${safeRemark}')">修改备注</button>
                        <button class="btn-outline-danger" style="padding:4px 10px; font-size:12px;" onclick="deleteMaterialRecord(${item.id})">删除</button>
                    </div>
                `;
            }

            row.innerHTML = `
                <div class="capsule-left">
                    <div class="capsule-time">🕒 ${item.date}</div>
                    <div class="capsule-stats">
                        <span class="capsule-use-tag">用料：<strong>${item.used} kg</strong></span>
                        <span class="capsule-product-tag">成品：<strong>${item.produced} kg</strong></span>
                    </div>
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
        const response = await fetch(`${API_BASE}/materials`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ used: usedVal, produced: productVal })
        });
        if (response.ok) {
            toggleModal('uploadMaterialModal', false); 
            document.getElementById('successNotifyDetail').innerText = `物料报表数据已成功存入安全持久层：\n\n🔴 消耗原材料: ${usedVal} kg\n🟢 产出总成品: ${productVal} kg`;
            toggleModal('uploadSuccessNotifyModal', true);
            if(currentTab === 'materials') fetchMaterialRecords();
        }
    } catch (e) { alert('物料断网上传异常'); }
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
    } catch (e) { alert('更新总库异常'); }
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
    } catch (e) { alert('修改流水失败'); }
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
    if (targetStatus === 'completed') {
        tipText.innerText = "🛑 确认将以下订单标记为【已完成】吗？"; submitBtn.className = "btn-success";
    } else {
        tipText.innerText = "⚠️ 确认将以下订单恢复为【未完成】吗？"; submitBtn.className = "btn-warning";
    }
    toggleModal('statusConfirmModal', true);
}

async function submitUpdateOrderStatus() {
    const id = document.getElementById('confirmTargetId').value;
    const status = document.getElementById('confirmTargetStatus').value;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ status: status }) });
        if (response.ok) { toggleModal('statusConfirmModal', false); fetchOrders(); }
    } catch (error) { alert('调整状态失败'); }
}

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
        let name = '';
        let address = '';

        let strWithoutPhone = line2.replace(phone, '').replace(/(?:电话|联系方式|手机)[:：]?\s*/g, '');

        let nameMatch = strWithoutPhone.match(/(?:姓名|收货人)[:：]\s*([^\s。，,;；]{1,5})/);
        if (nameMatch) {
            name = nameMatch[1];
            strWithoutPhone = strWithoutPhone.replace(nameMatch[0], '');
        } else {
            let qMatch = strWithoutPhone.match(/[?？]\s*([^\s。，,;；:：]{1,4})/);
            if (qMatch) {
                name = qMatch[1];
                strWithoutPhone = strWithoutPhone.replace(qMatch[0], '');
            }
        }

        let addrMatch = strWithoutPhone.match(/(?:地址)[:：]\s*(.*)/);
        if (addrMatch) {
            address = addrMatch[1];
            strWithoutPhone = strWithoutPhone.replace(addrMatch[0], '');
        } else {
            address = strWithoutPhone; 
        }

        if (!name) {
            let parts = address.split(/[\s。，,;；]+/).filter(p => p.trim() !== '');
            let potentialName = parts.find(p => p.length >= 2 && p.length <= 4 && !/[省市区县镇村街道路号栋室楼]/.test(p));
            if (potentialName) {
                name = potentialName;
                address = address.replace(potentialName, '');
            } else {
                let fallbackParts = line2.split(phone);
                name = fallbackParts[0].replace(/收货人|电话|联系方式|:|：/g, '').trim();
                address = (fallbackParts[1] || '').replace(/^[。，,.;:\s]+/, '').trim();
                if (name.length > 6 && address.length <= 6) {
                    let temp = name; name = address; address = temp;
                }
            }
        }

        name = name.replace(/^[。，,;；\s]+|[。，,;；\s]+$/g, '').replace(/[?？]/g, '');
        address = address.replace(/(?:地址)[:：]?/g, '').replace(/^[。，,;；\s]+|[。，,;；\s]+$/g, '');
        
        document.getElementById(`${prefix}ReceiverName`).value = name;
        document.getElementById(`${prefix}ReceiverPhone`).value = phone;
        document.getElementById(`${prefix}ReceiverAddress`).value = address;
    }

    if (lines.length > 2) {
        let goodsStr = lines.slice(2).join('\n');
        document.getElementById(`${prefix}GoodsName`).value = goodsStr;

        let totalWeight = 0;
        let tempStr = goodsStr;

        let calcRegex1 = /(\d+(?:\.\d+)?)\s*(?:[A-Za-z\u4e00-\u9fa5]{0,6})?\s*([*xX✖️×\/÷])\s*(\d+(?:\.\d+)?)/g;
        let match;
        while ((match = calcRegex1.exec(tempStr)) !== null) {
            let num1 = parseFloat(match[1]);
            let op = match[2];
            let num2 = parseFloat(match[3]);
            let val = 0;
            
            if (/[*xX✖️×]/.test(op)) val = num1 * num2;
            else if (/[/÷]/.test(op)) val = num1 / num2;
            
            let prefixStr = tempStr.substring(0, match.index).trim();
            if (prefixStr.endsWith('-')) totalWeight -= val;
            else totalWeight += val; 

            tempStr = tempStr.substring(0, match.index) + " ".repeat(match[0].length) + tempStr.substring(match.index + match[0].length);
        }

        let calcRegex2 = /([+-])\s*(\d+(?:\.\d+)?)/g;
        while ((match = calcRegex2.exec(tempStr)) !== null) {
            let sign = match[1];
            let num = parseFloat(match[2]);
            if (sign === '+') totalWeight += num;
            else if (sign === '-') totalWeight -= num;
        }
        
        if (totalWeight !== 0) {
            totalWeight = Math.round(totalWeight * 100) / 100;
            document.getElementById(`${prefix}GoodsWeight`).value = totalWeight + 'kg';
        } else {
            document.getElementById(`${prefix}GoodsWeight`).value = '';
        }
    }
}

function validatePayload(payload) {
    if (!payload.receiver_phone || !payload.receiver_address || !payload.goods_name || !payload.goods_weight) {
        return '【收货电话】、【收货地址】、【货物名称】、【货物重量】为必填项，请补充完整！';
    }
    const phoneRegex = /^(?:1[3-9]\d{9}|0\d{2,3}-\d{7,8})$/;
    if (!phoneRegex.test(payload.receiver_phone)) {
        return '【收货电话】格式不正确！请确保是 11位手机号，或是包含中划线的座机号（如 0571-88538883）。';
    }
    return null; 
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
            switchTab('pending'); 
        }
    } catch (error) { alert('断网发单失败'); }
}

function openEditOrderModal(orderId) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    
    document.getElementById('editOrderId').value = order.id;
    document.getElementById('editOrderDate').value = order.date || '';
    document.getElementById('editOrderType').value = order.type !== undefined ? order.type : 0;
    document.getElementById('editOrderTitle').value = order.title || '';
    
    document.getElementById('editOrderClient').value = order.order_client || '';
    document.getElementById('editReceiverName').value = order.receiver_name || '';
    document.getElementById('editReceiverPhone').value = order.receiver_phone || '';
    document.getElementById('editReceiverAddress').value = order.receiver_address || '';
    document.getElementById('editGoodsName').value = order.goods_name || '';
    document.getElementById('editGoodsWeight').value = order.goods_weight || '';
    document.getElementById('editGoodsQuantity').value = order.goods_quantity || '';
    
    document.getElementById('editGoodsPackaging').value = order.goods_packaging || '桶装';
    document.getElementById('editLogisticsService').value = order.logistics_service || '送货上门+回单拍照回传';
    document.getElementById('editOrderRemark').value = order.remark || '';
    
    toggleModal('editOrderModal', true);
}

async function submitEditOrder() {
    const id = document.getElementById('editOrderId').value;
    const date = document.getElementById('editOrderDate').value.trim();
    if (!date) return alert('创建时间不能为空！');

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

async function deleteOrder(id) {
    if (!confirm(`安全警告：确定要物理【删除】单号为 #${id} 的订单吗？`)) return;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'DELETE', headers: getHeaders() });
        if (response.ok) fetchOrders();
    } catch (e) {}
}

async function createUser() {
    const usernameInput = document.getElementById('newUsername');
    const passwordInput = document.getElementById('newPassword');
    const roleSelect = document.getElementById('newRole');
    if (!usernameInput.value.trim() || !passwordInput.value.trim()) return alert('请填写完整数据');
    try {
        const response = await fetch(`${API_BASE}/users`, {
            method: 'POST', headers: getHeaders(),
            body: JSON.stringify({ username: usernameInput.value.trim(), password: passwordInput.value.trim(), role: roleSelect.value })
        });
        const data = await response.json();
        if (response.ok && data.success) {
            alert('系统级账号创建成功！'); usernameInput.value = ''; passwordInput.value = ''; toggleModal('addUserModal', false);
        }
    } catch (e) {}
}

async function openViewUserModal() { toggleModal('viewUserModal', true); await refreshUserList(); }

async function refreshUserList() {
    try {
        const response = await fetch(`${API_BASE}/users`, { method: 'GET', headers: getHeaders() });
        const users = await response.json();
        const container = document.getElementById('userListContainer');
        container.innerHTML = '';
        users.forEach(user => {
            const row = document.createElement('div');
            row.className = 'user-item-row';
            const actionHtml = user.username === '1' ? `<span style="color:#aaa; font-size:12px;">原始核心安全策略保护</span>` : `
                <input id="pwd_${user.username}" value="${user.password}" style="width:110px; padding:4px; font-size:12px; margin-right:5px;" />
                <button class="btn-outline-primary" style="padding:4px 8px; font-size:12px;" onclick="modifyUserPassword('${user.username}')">改密</button>
                <button class="btn-outline-danger" style="padding:4px 8px; font-size:12px;" onclick="deleteUser('${user.username}')">注销</button>
            `;
            row.innerHTML = `<div class="user-item-info"><h5>ID: ${user.username}</h5><span>岗位: <strong>${getRoleName(user.role)}</strong></span></div><div style="display:flex; align-items:center;">${actionHtml}</div>`;
            container.appendChild(row);
        });
    } catch (e) {}
}

async function modifyUserPassword(u) {
    const p = document.getElementById(`pwd_${u}`).value.trim();
    if(!p) return alert('不能为空');
    try { await fetch(`${API_BASE}/users/${u}/password`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ password: p }) }); alert('密码重置成功！'); } catch(e) {}
}
async function deleteUser(u) {
    if(!confirm(`确定要注销账号 ${u} 吗？`)) return;
    try { await fetch(`${API_BASE}/users/${u}`, { method: 'DELETE', headers: getHeaders() }); refreshUserList(); } catch(e) {}
}

window.onload = function() {
    const savedUser = localStorage.getItem('local_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        renderUI();
        initFilterDates();
        switchTab('pending');
        setInterval(function() {
            refreshDashboardData();
            if (!document.getElementById('viewUserModal').classList.contains('hidden')) refreshUserList();
        }, 3000); 
    } else { renderUI(); }
};