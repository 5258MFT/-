# 导入自动化模块
from DrissionPage import ChromiumPage, ChromiumOptions
# 导入格式化输出模块
import json
# 导入csv模块
import csv
import time
import random
import logging
import os
import sys

# ================= 配置日志 =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='./data_code/spider_log.log'
)

# ================= 配置全局变量 =================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]

urls = [
    "https://we.51job.com/pc/search?jobArea=000000&keyword=你的关键词",
]

CSV_FILE = './data_code/data_51jobs1.csv'
PROGRESS_FILE = './data_code/progress.json'

# ================= 断点处理 =================
def save_progress(url, page_num, job_index=0):
    """保存当前进度到文件"""
    data = {}
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}
    
    # 保存URL、页码和岗位索引
    data[url] = {
        "page": page_num,
        "job_index": job_index,
        "timestamp": time.time()
    }
    
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_progress(url):
    """读取某个URL的上次进度"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                progress = data.get(url, {})
                return progress.get("page", 1), progress.get("job_index", 0)
        except:
            return 1, 0
    return 1, 0

# ================= CSV写入 =================
file_exists = os.path.exists(CSV_FILE)
f = open(CSV_FILE, mode='a', encoding='utf-8', newline='')
csv_writer = csv.DictWriter(f, fieldnames=[
    '岗位名称',
    '招聘地区',
    '招聘城区',
    '要求工作经验',
    '要求学历',
    '薪水',
    '发布时间',
    '公司名称',
    '公司信息',
    '职位技能关键词',
    '职位信息'
])
if not file_exists:
    csv_writer.writeheader()

# ================= 浏览器配置 =================
co = ChromiumOptions()
co.set_user_agent(random.choice(USER_AGENTS))
co.set_argument("--disable-blink-features=AutomationControlled")
co.set_argument("--start-maximized")
co.set_argument("--no-sandbox")
co.set_argument("--disable-dev-shm-usage")

dp = ChromiumPage(co)
main_tab = dp.latest_tab

# ================= 工具函数 =================
def random_sleep(min_sec=1, max_sec=2):
    sleep_time = random.uniform(min_sec, max_sec)
    time.sleep(sleep_time)
    return sleep_time

def random_scroll(page):
    scroll_height = page.run_js("return document.body.scrollHeight")
    if scroll_height > 1000:
        for _ in range(random.randint(2, 5)):
            scroll_pos = random.randint(100, scroll_height - 200)
            page.run_js(f"window.scrollTo(0, {scroll_pos})")
            time.sleep(random.uniform(0.5, 1.0))
    page.scroll.to_bottom()
    time.sleep(random.uniform(1, 1.5))

def retry(max_retries=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        logging.warning(f"尝试 {attempt+1} 失败: {e}，将在 {delay} 秒后重试")
                        time.sleep(delay)
                    else:
                        logging.error(f"超过最大重试次数 {max_retries}，操作失败: {e}")
                        raise e
        return wrapper
    return decorator

@retry(max_retries=3)
def fetch_job_details(new_tab):
    random_scroll(new_tab)
    job_description = ""
    job_msg_element = new_tab.ele('css:.bmsg.job_msg.inbox', timeout=10)
    if job_msg_element:
        job_description = job_msg_element.text
        job_description = job_description.replace('\n', ' ').replace('\r', ' ').strip()
    else:
        job_description = "未找到职位信息"
    return job_description

def navigate_to_page(target_page):
    """导航到指定页码"""
    if target_page <= 1:
        return True
        
    # 尝试直接输入页码跳转
    try:
        page_input = dp.ele('css:.jumpPage', timeout=5)
        if page_input:
            page_input.input(str(target_page))
            go_btn = dp.ele('css:.pageGo', timeout=3)
            if go_btn:
                go_btn.click()
                random_sleep(3, 5)
                return True
    except:
        pass
        
    # 如果直接跳转失败，尝试逐页翻页
    current_page = 1
    while current_page < target_page:
        try:
            next_btn = dp.ele('css:.btn-next', timeout=10)
            if next_btn:
                next_btn.click(by_js=True)
                random_sleep(3, 5)
                current_page += 1
            else:
                logging.error(f"无法翻页到第{target_page}页")
                return False
        except Exception as e:
            logging.error(f"翻页时出错: {e}")
            return False
            
    return True

# ================= 主逻辑 =================
for url in urls:
    try:
        dp.get(url)
        random_sleep(2, 3)

        # 判断是否手动指定了起始页
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            start_page = int(sys.argv[1])
            start_job_index = 0
            print(f"手动指定从第 {start_page} 页开始采集（覆盖断点）...")
        else:
            start_page, start_job_index = load_progress(url)
            print(f"从第 {start_page} 页的第 {start_job_index} 个岗位继续采集...")

        # 导航到目标页
        if not navigate_to_page(start_page):
            logging.error(f"无法导航到第{start_page}页，跳过此URL")
            continue

        current_page = start_page
        while current_page <= 50:
            logging.info(f'正在采集第{current_page}页（对应网址 {url}）的内容')
            print(f'正在采集第{current_page}页（对应网址 {url}）的内容')

            random_scroll(dp)
            divs = dp.eles('css:.joblist-item')

            if not divs:
                logging.warning(f"第{current_page}页未找到岗位信息，可能被反爬")
                dp.refresh()
                random_sleep(5, 8)
                continue

            # 从断点处开始采集岗位
            for job_index in range(start_job_index, len(divs)):
                try:
                    div = divs[job_index]
                    random_sleep(0.5, 1.5)
                    
                    # 获取岗位基本信息
                    info = div.ele('css:.joblist-item-job').attr('sensorsdata')
                    json_data = json.loads(info)
                    c_name = div.ele('css:.cname').attr('title')
                    c_info_list = [i.text for i in div.eles('css:.dc')]
                    tags = ''.join([j.text for j in div.eles('css:.tag')])

                    random_sleep(1, 2)
                    job_link = div.ele('css:.joblist-item-top')
                    job_link.click(by_js=True)
                    random_sleep(2, 3)

                    new_tab = dp.latest_tab
                    dp.activate_tab(new_tab)
                    job_description = fetch_job_details(new_tab)

                    dit = {
                        '岗位名称': json_data['jobTitle'],
                        '招聘地区': json_data['jobArea'],
                        '招聘城区': json_data.get('jobDistrict', ''),
                        '要求工作经验': json_data['jobYear'],
                        '要求学历': json_data['jobDegree'],
                        '薪水': json_data['jobSalary'],
                        '发布时间': json_data['jobTime'],
                        '公司名称': c_name,
                        '公司信息': ' '.join(c_info_list),
                        '职位技能关键词': tags,
                        '职位信息': job_description
                    }

                    csv_writer.writerow(dit)
                    print(dit)
                    logging.info(f"成功爬取: {json_data['jobTitle']}")

                    # 每成功采集一个岗位就保存进度
                    save_progress(url, current_page, job_index + 1)

                    random_sleep(1, 2)
                    new_tab.close()
                    dp.activate_tab(main_tab)

                except Exception as e:
                    logging.error(f"处理岗位时出错: {e}")
                    print(f"处理岗位时出错: {e}")
                    try:
                        dp.activate_tab(main_tab)
                    except:
                        pass
                    random_sleep(3, 5)
                    
                    # 保存当前进度，即使出错
                    save_progress(url, current_page, job_index)
                    break  # 跳出岗位循环，尝试翻页

            # 重置岗位索引为0，准备采集下一页
            start_job_index = 0
            
            # 尝试翻页
            try:
                random_scroll(dp)
                random_sleep(2, 3)
                next_btn = dp.ele('css:.btn-next', timeout=10)
                if next_btn:
                    next_btn.click(by_js=True)
                    logging.info(f"成功进入第{current_page+1}页")
                    random_sleep(4, 7)
                    current_page += 1
                    # 保存翻页后的进度
                    save_progress(url, current_page, 0)
                else:
                    logging.info("没有找到下一页按钮，提前结束。")
                    break
            except Exception as e:
                logging.error(f"翻页时出错: {e}")
                dp.refresh()
                random_sleep(5, 8)
                # 保存当前页进度
                save_progress(url, current_page, 0)
                break

    except Exception as e:
        logging.error(f"处理URL {url} 时出错: {e}")
        print(f"处理URL {url} 时出错: {e}")
        random_sleep(10, 15)

# ================= 结束清理 =================
f.close()
dp.quit()
print("数据采集完成！")







