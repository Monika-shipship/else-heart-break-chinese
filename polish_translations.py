import os
import re
import json
import time
import argparse
from typing import List, Tuple, Dict, Optional, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
  import requests  # type: ignore
except Exception:
  requests = None


PAIR_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*=>\s*"((?:[^"\\]|\\.)*)"\s*$')


def unescape(s: str) -> str:
  return bytes(s, 'utf-8').decode('unicode_escape') if '\\' in s else s


def escape(s: str) -> str:
  return s.replace('\\', r'\\').replace('"', r'\"')


def read_pairs_from_mtf(path: str) -> List[Tuple[str, str, str]]:
  """
  Returns list of (line, src, dst). If not a pair line, src/dst are empty.
  """
  pairs: List[Tuple[str, str, str]] = []
  with open(path, 'r', encoding='utf-8') as f:
    for line in f:
      m = PAIR_RE.match(line.rstrip('\n'))
      if m:
        src = m.group(1)
        dst = m.group(2)
        pairs.append((line, src, dst))
      else:
        pairs.append((line, '', ''))
  return pairs


def write_pairs_to_mtf(path: str, items: List[Tuple[str, str, str]]):
  with open(path, 'w', encoding='utf-8', newline='\n') as f:
    for line, src, dst in items:
      if src == '' and dst == '':
        f.write(line)
      else:
        f.write(f'"{escape(src)}" => "{escape(dst)}"\n')


def ensure_out_dir(path: str):
  if not os.path.isdir(path):
    os.makedirs(path, exist_ok=True)


def chunked(seq, n):
  for i in range(0, len(seq), n):
    yield seq[i:i+n]


def _read_text(path: str) -> str:
  try:
    with open(path, 'r', encoding='utf-8') as f:
      return f.read()
  except Exception:
    return ''


def load_background_docs(root: str) -> str:
  bg_dir = os.path.join(root, '背景信息')
  p1 = os.path.join(bg_dir, '背景信息汇总.md')
  p2 = os.path.join(bg_dir, '剧情与翻译参考详解.md')
  p3 = os.path.join(bg_dir, '专有名词与翻译对照.md')
  return (
    "\n\n=== 背景信息汇总.md ===\n" + _read_text(p1) +
    "\n\n=== 剧情与翻译参考详解.md ===\n" + _read_text(p2) +
    "\n\n=== 专有名词与翻译对照.md ===\n" + _read_text(p3)
  )


def build_system_prompt(background_blob: str) -> str:
  rules = (
    "你是一名资深游戏本地化编辑，负责 Else Heart.Break() 的文本润色。\n"
    "严格遵守以下要求：\n"
    "- 左侧瑞典语原文绝对不可改动；你只润色右侧译文。\n"
    "- 右侧输出为双语：英文在前，中文在后（英文→空格→中文）。\n"
    "- 不使用中文引号（不要出现 “ ” 或 ' '）。\n"
    "- 中文句末不加中文句号“。”（问号/感叹号/省略号保留）。\n"
    "- 占位/标记必须原样保留：%s、%d、{name}、{0}、<tag>、[link]、\\n、\\t 等。\n"
    "- 统一专名与口径（Wellspring、Devotchka、SPRAK、GRIMM、Slurp()、Queen of the Internet、kronor 等）。\n"
    "- 严格按输入顺序返回结果，不要输出解释或多余文本。\n"
    "- 输出为 JSON 数组，数组每个元素是对应行的‘右侧译文字符串’（英文在前 中文在后）。\n"
  )
  examples = (
    "示例：\n"
    "输入行：\\\"Vad gör du här?\\\" => \\\"What are you doing here 你在这里做什么？\\\"\n"
    "输出数组项示例：\\\"What are you doing here 你在这里做什么？\\\"\n"
  )
  return rules + "\n" + examples + "\n\n【背景信息（每次重发以确保上下文一致）】\n" + background_blob


