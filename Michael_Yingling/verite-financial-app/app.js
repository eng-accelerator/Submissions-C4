// Global state
let currentData = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const manualInputBtn = document.getElementById('manualInputBtn');
const manualInputModal = document.getElementById('manualInputModal');
const closeModal = document.getElementById('closeModal');
const manualInputForm = document.getElementById('manualInputForm');
const statusSection = document.getElementById('statusSection');
const statusMessage = document.getElementById('statusMessage');
const summarySection = document.getElementById('summarySection');
const summaryGrid = document.getElementById('summaryGrid');
const agentsSection = document.getElementById('agentsSection');
const agentTabs = document.querySelectorAll('.agent-tab');
const agentResults = document.getElementById('agentResults');

// Upload area interactions
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

// File upload handler
async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    showStatus('Processing your financial data...');
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentData = result.data;
            hideStatus();
            
            // Load and display the summary
            await loadSummary();
            
            // Show the sections
            showAgentsSection();
            
            showSuccess('✅ Document processed successfully!');
        } else {
            hideStatus();
            showError(result.error || 'Failed to process document');
        }
    } catch (error) {
        hideStatus();
        showError('Error uploading file: ' + error.message);
    }
}

// Manual input modal
manualInputBtn.addEventListener('click', () => {
    manualInputModal.style.display = 'flex';
});

closeModal.addEventListener('click', () => {
    manualInputModal.style.display = 'none';
});

manualInputModal.addEventListener('click', (e) => {
    if (e.target === manualInputModal) {
        manualInputModal.style.display = 'none';
    }
});

// Manual input form submission
manualInputForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(manualInputForm);
    
    // Collect expenses
    const expenses = {};
    document.querySelectorAll('.expense-row').forEach(row => {
        const category = row.querySelector('.expense-category').value;
        const amount = parseFloat(row.querySelector('.expense-amount').value) || 0;
        if (category) {
            expenses[category] = amount;
        }
    });
    
    // Collect debts
    const debts = [];
    document.querySelectorAll('.debt-row').forEach(row => {
        const name = row.querySelector('.debt-name').value;
        const balance = parseFloat(row.querySelector('.debt-balance').value) || 0;
        const rate = parseFloat(row.querySelector('.debt-rate').value) || 0;
        const payment = parseFloat(row.querySelector('.debt-payment').value) || 0;
        
        if (name) {
            debts.push({
                name: name,
                balance: balance,
                interest_rate: rate,
                minimum_payment: payment,
                type: 'unknown'
            });
        }
    });
    
    const data = {
        monthly_income: parseFloat(formData.get('monthly_income')) || 0,
        savings: parseFloat(formData.get('savings')) || 0,
        expenses: expenses,
        debts: debts,
        goals: formData.get('goals').split(',').map(g => g.trim()).filter(g => g),
        investments: {}
    };
    
    showStatus('Saving your financial data...');
    manualInputModal.style.display = 'none';
    
    try {
        const response = await fetch('/api/manual-input', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentData = data;
            hideStatus();
            
            // Load and display the summary
            await loadSummary();
            
            // Show the sections
            showAgentsSection();
            
            showSuccess('✅ Financial data saved successfully!');
        } else {
            hideStatus();
            showError(result.error || 'Failed to save data');
        }
    } catch (error) {
        hideStatus();
        showError('Error saving data: ' + error.message);
    }
});

// Add/Remove expense rows
function addExpense() {
    const container = document.getElementById('expensesContainer');
    const row = document.createElement('div');
    row.className = 'expense-row';
    row.innerHTML = `
        <input type="text" placeholder="Category (e.g., Rent)" class="expense-category">
        <input type="number" placeholder="Amount" class="expense-amount">
        <button type="button" class="btn-icon" onclick="removeExpense(this)">🗑️</button>
    `;
    container.appendChild(row);
}

function removeExpense(button) {
    const row = button.closest('.expense-row');
    if (document.querySelectorAll('.expense-row').length > 1) {
        row.remove();
    }
}

// Add/Remove debt rows
function addDebt() {
    const container = document.getElementById('debtsContainer');
    const row = document.createElement('div');
    row.className = 'debt-row';
    row.innerHTML = `
        <input type="text" placeholder="Debt Name" class="debt-name">
        <input type="number" placeholder="Balance" class="debt-balance">
        <input type="number" placeholder="Interest %" class="debt-rate" step="0.01">
        <input type="number" placeholder="Min Payment" class="debt-payment">
        <button type="button" class="btn-icon" onclick="removeDebt(this)">🗑️</button>
    `;
    container.appendChild(row);
}

