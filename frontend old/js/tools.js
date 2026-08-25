/* ========================================================
 * 🛠️ 全局公共工具库 (tools.js)
 * ========================================================
 * 封装与具体业务逻辑无关的纯净工具函数
 */
// 1. 禁用右键菜单和触摸屏长按弹出的菜单
document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});

// 2. 禁用 F12, F5, Ctrl+R, Ctrl+Shift+I 等开发者快捷键
document.addEventListener('keydown', function(e) {
    if (
        e.key === 'F12' || 
        (e.ctrlKey && e.shiftKey && e.key === 'I') || // 开发者工具
        e.key === 'F5' ||                             // 刷新
        (e.ctrlKey && e.key === 'r') ||               // 刷新
        (e.altKey && e.key === 'ArrowLeft') ||        // 快捷键后退
        (e.altKey && e.key === 'ArrowRight')          // 快捷键前进
    ) {
        e.preventDefault();
    }
});

// 1. 基础文本换行转义
function formatTextWithBreaks(text) { 
    return !text ? '' : text.replace(/\n/g, '<br>'); 
}

// 2. 获取当前高精度时间 (精确到分)
function getCurrentDateTime() {
    const now = new Date();
    const Y = now.getFullYear(); const M = String(now.getMonth() + 1).padStart(2, '0'); const D = String(now.getDate()).padStart(2, '0');
    const h = String(now.getHours()).padStart(2, '0'); const m = String(now.getMinutes()).padStart(2, '0');
    return `${Y}-${M}-${D} ${h}:${m}`;
}

// 3. 智能单行文本动态缩放比例引擎 (像素级视觉权重版)
/* =========================================================
 * 📏 智能视觉权重精算引擎 (融合局部放大翻倍补偿算法)
 * ========================================================= */
function calculateTextScale(text, maxChars = 12, isHighlightMode = false) {
    if (!text) return 1;
    let len = 0;
    
    for (let i = 0; i < text.length; i++) {
        let char = text[i];
        
        // 1. 中文字符（不受影响，固定算 1 个单位）
        if (char.match(/[\u4e00-\u9fa5]/)) {
            len += 1;
        }
        // 2. 🌟 终极修复：如果处于放大模式，且匹配到了会被 CSS 放大的【英文/数字/小数点】
        else if (isHighlightMode && char.match(/[a-zA-Z0-9.]/)) {
            // 因为 CSS 把它们放大了，所以我们把它们的长度权重直接“翻倍”！
            if (char.match(/[A-Z]/)) len += 1.8;      // 大写字母极宽，算1.8
            else if (char.match(/[0-9]/)) len += 1.4; // 数字，算1.4
            else len += 1.1;                          // 小写字母和点，算1.1
        }
        // 3. 普通模式下的英文字母和数字（未被放大）
        else {
            if (char.match(/[A-Z]/)) len += 0.9;
            else if (char.match(/[0-9]/)) len += 0.7;
            else len += 0.55;
        }
    }

    if (len <= maxChars) return 1;
    let scale = maxChars / len;
    return Math.max(scale, 0.35); // 最小缩放兜底，防看不清
}

// 4. 兼容性剪贴板复制兜底工具
function fallbackCopyTextToClipboard(text) {
    let textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed"; textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus(); textArea.select();
    try { 
        document.execCommand('copy'); 
        alert('✅ 极简物流信息已成功复制！'); 
    } catch (err) { 
        alert('⚠️ 自动复制失败，请手动复制。'); 
    }
    document.body.removeChild(textArea);
}

// 5. 新增/修改表单的有效性数据校验
function validatePayload(payload) {
    if (!payload.receiver_phone || !payload.receiver_address || !payload.goods_name || !payload.goods_weight) return '【收货电话】、【地址】、【名称】、【重量】为必填项！';
    if (!/^(?:1[3-9]\d{9}|0\d{2,3}-\d{7,8})$/.test(payload.receiver_phone)) return '【收货电话】格式不正确！必须是11位手机号或带区号的座机。';
    return null; 
}

// 6. 订单长文本智能一键分词与表单填充引擎
/* =========================================================
 * ⚡ 智能订单解析引擎 (双模版：支持系统标准化复制 + 原有高级模糊算术引擎)
 * ========================================================= */
