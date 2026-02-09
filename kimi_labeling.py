import os
import time
import random
import asyncio
import pandas as pd
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

# 配置
API_KEY_ENV = "KIMI_API_KEY1"
BASE_URL = "https://api.moonshot.cn/v1"
MODEL_NAME = "kimi-k2-turbo-preview"
STANDARD_FILE_PATH = "/Users/macute/Downloads/cxy_ai_project/standard.md"
DATA_FILE_PATH = "/Users/macute/Downloads/cxy_ai_project/B站电动车新国标评论数据集标注.csv"
INPUT_COLUMN = "评论内容"
OUTPUT_COLUMN = "标注"
BATCH_SAVE_SIZE = 20
MAX_CONCURRENCY = 50
RPM_LIMIT = 200

class RateLimiter:
    def __init__(self, requests_per_minute):
        self.interval = 60.0 / requests_per_minute
        self.next_request_time = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.time()
            wait_time = self.next_request_time - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.next_request_time = time.time() + self.interval

def get_api_key():
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise ValueError(f"未找到环境变量 '{API_KEY_ENV}'。请设置该变量后重试。")
    return api_key

def load_standard(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"标准文件未找到: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def load_data(file_path):
    metadata = []
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for _ in range(6):
                metadata.append(f.readline())
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='gb18030') as f:
            for _ in range(6):
                metadata.append(f.readline())
                
    try:
        df = pd.read_csv(file_path, header=6)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, header=6, encoding='gb18030')
        
    return metadata, df

def save_data(file_path, metadata, df):
    temp_file = file_path + ".temp"
    with open(temp_file, 'w', encoding='utf-8-sig') as f:
        f.writelines(metadata)
    df.to_csv(temp_file, mode='a', index=False, encoding='utf-8-sig')
    if os.path.exists(file_path):
        os.remove(file_path)
    os.rename(temp_file, file_path)

async def get_completion(client, system_prompt, user_content, limiter, semaphore, retries=3):
    async with semaphore:
        attempt = 0
        while attempt < retries:
            await limiter.acquire()
            try:
                response = await client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ]
                )
                content = response.choices[0].message.content.strip()
                try:
                    label = int(content)
                    if label in [0, 1, 2, 3]:
                        return label
                except ValueError:
                    pass
            except Exception as e:
                print(f"\nAPI Error: {e} (Attempt {attempt+1}/{retries})")
            
            attempt += 1
            await asyncio.sleep(random.uniform(1, 3))
        return None

async def process_row(index, row, df, client, system_prompt, limiter, semaphore, pbar, save_callback):
    # 跳过已有结果
    current_label = df.at[index, OUTPUT_COLUMN]
    if pd.notna(current_label) and str(current_label).strip() != "":
        pbar.update(1)
        return

    comment = str(row[INPUT_COLUMN])
    if not comment.strip():
        pbar.update(1)
        return

    label = await get_completion(client, system_prompt, comment, limiter, semaphore)
    
    if label is not None:
        df.at[index, OUTPUT_COLUMN] = label
        
    pbar.update(1)
    save_callback()

def main():
    try:
        print("初始化...")
        api_key = get_api_key()
        client = AsyncOpenAI(api_key=api_key, base_url=BASE_URL)
        
        standard_content = load_standard(STANDARD_FILE_PATH)
        metadata, df = load_data(DATA_FILE_PATH)
        
        if INPUT_COLUMN not in df.columns:
            raise KeyError(f"Missing column: {INPUT_COLUMN}")
        if OUTPUT_COLUMN not in df.columns:
            df[OUTPUT_COLUMN] = pd.NA
            
        system_prompt = f"""你是一个严格的数据标注员。请阅读以下评级标准：
{standard_content}

**重要输出规则**：
请仅根据标准将评论归类为以下数字，**只输出一个数字**，不要包含任何标点或文字：
- **1** : 有用 -> 正面 (包含明确和隐晦)
- **2** : 有用 -> 负面 (包含明确和隐晦)
- **3** : 有用 -> 中性 (包含和事佬、建议、群众关心、科普)
- **0** : 无用 (包含情绪输出、无关、低俗、不切实际)
"""

        print(f"开始异步标注 (Concurrency={MAX_CONCURRENCY}, RPM={RPM_LIMIT})...")
        
        limiter = RateLimiter(RPM_LIMIT)
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        processed_count = 0
        
        def save_check():
            nonlocal processed_count
            processed_count += 1
            if processed_count % BATCH_SAVE_SIZE == 0:
                save_data(DATA_FILE_PATH, metadata, df)

        async def run_tasks():
            tasks = []
            with tqdm(total=len(df)) as pbar:
                for index, row in df.iterrows():
                    task = asyncio.create_task(
                        process_row(index, row, df, client, system_prompt, limiter, semaphore, pbar, save_check)
                    )
                    tasks.append(task)
                await asyncio.gather(*tasks)

        asyncio.run(run_tasks())
        
        save_data(DATA_FILE_PATH, metadata, df)
        print("\n标注完成！")

    except Exception as e:
        print(f"\nCritical Error: {e}")

if __name__ == "__main__":
    main()