def build_user_prompt(file_name: str, items: List[Tuple[str, str]]) -> str:
  payload = {
    "file": file_name,
    "instruction": "请只润色右侧，保持双语顺序（英文在前 中文在后），返回等长 JSON 数组。",
    "items": [
      {"lhs_swedish": src, "rhs_current": rhs} for (src, rhs) in items
    ]
  }
  return json.dumps(payload, ensure_ascii=False)


def build_prompt(items: List[Tuple[str, str]]) -> str:
  """
  Ask the model to polish Chinese translations. Each item is (src, current_zh).
  We request strict JSON to ease parsing.
  """
  examples = []
  for src, zh in items:
    examples.append({"source": src, "currentChinese": zh})
  instructions = {
    "task": "Polish Chinese translations for a game.",
    "requirements": [
      "Return only a JSON array of strings, each the final Simplified Chinese translation.",
      "Preserve placeholders like %s, %d, {0}, {name}, <tag>, [link], and code fragments; do not translate them.",
      "Do not include the original English/Swedish in the output; output only natural Chinese.",
      "Keep meaning faithful, tone natural, concise where appropriate.",
      "Keep punctuation/ellipsis counts roughly consistent; avoid adding quotes.",
    ],
    "items": examples,
  }
  return json.dumps(instructions, ensure_ascii=False)


def call_deepseek(api_key: str, model: str, prompt: str, timeout: int = 60) -> List[str]:
  if requests is None:
    raise RuntimeError("The 'requests' package is required. Please install it.")
  url = "https://api.deepseek.com/chat/completions"
  headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
  }
  payload = {
    "model": model,
    "messages": [
      {"role": "system", "content": "You are a professional game localization editor for Simplified Chinese."},
      {"role": "user", "content": prompt},
    ],
    "temperature": 0.2,
  }
  resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
  resp.raise_for_status()
  data = resp.json()
  text = data["choices"][0]["message"]["content"].strip()
  try:
    arr = json.loads(text)
    if isinstance(arr, list) and all(isinstance(x, str) for x in arr):
      return arr
  except Exception:
    pass
  # Fallback: split lines
  return [x.strip() for x in text.splitlines() if x.strip()]


def call_deepseek_chat(api_key: str, model: str, system_prompt: str, user_prompt: str, timeout: int = 90, session: Optional['requests.Session'] = None, temperature: float = 1.3) -> List[str]:
  if requests is None:
    raise RuntimeError("The 'requests' package is required. Please install it.")
  url = "https://api.deepseek.com/chat/completions"
  headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
  }
  payload = {
    "model": model,
    "messages": [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_prompt},
    ],
    "temperature": temperature,
    "stream": False,
  }
  sess = session or requests
  resp = sess.post(url, headers=headers, json=payload, timeout=timeout)
  resp.raise_for_status()
  data = resp.json()
  text = data["choices"][0]["message"]["content"].strip()
  try:
    arr = json.loads(text)
    if isinstance(arr, list) and all(isinstance(x, str) for x in arr):
      return arr
  except Exception:
    pass
  # Fallback: split lines
  return [x.strip() for x in text.splitlines() if x.strip()]


def call_gemini(api_key: str, model: str, prompt: str, timeout: int = 60) -> List[str]:
  if requests is None:
    raise RuntimeError("The 'requests' package is required. Please install it.")
  url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
  headers = {"Content-Type": "application/json"}
  payload = {
    "contents": [
      {"role": "user", "parts": [{"text": prompt}]}
    ],
    "generationConfig": {
      "temperature": 0.2,
    }
  }
  resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
  resp.raise_for_status()
  data = resp.json()
  text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
  try:
    arr = json.loads(text)
    if isinstance(arr, list) and all(isinstance(x, str) for x in arr):
      return arr
  except Exception:
    pass
  return [x.strip() for x in text.splitlines() if x.strip()]


