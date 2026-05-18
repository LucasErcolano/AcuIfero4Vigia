#!/usr/bin/env bash
echo "=== Probe specific model IDs ==="
for U in \
  "litert-community/gemma-4-27B-it-litert-lm" \
  "litert-community/gemma-4-A4B-it-litert-lm" \
  "litert-community/gemma-4-26B-A4B-litert-lm" \
  "litert-community/gemma-4-large-it-litert-lm" \
  "litert-community/gemma-4-27B-A4B-it-litert-lm"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "https://huggingface.co/api/models/$U")
  echo "$U => $code"
done
echo
echo "=== List all litert-community Gemma 4 ==="
curl -s "https://huggingface.co/api/models?author=litert-community&search=gemma-4" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for m in d:
    print(m.get('id'))
"