function removeDebt(button) {
    const row = button.closest('.debt-row');
    if (document.querySelectorAll('.debt-row').length > 1) {
        row.remove();
    }
}

// Load financial summary
async function loadSummary() {
    console.log('Loading financial summary...');
    try {
        const response = await fetch('/api/summary');
        console.log('Summary response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Summary API error:', response.status, errorText);
            return;
        }
        
        const result = await response.json();
        console.log('Summary result:', result);
        
        if (result.success && result.data) {
            console.log('Displaying summary with data:', result.data);
            displaySummary(result.data);
            summarySection.style.display = 'block';
            console.log('Summary section displayed');
        } else {
            console.error('Summary response missing data:', result);
        }
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

// Display summary
function displaySummary(data) {
    summaryGrid.innerHTML = '';
    
    const cards = [
        {
            title: 'Monthly Income',
            value: formatCurrency(data.monthly_income),
            label: 'After tax',
            positive: true
        },
        {
            title: 'Monthly Expenses',
            value: formatCurrency(data.monthly_expenses),
            label: 'Fixed + Variable'
        },
        {
            title: 'Net Cash Flow',
            value: formatCurrency(data.net_monthly_cash_flow),
            label: 'Available monthly',
            positive: data.net_monthly_cash_flow > 0,
            negative: data.net_monthly_cash_flow < 0
        },
        {
            title: 'Total Debt',
            value: formatCurrency(data.total_debt),
            label: 'All obligations'
        },
        {
            title: 'Current Savings',
            value: formatCurrency(data.current_savings),
            label: 'Emergency + General'
        },
        {
            title: 'Savings Rate',
            value: data.savings_rate_percent.toFixed(1) + '%',
            label: 'Of gross income',
            positive: data.savings_rate_percent >= 15
        },
        {
            title: 'Debt-to-Income',
            value: data.debt_to_income_ratio_percent.toFixed(1) + '%',
            label: 'Total debt vs annual income',
            positive: data.debt_to_income_ratio_percent <= 36,
            negative: data.debt_to_income_ratio_percent > 50
        },
        {
            title: 'Financial Health',
            value: data.financial_health_score,
            label: 'Overall score'
        }
    ];
    
    cards.forEach(card => {
        const cardEl = document.createElement('div');
        cardEl.className = 'summary-card';
        
        const valueClass = card.positive ? 'positive' : (card.negative ? 'negative' : '');
        
        cardEl.innerHTML = `
            <h3>${card.title}</h3>
            <div class="value ${valueClass}">${card.value}</div>
            <div class="label">${card.label}</div>
        `;
        
        summaryGrid.appendChild(cardEl);
    });
    
    summarySection.style.display = 'block';
}

// Agent tab interactions
agentTabs.forEach(tab => {
    tab.addEventListener('click', async () => {
        if (tab.classList.contains('loading')) return;
        
        // Update active tab
        agentTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        const agentType = tab.dataset.agent;
        await loadAgentAnalysis(agentType);
    });
});

// Load agent analysis
async function loadAgentAnalysis(agentType) {
    const activeTab = document.querySelector('.agent-tab.active');
    activeTab.classList.add('loading');
    
    agentResults.innerHTML = `
        <div class="empty-state">
            <div class="spinner" style="margin: 0 auto 16px;"></div>
            <p>AI agent is analyzing your financial data...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`/api/analyze/${agentType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        // Check if response is OK
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Response not OK:', response.status, errorText);
            throw new Error(`Server error: ${response.status}`);
        }
        
        // Get content type
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const textResponse = await response.text();
            console.error('Non-JSON response:', textResponse);
            throw new Error('Server returned non-JSON response. Please check server logs.');
        }
        
        const result = await response.json();
        
        if (result.success) {
            displayAgentResult(result.data);
        } else {
            agentResults.innerHTML = `
                <div class="alert alert-error">
                    ⚠️ ${result.error || 'Failed to get analysis'}
                    ${result.details ? '<br><small>' + result.details + '</small>' : ''}
                </div>
            `;
        }
    } catch (error) {
        console.error('Error in loadAgentAnalysis:', error);
        agentResults.innerHTML = `
            <div class="alert alert-error">
                ⚠️ <strong>Error:</strong> ${error.message}
                <br><small>Please check that:
                <br>• You have uploaded or entered financial data
                <br>• Your ANTHROPIC_API_KEY is set correctly
                <br>• The server is running without errors
                <br>• Check the browser console (F12) for details</small>
            </div>
        `;
    } finally {
        activeTab.classList.remove('loading');
    }
}

