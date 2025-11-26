from pathlib import Path
import requests.auth
import json
import time
from common import get_current_time

base_url = "https://10.7.5.210"
target = "3800"
username = "admin"
password = "123qwe!@#QWE"

# 创建session对象来保持登录状态
session = requests.Session()
session.verify = False


def api_login():
    try:
        auth_url = f"{base_url}/api/sonicos/auth"
        body = {'override': True}
        headers = {
            'Content-Type': 'application/json',
            'Accept-Encoding': 'application/json'
        }
        print(f"Attempting API login to {target}")
        # 使用Digest认证
        r = session.post(
            auth_url,
            auth=requests.auth.HTTPDigestAuth(username=username, password=password),
            data=json.dumps(body),
            headers=headers,
            verify=False
        )
        print(f"Login response status: {r.status_code}")

        if r.status_code == 200:
            try:
                response_data = r.json()
                msg_res = response_data['status']['info'][0]['message']

                print(f"Login successful - {msg_res}")
                print(f"{target} : API login successfully! Session established.")
                return True

            except (KeyError, IndexError) as e:
                print(f"{target}: API login failed - error parsing response: {e}, Response: {r.text}")
                return False
        else:
            # 登录失败的情况
            try:
                error_data = r.json()
                msg_res = error_data.get('status', {}).get('info', [{}])[0].get('message', 'Unknown error')
                print(f"{target}: API login failed with status {r.status_code} - {msg_res}")
            except:
                print(f"{target}: API login failed with status {r.status_code}, Response: {r.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"{target}: API login request exception - {e}")
        return False
    except Exception as e:
        print(f"{target}: API login unexpected error - {e}")
        return False


def send_command():
    """
    使用API发送命令获取memory verbose数据
    """
    try:
        api_url = f"{base_url}/api/sonicos/direct/cli"
        command_data = "diag show memory verbose"
        headers = {
            "Content-Type": "text/plain",  # 使用纯文本格式
        }

        print(f"========{target} Memory Verbose Information========")
        print(f"Sending command to: {api_url}")
        response = session.post(api_url, data=command_data, headers=headers)
        print(f"Command response status: {response.status_code}")

        if response.status_code == 200:
            # 直接获取响应文本
            output = response.text
            print("=== Full Response ===")
            print(output)

            # 提取size数据
            print("\n=== Extracted Size Data ===")
            lines = output.split('\n')
            memory_data = {}

            for line in lines:
                if line.strip().startswith('size-'):
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        size_type = parts[0]  # size-16, size-32, etc.
                        bytes_allocated = parts[2]  # 第三列是Bytes Allocated
                        memory_data[size_type] = int(bytes_allocated)
                        print(f"{size_type}: {bytes_allocated} bytes")

            print(f"\nExtracted {len(memory_data)} size entries")

            # 保存到文件
            text_file = f"memory_verbose_{target}.txt"
            with open(text_file, "w+") as f:
                f.write(f'{get_current_time()} RAW Data:\n')
                f.write(output)
                f.close()
            print(f"Data saved to: {text_file}")

            return memory_data

        else:
            print(f"API command failed! Status: {response.status_code}")
            print("=== Error Response ===")
            print(response.text)
            return None

    except Exception as e:
        print(f"send command via API failed! {e}")
        return None


# 执行测试
if __name__ == "__main__":
    print("Starting API test...")

    # 登录
    if api_login():
        print("\n" + "=" * 50)
        print("Login successful, sending command...")
        print("=" * 50 + "\n")

        # 发送命令
        result = send_command()

        if result:
            print("\n" + "=" * 50)
            print("SUCCESS: Memory data extracted:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print("\nFAILED: Could not get memory data")
    else:
        print("Login failed, cannot send command.")