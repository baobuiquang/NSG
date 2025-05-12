def str2pydata(s):
    import ast
    return ast.literal_eval(s)

def jsonfile2dict(pth):
    import json
    with open(pth, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# Extract the JSON dictionary from LLM string result, return None if cannot extract
def str2dict_advanced(s):
    start = s.find('{')
    end = s.rfind('}')
    if start == -1 or end == -1 or start > end:
        return None
    else:
        res = s[start:end+1]
        res = str2pydata(res)
        if isinstance(res, dict):
            return res
        else:
            return None

# Beautify for print
def dict2str(d):
    import json
    return json.dumps(d, indent=4, ensure_ascii=False)
def list2str(l):
    return "\n".join([str(e) for e in l])