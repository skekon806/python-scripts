import json
import requests
import random
from hashlib import md5
import time
from lxml import html
import sys
import io
import os
import hmac
import hashlib
from datetime import datetime
from http.client import HTTPSConnection

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ==================== 配置文件加载 ====================
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    """从 config.json 加载密钥配置"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 提取百度配置
        baidu = config.get("baidu", {})
        baiduKey = {
            "id": baidu.get("app_id"),
            "secret": baidu.get("secret_key")
        }
        
        # 提取腾讯配置
        tencent = config.get("tencent", {})
        tencent_secret_id = tencent.get("secret_id")
        tencent_secret_key = tencent.get("secret_key")
        
        # 验证配置是否完整
        missing = []
        if not baiduKey["id"]:
            missing.append("baidu.app_id")
        if not baiduKey["secret"]:
            missing.append("baidu.secret_key")
        if not tencent_secret_id:
            missing.append("tencent.secret_id")
        if not tencent_secret_key:
            missing.append("tencent.secret_key")
        
        if missing:
            print(f"错误：config.json 中缺少以下配置项：{', '.join(missing)}")
            print("请检查 config.json 文件格式是否正确")
            sys.exit(1)
        
        return baiduKey, tencent_secret_id, tencent_secret_key
        
    except FileNotFoundError:
        print(f"错误：找不到配置文件 {CONFIG_FILE}")
        print("请在同目录下创建 config.json 文件，格式参考：")
        print('''
{
  "baidu": {
    "app_id": "你的百度翻译APP_ID",
    "secret_key": "你的百度翻译密钥"
  },
  "tencent": {
    "secret_id": "你的腾讯云SecretId",
    "secret_key": "你的腾讯云SecretKey"
  }
}
        ''')
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误：config.json 格式不正确 - {e}")
        sys.exit(1)

# 加载配置
baiduKey, TENCENT_SECRET_ID, TENCENT_SECRET_KEY = load_config()

# ==================== CSS 样式 ====================
css = """<style type="text/css">
.engine {
  font-size: 18px;
  color: #578bc5;
}
.originalText {
    font-size: 120%;
    font-weight: 600;
    font-family: 'Times New Roman';
    display: inline-block;
    margin: 0rem 0rem 0rem 0rem;
    color: #2a5598;
    margin-bottom: 0.6rem;
}
.frame {
    margin: 1rem 0.5rem 0.5rem 0;
    padding: 0.7rem 0.5rem 0.5rem 0;
    border-top: 3px dashed #eaeef6;
}
definition {
    height: 120px;
    padding: 0.05em;
    font-weight: 500;
    font-size: 16px;
}
</style>"""

originalText = sys.argv[1]

def output(engineName: str, definition: str):
    print('<span class="engine">' + engineName + "</span>")
    print('<div class="frame">')
    print('<definition>' + definition + '</definition>')
    print("</div>")
    print("<br>")

def Baidu():
    global originalText
    global baiduKey
    salt = random.randint(32768, 65536)
    s = baiduKey["id"] + originalText + str(salt) + baiduKey["secret"]
    sign = md5(s.encode('utf-8')).hexdigest()
    try:
        result = requests.post('http://api.fanyi.baidu.com/api/trans/vip/translate',
                              params={'appid': baiduKey["id"], 'q': originalText, 
                                     'from': 'auto', 'to': 'auto', 'salt': salt, 'sign': sign}).json()
        output("百度翻译", result["trans_result"][0]["dst"])
    except:
        output("百度翻译", "错误")

def Tencent():
    global originalText
    global TENCENT_SECRET_ID
    global TENCENT_SECRET_KEY
    
    try:
        secret_id = TENCENT_SECRET_ID
        secret_key = TENCENT_SECRET_KEY
        
        # API配置
        service = "tmt"
        host = "tmt.tencentcloudapi.com"
        region = "ap-guangzhou"
        version = "2018-03-21"
        action = "TextTranslate"
        
        # 构建请求参数
        params = {
            "SourceText": originalText,
            "Source": "auto",
            "Target": "zh",
            "ProjectId": 0
        }
        payload = json.dumps(params)
        
        # 签名计算
        algorithm = "TC3-HMAC-SHA256"
        timestamp = int(time.time())
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        
        # 步骤1：拼接规范请求串
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        ct = "application/json; charset=utf-8"
        canonical_headers = f"content-type:{ct}\nhost:{host}\nx-tc-action:{action.lower()}\n"
        signed_headers = "content-type;host;x-tc-action"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = f"{http_request_method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{hashed_request_payload}"
        
        # 步骤2：拼接待签名字符串
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"
        
        # 步骤3：计算签名
        def sign(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
        
        secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        
        # 步骤4：拼接Authorization
        authorization = f"{algorithm} Credential={secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
        
        # 步骤5：构造并发起请求
        headers = {
            "Authorization": authorization,
            "Content-Type": ct,
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": version,
            "X-TC-Region": region
        }
        
        # 发送请求
        conn = HTTPSConnection(host)
        conn.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
        response = conn.getresponse()
        response_data = response.read().decode('utf-8')
        conn.close()
        
        # 解析响应
        result = json.loads(response_data)
        
        # 提取翻译结果
        if "Response" in result and "TargetText" in result["Response"]:
            output("腾讯翻译", result["Response"]["TargetText"])
        elif "Response" in result and "Error" in result["Response"]:
            error_code = result["Response"]["Error"]["Code"]
            error_msg = result["Response"]["Error"]["Message"]
            
            if error_code == "FailedOperation.UserNotRegistered":
                output("腾讯翻译", "错误：未开通服务，请去腾讯云控制台开通")
            elif error_code == "FailedOperation.NoFreeAmount":
                output("腾讯翻译", "错误：免费额度已用完")
            else:
                output("腾讯翻译", f"错误：{error_msg}")
        else:
            output("腾讯翻译", "翻译失败")
            
    except Exception as err:
        output("腾讯翻译", f"请求失败：{str(err)}")

def content_filter_len(content):
    return len(content.split()) >= 2

# 主程序
if content_filter_len(originalText):
    print(css)
    print('<div class="originalText">' + originalText + '</div>')
    print('<br><br>')
    Baidu()
    Tencent()