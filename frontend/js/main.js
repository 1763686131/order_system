/* ========================================================
 * 🌟 核心运行配置与安全鉴权体系 (从旧项目完整移植)
 * ======================================================== */
const API_BASE = '/api';
let currentUser = { username: '', name: '', role: '', permissions: [] }; 
let allOrdersLocal = []; 
let currentTab = 'pending'; 

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
 * 🚀 NOMI 小圆(Xiao Yuan) 权限渲染引擎
 * ======================================================== */
function renderUI() {
    const loginSection = document.getElementById('loginSection');
    const mainSection = document.getElementById('mainSection');
    const fabContainer = document.getElementById('fabContainer');
    
    // 没登录：显示登录遮罩，把主界面和小圆藏起来
    if (!currentUser.username) {
        loginSection.classList.remove('hidden');
        mainSection.style.display = 'none';
        fabContainer.style.display = 'none';
        return;
    }

    // 登录成功：显示主界面和小圆，藏起登录遮罩
    loginSection.classList.add('hidden');
    mainSection.style.display = 'block';
    fabContainer.style.display = 'block';

    // 🌟 给小圆“注入灵魂”：根据身份决定她身上能展开哪些功能！
    const btnOpenViewUser = document.getElementById('btnOpenViewUser');
    const fabAddOrder = document.getElementById('fabAddOrder');
    const fabAddMaterial = document.getElementById('fabAddMaterial');

    // 只有管理员以上身份，小圆才会长出“账户控制”功能
    if (['super_admin', 'admin'].includes(currentUser.role)) {
        btnOpenViewUser.style.display = 'block';
    } else {
        btnOpenViewUser.style.display = 'none';
    }

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
            renderUI();
            
            // 登录成功后小圆立刻说话欢迎
            setTimeout(() => {
                const speechBubble = document.getElementById('aiSpeechBubble');
                if(speechBubble) {
                    speechBubble.textContent = `欢迎回来，${currentUser.name || currentUser.username} 主人！`;
                    speechBubble.classList.add('show');
                    setTimeout(() => speechBubble.classList.remove('show'), 4000);
                }
            }, 1000);
            
        } else { alert(resData.message || '凭证错误，登录失败'); }
    } catch (error) { alert('本地服务端连接失败，请检查 Docker。'); }
}

function handleLogout() {
    currentUser = { username: '', name: '', role: '', permissions: [] };
    localStorage.removeItem('local_user');
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
    renderUI();
}


/* ========================================================
 * 👥 账户与权限管理核心控制台 (从旧项目 100% 移植保留)
 * ======================================================== */
const PERMISSIONS_CONFIG = [
    {
        group: 'pending_order', label: '📦 未完成订单权限',
        children: [
            { key: 'pending.add', label: '操作：发布新订单' },
            { key: 'pending.complete', label: '操作：完成业务' },
            { key: 'pending.copy', label: '操作：复制物流' },
            { key: 'pending.edit', label: '操作：修改订单' },
            { key: 'pending.delete', label: '操作：删除订单' }
        ]
    },
    {
        group: 'completed_order', label: '✅ 已完成订单权限',
        children: [
            { key: 'completed.uncomplete', label: '操作：撤销完成状态' },
            { key: 'completed.delete', label: '操作：删除订单' }
        ]
    },
    {
        group: 'material', label: '🛢️ 生产物料库权限',
        children: [
            { key: 'material.add', label: '操作：录入消耗与产出' },
            { key: 'material.edit', label: '操作：修改流水备注' },
            { key: 'material.edit_stock', label: '操作：调整总物理库存' },
            { key: 'material.delete', label: '操作：删除流水记录' }
        ]
    }
];

let currentEditUser = null; 

