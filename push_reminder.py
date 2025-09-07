import requests
import json
from datetime import datetime, timedelta
import os

# 微信测试号配置（从环境变量获取）
APPID = os.getenv("WECHAT_APPID")
APPSECRET = os.getenv("WECHAT_APPSECRET")
OPENID = os.getenv("WECHAT_OPENID")
TEMPLATE_ID = os.getenv("WECHAT_TEMPLATE_ID")

# 微信接口URL
TOKEN_URL = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
PUSH_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}"

def get_access_token():
    """获取微信接口调用凭证"""
    response = requests.get(TOKEN_URL)
    result = response.json()
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"获取access_token失败：{result}")

def get_current_course():
    """获取当前时间应该提醒的课程（课前10分钟）"""
    # 当前时间 + 10分钟 = 课程开始时间
    target_time = datetime.now() + timedelta(minutes=10)
    target_str = target_time.strftime("%H:%M")
    today = datetime.now().strftime("%A")
    
    # 转换星期为中文（GitHub Actions运行环境为英文）
    weekday_map = {
        "Monday": "星期一",
        "Tuesday": "星期二",
        "Wednesday": "星期三",
        "Thursday": "星期四",
        "Friday": "星期五",
        "Saturday": "星期六",
        "Sunday": "星期日"
    }
    today_cn = weekday_map.get(today, "")
    if not today_cn:
        return None
    
    # 读取课表并匹配
    with open("schedule.json", "r", encoding="utf-8") as f:
        schedule = json.load(f)
    
    for course in schedule.get(today_cn, []):
        # 连堂课程只在第一节开始前提醒
        if course["startTime"] == target_str:
            return course
    return None

def send_reminder(course):
    """发送模板消息提醒"""
    access_token = get_access_token()
    data = {
        "touser": OPENID,
        "template_id": TEMPLATE_ID,
        "data": {
            "course": {"value": course["course"]},
            "time": {"value": f"{course['startTime']}-{course['endTime']}"},
            "location": {"value": f"{course['building']}{course['room']}"}
        }
    }
    
    response = requests.post(PUSH_URL.format(access_token), json=data)
    result = response.json()
    if result["errcode"] == 0:
        print("推送成功")
    else:
        print(f"推送失败：{result}")

if __name__ == "__main__":
    current_course = get_current_course()
    if current_course:
        send_reminder(current_course)
    else:
        print("当前无需要提醒的课程")
