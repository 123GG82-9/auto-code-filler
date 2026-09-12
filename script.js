class AutoCodeFiller {
    constructor() {
        this.inputPos = null;
        this.submitPos = null;
        this.isMarking = false;
        this.codes = [];
        this.isRunning = false;
        this.currentIndex = 0;
        this.markingMode = null;
        
        this.initElements();
        this.bindEvents();
    }

    initElements() {
        // 按钮
        this.markInputBtn = document.getElementById('markInputBtn');
        this.markSubmitBtn = document.getElementById('markSubmitBtn');
        this.resetMarkBtn = document.getElementById('resetMarkBtn');
        this.loadFromFileBtn = document.getElementById('loadFromFileBtn');
        this.clearInputBtn = document.getElementById('clearInputBtn');
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        
        // 输入框
        this.codeInput = document.getElementById('codeInput');
        this.delayInput = document.getElementById('delayInput');
        this.retryInput = document.getElementById('retryInput');
        this.autoClickCheck = document.getElementById('autoClickCheck');
        this.fileInput = document.getElementById('fileInput');
        
        // 显示元素
        this.inputPosSpan = document.getElementById('inputPos');
        this.submitPosSpan = document.getElementById('submitPos');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.logBox = document.getElementById('logBox');
        
        // 覆盖层
        this.markingOverlay = document.getElementById('markingOverlay');
    }

    bindEvents() {
        this.markInputBtn.addEventListener('click', () => this.startMarking('input'));
        this.markSubmitBtn.addEventListener('click', () => this.startMarking('submit'));
        this.resetMarkBtn.addEventListener('click', () => this.resetMarks());
        this.loadFromFileBtn.addEventListener('click', () => this.fileInput.click());
        this.clearInputBtn.addEventListener('click', () => this.codeInput.value = '');
        this.startBtn.addEventListener('click', () => this.start());
        this.stopBtn.addEventListener('click', () => this.stop());
        
        this.fileInput.addEventListener('change', (e) => this.loadFromFile(e));
        this.markingOverlay.addEventListener('click', (e) => this.capturePosition(e));
        document.addEventListener('mousemove', (e) => this.updateCursorPosition(e));
    }

    startMarking(mode) {
        this.isMarking = true;
        this.markingMode = mode;
        this.markingOverlay.classList.add('active', `marking-${mode}`);
        
        if (mode === 'input') {
            this.markInputBtn.disabled = true;
        } else {
            this.markSubmitBtn.disabled = true;
        }
    }

    capturePosition(e) {
        if (!this.isMarking) return;

        const x = e.clientX;
        const y = e.clientY;

        if (this.markingMode === 'input') {
            this.inputPos = { x, y };
            this.inputPosSpan.textContent = `(${x}, ${y})`;
            this.markInputBtn.disabled = false;
        } else if (this.markingMode === 'submit') {
            this.submitPos = { x, y };
            this.submitPosSpan.textContent = `(${x}, ${y})`;
            this.markSubmitBtn.disabled = false;
        }

        this.isMarking = false;
        this.markingMode = null;
        this.markingOverlay.classList.remove('active', 'marking-input', 'marking-submit');
        this.addLog(`已标记 ${this.markingMode === 'input' ? '输入框' : '确认按钮'} 位置: (${x}, ${y})`, 'success');
    }

    updateCursorPosition(e) {
        if (!this.isMarking) return;
        
        const x = e.clientX;
        const y = e.clientY;
        
        let indicator = document.querySelector('.mark-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = `mark-indicator ${this.markingMode}`;
            document.body.appendChild(indicator);
        }
        
        indicator.style.left = (x - 25) + 'px';
        indicator.style.top = (y - 25) + 'px';
    }

    resetMarks() {
        this.inputPos = null;
        this.submitPos = null;
        this.inputPosSpan.textContent = '未标记';
        this.submitPosSpan.textContent = '未标记';
        this.markInputBtn.disabled = false;
        this.markSubmitBtn.disabled = false;
        this.addLog('已重置所有标记', 'info');
    }

    loadFromFile(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const content = event.target.result;
            this.codeInput.value = content;
            this.addLog(`已加载文件: ${file.name}`, 'success');
        };
        reader.readAsText(file);
    }

    async start() {
        if (!this.inputPos || !this.submitPos) {
            this.addLog('❌ 错误: 请先标记输入框和确认按钮位置', 'error');
            return;
        }

        const codeText = this.codeInput.value.trim();
        if (!codeText) {
            this.addLog('❌ 错误: 请输入代码', 'error');
            return;
        }

        this.codes = codeText.split('\n').map(code => code.trim()).filter(code => code);
        if (this.codes.length === 0) {
            this.addLog('❌ 错误: 没有有效的代码', 'error');
            return;
        }

        this.isRunning = true;
        this.currentIndex = 0;
        this.startBtn.disabled = true;
        this.stopBtn.disabled = false;
        
        this.addLog(`📝 开始填写 ${this.codes.length} 个代码`, 'info');
        
        await this.fillCodes();
    }

    async fillCodes() {
        const delay = parseInt(this.delayInput.value);
        const retries = parseInt(this.retryInput.value);
        const autoClick = this.autoClickCheck.checked;

        while (this.currentIndex < this.codes.length && this.isRunning) {
            const code = this.codes[this.currentIndex];
            let success = false;

            for (let attempt = 1; attempt <= retries; attempt++) {
                if (!this.isRunning) break;

                try {
                    this.addLog(`📌 第 ${this.currentIndex + 1}/${this.codes.length} 次 (尝试 ${attempt}/${retries}): 输入 "${code}"`, 'info');
                    
                    // 获取输入框元素
                    const inputElement = this.getElementAtPosition(this.inputPos);
                    
                    if (!inputElement) {
                        throw new Error('未找到输入框元素');
                    }

                    // 清空输入框
                    inputElement.value = '';
                    inputElement.click();
                    inputElement.focus();

                    // 等待焦点稳定
                    await this.sleep(100);

                    // 逐字输入
                    await this.typeCode(inputElement, code);

                    this.addLog(`✅ 成功输入: "${code}"`, 'success');

                    // 自动点击确认按钮
                    if (autoClick) {
                        await this.sleep(200);
                        const submitElement = this.getElementAtPosition(this.submitPos);
                        
                        if (submitElement) {
                            submitElement.click();
                            this.addLog(`🔘 已点击确认按钮`, 'info');
                            await this.sleep(delay);
                        } else {
                            this.addLog(`⚠️ 未找到确认按钮`, 'warning');
                        }
                    } else {
                        await this.sleep(delay);
                    }

                    success = true;
                    break;

                } catch (error) {
                    this.addLog(`❌ 尝试 ${attempt} 失败: ${error.message}`, 'error');
                    
                    if (attempt < retries) {
                        await this.sleep(1000);
                    }
                }
            }

            if (success) {
                this.currentIndex++;
            } else {
                this.addLog(`⏭️ 跳过该代码，继续下一个`, 'warning');
                this.currentIndex++;
            }

            // 更新进度
            this.updateProgress();
        }

        if (this.isRunning) {
            this.addLog(`✨ 完成! 已填写 ${this.currentIndex}/${this.codes.length} 个代码`, 'success');
        } else {
            this.addLog(`⛔ 已停止，完成 ${this.currentIndex}/${this.codes.length} 个代码`, 'warning');
        }

        this.isRunning = false;
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
    }

    async typeCode(element, code) {
        for (const char of code) {
            element.value += char;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            await this.sleep(50);
        }
    }

    getElementAtPosition(pos) {
        return document.elementFromPoint(pos.x, pos.y);
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    updateProgress() {
        const progress = (this.currentIndex / this.codes.length) * 100;
        this.progressFill.style.width = progress + '%';
        this.progressText.textContent = `进度: ${this.currentIndex}/${this.codes.length} (${Math.round(progress)}%)`;
    }

    stop() {
        this.isRunning = false;
        this.addLog('⛔ 已停止执行', 'warning');
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
    }

    addLog(message, type = 'info') {
        const logItem = document.createElement('div');
        logItem.className = `log-item ${type}`;
        const timestamp = new Date().toLocaleTimeString();
        logItem.textContent = `[${timestamp}] ${message}`;
        this.logBox.appendChild(logItem);
        this.logBox.scrollTop = this.logBox.scrollHeight;
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    new AutoCodeFiller();
});