// Display agent result
function displayAgentResult(data) {
    let content = '';
    
    // Handle direct response (single agent)
    if (data.response) {
        content = formatMarkdown(data.response);
    } 
    // Handle message format (fallback for no data)
    else if (data.message) {
        content = `<div class="alert alert-info">ℹ️ ${data.message}</div>`;
    }
    // Handle comprehensive plan
    else if (data.summary) {
        content = '<h3>📊 Financial Summary</h3>';
        content += formatSummaryData(data.summary);
        
        if (data.debt_analysis && data.debt_analysis.response) {
            content += '<h3>💳 Debt Analysis</h3>';
            content += formatMarkdown(data.debt_analysis.response);
        }
        
        if (data.savings_strategy && data.savings_strategy.response) {
            content += '<h3>💰 Savings Strategy</h3>';
            content += formatMarkdown(data.savings_strategy.response);
        }
        
        if (data.budget_optimization && data.budget_optimization.response) {
            content += '<h3>📊 Budget Optimization</h3>';
            content += formatMarkdown(data.budget_optimization.response);
        }
        
        if (data.investment_advice && data.investment_advice.response) {
            content += '<h3>📈 Investment Advice</h3>';
            content += formatMarkdown(data.investment_advice.response);
        }
        
        if (data.tax_optimization && data.tax_optimization.response) {
            content += '<h3>🏛️ Tax Optimization</h3>';
            content += formatMarkdown(data.tax_optimization.response);
        }
        
        if (data.emergency_fund && data.emergency_fund.response) {
            content += '<h3>🚨 Emergency Fund Plan</h3>';
            content += formatMarkdown(data.emergency_fund.response);
        }
    }
    // Fallback for unexpected format
    else {
        content = `<div class="alert alert-info">Received data: ${JSON.stringify(data, null, 2)}</div>`;
    }
    
    agentResults.innerHTML = `<div class="result-content">${content}</div>`;
}

// Format summary data
function formatSummaryData(summary) {
    return `
        <ul>
            <li><strong>Monthly Income:</strong> ${formatCurrency(summary.monthly_income)}</li>
            <li><strong>Monthly Expenses:</strong> ${formatCurrency(summary.monthly_expenses)}</li>
            <li><strong>Net Cash Flow:</strong> ${formatCurrency(summary.net_monthly_cash_flow)}</li>
            <li><strong>Total Debt:</strong> ${formatCurrency(summary.total_debt)}</li>
            <li><strong>Current Savings:</strong> ${formatCurrency(summary.current_savings)}</li>
            <li><strong>Savings Rate:</strong> ${summary.savings_rate_percent.toFixed(1)}%</li>
            <li><strong>Debt-to-Income Ratio:</strong> ${summary.debt_to_income_ratio_percent.toFixed(1)}%</li>
            <li><strong>Financial Health Score:</strong> ${summary.financial_health_score}</li>
        </ul>
    `;
}

// Simple markdown formatter
function formatMarkdown(text) {
    // Convert markdown-style formatting to HTML
    text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Convert numbered lists
    text = text.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ol>$&</ol>');
    
    // Convert bullet lists
    text = text.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    
    // Convert paragraphs
    text = text.replace(/\n\n/g, '</p><p>');
    text = '<p>' + text + '</p>';
    
    // Clean up empty paragraphs
    text = text.replace(/<p>\s*<\/p>/g, '');
    
    return text;
}

// Helper functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function showStatus(message) {
    statusMessage.textContent = message;
    statusSection.style.display = 'block';
}

function hideStatus() {
    statusSection.style.display = 'none';
}

function showAgentsSection() {
    agentsSection.style.display = 'block';
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.textContent = message;
    
    document.querySelector('.main-content').insertBefore(
        alert,
        document.querySelector('.card')
    );
    
    setTimeout(() => alert.remove(), 5000);
}

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.textContent = '⚠️ ' + message;
    
    document.querySelector('.main-content').insertBefore(
        alert,
        document.querySelector('.card')
    );
    
    setTimeout(() => alert.remove(), 8000);
}

// Make functions globally accessible
window.addExpense = addExpense;
window.removeExpense = removeExpense;
window.addDebt = addDebt;
window.removeDebt = removeDebt;
