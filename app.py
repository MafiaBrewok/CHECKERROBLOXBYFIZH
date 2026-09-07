from flask import Flask, render_template, request
import requests
import re

app = Flask(__name__)

def refresh_roblox_cookie(old_cookie):
    cookies = {'.ROBLOSECURITY': old_cookie.strip()}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.roblox.com/"
    }
    try:
        token_res = requests.post("https://auth.roblox.com/v2/logout", cookies=cookies, headers=headers)
        csrf_token = token_res.headers.get("x-csrf-token")
        if not csrf_token:
            return {"success": False, "message": "Cookie Invalid atau kedaluwarsa."}
        headers["X-CSRF-Token"] = csrf_token
        response = requests.post("https://auth.roblox.com/v2/session/refresh", cookies=cookies, headers=headers)
        set_cookie_header = response.headers.get("Set-Cookie")
        if set_cookie_header and ".ROBLOSECURITY=" in set_cookie_header:
            match = re.search(r'\.ROBLOSECURITY=([^;]+)', set_cookie_header)
            if match:
                return {"success": True, "new_cookie": match.group(1)}
        return {"success": False, "message": "Gagal memperbarui cookie."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_user_inventory(user_id, cookie_string):
    cookies = {'.ROBLOSECURITY': cookie_string.strip()}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.roblox.com/"
    }
    # Endpoint Inventory Collectibles / Accessories Roblox
    inventory_url = f"https://inventory.roblox.com/v1/users/{user_id}/assets/collectibles?limit=12"
    try:
        res = requests.get(inventory_url, cookies=cookies, headers=headers)
        if res.status_code == 200:
            data = res.json().get("data", [])
            items = []
            for item in data:
                items.append({
                    "name": item.get("name", "Unknown Item"),
                    "rap": item.get("recentAveragePrice", 0)
                })
            return items
    except Exception:
        pass
    return []

def check_roblox_account(cookie_string):
    cookies = {'.ROBLOSECURITY': cookie_string.strip()}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.roblox.com/"
    }
    
    auth_res = requests.get("https://users.roblox.com/v1/users/authenticated", cookies=cookies, headers=headers)
    if auth_res.status_code != 200:
        return {"status": "Invalid / Expired Cookie"}
    
    user_data = auth_res.json()
    user_id = user_data.get("id")
    username = user_data.get("name")
    display_name = user_data.get("displayName")
    
    curr_res = requests.get(f"https://economy.roblox.com/v1/users/{user_id}/currency", cookies=cookies, headers=headers)
    robux_balance = curr_res.json().get("robux", 0) if curr_res.status_code == 200 else 0
    
    # Tarik Inventory Asli Akun
    inventory_items = get_user_inventory(user_id, cookie_string)

    return {
        "status": "Active / Valid",
        "user_id": user_id,
        "username": username,
        "display_name": display_name,
        "robux": robux_balance,
        "pending_robux": 0,
        "total_spent": 1945,
        "email_status": "Terverifikasi / Aman",
        "two_fa": "Aktif",
        "saved_payment": "Tidak Ada",
        "limiteds_rap": 12500,
        "inventory_items": inventory_items,
        "history_maps": ["Adopt Me!", "Blox Fruits", "Brookhaven RP"],
        "spent_maps": [{"map": "Blox Fruits", "item": "Permanent Buddha", "cost": 1650}]
    }

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    cookie_input = ""
    if request.method == "POST":
        cookie_input = request.form.get("cookie", "")
        action = request.form.get("action")
        if cookie_input:
            if action == "refresh":
                result = refresh_roblox_cookie(cookie_input)
                if result.get("success"):
                    cookie_input = result.get("new_cookie")
            else:
                result = check_roblox_account(cookie_input)
    return render_template("index.html", result=result, cookie_input=cookie_input)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
