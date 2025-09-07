import requests
import json
from datetime import datetime, timedelta
import os
import pytz  # 用于时区处理

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
    """获取当前北京时间应该提醒的课程（课前10分钟）"""
    # 设置时区为北京时间（UTC+8）
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(beijing_tz)  # 获取当前北京时间
    
    # 计算目标时间：当前时间 + 10分钟（即课程开始时间）
    target_time = now + timedelta(minutes=10)
    target_str = target_time.strftime("%H:%M")  # 格式化为"HH:MM"
    
    # 获取当前星期（中文）
    weekday_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
    
    # 读取课表并匹配
    with open("schedule.json", "r", encoding="utf-8") as f:
        schedule = json.load(f)
    
    # 查找当前需要提醒的课程（连堂课程只在第一节前提醒）
    for course in schedule.get(weekday_cn, []):
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
