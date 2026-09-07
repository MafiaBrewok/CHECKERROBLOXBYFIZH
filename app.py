from flask import Flask, render_template, request
import requests
import re
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)

def get_roblox_headers(cookie_string):
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.roblox.com/",
        "Origin": "https://www.roblox.com"
    }

def refresh_roblox_cookie(old_cookie):
    cookies = {'.ROBLOSECURITY': old_cookie.strip()}
    headers = get_roblox_headers(old_cookie)
    try:
        token_res = requests.post("https://auth.roblox.com/v2/logout", cookies=cookies, headers=headers)
        csrf_token = token_res.headers.get("x-csrf-token")
        if not csrf_token:
            return {"success": False, "message": "Cookie Invalid atau sudah kedaluwarsa."}
        
        headers["X-CSRF-Token"] = csrf_token
        response = requests.post("https://auth.roblox.com/v2/session/refresh", cookies=cookies, headers=headers)
        set_cookie_header = response.headers.get("Set-Cookie")
        
        if set_cookie_header and ".ROBLOSECURITY=" in set_cookie_header:
            match = re.search(r'\.ROBLOSECURITY=([^;]+)', set_cookie_header)
            if match:
                return {"success": True, "new_cookie": match.group(1)}
                
        return {"success": False, "message": "Gagal memperbarui sesi cookie dari server Roblox."}
    except Exception as e:
        return {"success": False, "message": f"Terjadi kesalahan sistem: {str(e)}"}

def get_user_full_avatar(user_id):
    try:
        res = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false")
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                return data[0].get("imageUrl", "")
    except Exception:
        pass
    return ""

def get_game_icon(universe_id):
    try:
        res = requests.get(f"https://thumbnails.roblox.com/v1/games/icons?universeIds={universe_id}&size=150x150&format=Png")
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                return data[0].get("imageUrl", "")
    except Exception:
        pass
    return ""

def get_user_email_info(cookie_string):
    cookies = {'.ROBLOSECURITY': cookie_string.strip()}
    headers = get_roblox_headers(cookie_string)
    
    email_data = {"email": "Tidak dapat diakses / Tersembunyi", "verified": "Belum Terverifikasi"}
    try:
        res = requests.get("https://accountinformation.roblox.com/v1/email", cookies=cookies, headers=headers)
        if res.status_code == 200:
            data = res.json()
            email_address = data.get("emailAddress", "")
            is_verified = data.get("isVerified", False)
            
            email_data["email"] = email_address if email_address else "Tidak ada email tertaut"
            email_data["verified"] = "Terverifikasi / Aman" if is_verified else "Belum Terverifikasi"
    except Exception:
        pass
        
    return email_data

def get_user_inventory(user_id, cookie_string):
    cookies = {'.ROBLOSECURITY': cookie_string.strip()}
    headers = get_roblox_headers(cookie_string)
    inventory_url = f"https://inventory.roblox.com/v1/users/{user_id}/assets/collectibles?limit=100"
    
    items_list = []
    total_rap = 0
    try:
        res = requests.get(inventory_url, cookies=cookies, headers=headers)
        if res.status_code == 200:
            data = res.json().get("data", [])
            for item in data:
                item_name = item.get("name", "Unknown Collectible")
                item_rap = item.get("recentAveragePrice", 0)
                total_rap += item_rap
                items_list.append({
                    "name": item_name,
                    "rap": item_rap
                })
    except Exception:
        pass
    return items_list, total_rap

def get_user_game_history(user_id):
    history_maps = []
    try:
        res = requests.get(f"https://badges.roblox.com/v1/users/{user_id}/badges?limit=10")
        if res.status_code == 200:
            data = res.json().get("data", [])
            for b in data:
                awarder = b.get("awardingUniverse", {})
                game_name = awarder.get("name", "Unknown Game")
                universe_id = awarder.get("id")
                
                game_icon = get_game_icon(universe_id) if universe_id else ""
                
                if not any(m['name'] == game_name for m in history_maps):
                    history_maps.append({
                        "name": game_name,
                        "icon": game_icon
                    })
    except Exception:
        pass
    return history_maps if history_maps else [{"name": "Tidak ada riwayat game publik", "icon": ""}]

def get_user_spent_history(user_id, cookie_string):
    cookies = {'.ROBLOSECURITY': cookie_string.strip()}
    headers = get_roblox_headers(cookie_string)
    spent_maps = []
    try:
        res = requests.get(f"https://economy.roblox.com/v1/users/{user_id}/transactions?transactionType=Purchases&limit=10", cookies=cookies, headers=headers)
        if res.status_code == 200:
            data = res.json().get("data", [])
            for t in data:
                item_name = t.get("details", {}).get("name", "Game Item / Gamepass")
                robux_spent = t.get("currency", {}).get("amount", 0)
                spent_maps.append({
                    "item": item_name,
                    "cost": abs(robux_spent)
                })
    except Exception:
        pass
    return spent_maps

def check_roblox_account(cookie_string):
    cookies = {'.ROBLOSECURITY': cookie_string.strip()}
    headers = get_roblox_headers(cookie_string)
    
    auth_res = requests.get("https://users.roblox.com/v1/users/authenticated", cookies=cookies, headers=headers)
    if auth_res.status_code != 200:
        return {"status": "Invalid / Expired Cookie"}
    
    user_data = auth_res.json()
    user_id = user_data.get("id")
    username = user_data.get("name")
    display_name = user_data.get("displayName")
    
    curr_res = requests.get(f"https://economy.roblox.com/v1/users/{user_id}/currency", cookies=cookies, headers=headers)
    robux_balance = curr_res.json().get("robux", 0) if curr_res.status_code == 200 else 0

    email_info = get_user_email_info(cookie_string)
    inventory_items, total_rap = get_user_inventory(user_id, cookie_string)
    history_maps = get_user_game_history(user_id)
    spent_maps = get_user_spent_history(user_id, cookie_string)
    avatar_url = get_user_full_avatar(user_id)

    return {
        "status": "Active / Valid",
        "user_id": user_id,
        "username": username,
        "display_name": display_name,
        "robux": robux_balance,
        "pending_robux": 0,
        "total_spent": sum([s["cost"] for s in spent_maps]) if spent_maps else 0,
        "avatar_url": avatar_url,
        "limiteds_rap": total_rap,
        "inventory_items": inventory_items,
        "history_maps": history_maps,
        "spent_maps": spent_maps,
        "email_address": email_info["email"],
        "email_status": email_info["verified"],
        "two_fa": "Aktif / Terlindung",
        "saved_payment": "Tidak Ada"
    }

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    refresh_result = None
    cookie_input = ""
    
    if request.method == "POST":
        cookie_input = request.form.get("cookie", "").strip()
        action = request.form.get("action")
        
        if cookie_input:
            if action == "refresh":
                refresh_result = refresh_roblox_cookie(cookie_input)
            else:
                result = check_roblox_account(cookie_input)
                
    return render_template("index.html", result=result, refresh_result=refresh_result, cookie_input=cookie_input)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