def polish_batch(provider: str, model: str, api_key: str, items: List[Tuple[str, str]]) -> List[str]:
  prompt = build_prompt(items)
  if provider == 'deepseek':
    return call_deepseek(api_key, model, prompt)
  elif provider == 'gemini':
    return call_gemini(api_key, model, prompt)
  else:
    raise ValueError(f"Unsupported provider: {provider}")


def _placeholders(s: str) -> List[str]:
  pats: List[str] = []
  pats += re.findall(r'%[sdif]', s)
  pats += re.findall(r'\{[^}]+\}', s)
  pats += re.findall(r'<[^>]+>', s)
  pats += re.findall(r'\[[^\]]+\]', s)
  pats += re.findall(r'\\[nt]', s)
  return pats


def _validate_rhs(new_rhs: str, old_rhs: str) -> Optional[str]:
  rhs = new_rhs.strip().strip('\u200b')
  if (rhs.startswith('"') and rhs.endswith('"')) or (rhs.startswith("'") and rhs.endswith("'")):
    rhs = rhs[1:-1]
  rhs = rhs.replace('\r', ' ').replace('\n', ' ').strip()
  if rhs.endswith('。'):
    rhs = rhs[:-1]
  if not rhs:
    return None
  req = set(_placeholders(old_rhs))
  got = set(_placeholders(rhs))
  if not req.issubset(got):
    return None
  return rhs


def _iter_target_files(src_dir: str, prefixes: Iterable[str]) -> List[str]:
  names: List[str] = []
  pref_set = {p.lower() for p in prefixes if p}
  for fname in sorted(os.listdir(src_dir)):
    if not fname.endswith('.mtf'):
      continue
    if fname and fname[0].lower() in pref_set:
      names.append(fname)
  return names


def _do_request_with_retry(provider: str, model: str, api_key: str, system_prompt: str, user_prompt: str, timeout: int, session: Optional['requests.Session']):
  # Only deepseek path is used in this workflow
  backoff = 1.0
  for attempt in range(5):
    try:
      return call_deepseek_chat(api_key, model, system_prompt, user_prompt, timeout=timeout, session=session, temperature=1.3)
    except Exception as e:
      if attempt >= 4:
        raise
      time.sleep(backoff)
      backoff *= 1.8
  raise RuntimeError('unreachable')


def load_cache(path: Optional[str]) -> Dict[str, str]:
  if not path or not os.path.isfile(path):
    return {}
  cache: Dict[str, str] = {}
  with open(path, 'r', encoding='utf-8') as f:
    for line in f:
      try:
        obj = json.loads(line)
        k = obj.get('key')
        v = obj.get('value')
        if isinstance(k, str) and isinstance(v, str):
          cache[k] = v
      except Exception:
        continue
  return cache


def append_cache(path: Optional[str], key: str, value: str):
  if not path:
    return
  with open(path, 'a', encoding='utf-8') as f:
    f.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")


