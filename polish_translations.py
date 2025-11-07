import os
import re
import json
import time
import argparse
from typing import List, Tuple, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
  import requests  # type: ignore
except Exception:
  requests = None


PAIR_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*=>\s*"((?:[^"\\]|\\.)*)"\s*$')


def read_pairs(path: str) -> List[Tuple[str, str, str]]:
  items: List[Tuple[str, str, str]] = []
  with open(path, 'r', encoding='utf-8') as f:
    for line in f:
      m = PAIR_RE.match(line.rstrip('\n'))
      if m:
        items.append((line, m.group(1), m.group(2)))
      else:
        items.append((line, '', ''))
  return items


def write_pairs(path: str, items: List[Tuple[str, str, str]]):
  with open(path, 'w', encoding='utf-8', newline='\n') as f:
    for line, lhs, rhs in items:
      if lhs == '' and rhs == '':
        f.write(line)
      else:
        f.write(f'"{lhs}" => "{rhs}"\n')


def _read_text(p: str) -> str:
  try:
    with open(p, 'r', encoding='utf-8') as f:
      return f.read()
  except Exception:
    return ''


def build_system_prompt(root: str) -> str:
  bg = os.path.join(root, '背景信息')
  t1 = _read_text(os.path.join(bg, '背景信息汇总.md'))
  t2 = _read_text(os.path.join(bg, '剧情与翻译参考详解.md'))
  t3 = _read_text(os.path.join(bg, '专有名词与翻译对照.md'))
  rules = (
    '你是一名资深游戏本地化编辑，负责 Else Heart.Break() 的文本润色。\n'
    '务必遵守：\n'
    '1) 左侧瑞典语绝对不可改动；你只输出右侧译文。\n'
    '2) 右侧为双语：英文在前，中文在后（以单个空格分隔）。\n'
    '3) 不使用中文引号；中文句末不加中文句号“。”（问号/叹号/省略号保留）。\n'
    '4) 保留占位/标记：%s、%d、{name}、{0}、<tag>、[link]、\\n、\\t 等。\n'
    '5) 专名与口径统一：Wellspring、Devotchka、SPRAK、GRIMM、Slurp()、Queen of the Internet、kronor 等。\n'
    '6) 只输出 JSON 对象：{"rhs": "英文在前 中文在后"}，不要输出任何说明/代码块。\n'
  )
  ctx = (
    "\n【背景信息：每次均附带，保持口径一致】\n"
    "=== 背景信息汇总.md ===\n" + t1 +
    "\n=== 剧情与翻译参考详解.md ===\n" + t2 +
    "\n=== 专有名词与翻译对照.md ===\n" + t3
  )
  return rules + ctx


def build_user_prompt(file_name: str, lhs: str, rhs_current: str) -> str:
  def _context_hint(name: str) -> str:
    base = name
    if '.' in base:
      base = base.split('.', 1)[0]
    speaker = ''
    scene = ''
    # 形如 Araki_AfterGhostVisit 或 _OnThePhone
    if base.startswith('_'):
      speaker = ''
      scene = base.lstrip('_')
    else:
      parts = base.split('_', 1)
      speaker = parts[0]
      scene = parts[1] if len(parts) > 1 else ''
    return f"Speaker: {speaker or '-'}; Scene: {scene or '-'}"

  hint = _context_hint(file_name)
  payload = {
    "file": file_name,
    "instruction": (
      '请润色右侧译文 rhs，使其自然、符合口径，保持双语顺序（英文在前 中文在后）。\n'
      '输出严格 JSON 对象：{"rhs": "..."}，不要返回代码块/数组/多余文字。\n'
      '保留占位/标签/转义，不要改动左侧瑞典语。\n'
      f'注意：文件名中包含当前说话者/场景线索（{hint}），请在口吻与词汇上与该说话者和场景保持一致。'
    ),
    "lhs_swedish": lhs,
    "rhs_current": rhs_current,
    "context_hint": hint,
    "expect": {"rhs": "英文在前 中文在后"}
  }
  return json.dumps(payload, ensure_ascii=False)


