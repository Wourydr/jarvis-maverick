import json

with open(r'C:\Users\LENOVO\.gemini\antigravity\brain\7304c75f-1a46-41d2-902b-0bad3fd477c5\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('step_index', 0) >= 860:
            if obj.get('source') == 'USER_EXPLICIT' or 'media' in obj:
                print('step:', obj.get('step_index'), 'source:', obj.get('source'), 'media:', obj.get('media'))
                print('content:', repr(obj.get('content', ''))[:100])
