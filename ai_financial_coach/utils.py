import pdfplumber
import pandas as pd
import re

def generate_alerts(income, expenses, emi_due):
    alerts = []

    if expenses > income:
        alerts.append("⚠️ Overspending Alert")

    if emi_due:
        alerts.append("📅 EMI Due Reminder")

    return alerts

def parse_bank_statement_pdf(uploaded_file):
    """
    Parses a PDF bank statement to extract transactions.
    Returns a dataframe with Date, Description, Amount, Category.
    """
    transactions = []
    
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Generic regex to find date at start of line
                    # Supports DD/MM/YYYY, DD-MM-YYYY, DD Mon YYYY
                    date_match = re.search(r'^(\d{2}[/-]\d{2}[/-]\d{4}|\d{2}\s[A-Za-z]{3}\s\d{4})', line)
                    
                    if date_match:
                        date_str = date_match.group(1)
                        date_end_pos = date_match.end()
                        
                        # Find all numbers that look like currency (1,234.56 or 1234.56)
                        amount_matches = list(re.finditer(r'[-+]?[\d,]+\.\d{2}', line))
                        
                        if amount_matches:
                            # Heuristic: 
                            # If >= 2 matches, likely [Transaction Amount, Balance] -> Take second to last
                            # If 1 match, likely [Transaction Amount] -> Take last (only)
                            target_match = amount_matches[-1]
                            if len(amount_matches) >= 2:
                                target_match = amount_matches[-2]
                            
                            amount_str = target_match.group().replace(',', '')
                            try:
                                amount = float(amount_str)
                            except ValueError:
                                continue
                                
                            # Description is text between date and the target amount
                            # We strip to clean up spaces
                            description = line[date_end_pos:target_match.start()].strip()
                            
                            # Determine if transaction is Income (Credit) or Expense (Debit)
                            # Heuristic:
                            # 1. Look for keywords in description
                            # 2. If multiple amount columns, check if one matches 'Credit' (hard without headers)
                            # 3. If amount is negative? (Some banks do this)
                            
                            txn_type = "Expense"
                            
                            # Keyword based detection
                            income_keywords = ['salary', 'credit', 'interest', 'refund', 'dividend', 'deposit']
                            if any(keyword in description.lower() for keyword in income_keywords):
                                txn_type = "Income"
                            
                            # If amount string was explicitly positive/negative?
                            # Usually bank statements don't sign them unless specified.
                            
                            transactions.append({
                                "Date": date_str,
                                "Description": description,
                                "Amount": abs(amount), 
                                "Type": txn_type,
                                "Category": "Uncategorized" if txn_type == "Expense" else "Income"
                            })
                            
        if not transactions:
            return pd.DataFrame(columns=["Date", "Description", "Amount", "Type", "Category"])
            
        df = pd.DataFrame(transactions)
        
        # Basic date parsing
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors='coerce')
        
        return df
        
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return pd.DataFrame(columns=["Date", "Description", "Amount", "Category"])