def _placeholders(s: str) -> List[str]:
  pats: List[str] = []
  pats += re.findall(r'%[sdif]', s)
  pats += re.findall(r'\{[^}]+\}', s)
  pats += re.findall(r'<[^>]+>', s)
  pats += re.findall(r'\[[^\]]+\]', s)
  pats += re.findall(r'\\[nt]', s)
  return pats


def _sanitize_rhs(rhs: str) -> Optional[str]:
  s = rhs.strip().strip('\u200b')
  if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
    s = s[1:-1]
  s = s.replace('\r', ' ').replace('\n', ' ').strip()
  if s.endswith('。'):
    s = s[:-1]
  if not s:
    return None
  # 不允许代码块/JSON样式
  if '```' in s or s.startswith('[') or s.startswith('{') or '"index"' in s or '\\"index\\"' in s:
    return None
  # 不允许中文引号
  if '“' in s or '”' in s or '‘' in s or '’' in s:
    return None
  return s


def call_deepseek_line(api_key: str, system_prompt: str, file_name: str, lhs: str, rhs: str,
                       timeout: int = 60, temperature: float = 1.0, max_tokens: int = 400,
                       session: Optional['requests.Session'] = None) -> Tuple[str, str, str]:
  if requests is None:
    raise RuntimeError("缺少 requests 库，请先 pip install requests")
  url = "https://api.deepseek.com/chat/completions"
  headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
  }
  user_prompt = build_user_prompt(file_name, lhs, rhs)
  payload = {
    "model": "deepseek-chat",
    "messages": [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_prompt}
    ],
    "response_format": {"type": "json_object"},
    "temperature": temperature,
    "max_tokens": max_tokens,
    "stream": False,
  }
  sess = session or requests
  for attempt in range(5):
    r = sess.post(url, headers=headers, json=payload, timeout=timeout)
    if r.status_code >= 500:
      time.sleep(1.0 + attempt * 0.8)
      continue
    r.raise_for_status()
    data = r.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    raw = text
    # fenced 代码块提取
    if "```" in raw:
      m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
      if m:
        raw = m.group(1).strip()
    # 解析对象
    obj = None
    try:
      obj = json.loads(raw)
    except Exception:
      # 尝试截取第一个对象片段
      if '{' in raw and '}' in raw:
        a = raw.find('{'); b = raw.rfind('}')
        if b > a:
          frag = raw[a:b+1]
          obj = json.loads(frag)
    if not isinstance(obj, dict) or 'rhs' not in obj or not isinstance(obj['rhs'], str):
      raise ValueError("模型未返回形如 {\"rhs\": \"...\"} 的 JSON 对象")
    return obj['rhs'], raw, user_prompt
  raise RuntimeError("多次请求失败")


def _sanitize_filename(s: str) -> str:
  return re.sub(r'[^\w\-\.]+', '_', s)


def _write_line_log(log_dir: str, file_name: str, idx: int, lhs: str, rhs_current: str,
                    system_prompt: Optional[str], user_prompt: Optional[str], raw_response: Optional[str], parsed_rhs: Optional[str],
                    error: Optional[str]) -> None:
  try:
    os.makedirs(log_dir, exist_ok=True)
    ts = int(time.time() * 1000)
    base = f"{ts}_{_sanitize_filename(file_name)}_{idx}"
    path = os.path.join(log_dir, base + '.json')
    with open(path, 'w', encoding='utf-8') as f:
      json.dump({
        'file': file_name,
        'index': idx,
        'lhs': lhs,
        'rhs_current': rhs_current,
        'system_prompt': system_prompt,
        'user_prompt': user_prompt,
        'raw_response': raw_response,
        'parsed_rhs': parsed_rhs,
        'error': error,
      }, f, ensure_ascii=False, indent=2)
  except Exception:
    pass


def _fmt_eta(seconds: float) -> str:
  if seconds <= 0 or seconds == float('inf'):
    return '--:--:--'
  m, s = divmod(int(seconds), 60)
  h, m = divmod(m, 60)
  return f"{h:02d}:{m:02d}:{s:02d}"


