import requests
import json
from datetime import datetime, timedelta
import os
import pytz  # 用于时区处理

# 微信测试服务号配置（从环境变量获取）
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
    """获取当前北京时间应该提醒的课程及距离开课的分钟数（仅处理1小时内的课程）"""
    # 设置时区为北京时间（UTC+8）
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(beijing_tz)  # 获取当前北京时间
    print(f"=== 调试：当前北京时间 ===")
    print(f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取当前星期（中文）
    weekday_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
    
    # 读取课表并匹配
    with open("schedule.json", "r", encoding="utf-8") as f:
        schedule = json.load(f)
    
    # 查找需要提醒的课程（距离开课时间在1小时内）
    for course in schedule.get(weekday_cn, []):
        # 解析课程开始时间
        start_time = datetime.strptime(course["startTime"], "%H:%M").time()
        # 正确的时区处理方式：使用localize()方法
        naive_datetime = datetime.combine(now.date(), start_time)
        start_datetime = beijing_tz.localize(naive_datetime)
        # 计算距离开课的分钟数
        time_diff = (start_datetime - now).total_seconds() / 60
        
        # 只处理未来30-60分钟或30分钟内的课程
        if 0 < time_diff <= 60:  # 新增：大于0且小于等于60分钟才提醒
            # 返回课程信息和距离开课的分钟数
            return {
                "course": course,
                "minutes_until_start": time_diff
            }
    
    return None
    
def send_reminder(reminder_info):
    """发送模板消息提醒，根据距离开课时间显示不同内容"""
    course = reminder_info["course"]
    minutes_until_start = reminder_info["minutes_until_start"]
    
    # 根据距离开课时间设置不同的提醒内容
    if 30 <= minutes_until_start <= 60:  # 30-60分钟
        reminder_text = f"距离上课还有{int(minutes_until_start)}分钟"
    else:  # 小于30分钟
        reminder_text = f"距离上课还有{int(minutes_until_start)}分钟，请尽快前往对应教室"
    
    access_token = get_access_token()
    data = {
        "touser": OPENID,
        "template_id": TEMPLATE_ID,
        "data": {
            "course": {"value": course["course"], "color": "#173177"},
            "time": {"value": f"{course['startTime']}-{course['endTime']}", "color": "#173177"},
            "location": {"value": f"{course['building']}{course['room']}", "color": "#173177"},
            "reminder": {"value": reminder_text, "color": "#ff0000" if minutes_until_start < 30 else "#173177"}
        }
    }
    
    response = requests.post(PUSH_URL.format(access_token), json=data)
    result = response.json()
    print(f"微信接口返回详情：{json.dumps(result, ensure_ascii=False)}")
    if result["errcode"] == 0:
        print(f"✅ 推送成功：{course['course']}")
    else:
        print(f"❌ 推送失败：{result['errmsg']}（错误码：{result['errcode']}）")

if __name__ == "__main__":
    reminder_info = get_current_course()
    if reminder_info:
        # 输出调试信息
        course = reminder_info["course"]
        minutes = reminder_info["minutes_until_start"]
        print(f"=== 调试信息 ===")
        print(f"发现课程：{course['course']}")
        print(f"开课时间：{course['startTime']}")
        print(f"距离开课：{int(minutes)}分钟")
        
        send_reminder(reminder_info)
    else:
        print("当前无需要提醒的课程（只提醒1小时内的课程）")