function smartParse(prefix) {
    const text = document.getElementById(`${prefix}OrderTitle`).value;
    if (!text.trim()) return alert('请先在上方输入框粘贴或填写内容，再点击识别！');
    const lines = text.split('\n').map(l => l.trim()).filter(l => l !== '');
    if (lines.length === 0) return;

    // =====================================================
    // 🌟 模式 1：系统标准化复制文本 (完美精准逆向解析)
    // =====================================================
    if (text.startsWith('【中固订单】') || text.startsWith('【绝缘订单】')) {
        // 1. 自动切换顶部的“订单类型”下拉框
        const orderTypeSelect = document.getElementById(`${prefix}OrderType`);
        if (orderTypeSelect) {
            orderTypeSelect.value = text.startsWith('【中固订单】') ? "0" : "1";
        }

        // 2. 历遍剩下的每一行，通过冒号分割成字典 (兼容全角和半角冒号)
        const dataMap = {};
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i];
            const separatorIndex = line.includes('：') ? line.indexOf('：') : line.indexOf(':');
            if (separatorIndex !== -1) {
                const key = line.substring(0, separatorIndex).trim();
                const val = line.substring(separatorIndex + 1).trim();
                dataMap[key] = val;
            }
        }

        // 3. 将字典中的值，精准填入右侧表单对应位置
        const setVal = (idSuffix, val) => {
            const el = document.getElementById(prefix + idSuffix);
            if (el && val !== undefined) el.value = val;
        };

        setVal('ReceiverName', dataMap['姓名']);
        setVal('ReceiverPhone', dataMap['电话']);
        setVal('ReceiverAddress', dataMap['地址']);
        setVal('GoodsName', dataMap['名称']);
        setVal('GoodsWeight', dataMap['重量']);
        setVal('GoodsQuantity', dataMap['件数']);
        setVal('GoodsPackaging', dataMap['包装']);
        setVal('LogisticsService', dataMap['服务']);

        // 触发你之前要的“自动清洗算术符号”机制
        const elGoodsName = document.getElementById(`${prefix}GoodsName`);
        if (elGoodsName) elGoodsName.dispatchEvent(new Event('blur'));

        alert("✅ 检测到标准化系统复制格式，表单已精准无缝填充！");
        return; // 🛑 核心：如果是标准文本，到这里直接结束，不再执行下方的模糊解析
    }

    // =====================================================
    // 🧠 模式 2：执行你原有的高级模糊提取与重量算术引擎
    // =====================================================
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
        let addrMatch = strWithoutPhone.match(/(?:地址)[:：]?\s*(.*)/);
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

        // 同样在模糊匹配结束后，触发挥发清洗功能
        const elGoodsName = document.getElementById(`${prefix}GoodsName`);
        if (elGoodsName) elGoodsName.dispatchEvent(new Event('blur'));
    }
}



// ========================================================
// 🖱️ 万能图片拖拽上传引擎 (抽象工具类)
// ========================================================
/**
 * 为指定的区域绑定拖拽上传功能
 * @param {string} dropZoneId - 接收拖拽的容器 ID
 * @param {string} inputId - 隐藏的 input[type="file"] 的 ID
 * @param {function} previewCallback - 拿到文件后触发的预览回调函数
 */
window.enableDragAndDropUpload = function(dropZoneId, inputId, previewCallback) {
    window.addEventListener('load', function() {
        const dropZone = document.getElementById(dropZoneId);
        const fileInput = document.getElementById(inputId);
        if (!dropZone || !fileInput) return;

        // 1. 阻止浏览器默认的全屏打开图片行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // 2. 视觉反馈：拖入时泛起猛男粉
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.style.backgroundColor = '#fff0f6';
                dropZone.style.borderRadius = '8px';
                dropZone.style.border = '2px dashed #eb2f96';
                dropZone.style.transition = 'all 0.2s';
            }, false);
        });

        // 3. 视觉恢复：移开或松手后恢复原样
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.style.backgroundColor = '';
                dropZone.style.border = '';
            }, false);
        });

        // 4. 核心拦截：松手移交文件
        dropZone.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files && files.length > 0) {
                const file = files[0];
                if (!file.type.startsWith('image/')) {
                    alert('安全拦截：请拖入有效的图片文件（如 jpg, png 等）！');
                    return;
                }
                
                // 把文件强制塞给隐藏的 input
                fileInput.files = files; 
                
                // 触发回调函数进行本地预览渲染
                if (typeof previewCallback === 'function') {
                    previewCallback({ target: fileInput });
                }
            }
        }, false);
    });
    
}

// ========================================================
// 🔍 优雅的全屏大图预览引擎 (Lightbox) - 极致纯净大图版
// ========================================================
window.openLargeImagePreview = function(src) {
    if (!src) return;
    
    // 1. 创建一层深色半透明的全屏遮罩
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.85)';
    overlay.style.zIndex = '999999'; 
    overlay.style.display = 'flex';
    // 删除了垂直排版，因为下面没有按钮了
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.opacity = '0';
    overlay.style.cursor = 'zoom-out'; // 鼠标变成缩小放大镜手势，提示“点击即可关闭”
    overlay.style.transition = 'opacity 0.2s ease';

    // 2. 创建大图 (去除旋转逻辑后，没有爆出屏幕的风险，尺寸直接拉满)
    const img = document.createElement('img');
    img.src = src;
    img.style.maxWidth = '95vw';   // 横向拉大到 95% 屏幕宽度
    img.style.maxHeight = '95vh';  // 纵向拉大到 95% 屏幕高度
    img.style.objectFit = 'contain';
    img.style.borderRadius = '8px';
    img.style.boxShadow = '0 10px 40px rgba(0,0,0,0.6)';
    img.style.transform = 'scale(0.8)'; // 取消了旋转角度的记忆
    img.style.transition = 'transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)'; // 极致丝滑的弹性动画

    // 3. 统一的关闭函数 (清除了旋转相关的角度重置)
    const closeOverlay = function() {
        overlay.style.opacity = '0';
        img.style.transform = 'scale(0.8)'; // 保持缩小隐藏
        setTimeout(() => {
            if (document.body.contains(overlay)) {
                document.body.removeChild(overlay);
            }
        }, 200);
    };

    // 把图片塞进遮罩层，直接上树！(不需要 toolbar 了)
    overlay.appendChild(img);
    document.body.appendChild(overlay);

    // 4. 入场丝滑放大动画
    requestAnimationFrame(() => {
        overlay.style.opacity = '1';
        img.style.transform = 'scale(1)';
    });

    // 5. 点击遮罩层的空白黑底区域或者图片，直接优雅关闭
    // 删除了之前的 if(e.target === overlay) 限制，现在随便盲点屏幕任何一处都能关
    overlay.onclick = function() {
        closeOverlay();
    };
};