def process_file(api_key: str, system_prompt: str, in_path: str, max_workers: int,
                 timeout: int, temperature: float, max_tokens: int, log_dir: Optional[str] = None,
                 progress: Optional[Dict[str, float]] = None) -> Tuple[int, int]:
  file_name = os.path.basename(in_path)
  pairs = read_pairs(in_path)
  # 收集任务
  jobs: List[Tuple[int, str, str]] = []  # (index, lhs, rhs)
  for idx, (line, lhs, rhs) in enumerate(pairs):
    if lhs and rhs:
      jobs.append((idx, lhs, rhs))

  if not jobs:
    return (0, 0)

  ok = fail = 0
  session = requests.Session() if requests else None
  with ThreadPoolExecutor(max_workers=max_workers) as ex:
    fut_map = {}
    for idx, lhs, rhs in jobs:
      fut = ex.submit(call_deepseek_line, api_key, system_prompt, file_name, lhs, rhs,
                      timeout, temperature, max_tokens, session)
      fut_map[fut] = (idx, lhs, rhs)
    for fut in as_completed(fut_map.keys()):
      idx, lhs, old_rhs = fut_map[fut]
      try:
        new_rhs_raw, raw_response, user_prompt = fut.result()
      except Exception as e:
        fail += 1
        print(f"[失败] {file_name}:{idx} {e}")
        if log_dir:
          _write_line_log(log_dir, file_name, idx, lhs, old_rhs, system_prompt, None, None, None, str(e))
        continue
      new_rhs = _sanitize_rhs(new_rhs_raw)
      if new_rhs is None:
        fail += 1
        print(f"[失败] {file_name}:{idx} 返回格式不合规")
        if log_dir:
          _write_line_log(log_dir, file_name, idx, lhs, old_rhs, system_prompt, user_prompt, raw_response, None, '返回格式不合规')
        continue
      # 占位符校验：以左侧瑞典语为准，避免旧 RHS 污染干扰
      required = set(_placeholders(lhs))
      if required and not required.issubset(set(_placeholders(new_rhs))):
        fail += 1
        print(f"[失败] {file_name}:{idx} 占位符不匹配")
        if log_dir:
          _write_line_log(log_dir, file_name, idx, lhs, old_rhs, system_prompt, user_prompt, raw_response, new_rhs, '占位符不匹配')
        continue
      # 写入
      line, _lhs, _rhs = pairs[idx]
      pairs[idx] = (line, lhs, new_rhs)
      ok += 1
      if log_dir:
        _write_line_log(log_dir, file_name, idx, lhs, old_rhs, system_prompt, user_prompt, raw_response, new_rhs, None)
      # 进度与 ETA
      if progress is not None:
        progress['done'] = progress.get('done', 0) + 1
        done = int(progress['done'])
        total = int(progress.get('total', 0))
        elapsed = time.time() - progress.get('start', time.time())
        rate = done / elapsed if elapsed > 0 else 0.0
        eta = _fmt_eta((total - done) / rate if rate > 0 else float('inf'))
        pct = (done / total * 100.0) if total > 0 else 0.0
        if ok % 10 == 0:
          print(f"[进度] 行 {done}/{total} ({pct:.1f}%), 文件 {int(progress.get('files_done', 0))}/{int(progress.get('files_total', 0))}, 预计剩余 {eta}")
      else:
        if ok % 10 == 0:
          print(f"[进度] {file_name} 成功 {ok} 行，失败 {fail} 行")

  write_pairs(in_path, pairs)
  if progress is not None:
    # 更新文件计数并输出一次汇总
    progress['files_done'] = progress.get('files_done', 0) + 1
    done = int(progress.get('done', 0))
    total = int(progress.get('total', 0))
    files_done = int(progress.get('files_done', 0))
    files_total = int(progress.get('files_total', 0))
    elapsed = time.time() - progress.get('start', time.time())
    rate = done / elapsed if elapsed > 0 else 0.0
    eta = _fmt_eta((total - done) / rate if rate > 0 else float('inf'))
    pct = (done / total * 100.0) if total > 0 else 0.0
    print(f"[写入] {in_path} 完成：成功 {ok}，失败 {fail}")
    print(f"[文件] 完成 {files_done}/{files_total} —— 行进度 {done}/{total} ({pct:.1f}%), 预计剩余 {eta}")
  else:
    print(f"[写入] {in_path} 完成：成功 {ok}，失败 {fail}")
  return (ok, fail)


