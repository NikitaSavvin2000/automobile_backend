import json
import os


home = os.getcwd()
version_path = os.path.join(home, "src", "utils", "version.json")


def get_version():
    with open(version_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"version": data.get("version")}


def update_version(new_version):
    with open(version_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = new_version
    with open(version_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_version(client_version):
    with open(version_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    current_version = data.get("version")
    if client_version != current_version:
        return {
            "is_actual": False,
            "message": "Обновите версию",
            "links": {
                "appstore": "https://apps.apple.com/",
                "rustore": "https://www.rustore.ru/",
                "playmarket": "https://play.google.com/store",
                "appgallery": "https://appgallery.huawei.com/"
            }
        }
    return {"is_actual": True, "message": "Версия актуальна"}






