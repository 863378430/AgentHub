import requests

# -------------------------- 极简测试配置 --------------------------
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "admin@example.com"
TEST_USER_PASSWORD = "123456"
TEST_USERNAME = "admin"
TEST_MODES = ["自动", "数据", "配置", "翻译", "代码"]  # 要测试的模式列表

# 全局变量（仅保留必要的）
access_token = ""
conversation_id = ""

# -------------------------- 极简工具函数 --------------------------
def print_divider(desc: str):
    """简化版分隔线"""
    print(f"\n{'='*40}\n【{desc}】\n{'='*40}")

def get_headers():
    """获取带token的请求头"""
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

# -------------------------- 核心测试：仅测试模式化聊天接口 --------------------------
if __name__ == "__main__":
    try:
        # 1. 仅登录获取token（必要前置）
        print_divider("1. 登录获取Token")
        login_res = requests.post(f"{BASE_URL}/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_res.status_code == 200, f"登录失败：{login_res.text}"
        access_token = login_res.json()["access_token"]
        print(f"✅ 登录成功，Token：{access_token[:15]}...")

        # 2. 仅创建对话获取conversation_id（必要前置）
        print_divider("2. 创建测试对话")
        create_conv_res = requests.post(
            f"{BASE_URL}/api/conversation",
            json={"username": TEST_USERNAME, "title": "模式测试临时对话"},
            headers=get_headers()
        )
        assert create_conv_res.status_code == 200, f"创建对话失败：{create_conv_res.text}"
        conversation_id = create_conv_res.json()["conversation_id"]
        print(f"✅ 创建对话成功，ID：{conversation_id}")

        # 3. 核心测试：模式化聊天接口（仅保留这一步）
        print_divider("3. 测试所有模式的/api/chat接口")
        chat_url = f"{BASE_URL}/api/chat"
        test_content = "测试模式化回复"  # 测试输入内容

        for mode in TEST_MODES:
            # 发送模式化聊天请求
            chat_res = requests.post(
                chat_url,
                json={
                    "conversation_id": conversation_id,
                    "username": TEST_USERNAME,
                    "content": test_content,
                    "mode": mode
                },
                headers=get_headers()
            )

            # 断言验证
            assert chat_res.status_code == 200, f"{mode}模式失败：{chat_res.text}"
            chat_result = chat_res.json()
            
            # 核心验证点
            assert chat_result["mode"] == mode, f"{mode}模式返回值错误"
            assert chat_result["conversation_id"] == conversation_id, "对话ID不匹配"
            assert test_content in chat_result["content"], "回复未包含测试内容"

            # 打印结果（精简版）
            print(f"✅ {mode}模式：{chat_result['content']}")

        # 清理：删除测试对话（可选）
        requests.delete(f"{BASE_URL}/api/conversation/{conversation_id}", headers=get_headers())
        print("\n🎉 所有模式的聊天接口测试通过！")

    except Exception as e:
        print(f"\n❌ 测试失败：{str(e)}")
        if "chat_res" in locals():
            print(f"接口响应：{chat_res.text}")