def main():
  parser = argparse.ArgumentParser(description='批量并行润色 .mtf 右侧译文（DeepSeek）')
  parser.add_argument('--src-dir', default='English', help='源目录（包含 .mtf）')
  parser.add_argument('--only-files', default='', help='仅处理这些文件（逗号分隔），如 "A.mtf,B.mtf"')
  parser.add_argument('--letters', default='', help='按文件名首字符筛选，如 "A_"（下划线与 A）')
  parser.add_argument('--max-workers', type=int, default=16, help='并行请求数')
  parser.add_argument('--timeout', type=int, default=60, help='HTTP 超时（秒）')
  parser.add_argument('--temperature', type=float, default=1.3, help='采样温度，翻译推荐 1.3')
  parser.add_argument('--max-tokens', type=int, default=400, help='回复最大 tokens（避免截断）')
  parser.add_argument('--dry-run', action='store_true', help='仅统计，不调用 API 不写入')
  parser.add_argument('--log-dir', default='logs/deepseek', help='日志目录（记录每行的输入/输出）')
  args = parser.parse_args()

  api_key = os.getenv('DEEPSEEK_API_KEY', '').strip()
  if not args.dry_run and not api_key:
    print('缺少 API 密钥，请设置环境变量 DEEPSEEK_API_KEY')
    return

  root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
  system_prompt = build_system_prompt(root)

  # 目标文件
  targets: List[str] = []
  only = [x.strip() for x in args.only_files.split(',') if x.strip()]
  if only:
    allset = set(os.listdir(args.src_dir))
    for name in only:
      if name in allset and name.endswith('.mtf'):
        targets.append(name)
      else:
        print(f"[提示] 未找到文件：{name}")
  else:
    letters = set((args.letters or '').lower())
    for name in sorted(os.listdir(args.src_dir)):
      if not name.endswith('.mtf'):
        continue
      if not letters or name[0].lower() in letters:
        targets.append(name)

  if not targets:
    print('未找到任何待处理文件')
    return

  # 干跑
  if args.dry_run:
    total = 0
    for name in targets:
      path = os.path.join(args.src_dir, name)
      pairs = read_pairs(path)
      n = sum(1 for _line, lhs, rhs in pairs if lhs and rhs)
      total += n
    print(f"[DRY] 待润色文件: {len(targets)}，合计行数: {total}")
    for name in targets:
      print(f"  - {name}")
    return

  # 预计算总行数用于 ETA
  total_lines = 0
  for name in targets:
    path = os.path.join(args.src_dir, name)
    pairs = read_pairs(path)
    total_lines += sum(1 for _line, lhs, rhs in pairs if lhs and rhs)
  print(f"[开始] 文件 {len(targets)} 个，总行数 {total_lines}")

  progress = {
    'start': time.time(),
    'done': 0.0,
    'total': float(total_lines),
    'files_done': 0.0,
    'files_total': float(len(targets)),
  }

  # 为本次运行创建独立日志目录（时间命名），便于定位本轮日志
  run_log_dir: Optional[str] = None
  if args.log_dir:
    run_log_dir = os.path.join(args.log_dir, time.strftime('%Y%m%d-%H%M%S'))
    try:
      os.makedirs(run_log_dir, exist_ok=True)
      print(f"[日志] 本次运行日志目录：{run_log_dir}")
    except Exception:
      run_log_dir = args.log_dir

  # 正式执行
  grand_ok = grand_fail = 0
  for name in targets:
    ok, fail = process_file(api_key, system_prompt, os.path.join(args.src_dir, name),
                            args.max_workers, args.timeout, args.temperature, args.max_tokens, run_log_dir, progress)
    grand_ok += ok; grand_fail += fail
  print(f"[完成] 成功 {grand_ok} 行，失败 {grand_fail} 行。")


if __name__ == '__main__':
  main()
