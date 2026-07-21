/* ========================================================
 * 🛠️ 全局公共工具库 (tools.js)
 * ========================================================
 * 封装与具体业务逻辑无关的纯净工具函数
 */

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
function calculateTextScale(text, targetLen = 14) {
    if (!text) return 1;
    let currentLen = 0;
    
    for(let i = 0; i < text.length; i++) {
        let char = text[i];
        
        // 1. 汉字及全角标点符号 (最宽，基准值为 1)
        if (/[\u4e00-\u9fa5\u3000-\u303F\uFF00-\uFFEF]/.test(char)) {
            currentLen += 1.0; 
        } 
        // 2. 大写英文字母 (精细拆分)
        else if (/[A-Z]/.test(char)) {
            if (/[WM]/.test(char)) currentLen += 0.95; // W和M极宽，几乎等同于汉字
            else if (/[OQD]/.test(char)) currentLen += 0.85; 
            else if (/[I]/.test(char)) currentLen += 0.45; // I特别瘦
            else currentLen += 0.75; // 普通大写字母
        } 
        // 3. 小写英文字母 (精细拆分)
        else if (/[a-z]/.test(char)) {
            if (/[wm]/.test(char)) currentLen += 0.8; 
            else if (/[iljt]/.test(char)) currentLen += 0.4; // 这些小写字母很瘦
            else currentLen += 0.6; // 普通小写字母
        } 
        // 4. 数字 (精细拆分)
        else if (/[0-9]/.test(char)) {
            if (char === '1') currentLen += 0.45; // 1特别瘦
            else currentLen += 0.65; // 0,8,9等数字偏宽
        } 
        // 5. 空格与其他半角符号
        else {
            if (char === ' ') currentLen += 0.3; 
            else currentLen += 0.5; 
        }
    }
    
    if (currentLen === 0) return 1;
    
    // 计算缩放比例：基准长度 / 实际视觉长度
    let scale = targetLen / currentLen;
    
    // 限制缩放范围：最大放大 1.15 倍，最小缩小 0.35 倍（保证再极端的长文本也能缩得下）
    return Math.min(Math.max(scale, 0.35), 1.15);
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
// 🔍 优雅的全屏大图预览引擎 (Lightbox) - 附带3D旋转与悬浮操作台
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
    overlay.style.flexDirection = 'column'; // 垂直排版，上面图片，下面按钮
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.opacity = '0';
    overlay.style.transition = 'opacity 0.2s ease';

    // 2. 创建大图 (采用 vmin 视口最小限制，保证旋转90度时绝不爆出屏幕)
    const img = document.createElement('img');
    img.src = src;
    img.style.maxWidth = '85vmin'; 
    img.style.maxHeight = '85vmin';
    img.style.objectFit = 'contain';
    img.style.borderRadius = '8px';
    img.style.boxShadow = '0 10px 40px rgba(0,0,0,0.6)';
    img.style.transform = 'scale(0.8) rotate(0deg)';
    img.style.transition = 'transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)'; // 极致丝滑的弹性动画

    let currentRotation = 0; // 记录当前旋转角度

    // 3. 创建底部悬浮毛玻璃操作台
    const toolbar = document.createElement('div');
    toolbar.style.marginTop = '35px';
    toolbar.style.display = 'flex';
    toolbar.style.gap = '20px';
    toolbar.style.zIndex = '1000000';

    // 🌀 旋转按钮
    const rotateBtn = document.createElement('button');
    rotateBtn.innerHTML = '↻ 旋转 90°';
    rotateBtn.style.padding = '10px 28px';
    rotateBtn.style.fontSize = '15px';
    rotateBtn.style.fontWeight = 'bold';
    rotateBtn.style.color = '#fff';
    rotateBtn.style.background = 'rgba(255, 255, 255, 0.15)';
    rotateBtn.style.border = '1px solid rgba(255, 255, 255, 0.3)';
    rotateBtn.style.borderRadius = '30px';
    rotateBtn.style.cursor = 'pointer';
    rotateBtn.style.backdropFilter = 'blur(8px)'; // 毛玻璃特效
    rotateBtn.style.transition = 'all 0.2s';
    
    rotateBtn.onmouseover = () => rotateBtn.style.background = 'rgba(255, 255, 255, 0.25)';
    rotateBtn.onmouseout = () => rotateBtn.style.background = 'rgba(255, 255, 255, 0.15)';
    
    // 点击旋转逻辑 (阻止冒泡防止关闭弹窗)
    rotateBtn.onclick = function(e) {
        e.stopPropagation(); 
        currentRotation += 90;
        img.style.transform = `scale(1) rotate(${currentRotation}deg)`;
    };

    // ❌ 关闭按钮
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕ 关闭预览';
    closeBtn.style.padding = '10px 28px';
    closeBtn.style.fontSize = '15px';
    closeBtn.style.fontWeight = 'bold';
    closeBtn.style.color = '#fff';
    closeBtn.style.background = 'rgba(255, 77, 79, 0.8)';
    closeBtn.style.border = '1px solid rgba(255, 77, 79, 0.5)';
    closeBtn.style.borderRadius = '30px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.transition = 'all 0.2s';
    
    closeBtn.onmouseover = () => closeBtn.style.background = 'rgba(255, 77, 79, 1)';
    closeBtn.onmouseout = () => closeBtn.style.background = 'rgba(255, 77, 79, 0.8)';

    // 统一的关闭函数
    const closeOverlay = function() {
        overlay.style.opacity = '0';
        img.style.transform = `scale(0.8) rotate(${currentRotation}deg)`; // 保持当前角度缩小隐藏
        setTimeout(() => {
            if (document.body.contains(overlay)) {
                document.body.removeChild(overlay);
            }
        }, 200);
    };

    closeBtn.onclick = function(e) {
        e.stopPropagation();
        closeOverlay();
    };

    toolbar.appendChild(rotateBtn);
    toolbar.appendChild(closeBtn);

    overlay.appendChild(img);
    overlay.appendChild(toolbar);
    document.body.appendChild(overlay);

    // 4. 入场丝滑放大动画
    requestAnimationFrame(() => {
        overlay.style.opacity = '1';
        img.style.transform = 'scale(1) rotate(0deg)';
    });

    // 5. 点击遮罩层的空白黑底区域，也能优雅关闭
    overlay.onclick = function(e) {
        if (e.target === overlay) {
            closeOverlay();
        }
    };
};