def main():
  parser = argparse.ArgumentParser(description='并行润色 .mtf 右侧译文（DeepSeek/OpenAI 兼容接口）')
  parser.add_argument('--src-dir', default='English', help='包含 .mtf 的目录（就地修改右侧）')
  parser.add_argument('--provider', choices=['gemini', 'deepseek'], required=False, help='LLM 提供商（默认 deepseek）')
  parser.add_argument('--model', default=None, help='模型名（默认 deepseek-chat）')
  parser.add_argument('--group-size', type=int, default=5, help='每次请求处理的行数')
  parser.add_argument('--max-workers', type=int, default=8, help='并行请求数')
  parser.add_argument('--timeout', type=int, default=90, help='HTTP 超时时间(秒)')
  parser.add_argument('--letters', default='A_', help='按文件首字符筛选，如 "A_"')
  parser.add_argument('--cache', default='.polish_cache.jsonl', help='结果缓存(JSONL)')
  parser.add_argument('--dry-run', action='store_true', help='仅演示计划与进度，不实际请求与写入')
  args = parser.parse_args()

  provider = args.provider or os.getenv('TRANSLATE_PROVIDER') or 'deepseek'
  default_model = 'gemini-1.5-flash-latest' if provider == 'gemini' else 'deepseek-chat'
  model = args.model or os.getenv('TRANSLATE_MODEL') or default_model

  api_key_env = 'GEMINI_API_KEY' if provider == 'gemini' else 'DEEPSEEK_API_KEY'
  api_key = os.getenv(api_key_env, '')
  if not args.dry_run and not api_key:
    print(f'缺少 API 密钥。请设置环境变量 {api_key_env}。')
    return

  root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
  background_blob = load_background_docs(root)
  system_prompt = build_system_prompt(background_blob)
  cache = load_cache(args.cache)

  targets = _iter_target_files(args.src_dir, list(args.letters))
  if not targets:
    print('未找到匹配的文件。')
    return

  # 构建任务
  jobs = []  # (fname, start_index, items)
  per_file_pairs: Dict[str, List[Tuple[str, str, str]]] = {}
  for fname in targets:
    path = os.path.join(args.src_dir, fname)
    pairs = read_pairs_from_mtf(path)
    per_file_pairs[fname] = pairs
    batch: List[Tuple[str, str]] = []
    batch_idxs: List[int] = []
    for idx, (_line, src, dst) in enumerate(pairs):
      if not src and not dst:
        continue
      key = f'{src}\u0001{dst}'
      if key in cache:
        continue
      batch.append((src, dst))
      batch_idxs.append(idx)
      if len(batch) >= args.group_size:
        jobs.append((fname, batch_idxs[0], batch))
        batch = []
        batch_idxs = []
    if batch:
      jobs.append((fname, batch_idxs[0], batch))

  total = sum(len(items) for _f, _s, items in jobs)
  if args.dry_run:
    print(f'[DRY] 待润色文件: {len(targets)}，批次数: {len(jobs)}，合计行数: {total}')
    for fname in targets:
      print(f'  - {fname}')
    return

  print(f'待润色文件: {len(targets)}，批次数: {len(jobs)}，合计行数: {total}')
  done = ok = fail = 0
  session = requests.Session() if requests else None
  futures = []
  with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
    for fname, start_idx, items in jobs:
      user_prompt = build_user_prompt(fname, items)
      futures.append(ex.submit(_do_request_with_retry, provider, model, api_key, system_prompt, user_prompt, args.timeout, session))

    for fut, (fname, start_idx, items) in zip(as_completed(futures), jobs):
      try:
        results = fut.result()
      except Exception as e:
        fail += len(items)
        done += len(items)
        print(f'[失败] {fname} 第{start_idx}行起 共{len(items)}行: {e}')
        continue
      if not isinstance(results, list):
        results = []
      if len(results) != len(items):
        results = (results + [x[1] for x in items])[:len(items)]

      pairs = per_file_pairs[fname]
      for i, new_rhs in enumerate(results):
        idx = start_idx + i
        line, src, old_rhs = pairs[idx]
        final_rhs = _validate_rhs(new_rhs, old_rhs)
        if final_rhs is None:
          fail += 1
          continue
        pairs[idx] = (line, src, final_rhs)
        cache_key = f'{src}\u0001{old_rhs}'
        cache[cache_key] = final_rhs
        append_cache(args.cache, cache_key, final_rhs)
        ok += 1
      done += len(items)
      print(f'[进度] 完成 {done}/{total}，成功 {ok}，失败 {fail} —— {fname}')

  # 写回文件（就地更新）
  changed = 0
  for fname in targets:
    path = os.path.join(args.src_dir, fname)
    pairs = per_file_pairs[fname]
    write_pairs_to_mtf(path, pairs)
    changed += 1
    print(f'[写入] {path}')

  print(f'[完成] 写入文件 {changed} 个；成功 {ok}，失败 {fail}。')


if __name__ == '__main__':
  main()
