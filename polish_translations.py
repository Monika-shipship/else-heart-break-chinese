import os
import re
import json
import time
import argparse
from typing import List, Tuple, Dict, Optional

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
  parser = argparse.ArgumentParser(description='Polish .mtf translations via Gemini/DeepSeek')
  parser.add_argument('--src-dir', default='English', help='Input folder containing .mtf files')
  parser.add_argument('--out-dir', default='Chinese', help='Output folder for polished files')
  parser.add_argument('--provider', choices=['gemini', 'deepseek'], required=False, help='LLM provider')
  parser.add_argument('--model', default=None, help='Model name (e.g., gemini-1.5-flash-latest, deepseek-chat)')
  parser.add_argument('--batch-size', type=int, default=20, help='Number of lines per request')
  parser.add_argument('--sleep', type=float, default=0.5, help='Sleep seconds between requests')
  parser.add_argument('--cache', default='.polish_cache.jsonl', help='Cache file (JSONL) for results/resume')
  parser.add_argument('--dry-run', action='store_true', help='Only show what would be processed (no API calls)')
  args = parser.parse_args()

  provider = args.provider or os.getenv('TRANSLATE_PROVIDER') or ''
  if not provider:
    print('Please specify --provider gemini|deepseek or set TRANSLATE_PROVIDER env var')
    return

  default_model = 'gemini-1.5-flash-latest' if provider == 'gemini' else 'deepseek-chat'
  model = args.model or os.getenv('TRANSLATE_MODEL') or default_model

  api_key_env = 'GEMINI_API_KEY' if provider == 'gemini' else 'DEEPSEEK_API_KEY'
  api_key = os.getenv(api_key_env, '')
  if not args.dry_run and not api_key:
    print(f'Missing API key. Set {api_key_env} env var.')
    return

  ensure_out_dir(args.out_dir)
  cache = load_cache(args.cache)

  for fname in sorted(os.listdir(args.src_dir)):
    if not fname.endswith('.mtf'):
      continue
    in_path = os.path.join(args.src_dir, fname)
    out_path = os.path.join(args.out_dir, fname)

    pairs = read_pairs_from_mtf(in_path)
    to_process_idx: List[int] = []
    batch_items: List[Tuple[str, str]] = []

    # Build worklist
    for idx, (line, src, dst) in enumerate(pairs):
      if not src and not dst:
        continue
      # key for cache: source + current target
      key = f'{src}\u0001{dst}'
      if key in cache:
        continue
      to_process_idx.append(idx)
      batch_items.append((src, dst))

    if args.dry_run:
      print(f'[DRY] {fname}: {len(batch_items)} lines to polish')
      # Still copy file as-is to out_dir for structure
      write_pairs_to_mtf(out_path, pairs)
      continue

    # Process in chunks
    cursor = 0
    for chunk in chunked(batch_items, args.batch_size):
      attempt = 0
      while True:
        try:
          results = polish_batch(provider, model, api_key, chunk)
          break
        except Exception as e:
          attempt += 1
          if attempt >= 3:
            raise
          time.sleep(1.5 * attempt)
      # Assign back
      for i, zh in enumerate(results):
        if i >= len(chunk):
          break
        global_index = to_process_idx[cursor + i]
        line, src, _old = pairs[global_index]
        # store result; keep only polished Chinese
        pairs[global_index] = (line, src, zh)
        cache_key = f'{src}\u0001{_old}'
        cache[cache_key] = zh
        append_cache(args.cache, cache_key, zh)
      cursor += len(chunk)
      time.sleep(args.sleep)

    # For any cached ones, fill them too
    for idx, (line, src, dst) in enumerate(pairs):
      if not src and not dst:
        continue
      key = f'{src}\u0001{dst}'
      if key in cache:
        pairs[idx] = (line, src, cache[key])

    write_pairs_to_mtf(out_path, pairs)
    print(f'Wrote {out_path}')


if __name__ == '__main__':
  main()