function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (show) modal.classList.remove('hidden');
    else modal.classList.add('hidden');
}

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
            
            if (currentUser.role === 'admin' && user.role !== 'employee' && user.role !== 'operator') {
                return; 
            }

            let roleName = getRoleName(user.role);
            let color = user.role === 'super_admin' ? '#ff4d4f' : (user.role === 'admin' ? '#faad14' : '#52c41a');
            let displayName = user.name ? user.name : user.username;
            
            row.innerHTML = `<div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size: 15px; font-weight: bold; color: #333;">👤 ${displayName} <span style="font-size:12px;color:#999;font-weight:normal;">(${user.username})</span></span>
                <span style="font-size: 12px; background: ${color}20; color: ${color}; padding: 2px 8px; border-radius: 12px; font-weight: bold;">${roleName}</span>
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
    document.getElementById('detailName').value = '';
    document.getElementById('detailPassword').value = '';
    
    document.getElementById('btnUpdatePwd').style.display = 'none';
    document.getElementById('btnDeleteUser').style.display = 'none';
    document.getElementById('btnSaveUser').style.display = 'inline-block';
    
    document.getElementById('detailRole').style.display = 'inline-block';
    document.getElementById('detailRoleText').style.display = 'none';
    
    renderPermissionTree([]);
}

function loadUserDetail(user) {
    currentEditUser = user;
    document.querySelectorAll('.user-list-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    document.getElementById('userDetailPanel').style.display = 'block';
    let detailDisplayName = user.name ? user.name : user.username;
    document.getElementById('detailTitle').innerText = `⚙️ 配置用户：${detailDisplayName}`;
    
    document.getElementById('detailUsername').value = user.username;
    document.getElementById('detailUsername').disabled = true; 
    document.getElementById('detailName').value = user.name || ''; 
    document.getElementById('detailPassword').value = user.password;
    
    document.getElementById('btnUpdatePwd').style.display = 'inline-block';
    document.getElementById('btnSaveUser').style.display = 'inline-block';
    
    if (currentUser.role === 'super_admin' && user.role !== 'super_admin') {
        document.getElementById('btnDeleteUser').style.display = 'inline-block';
    } else {
        document.getElementById('btnDeleteUser').style.display = 'none';
    }
    
    const roleSelect = document.getElementById('detailRole');
    const roleText = document.getElementById('detailRoleText');
    if (user.role === 'super_admin') {
        roleSelect.style.display = 'none';
        roleText.style.display = 'inline-block';
        roleText.innerText = '最高级安全守护者 (不可更改)';
        document.getElementById('permissionsWrapper').style.display = 'none'; 
    } else {
        roleSelect.style.display = 'inline-block';
        roleText.style.display = 'none';
        roleSelect.value = (user.role === 'operator') ? 'employee' : user.role;
        document.getElementById('permissionsWrapper').style.display = 'block';
        
        if (currentUser.role === 'admin') roleSelect.disabled = true;
        else roleSelect.disabled = false;
        
        renderPermissionTree(user.permissions || []);
    }
}

function renderPermissionTree(userPerms) {
    let treeHtml = '';
    const adminRestricted = ['pending.edit', 'pending.delete', 'completed.delete', 'material.edit', 'material.edit_stock', 'material.delete'];

    PERMISSIONS_CONFIG.forEach(group => {
        treeHtml += `<div class="perm-group">
            <label><input type="checkbox" class="perm-parent" data-group="${group.group}" onchange="toggleGroupPerms(this)"> ${group.label}</label>
            <div class="perm-children">`;

        group.children.forEach(child => {
            let isChecked = userPerms.includes(child.key) ? 'checked' : '';
            let disabledStr = '';
            let labelClass = '';
            if (currentUser.role === 'admin' && adminRestricted.includes(child.key)) {
                disabledStr = 'disabled title="系统限制：管理员无权授予或撤销此危险权限"';
                labelClass = 'disabled-perm';
            }
            treeHtml += `<label class="${labelClass}"><input type="checkbox" class="perm-cb" value="${child.key}" data-group="${group.group}" onchange="checkParentPerm(this)" ${isChecked} ${disabledStr}> ${child.label}</label>`;
        });
        
        treeHtml += `</div></div>`;
    });
    
    document.getElementById('permTreeContainer').innerHTML = treeHtml;
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
    parentCb.checked = Array.from(cbs).some(cb => cb.checked);
}

function getSelectedPermissions() {
    const perms = [];
    document.querySelectorAll('.perm-cb:checked').forEach(cb => perms.push(cb.value));
    return perms;
}

async function saveUserData() {
    const n = document.getElementById('detailName').value.trim(); 

    if (!currentEditUser) {
        const u = document.getElementById('detailUsername').value.trim();
        const p = document.getElementById('detailPassword').value.trim();
        const r = document.getElementById('detailRole').value;
        if (!u || !p) return alert('账号密码不能为空！');
        
        const payload = { username: u, name: n, password: p, role: r, permissions: getSelectedPermissions() };
        try {
            const res = await fetch(`${API_BASE}/users`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(payload) });
            if (res.ok) { alert('✨ 新系统账户创建并赋权成功！'); window.location.reload(); } 
            else alert('账户名称已存在或无权限！');
        } catch(e) { alert('网络异常'); }
    } else {
        const r = document.getElementById('detailRole').value;
        const payload = { name: n, permissions: getSelectedPermissions(), role: r }; 
        try {
            const res = await fetch(`${API_BASE}/users/${currentEditUser.username}/permissions`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify(payload) });
            if (res.ok) { alert(`✅ 已成功更新信息！`); window.location.reload(); } 
            else alert('更新失败，可能权限不足');
        } catch(e) { alert('更新权限失败'); }
    }
}

async function updateUserPassword() {
    if (!currentEditUser) return;
    const p = document.getElementById('detailPassword').value.trim();
    if(!p) return alert('密码不能为空');
    try { 
        const res = await fetch(`${API_BASE}/users/${currentEditUser.username}/password`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ password: p }) }); 
        if (res.ok) { alert('✅ 密码重置成功！'); window.location.reload(); }
    } catch(e) {}
}

async function deleteCurrentUser() {
    if (!currentEditUser) return;
    if (!confirm(`💣 严重警告：确定要彻底物理删除账户 [${currentEditUser.username}] 吗？`)) return;
    try { 
        const res = await fetch(`${API_BASE}/users/${currentEditUser.username}`, { method: 'DELETE', headers: getHeaders() }); 
        if (res.ok) { alert('账户已彻底销毁！'); window.location.reload(); } 
        else alert('❌ 物理销毁失败：接口异常或越权操作');
    } catch(e) {}
}


/* ========================================================
 * 第一部分：全新 UI 界面的交互动效 (完全来自 test.html 原作，一字未改)
 * ======================================================== */
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

function closeFabMenuOnOutsideClick(e) {
  if (fabContainer && fabContainer.classList.contains('active') && !fabContainer.contains(e.target)) {
    fabContainer.classList.remove('active');
  }
}
document.addEventListener('mousedown', closeFabMenuOnOutsideClick);
document.addEventListener('touchstart', closeFabMenuOnOutsideClick, { passive: true });

const fabItemsList = document.querySelectorAll('.fab-item');
fabItemsList.forEach(item => {
  item.addEventListener('click', function() {
    setTimeout(() => { fabContainer.classList.remove('active'); }, 100);
  });
});

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
  if (!fabContainer || !speechBubble) return;
  if (fabContainer.classList.contains('active') || isDragging) return;
  const randomPhrase = aiPhrases[Math.floor(Math.random() * aiPhrases.length)];
  speechBubble.textContent = randomPhrase;
  speechBubble.classList.add('show');
  setTimeout(() => { speechBubble.classList.remove('show'); }, 4000);
}
setInterval(triggerAiSpeech, 30000);


/* ========================================================
 * 🔄 系统初始化启动挂载点
 * ======================================================== */
window.onload = function() {
    const savedUser = localStorage.getItem('local_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        if (!currentUser.permissions) currentUser.permissions = [];
        renderUI();
    } else {
        renderUI(); // 如果没登录，渲染引擎会拉起登录遮罩
    }
};